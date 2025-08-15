# Kali AI OS Voice Engine

This document provides an overview of the voice engine for the Kali AI OS project.

## Overview

The voice engine is responsible for listening for a wake word, recording voice commands, transcribing them to text, and providing text-to-speech functionality. It uses a combination of local and cloud-based services to achieve this.

## Features

- **Wake Word Detection:** Listens for the wake word "computer" using the Porcupine wake word engine.
- **Voice Activity Detection (VAD):** Automatically detects when speech has started and stopped to record commands accurately.
- **Noise Reduction:** Calibrates for ambient noise to improve transcription accuracy.
- **Speech-to-Text (STT):** Uses Google's Generative AI (Gemini 1.5 Flash) to transcribe voice commands.
- **Text-to-Speech (TTS):** Uses a local TTS engine (`pyttsx3`) to speak responses.

## How to Use

1.  **Set up Environment Variables:**
    Create a `.env` file in the `kali-ai-os` directory with the following variables:
    ```
    GOOGLE_AI_API_KEY="YOUR_GOOGLE_AI_API_KEY"
    PICOVOICE_ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY"
    ```

2.  **Install Dependencies:**
    Navigate to the `kali-ai-os` directory and run:
    ```bash
    uv sync --all-extras
    ```

3.  **Run the Main Script:**
    From the `kali-ai-os` directory, run:
    ```bash
    python main.py
    ```

The script will then:
1.  Calibrate for ambient noise.
2.  Listen for the wake word "computer".
3.  Once the wake word is detected, it will listen for a voice command.
4.  After you stop speaking, it will transcribe the command and print it to the console.

## Configuration

The audio configuration can be modified in `kali-ai-os/src/voice/config/audio_config.py`. The default settings are:

```python
AUDIO_CONFIG = {
    "sample_rate": 44100,
    "record_duration_seconds": 5,
    "channels": 1,
    "wake_words": ["computer"],
    "wake_word_sensitivity": 0.5,
}
```

## Dependencies

The main dependencies for this project are:

- `google-generativeai`
- `python-dotenv`
- `pvporcupine`
- `pyaudio`
- `sounddevice`
- `scipy`
- `numpy`
- `pyttsx3`
- `webrtcvad`
- `setuptools<66`

Development dependencies include `pytest`, `ruff`, `black`, `isort`, and `mypy`.
