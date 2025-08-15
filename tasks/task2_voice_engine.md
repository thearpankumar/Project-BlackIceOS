# Task 2: Voice Recognition Engine

## What This Task Is About
This task creates the voice interface for Kali AI-OS that enables natural language interaction with security tools. The implementation uses an online service for high-accuracy speech recognition, a local wake word engine, and a local engine for voice feedback.
- **Wake Word Detection** using `pvporcupine` to activate the AI without manual input (e.g., "Computer").
- **Voice-to-Text Recognition** using `google-generativeai` for highly accurate, online transcription.
- **Local Audio Recording** to capture the user's voice commands directly from the microphone after the wake word is detected.
- **Local Text-to-Speech** using the system's native voice engine via `pyttsx3` for feedback.
- **Intelligent Command Parsing** where the powerful `google-generativeai` model directly interprets security terms and extracts parameters, removing the need for a custom cybersecurity vocabulary.

## Why This Task Is Critical
- **Natural Interface**: Enables hands-free operation during security assessments.
- **Accessibility**: Voice commands are faster than typing complex security tool syntax.
- **Multitasking**: Users can continue working while giving voice commands.
- **Unique Selling Point**: A voice-controlled cybersecurity OS.

## How to Complete This Task - Step by Step

### Phase 1: Setup Voice Environment (45 minutes)
```bash
# 1. Install system audio dependencies (in VM)
sudo apt update
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y espeak espeak-data libespeak-dev # For pyttsx3

# 2. Setup Python environment with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv add google-generativeai sounddevice scipy numpy pyttsx3 python-dotenv pvporcupine pyaudio
uv add pytest pytest-asyncio pytest-mock --dev
uv sync --all-extras

# 3. Test audio system
arecord -l  # List recording devices
aplay -l   # List playback devices
arecord -f cd -t wav -d 5 test.wav && aplay test.wav  # Test microphone

# 4. Configure API Keys for Development
# In the final system, API keys will be provided by the auth server.
# For local development, you will need to create a .env file in the project root.
# The auth server task (.env.example) defines the production variables.
# For this task, you can create a separate .env with these keys:
echo 'GOOGLE_AI_API_KEY="YOUR_GOOGLE_AI_API_KEY"' > .env
echo 'PICOVOICE_ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY"' >> .env
# Get a free PicoVoice Access Key from https://console.picovoice.ai/
```

### Phase 2: Write Voice Tests First (1 hour)
```python
# tests/voice/test_recognition.py - Create comprehensive tests
import pytest
from unittest.mock import patch, MagicMock

def test_wake_word_detection_initialization():
    """Test that the wake word detector initializes correctly."""
    # This test would verify that pvporcupine is called with the correct keys.

@patch('sounddevice.rec')
@patch('sounddevice.wait')
def test_audio_recording(mock_wait, mock_rec):
    """Test that audio is recorded correctly from the microphone."""
    # Test recording a short audio clip and verify the file is created and parameters are correct.

def test_speech_to_text_transcription():
    """Test basic speech-to-text with Google GenAI."""
    # Test with a pre-recorded audio sample of a security command.

def test_local_text_to_speech_generation():
    """Test local text-to-speech generation."""
    # Test that pyttsx3 can generate audible speech from text.
```

### Phase 3: Core Implementation (3 hours)
```python
# src/voice/recognition/audio_processor.py
# (This is a more detailed implementation plan)
import os
import struct
import sounddevice as sd
from scipy.io.wavfile import write
import google.generativeai as genai
import pyttsx3
import pvporcupine
import pyaudio
from dotenv import load_dotenv

class AudioProcessor:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.picovoice_key = os.getenv("PICOVOICE_ACCESS_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_AI_API_KEY not found. Please set it in your .env file.")
        genai.configure(api_key=self.api_key)

        self.stt_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        self.tts_engine = pyttsx3.init()

    def listen_for_wake_word(self):
        # ... implementation ...

    def record_audio(self, filename="command.wav", duration=5, sr=44100):
        # ... implementation ...

    def transcribe_audio(self, audio_file_path: str) -> str:
        # ... implementation ...

    def speak_text(self, text: str):
        # ... implementation ...

    def process_voice_command(self, duration=5):
        # ... implementation ...
```

### Phase 4: Integration & Testing (1 hour)
```python
# main.py - Example usage
from src.voice.recognition.audio_processor import AudioProcessor

def main():
    processor = AudioProcessor()

    # Listen for wake word, then get a voice command
    processor.speak_text("I am ready. Say the wake word to begin.")
    command = processor.process_voice_command(duration=5)

    # The 'command' text can now be sent to the AI processing layer (Task 4)
    processor.speak_text(f"Executing command: {command}")

if __name__ == "__main__":
    main()
```

## Overview
Build a voice recognition system using `pvporcupine` for wake word detection, `google-generativeai` for online speech-to-text, and `pyttsx3` for local text-to-speech. This system runs in the Kali AI-OS VM and processes voice commands for security operations.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── voice/
│   │   │   ├── __init__.py
│   │   │   ├── recognition/
│   │   │   │   ├── __init__.py
│   │   │   │   └── audio_processor.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       └── audio_config.py
│   │   └── tests/
│   │       ├── voice/
│   │       │   ├── __init__.py
│   │       │   ├── test_recognition.py
│   │       │   └── test_audio_samples/
│   │       │       └── test_command.wav
│   └── requirements/
│       └── voice_requirements.txt
```

## Technology Stack
- **Wake Word Detection**: `pvporcupine`
- **STT Engine**: `google-generativeai` (online recognition)
- **Audio Recording**: `sounddevice`, `scipy`, `numpy`, `pyaudio`
- **Text-to-Speech**: `pyttsx3`, `espeak`
- **Development**: `uv`, `pytest`, `pytest-mock`

## Implementation Requirements

### Core Components

#### 1. Wake Word Detection
```python
# src/voice/recognition/audio_processor.py (listen_for_wake_word method)
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
        porcupine = pvporcupine.create(access_key=self.picovoice_key, keywords=['computer'])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
            input=True, frames_per_buffer=porcupine.frame_length
        )
        print("--- Listening for wake word ('computer') ---")
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                print("Wake word detected!")
                break
    finally:
        if porcupine: porcupine.delete()
        if audio_stream: audio_stream.close()
        if pa: pa.terminate()
```

#### 2. Speech-to-Text (STT)
```python
# src/voice/recognition/audio_processor.py (transcribe_audio method)
def transcribe_audio(self, audio_file_path: str) -> str:
    """Transcribes audio file to text using Google GenAI."""
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
```

## Testing Strategy

### Unit Tests (80% coverage minimum)
```bash
# Run voice recognition tests using uv
uv run pytest tests/voice/ -v --cov=src.voice --cov-report=html

# Expected test categories:
# - Wake word detection initialization and processing (mocked)
# - Audio recording parameters and file output
# - STT transcription accuracy with sample files
# - TTS speech generation
# - Graceful error handling for API failures
```
```python
# tests/voice/test_recognition.py
import pytest
from unittest.mock import patch, MagicMock
from src.voice.recognition.audio_processor import AudioProcessor

@patch('pvporcupine.create')
def test_wake_word_initialization(mock_pv_create):
    """Test that pvporcupine is initialized with the correct access key and keywords."""
    processor = AudioProcessor()
    processor.listen_for_wake_word()
    mock_pv_create.assert_called_with(access_key=processor.picovoice_key, keywords=['computer'])

@patch('google.generativeai.GenerativeModel.generate_content')
def test_transcription_api_call(mock_generate_content):
    """Test that the Google GenAI API is called correctly."""
    # Mock the response from the API
    mock_response = MagicMock()
    mock_response.text = "scan example.com"
    mock_generate_content.return_value = mock_response

    processor = AudioProcessor()
    # Assume 'test.wav' is a valid dummy file
    result = processor.transcribe_audio('test.wav')

    assert result == "scan example.com"
    mock_generate_content.assert_called_once()
```

### Integration Tests
- Test the full pipeline: wake word -> record -> transcribe -> speak.
- Test with a real microphone in the VM to ensure audio hardware is correctly configured.
- Test failure modes, such as an invalid Google API key or no internet connection.

## VM Integration

### Audio System Setup in Kali VM
```bash
# Install audio dependencies in VM
sudo apt update
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y espeak espeak-data libespeak-dev

# Configure audio passthrough from host
echo "load-module module-udev-detect" >> ~/.config/pulse/default.pa
echo "load-module module-native-protocol-unix" >> ~/.config/pulse/default.pa

# Test audio setup
arecord -l  # List recording devices
aplay -l   # List playback devices
arecord -f cd -t wav -d 5 test.wav && aplay test.wav
```

## Deployment & Testing

### Setup Commands with uv
```bash
# 1. Install all dependencies
uv sync --all-extras

# 2. Configure API keys in .env file
# (As described in Phase 1)

# 3. Run comprehensive tests
uv run pytest tests/voice/ -v
```

### Validation Criteria
✅ **Must pass before considering task complete:**

1.  **Functionality Tests**
    -   Wake word detection works reliably.
    -   STT recognizes cybersecurity terms accurately (>95%).
    -   Audio is recorded clearly.
    -   TTS output is clear and understandable.
    -   Full listen -> record -> transcribe -> speak loop works.

2.  **Integration Tests**
    -   Correctly uses API keys from the environment.
    -   Handles potential network errors gracefully when calling the Google API.
    -   Handles missing PicoVoice key by falling back to manual start.

3.  **Performance Tests**
    -   Recognition latency (including network) is under 3 seconds for a 5-second clip.
    -   Wake word listener has low, constant CPU overhead.

### Success Metrics
- ✅ 95%+ wake word detection accuracy.
- ✅ 95%+ cybersecurity term recognition accuracy.
- ✅ <3s voice processing latency (post-recording).
- ✅ All integration tests pass.
- ✅ Audio system configured and working in the VM.

## Configuration Files

### voice_requirements.txt
```txt
# Voice Recognition & AI
google-generativeai
python-dotenv

# Wake Word
pvporcupine
pyaudio

# Audio Recording
sounddevice
scipy
numpy

# Text-to-Speech
pyttsx3

# Testing
pytest
pytest-asyncio
pytest-mock
```

### Audio Configuration
```python
# src/voice/config/audio_config.py
AUDIO_CONFIG = {
    'sample_rate': 44100,
    'record_duration_seconds': 5,
    'channels': 1,
    'wake_words': ['computer'],
    'wake_word_sensitivity': 0.5
}
```

## Next Steps
After completing this task:
1.  Integrate the transcribed text output with the AI Processing Layer (Task 4).
2.  Proceed to Task 3: Desktop Automation Core.
