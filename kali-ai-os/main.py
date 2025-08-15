from src.voice.recognition.audio_processor import AudioProcessor


def main():
    processor = AudioProcessor()

    # Listen for wake word, then get a voice command
    processor.speak_text("I am ready. Say the wake word to begin.")
    command = processor.process_voice_command()

    # The 'command' text can now be sent to the AI processing layer (Task 4)
    processor.speak_text(f"Executing command: {command}")


if __name__ == "__main__":
    main()
