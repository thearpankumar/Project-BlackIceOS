# Task 2: Voice Recognition Engine

## What This Task Is About
This task creates the voice interface for Kali AI-OS that enables natural language interaction with security tools:
- **Voice-to-Text Recognition** using Vosk (offline, no internet required)
- **Cybersecurity Vocabulary** for accurate recognition of security terms like "nmap", "burpsuite", "metasploit"
- **Wake Word Detection** to activate AI without manual input ("Hey Kali", "Security AI")
- **Noise Filtering** for use in various environments (offices, coffee shops, conferences)
- **Real-time Processing** with low latency for responsive interaction

## Why This Task Is Critical
- **Natural Interface**: Enables hands-free operation during security assessments
- **Accessibility**: Voice commands are faster than typing complex security tool syntax
- **Multitasking**: Users can continue working while giving voice commands
- **Unique Selling Point**: First voice-controlled cybersecurity OS

## How to Complete This Task - Step by Step

### Phase 1: Setup Voice Environment (45 minutes)
```bash
# 1. Install system audio dependencies (run in VM)
sudo apt update
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y espeak espeak-data libespeak-dev

# 2. Setup Python environment with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv add vosk pyaudio speech-recognition
uv add pytest pytest-asyncio --dev
uv sync --all-extras

# 3. Test audio system
arecord -l  # List recording devices
aplay -l   # List playback devices
arecord -f cd -t wav -d 5 test.wav && aplay test.wav  # Test microphone

# 4. Download Vosk model
cd kali-ai-os/src/voice/models/
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
mv vosk-model-en-us-0.22 vosk-model-en-us
```

### Phase 2: Write Voice Tests First (1 hour)
```python
# tests/voice/test_recognition.py - Create comprehensive tests
def test_basic_speech_recognition():
    """Test basic speech-to-text works"""
    # Test with clean audio sample

def test_cybersecurity_term_recognition():
    """Test recognition of security terms"""
    # Test: "nmap", "burpsuite", "metasploit", "wireshark"

def test_wake_word_detection():
    """Test wake word detection accuracy"""
    # Test: "hey kali", "kali ai", "security ai"

def test_noise_filtering():
    """Test noise reduction improves accuracy"""
    # Test with noisy vs clean audio

def test_parameter_extraction():
    """Test extracting IPs, URLs, ports from voice"""
    # Test: "scan 192.168.1.1 for open ports"
```

### Phase 3: Core Voice Recognition (2 hours)
```python
# src/voice/recognition/vosk_engine.py
import vosk
import json
import pyaudio

class VoskSTTEngine:
    def __init__(self, model_path):
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, 16000)

    def transcribe_real_time(self, audio_stream):
        # Implement real-time transcription
        # Return: {"text": "scan example.com", "confidence": 0.95}

    def transcribe_file(self, audio_file):
        # Implement file-based transcription for testing
        # Return: {"text": "...", "confidence": 0.85, "success": True}
```

### Phase 4: Cybersecurity Vocabulary (1 hour)
```python
# src/voice/vocabulary/cybersec_terms.py
class CybersecurityVocabulary:
    def __init__(self):
        self.security_tools = {
            # Common voice recognition errors -> correct terms
            "map": "nmap",
            "burp sweet": "burpsuite",
            "wire shark": "wireshark",
            "metal split": "metasploit",
            "nick to": "nikto"
        }

    def correct_terms(self, text):
        # Fix common voice recognition errors
        # "map scan example.com" -> "nmap scan example.com"

    def extract_parameters(self, text):
        # Extract IPs, domains, ports from voice command
        # "scan 192.168.1.1 port 80" -> {"ips": ["192.168.1.1"], "ports": [80]}
```

### Phase 5: Wake Word Detection (1 hour)
```python
# src/voice/recognition/wake_word_detector.py
import pvporcupine

class WakeWordDetector:
    def __init__(self, wake_words=["hey kali", "kali ai"]):
        # Initialize Picovoice Porcupine for wake word detection
        self.wake_words = wake_words

    def detect_wake_word(self, audio_chunk):
        # Return True if wake word detected
        # Enable continuous listening mode

    def continuous_listen(self):
        # Background thread listening for wake words
        # Activate voice recognition when detected
```

### Phase 6: Noise Filtering (45 minutes)
```python
# src/voice/recognition/noise_filter.py
import noisereduce as nr
import librosa

class NoiseFilter:
    def reduce_noise(self, audio_data):
        # Apply noise reduction algorithms
        # Improve speech clarity for better recognition

    def enhance_speech(self, audio_data):
        # Enhance speech frequencies
        # Suppress background noise
```

### Phase 7: Integration & Testing (1 hour)
```python
# src/voice/recognition/audio_processor.py - Main integration class
class AudioProcessor:
    def __init__(self):
        self.stt_engine = VoskSTTEngine("models/vosk-model-en-us")
        self.wake_detector = WakeWordDetector()
        self.vocab = CybersecurityVocabulary()
        self.noise_filter = NoiseFilter()

    async def process_voice_command(self, audio_input):
        # Complete pipeline:
        # 1. Noise filtering
        # 2. Speech recognition
        # 3. Vocabulary correction
        # 4. Parameter extraction
        # Return processed command ready for AI layer
```

### Phase 8: Performance Optimization (30 minutes)
```bash
# Test recognition speed and accuracy
python -c "
from src.voice.recognition.audio_processor import AudioProcessor
import time

processor = AudioProcessor()
start = time.time()
result = processor.process_voice_command('test_audio.wav')
print(f'Processing time: {time.time() - start:.2f}s')
print(f'Recognition result: {result}')
"

# Optimize for:
# - <300ms processing latency
# - >90% accuracy on security terms
# - >95% wake word detection accuracy
```

## Overview
Build a sophisticated voice recognition system with cybersecurity-specific vocabulary, wake word detection, and noise filtering. This system runs in the Kali AI-OS VM and processes voice commands for security operations.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── voice/
│   │   │   ├── __init__.py
│   │   │   ├── recognition/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── vosk_engine.py
│   │   │   │   ├── wake_word_detector.py
│   │   │   │   ├── noise_filter.py
│   │   │   │   └── audio_processor.py
│   │   │   ├── vocabulary/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cybersec_terms.py
│   │   │   │   ├── tool_names.py
│   │   │   │   ├── parameter_parser.py
│   │   │   │   └── command_corrector.py
│   │   │   ├── synthesis/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tts_engine.py
│   │   │   │   ├── response_formatter.py
│   │   │   │   └── audio_output.py
│   │   │   ├── models/
│   │   │   │   ├── vosk-model-en-us/     # Downloaded model
│   │   │   │   ├── cybersec-vocab.json
│   │   │   │   └── wake-words.json
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── audio_config.py
│   │   │       └── voice_settings.py
│   │   └── tests/
│   │       ├── voice/
│   │       │   ├── __init__.py
│   │       │   ├── test_recognition.py
│   │       │   ├── test_wake_word.py
│   │       │   ├── test_vocabulary.py
│   │       │   ├── test_noise_filter.py
│   │       │   └── test_audio_samples/
│   │       │       ├── clean_command.wav
│   │       │       ├── noisy_command.wav
│   │       │       ├── wake_word_test.wav
│   │       │       └── cybersec_terms.wav
│   └── requirements/
│       ├── voice_requirements.txt
│       └── system_requirements.txt
```

## Technology Stack
- **STT Engine**: Vosk 0.3.45 (offline recognition)
- **Audio Processing**: SpeechRecognition 3.10.0, pyaudio 0.2.11
- **Noise Filtering**: noisereduce 3.0.0, librosa 0.10.1
- **Text-to-Speech**: pyttsx3 2.90, espeak
- **Wake Word Detection**: pvporcupine 3.0.0 (Picovoice)
- **Audio Utils**: sounddevice 0.4.6, wave, numpy

### 2. Audio Quality Tests
```python
# tests/voice/test_audio_quality.py
def test_microphone_calibration():
    """Test microphone input levels and quality"""
    from src.voice.config.audio_config import AudioConfig

    config = AudioConfig()

    # Test microphone detection
    mics = config.detect_microphones()
    assert len(mics) > 0

    # Test audio quality
    sample = config.record_test_sample(duration=2.0)
    quality_score = config.analyze_audio_quality(sample)

    assert quality_score['snr'] > 10  # Signal-to-noise ratio
    assert quality_score['volume'] > 0.1  # Adequate volume
    assert quality_score['clipping'] < 0.05  # Minimal clipping

def test_latency_requirements():
    """Test voice processing latency meets requirements"""
    import time

    start_time = time.time()

    # Simulate full voice processing pipeline
    result = stt_engine.transcribe_real_time("test command")

    end_time = time.time()
    latency = end_time - start_time

    # Should process voice in under 500ms
    assert latency < 0.5
```

## Implementation Requirements

### Core Components

#### 1. Vosk STT Engine
```python
# src/voice/recognition/vosk_engine.py
import json
import vosk
import pyaudio
import numpy as np
from typing import Optional, Dict, Any

class VoskSTTEngine:
    def __init__(self, model_path: str, sample_rate: int = 16000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, sample_rate)

    def transcribe_file(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio file to text"""
        # Implementation here
        pass

    def transcribe_real_time(self, audio_stream) -> Dict[str, Any]:
        """Real-time transcription from audio stream"""
        # Implementation here
        pass
```

#### 2. Cybersecurity Vocabulary
```python
# src/voice/vocabulary/cybersec_terms.py
class CybersecurityVocabulary:
    def __init__(self):
        self.security_tools = {
            # Common misheard -> correct
            "map": "nmap",
            "burp sweet": "burpsuite",
            "burp suit": "burpsuite",
            "wire shark": "wireshark",
            "metal split": "metasploit",
            "nick to": "nikto"
        }

        self.security_terms = {
            "recon": "reconnaissance",
            "vuln": "vulnerability",
            "pen test": "penetration test",
            "priv esc": "privilege escalation"
        }

    def correct_terms(self, text: str) -> str:
        """Auto-correct common voice recognition errors"""
        # Implementation here
        pass

    def extract_parameters(self, text: str) -> Dict[str, list]:
        """Extract IPs, URLs, ports, etc. from voice command"""
        # Implementation here
        pass
```

#### 3. Wake Word Detection
```python
# src/voice/recognition/wake_word_detector.py
import pvporcupine
from typing import List

class WakeWordDetector:
    def __init__(self, wake_words: List[str]):
        self.wake_words = wake_words
        self.porcupine = pvporcupine.create(
            keywords=wake_words,
            access_key="YOUR_PICOVOICE_ACCESS_KEY"
        )

    def detect_wake_word(self, audio_chunk: bytes) -> bool:
        """Detect wake word in audio chunk"""
        # Implementation here
        pass
```

#### 4. Noise Filter
```python
# src/voice/recognition/noise_filter.py
import noisereduce as nr
import librosa

class NoiseFilter:
    def __init__(self):
        self.filter_settings = {
            'stationary': True,
            'prop_decrease': 0.8
        }

    def reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply noise reduction to audio"""
        # Implementation here
        pass

    def enhance_speech(self, audio_data: np.ndarray) -> np.ndarray:
        """Enhance speech clarity"""
        # Implementation here
        pass
```

### Voice Command Processing Pipeline

#### 1. Audio Capture
- Continuous microphone monitoring
- Wake word detection
- Automatic gain control
- Background noise suppression

#### 2. Speech Recognition
- Vosk offline STT processing
- Cybersecurity vocabulary correction
- Confidence scoring
- Real-time streaming

#### 3. Command Parsing
- Intent classification
- Parameter extraction (IPs, URLs, ports)
- Tool name recognition
- Context awareness

#### 4. Response Generation
- Text-to-speech feedback
- Progress announcements
- Error notifications
- Success confirmations

## Testing Strategy

### Unit Tests (80% coverage minimum)
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run voice recognition tests
cd kali-ai-os
python -m pytest tests/voice/ -v --cov=src.voice --cov-report=html

# Expected test categories:
# - STT accuracy tests
# - Wake word detection
# - Noise filtering
# - Vocabulary correction
# - Parameter extraction
# - Real-time processing
```

### Integration Tests
```bash
# Test with real microphone
python -m pytest tests/voice/test_microphone_integration.py -v

# Test voice command pipeline
python -m pytest tests/voice/test_voice_pipeline.py -v

# Test audio quality
python -m pytest tests/voice/test_audio_quality.py -v
```

### Performance Tests
```python
def test_recognition_speed():
    """Test voice recognition speed meets requirements"""
    import time

    start_time = time.time()
    result = voice_engine.process_command("scan example.com")
    end_time = time.time()

    # Should process in under 300ms
    assert (end_time - start_time) < 0.3

def test_accuracy_with_noise():
    """Test recognition accuracy in noisy environments"""
    # Test with different noise levels
    noise_levels = [0.1, 0.3, 0.5]  # SNR ratios

    for noise_level in noise_levels:
        accuracy = test_recognition_with_noise(noise_level)

        if noise_level <= 0.1:
            assert accuracy > 0.95  # 95% accuracy in quiet
        elif noise_level <= 0.3:
            assert accuracy > 0.85  # 85% accuracy with moderate noise
        else:
            assert accuracy > 0.70  # 70% accuracy with high noise
```

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

# Test microphone
arecord -f cd -t wav -d 5 test.wav && aplay test.wav
```

### Shared Folder Configuration
```bash
# Mount shared folder for voice models
sudo mkdir -p /mnt/shared
sudo mount -t 9p -o trans=virtio,version=9p2000.L shared /mnt/shared

# Create symlink to voice models
ln -s /mnt/shared/voice-models ~/kali-ai-os/src/voice/models/
```

## Deployment & Testing

### Setup Commands
```bash
# 1. Download Vosk model
cd kali-ai-os/src/voice/models/
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
mv vosk-model-en-us-0.22 vosk-model-en-us

# 2. Install Python dependencies
pip install -r requirements/voice_requirements.txt

# 3. Configure audio system
python src/voice/config/setup_audio.py

# 4. Test voice recognition
python -c "
from src.voice.recognition.vosk_engine import VoskSTTEngine
engine = VoskSTTEngine('src/voice/models/vosk-model-en-us')
print('Voice engine ready!')
"

# 5. Run comprehensive tests
python -m pytest tests/voice/ -v
```

### Validation Criteria
✅ **Must pass before considering task complete:**

1. **Functionality Tests**
   - Wake word detection works (>95% accuracy)
   - STT recognizes cybersecurity terms (>90% accuracy)
   - Noise filtering improves recognition
   - Real-time processing under 300ms latency

2. **Audio Quality Tests**
   - Microphone input properly configured
   - Audio quality meets minimum thresholds
   - Background noise properly filtered
   - TTS output clear and understandable

3. **Integration Tests**
   - Voice commands properly parsed
   - Parameters extracted correctly
   - Error handling for audio issues
   - Graceful degradation with poor audio

4. **Performance Tests**
   - Recognition speed < 300ms
   - Memory usage < 256MB
   - CPU usage < 25% during recognition
   - Works with various microphone types

### Success Metrics
- ✅ 95%+ wake word detection accuracy
- ✅ 90%+ cybersecurity term recognition
- ✅ <300ms voice processing latency
- ✅ All integration tests pass
- ✅ Audio system configured in VM

## Configuration Files

### voice_requirements.txt
```txt
# Voice Recognition
vosk==0.3.45
SpeechRecognition==3.10.0
pyaudio==0.2.11

# Audio Processing
librosa==0.10.1
noisereduce==3.0.0
sounddevice==0.4.6
numpy==1.24.3

# Wake Word Detection
pvporcupine==3.0.0

# Text-to-Speech
pyttsx3==2.90

# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-asyncio==0.21.1
```

### Audio Configuration
```python
# src/voice/config/audio_config.py
AUDIO_CONFIG = {
    'sample_rate': 16000,
    'chunk_size': 1024,
    'channels': 1,
    'format': 'int16',
    'wake_words': ['hey kali', 'kali ai', 'security ai'],
    'noise_threshold': 0.01,
    'min_speech_duration': 0.5,
    'max_speech_duration': 10.0,
    'silence_timeout': 2.0
}
```

## Next Steps
After completing this task:
1. Document voice command syntax for users
2. Create voice command reference guide
3. Optimize for different accents and speech patterns
4. Proceed to Task 3: Desktop Automation Core

## Troubleshooting
Common issues and solutions:
- **No microphone detected**: Check audio drivers and permissions
- **Poor recognition accuracy**: Calibrate microphone levels and noise filtering
- **High latency**: Optimize Vosk model size and processing pipeline
- **Wake word false positives**: Adjust sensitivity settings
