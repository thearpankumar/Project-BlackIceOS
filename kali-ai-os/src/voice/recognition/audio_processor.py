import os
import tempfile
from typing import Any

import google.generativeai as genai
import numpy as np
import pyttsx3
import sounddevice as sd
from dotenv import load_dotenv
from scipy.io.wavfile import write  # type: ignore[import-untyped]


class SimpleAudioProcessor:
    """Simplified audio processor without wake word detection - button-based recording only"""

    def __init__(self, sample_rate: int = 16000) -> None:
        load_dotenv()
        # Try GOOGLE_AI_API_KEY first, then fallback to GEMINI_API_KEY for compatibility
        self.api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key not found. Please set either GOOGLE_AI_API_KEY or"
                " GEMINI_API_KEY in your .env file."
            )
        genai.configure(api_key=self.api_key)

        self.stt_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        self.tts_engine = pyttsx3.init()
        self.sample_rate = sample_rate
        self.is_recording = False
        self.recording_data: list[Any] = []

    def start_recording(self) -> None:
        """Start recording audio data"""
        self.is_recording = True
        self.recording_data = []
        print("Started recording audio...")

    def stop_recording(self) -> None:
        """Stop recording audio data"""
        self.is_recording = False
        print("Stopped recording audio...")

    def record_audio_data(
        self, indata: np.ndarray, frames: int, time: object, status: sd.CallbackFlags
    ) -> None:
        """Callback function to collect audio data during recording"""
        if self.is_recording:
            self.recording_data.append(indata.copy())

    def save_recording(self, filename: str | None = None) -> str | None:
        """Save recorded audio to file"""
        if not self.recording_data:
            return None

        if filename is None:
            filename = os.path.join(tempfile.gettempdir(), "voice_recording.wav")

        try:
            # Convert to numpy array and save as wav
            audio_data = np.concatenate(self.recording_data, axis=0)

            # Convert to int16 for wav file
            audio_int16 = (audio_data * 32767).astype(np.int16)
            write(filename, self.sample_rate, audio_int16)

            print(f"Recording saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving recording: {e}")
            return None

    def transcribe_audio_file(self, audio_file_path: str) -> str:
        """Transcribes audio file to text using Google GenAI"""
        if not os.path.exists(audio_file_path):
            return "Error: Audio file not found."

        try:
            print("Transcribing audio with LLM...")

            # Read audio file as bytes
            with open(audio_file_path, 'rb') as f:
                audio_content = f.read()

            # Send to LLM for transcription
            prompt = (
                "Please transcribe this audio to text. Only return the transcribed"
                " text, nothing else."
            )
            response = self.stt_model.generate_content(
                [prompt, {"mime_type": "audio/wav", "data": audio_content}]
            )

            transcribed_text = str(response.text).strip() if response.text else ""
            print(f"Transcribed: '{transcribed_text}'")
            return transcribed_text

        except Exception as e:
            print(f"Error during transcription: {e}")
            return "Error: Could not transcribe audio."

    def transcribe_recording(self) -> str:
        """Transcribe the current recording"""
        if not self.recording_data:
            return "Error: No audio recorded."

        # Save recording to temporary file
        temp_file = self.save_recording()
        if not temp_file:
            return "Error: Could not save recording."

        try:
            # Transcribe the file
            result = self.transcribe_audio_file(temp_file)

            # Clean up temporary file
            os.remove(temp_file)

            return result
        except Exception as e:
            return f"Error: {e}"

    def speak_text(self, text: str) -> None:
        """Convert text to speech"""
        try:
            print(f"Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def record_and_transcribe(self, duration: float = 5.0) -> str:
        """Simple recording method for testing - records for specified duration"""
        print(f"Recording for {duration} seconds...")

        try:
            # Record audio for specified duration
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
            )
            sd.wait()  # Wait until recording is finished

            # Save to temporary file
            temp_file = os.path.join(tempfile.gettempdir(), "test_recording.wav")
            audio_int16 = (recording * 32767).astype(np.int16)
            write(temp_file, self.sample_rate, audio_int16.flatten())

            # Transcribe
            result = self.transcribe_audio_file(temp_file)

            # Clean up
            os.remove(temp_file)

            return result

        except Exception as e:
            return f"Error during recording: {e}"


# Maintain backward compatibility - alias the old name
AudioProcessor = SimpleAudioProcessor
