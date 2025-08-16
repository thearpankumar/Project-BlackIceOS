# Task 2: Voice Interface Integration

## What This Task Is About
This task creates the voice interface for Samsung AI-OS that enables natural language interaction with security tools through a simple, GUI-based approach integrated directly into the main application.
- **GUI Voice Button** - Simple 🎤 Voice Command button in the main interface
- **Direct Gemini Integration** - Voice recordings sent directly to Google Gemini API for transcription
- **Real-time Processing** - Commands processed through the same pipeline as text input
- **Seamless Integration** - Voice commands trigger the same desktop automation as text commands

## Why This Task Is Critical
- **Natural Interface**: Enables hands-free operation during security assessments
- **Simplicity**: No complex wake word detection or audio processing pipeline needed
- **Integration**: Voice commands work through existing text command infrastructure
- **User Experience**: Intuitive GUI button for voice activation

## How to Complete This Task - Step by Step

### Phase 1: Environment Setup (15 minutes)
```bash
# 1. Basic audio system setup (minimal requirements)
sudo apt update
sudo apt install -y python3-sounddevice alsa-utils

# 2. Test audio recording capability
arecord -l  # List recording devices
python3 -c "import sounddevice; print('Audio system ready')"

# 3. Verify API key configuration
# Voice processing uses the same Google AI API key as text processing
# Configured in main .env file:
echo 'GOOGLE_AI_API_KEY="YOUR_GOOGLE_AI_API_KEY"' >> .env
```

### Phase 2: Voice Integration Implementation (45 minutes)
```python
# Integration with main.py GUI - Voice button functionality

def toggle_voice_recording(self):
    """Handle voice button click - start/stop recording"""
    if not self.is_recording:
        # Start voice recording
        self.is_recording = True
        self.voice_button.config(
            text="🛑 Stop Recording",
            bg='#dc3545'
        )

        # Start recording in background thread
        def record_audio():
            try:
                # Record audio using sounddevice
                def audio_callback(indata, frames, time, status):
                    if self.is_recording:
                        self.recording_data.append(indata.copy())

                # Start audio stream
                stream = sd.InputStream(callback=audio_callback)
                stream.start()

                # Wait for recording to stop
                while self.is_recording:
                    time.sleep(0.1)

                stream.stop()

            except Exception as e:
                self.log_message(f"Recording error: {e}", 'ERROR')

        threading.Thread(target=record_audio, daemon=True).start()

    else:
        # Stop recording and process with Gemini
        self.is_recording = False
        self.process_voice_with_gemini()

def process_voice_with_gemini(self):
    """Process recorded audio with Gemini API"""
    try:
        # Convert recording data to audio file
        audio_data = np.concatenate(self.recording_data)

        # Save as temporary WAV file
        temp_file = "/tmp/voice_command.wav"
        sf.write(temp_file, audio_data, 44100)

        # Upload to Gemini for transcription
        audio_file = genai.upload_file(path=temp_file)
        response = self.ai_model.generate_content([
            "Transcribe this audio clearly:",
            audio_file
        ])

        # Process transcribed text as command
        transcribed_text = response.text.strip()
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, transcribed_text)

        # Execute the command automatically
        self.process_command()

    except Exception as e:
        self.log_message(f"Voice processing error: {e}", 'ERROR')
    finally:
        # Reset voice button
        self.voice_button.config(
            text="🎤 Voice Command",
            bg='#1e7ce8'
        )
```

### Phase 3: Testing Voice Integration (30 minutes)
```python
# tests/voice/test_voice_integration.py
import pytest
from unittest.mock import patch, MagicMock

def test_voice_button_functionality():
    """Test voice button toggles recording state"""
    # Test button text changes when recording starts/stops
    # Test recording state management

@patch('sounddevice.InputStream')
def test_audio_recording_integration(mock_stream):
    """Test audio recording through sounddevice"""
    # Test recording starts and captures audio data
    # Test recording stops cleanly

@patch('google.generativeai.upload_file')
@patch('google.generativeai.GenerativeModel.generate_content')
def test_gemini_transcription(mock_generate, mock_upload):
    """Test Gemini API integration for voice transcription"""
    mock_response = MagicMock()
    mock_response.text = "open terminal and scan 192.168.1.1"
    mock_generate.return_value = mock_response

    # Test voice file upload and transcription
    # Test transcribed text integration with command system

def test_voice_command_execution():
    """Test voice commands trigger same actions as text commands"""
    # Test voice "open terminal" = text "open terminal"
    # Test command processing pipeline integration
```

### Phase 4: User Experience & Validation (15 minutes)
```python
# Voice command examples that work through the GUI:

# User clicks 🎤 Voice Command button
# Records: "open terminal and run nmap scan on 192.168.1.1"
# System transcribes and executes automatically

# User clicks 🎤 Voice Command button
# Records: "launch burp suite and configure proxy"
# System processes as text command

# User clicks 🎤 Voice Command button
# Records: "take a screenshot of the current desktop"
# System captures AI desktop screenshot

# Integration validation:
# 1. Voice button appears in main GUI
# 2. Recording works without audio setup complexity
# 3. Gemini transcription is accurate for security terms
# 4. Voice commands execute same as text commands
# 5. Error handling works for poor audio/network issues
```

## Overview
Build a simple, GUI-integrated voice interface using `sounddevice` for audio recording and `google-generativeai` for direct speech-to-text transcription. This system is embedded in the main Samsung AI-OS GUI and processes voice commands through the existing text command pipeline.

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
- **GUI Integration**: `tkinter` (built into main.py)
- **Audio Recording**: `sounddevice` (simple recording)
- **Speech-to-Text**: `google-generativeai` (direct transcription)
- **File Handling**: `soundfile` (WAV file creation)
- **Development**: `pytest` (simple integration tests)

## Implementation Requirements

### Core Components

#### 1. Voice Button Integration
```python
# Integration with main.py GUI - Voice button in tkinter interface
def setup_voice_interface(self):
    """Setup voice button in main GUI"""
    self.voice_button = tk.Button(
        self.button_frame,
        text="🎤 Voice Command",
        command=self.toggle_voice_recording,
        bg='#1e7ce8',
        fg='white',
        font=('Arial', 10, 'bold'),
        relief='raised',
        borderwidth=2
    )
    self.voice_button.grid(row=0, column=4, padx=5, pady=5)

    # Initialize voice recording state
    self.is_recording = False
    self.recording_data = []
```

#### 2. Simple Audio Recording
```python
# Direct audio recording with sounddevice - no complex processing
def start_voice_recording(self):
    """Start recording audio using sounddevice"""
    try:
        import sounddevice as sd
        import soundfile as sf

        # Configure recording parameters
        duration = 10  # Maximum 10 seconds
        sample_rate = 44100

        # Record audio
        audio_data = sd.rec(int(duration * sample_rate),
                           samplerate=sample_rate,
                           channels=1,
                           dtype='float64')

        # Save as temporary file
        temp_file = "/tmp/voice_command.wav"
        sf.write(temp_file, audio_data, sample_rate)

        return temp_file

    except Exception as e:
        self.log_message(f"Recording error: {e}", 'ERROR')
        return None
```

## Testing Strategy

### Unit Tests (20% coverage minimum - matching current codebase standards)
```bash
# Run voice integration tests using uv
uv run pytest tests/voice/ -v --cov=src.voice --cov-report=html

# Expected test categories:
# - Voice button functionality and state management
# - Audio recording with sounddevice (mocked)
# - Gemini API transcription integration
# - Error handling for recording/network failures
```
```python
# tests/voice/test_voice_integration.py
import pytest
from unittest.mock import patch, MagicMock

@patch('sounddevice.rec')
@patch('soundfile.write')
def test_audio_recording(mock_sf_write, mock_sd_rec):
    """Test audio recording functionality"""
    # Mock audio data
    mock_audio_data = [[0.1], [0.2], [0.3]]
    mock_sd_rec.return_value = mock_audio_data

    # Test recording process
    from main import VoiceInterface  # Assuming integration in main.py
    voice = VoiceInterface()
    temp_file = voice.start_voice_recording()

    assert temp_file == "/tmp/voice_command.wav"
    mock_sd_rec.assert_called_once()
    mock_sf_write.assert_called_once_with("/tmp/voice_command.wav", mock_audio_data, 44100)

@patch('google.generativeai.upload_file')
@patch('google.generativeai.GenerativeModel.generate_content')
def test_gemini_transcription(mock_generate, mock_upload):
    """Test Gemini API transcription"""
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = "open terminal and run nmap scan"
    mock_generate.return_value = mock_response

    from main import VoiceInterface
    voice = VoiceInterface()
    result = voice.process_voice_with_gemini("/tmp/test.wav")

    assert result == "open terminal and run nmap scan"
    mock_upload.assert_called_once_with(path="/tmp/test.wav")
    mock_generate.assert_called_once()
```

### Integration Tests
- Test the complete workflow: button click -> record -> transcribe -> command execution
- Test audio system availability in VM environment
- Test graceful fallback when audio hardware unavailable
- Test network failure handling for Gemini API calls

## VM Integration

### Minimal Audio System Setup
```bash
# Install minimal audio dependencies for recording
sudo apt update
sudo apt install -y python3-sounddevice alsa-utils

# Test basic audio recording capability
arecord -l  # List recording devices
python3 -c "import sounddevice; print('Audio system ready')"

# Simple recording test
python3 -c "
import sounddevice as sd
import soundfile as sf
print('Recording 3 seconds...')
audio = sd.rec(int(3 * 44100), samplerate=44100, channels=1)
sd.wait()
sf.write('test.wav', audio, 44100)
print('Recording saved to test.wav')
"
```

## Deployment & Testing

### Setup Commands with uv
```bash
# 1. Install voice dependencies
uv add sounddevice soundfile
uv sync

# 2. Verify API key configuration
# Voice uses same Google AI API key as main application
echo 'GOOGLE_AI_API_KEY="YOUR_API_KEY"' >> .env

# 3. Test audio system
python3 -c "import sounddevice; print('Audio ready')"

# 4. Run voice integration tests
uv run pytest tests/voice/ -v
```

### Validation Criteria
✅ **Must pass before considering task complete:**

1.  **Functionality Tests**
    -   Voice button appears and toggles recording state correctly
    -   Audio recording works without complex setup
    -   Gemini transcription accurately processes security commands
    -   Transcribed text integrates with existing command pipeline
    -   Voice commands execute same actions as text commands

2.  **Integration Tests**
    -   Uses existing Google AI API key from .env file
    -   Handles network errors gracefully during transcription
    -   Works with existing GUI layout and design
    -   Integrates seamlessly with current authentication system

3.  **Performance Tests**
    -   Voice processing completes within 5 seconds for 10-second clips
    -   No impact on main application responsiveness
    -   Minimal memory overhead during recording

### Success Metrics
- ✅ Voice button functional in main GUI
- ✅ 90%+ transcription accuracy for security commands
- ✅ <5s total voice processing time
- ✅ Seamless integration with existing command system
- ✅ Zero complex audio processing dependencies

## Configuration Files

### Voice Dependencies (added to main pyproject.toml)
```toml
# Add to existing dependencies in pyproject.toml
[project]
dependencies = [
    # ... existing dependencies ...
    "sounddevice>=0.4.0",
    "soundfile>=0.12.0",
    # google-generativeai already included
]
```

### Voice Configuration
```python
# Voice settings integrated into main.py configuration
VOICE_CONFIG = {
    'sample_rate': 44100,
    'max_duration_seconds': 10,
    'channels': 1,
    'temp_file_path': '/tmp/voice_command.wav',
    'button_text_recording': '🛑 Stop Recording',
    'button_text_idle': '🎤 Voice Command'
}
```

## Next Steps
After completing this task:
1. Voice commands integrate directly with existing command processing pipeline
2. Proceed to Task 3: Desktop Automation Core with template → agentic AI evolution
3. Future enhancement: Direct screenshot-to-AI decision making replaces current hybrid approach
