import os
import queue
import struct

import google.generativeai as genai
import noisereduce as nr
import numpy as np
import pvporcupine
import pyaudio
import pyttsx3
import sounddevice as sd
import webrtcvad
from dotenv import load_dotenv
from scipy.io.wavfile import write


class AudioProcessor:
    def __init__(self, sr=16000, vad_aggressiveness=3, silence_duration=3.0):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.picovoice_key = os.getenv("PICOVOICE_ACCESS_KEY")

        if not self.api_key:
            raise ValueError(
                "GOOGLE_AI_API_KEY not found. Please set it in your .env file."
            )
        genai.configure(api_key=self.api_key)

        self.stt_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        self.tts_engine = pyttsx3.init()

        self.sr = sr
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.silence_duration = silence_duration
        self.frame_duration = 30  # VAD frame duration in ms
        self.frame_size = int(self.sr * self.frame_duration / 1000)
        self.audio_queue = queue.Queue()
        self.noise_profile = None

    def _calibrate_noise(self):
        """Listens for a short period to create a noise profile."""
        print("Calibrating for ambient noise... Please be quiet for 2 seconds.")
        noise_frames = []
        with sd.InputStream(
            samplerate=self.sr, channels=1, dtype="int16", blocksize=self.frame_size
        ):
            for _ in range(int(2000 / self.frame_duration)):  # 2 seconds of audio
                noise_frames.append(
                    sd.rec(
                        self.frame_size, samplerate=self.sr, channels=1, dtype="int16"
                    )
                )

        noise_sample = np.concatenate(noise_frames, axis=0).flatten()
        self.noise_profile = nr.reduce_noise(
            y=noise_sample, sr=self.sr, stationary=True
        )
        print("Calibration complete.")

    def listen_for_wake_word(self):
        """Listens for a wake word and returns when one is detected."""
        if not self.picovoice_key:
            print("PICOVOICE_ACCESS_KEY not set. Manual start required.")
            input("Press Enter to start recording...")
            return

        porcupine = None
        audio_stream = None
        pa = None
        try:
            porcupine = pvporcupine.create(
                access_key=self.picovoice_key, keywords=["computer"]
            )
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
            )
            print("--- Listening for wake word ('computer') ---")
            while True:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                if porcupine.process(pcm) >= 0:
                    print("Wake word detected!")
                    break
        finally:
            if porcupine:
                porcupine.delete()
            if audio_stream:
                audio_stream.close()
            if pa:
                pa.terminate()

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, flush=True)

        # Perform noise reduction
        reduced_noise_frame = nr.reduce_noise(
            y=indata.flatten(), sr=self.sr, y_noise=self.noise_profile
        )
        self.audio_queue.put(reduced_noise_frame.astype(np.int16))

    def record_audio(self, filename="command.wav"):
        """
        Waits for speech to start, then records until a 3-second silence is detected using VAD.
        """
        self.audio_queue = queue.Queue()

        with sd.InputStream(
            samplerate=self.sr,
            channels=1,
            dtype="int16",
            blocksize=self.frame_size,
            callback=self._audio_callback,
        ):
            print("Listening for command... (you have 5s to start)")

            # 1. Wait for speech to start
            frames = []
            try:
                while True:
                    frame = self.audio_queue.get(timeout=5)
                    is_speech = self.vad.is_speech(frame.tobytes(), self.sr)
                    if is_speech:
                        print("Speech detected, starting recording.")
                        frames.append(frame)
                        break
            except queue.Empty:
                print("No speech detected within the timeout period.")
                self.speak_text("I didn't hear anything. Please try again.")
                return False

            # 2. Record until silence is detected
            silent_frames = 0
            num_silent_frames_to_stop = int(
                self.silence_duration * 1000 / self.frame_duration
            )

            while True:
                try:
                    frame = self.audio_queue.get(timeout=self.silence_duration + 0.5)
                    frames.append(frame)
                    is_speech = self.vad.is_speech(frame.tobytes(), self.sr)

                    if not is_speech:
                        silent_frames += 1
                    else:
                        silent_frames = 0

                    if silent_frames >= num_silent_frames_to_stop:
                        print(
                            f"Silence of {self.silence_duration}s detected, stopping recording."
                        )
                        break
                except queue.Empty:
                    print("Recording finished due to timeout (silence).")
                    break

        recording = np.concatenate(frames, axis=0)
        write(filename, self.sr, recording)
        print(f"Recording saved to {filename}")
        return True

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribes audio file to text using Google GenAI."""
        if not os.path.exists(audio_file_path):
            return "Error: No audio was recorded."
        try:
            print("Uploading and transcribing audio...")
            audio_file = genai.upload_file(path=audio_file_path)
            response = self.stt_model.generate_content(
                ["Transcribe the following audio:", audio_file]
            )
            return response.text
        except Exception as e:
            print(f"Error during transcription: {e}")
            return "Error: Could not transcribe audio."

    def speak_text(self, text: str):
        print(f"Speaking: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def process_voice_command(self):
        if self.noise_profile is None:
            self._calibrate_noise()
        self.listen_for_wake_word()
        if self.record_audio():
            transcribed_text = self.transcribe_audio("command.wav")
            return transcribed_text
        return "No command processed."
