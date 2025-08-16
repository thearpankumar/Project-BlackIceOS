# Samsung AI-OS Voice Interface

This document provides an overview of the voice interface implementation in Samsung AI-OS.

## Overview

The voice interface enables users to control cybersecurity tools through natural language commands. The current implementation uses Google's Gemini API for direct voice transcription and processing, integrated into the main GUI application.

## Current Implementation

- **Direct Voice Input:** Voice recording through the main GUI application
- **Google Gemini Integration:** Direct transcription using Google's Generative AI
- **Command Processing:** Voice commands processed alongside text input
- **GUI Integration:** Voice interface embedded in the main Samsung AI-OS GUI

## How to Use

1.  **Set up Environment Variables:**
    Create a `.env` file in the `kali-ai-os` directory:
    ```bash
    # Required API key for voice transcription
    GOOGLE_AI_API_KEY="YOUR_GOOGLE_AI_API_KEY"
    
    # Authentication server
    AUTH_SERVER_URL="http://192.168.1.100:8000"
    ```

2.  **Install Dependencies:**
    ```bash
    # Install system dependencies
    sudo apt update && sudo apt install -y \
      python3 python3-pip python3-venv \
      xvfb x11-utils wmctrl xdotool

    # Install Python dependencies
    cd kali-ai-os
    uv sync
    ```

3.  **Run the Application:**
    ```bash
    uv run python main.py
    ```

4.  **Using Voice Commands:**
    - Click the "🎤 Voice Input" button in the GUI
    - Speak your command clearly
    - Commands are processed by Google Gemini API
    - Results appear in the response area

## Voice Command Examples

The voice interface supports natural language commands for cybersecurity tasks:

```
"Open terminal and run nmap scan on 192.168.1.1"
"Launch Burp Suite and configure proxy for example.com"
"Start Wireshark packet capture"
"Take a screenshot of the current scan results"
"Open file manager and browse to downloads"
"Run calculator to calculate subnet ranges"
```

## Technical Implementation

### Google Gemini Integration
- Voice commands are directly processed by Google's Gemini API
- No local speech processing required
- Real-time transcription and interpretation
- Natural language understanding for cybersecurity contexts

### GUI Integration
The voice interface is embedded in the main application GUI (`main.py`):
- Voice input button activates recording
- Commands processed through the same pipeline as text input
- Results displayed in the main interface
- Integration with desktop automation system

### Dependencies

**Required Dependencies:**
- `google-generativeai` - Google's Generative AI for voice processing
- `python-dotenv` - Environment variable management
- `tkinter` - GUI framework (built into Python)
- `pyautogui` - Desktop automation
- `subprocess` - System command execution

**System Requirements:**
- Python 3.9+ 
- Active internet connection for Gemini API
- Valid Google AI API key
- X11 display system (for desktop automation)

## Troubleshooting

### Common Issues

**Error: "GOOGLE_AI_API_KEY not found"**
- Ensure `.env` file exists in the `kali-ai-os` directory
- Add your Google AI API key to the `.env` file
- Restart the application

**Error: "Authentication server not reachable"**
- Check that AUTH_SERVER_URL in `.env` points to your auth server
- Verify the auth server is running: `curl http://your-server:8000/health`
- Update the IP address if the server has moved

**Voice input not working**
- Ensure you have a working microphone
- Check system audio permissions
- Verify internet connection for Gemini API

**Desktop automation failing**
- Ensure virtual display is running (handled automatically)
- Check that required applications are installed
- Verify X11 system is working: `echo $DISPLAY`

### Performance Issues

**Slow voice processing**
- Check internet connection speed
- Verify Google AI API quotas and limits
- Consider shorter voice commands for faster processing

**GUI responsiveness**
- Close unnecessary applications
- Ensure adequate system resources (4GB+ RAM recommended)
- Check system load: `htop`

### Integration Issues

**Voice commands not executing desktop actions**
- Verify desktop automation is working: test with text commands first
- Check authentication with server
- Ensure target applications are installed and accessible

For additional help, see the main setup guide: `docs/setup_guide.md`
