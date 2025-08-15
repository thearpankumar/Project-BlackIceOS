import queue
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Manually insert mocks for problematic modules BEFORE importing the application code.
MOCK_MODULES = {
    "pvporcupine": MagicMock(),
    "pyaudio": MagicMock(),
    "sounddevice": MagicMock(),
    "pyttsx3": MagicMock(),
    "webrtcvad": MagicMock(),
    "noisereduce": MagicMock(),
}
sys.modules.update(MOCK_MODULES)

# Now, we can safely import the class we want to test
from src.voice.recognition.audio_processor import AudioProcessor  # noqa: E402


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for all tests."""
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "dummy_google_key")
    monkeypatch.setenv("PICOVOICE_ACCESS_KEY", "dummy_pico_key")


@pytest.fixture(autouse=True)
def mock_external_libs_auto():
    """A fixture to automatically mock all external libraries for every test."""
    with (
        patch("google.generativeai.configure"),
        patch("google.generativeai.upload_file"),
        patch("src.voice.recognition.audio_processor.write"),
    ):
        yield


def test_audio_processor_initialization():
    """Tests if the AudioProcessor initializes correctly."""
    processor = AudioProcessor()
    assert processor.api_key == "dummy_google_key"
    assert processor.picovoice_key == "dummy_pico_key"


@patch("pyaudio.PyAudio")
@patch("pvporcupine.create")
def test_listen_for_wake_word_calls_porcupine(mock_pv_create, mock_pyaudio):
    """Tests that the wake word listener correctly initializes and uses pvporcupine."""
    mock_porcupine_instance = MagicMock()
    mock_porcupine_instance.process.side_effect = [-1, -1, 0]
    mock_porcupine_instance.frame_length = 512
    mock_pv_create.return_value = mock_porcupine_instance

    mock_stream = MagicMock()
    mock_stream.read.return_value = b"\x00" * (mock_porcupine_instance.frame_length * 2)
    mock_pyaudio.return_value.open.return_value = mock_stream

    processor = AudioProcessor()
    processor.listen_for_wake_word()

    mock_pv_create.assert_called_with(
        access_key="dummy_pico_key", keywords=["computer"]
    )
    assert mock_porcupine_instance.process.call_count == 3


@patch("src.voice.recognition.audio_processor.write")
@patch("sounddevice.InputStream")
@patch("src.voice.recognition.audio_processor.queue.Queue")
def test_record_audio_logic(mock_queue, mock_input_stream, mock_write):
    """Tests the recording logic by providing a pre-filled queue."""
    # --- Setup ---
    mock_input_stream.return_value.__enter__.return_value = None
    mock_input_stream.return_value.__exit__.return_value = None

    # Create a pre-populated queue that the AudioProcessor will receive
    q = queue.Queue()
    # The frame size is 16000 * 30 / 1000 = 480
    audio_chunk = np.zeros(480, dtype=np.int16)
    for _ in range(150):  # Simulate plenty of audio frames
        q.put(audio_chunk)
    mock_queue.return_value = q

    processor = AudioProcessor()

    # Simulate speech for a few frames, then silence
    vad_side_effect = [False, True, True, True, True, True] + ([False] * 145)
    with patch.object(processor.vad, "is_speech", side_effect=vad_side_effect):
        # --- Action ---
        result = processor.record_audio()

    # --- Asserts ---
    assert result is True
    mock_write.assert_called_once()


@patch("os.path.exists", return_value=True)
@patch("google.generativeai.GenerativeModel")
def test_transcription_api_call(mock_gen_model, mock_exists):
    """Tests that the transcription function calls the Google API correctly."""
    mock_model_instance = mock_gen_model.return_value
    mock_model_instance.generate_content.return_value.text = "scan the network"

    processor = AudioProcessor()
    result = processor.transcribe_audio("dummy.wav")

    assert result == "scan the network"
    mock_model_instance.generate_content.assert_called_once()


@patch("pyttsx3.init")
def test_local_text_to_speech_generation(mock_tts_init):
    """Tests that the TTS function calls the TTS engine correctly."""
    mock_engine = MagicMock()
    mock_tts_init.return_value = mock_engine

    processor = AudioProcessor()
    processor.speak_text("hello")

    mock_engine.say.assert_called_with("hello")
    mock_engine.runAndWait.assert_called_once()
