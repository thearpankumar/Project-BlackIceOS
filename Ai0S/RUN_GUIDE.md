# 🚀 AI0S - Complete Run Guide

## Quick Start
```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
uv sync

# 3. Run the application
uv run ai0s
```

## Running Methods

### 🎯 Full Application (Recommended)
```bash
uv run ai0s
```
- Starts backend service + desktop GUI
- Complete voice-controlled AI system
- Real-time visual monitoring
- WebSocket API on ws://127.0.0.1:8001

### 🖥️ Backend Service Only
```bash
uv run python -m Ai0S.backend.main
```
- Headless operation
- API/WebSocket access only
- Perfect for servers/integration
- All AI capabilities available

### 🎨 Desktop App Only
```bash
uv run python -m Ai0S.desktop_app.main_window
```
- GUI interface only
- Requires backend running separately
- Professional CustomTkinter interface

### 🔧 Development Mode
```bash
DEBUG_MODE=true LOG_LEVEL=DEBUG uv run ai0s
```
- Verbose logging
- Development features enabled
- Additional debugging info

## Environment Setup

### Required API Keys (.env file)
```bash
GROQ_API_KEY=your_groq_api_key_here          # Get from console.groq.com
GEMINI_API_KEY=your_gemini_api_key_here      # Get from ai.google.dev
```

### Optional Configuration
```bash
# UI Settings
UI_THEME=dark
WINDOW_WIDTH=1400
WINDOW_HEIGHT=800

# Voice Settings
ENABLE_VOICE=true
VOICE_DETECTION_TIMEOUT=30

# Performance
MAX_PARALLEL_STEPS=3
SCREENSHOT_QUALITY=0.8
```

## Platform-Specific Instructions

### Linux (X11/Wayland)
```bash
# Standard desktop
uv run ai0s

# Server/headless
uv run python -m Ai0S.backend.main

# With virtual display
xvfb-run -a uv run ai0s
```

### Windows
```powershell
# PowerShell/CMD
uv run ai0s
```

### macOS
```bash
# Terminal
uv run ai0s
```

## API Integration

### WebSocket API
```javascript
const ws = new WebSocket('ws://127.0.0.1:8001');

// Execute AI task
ws.send(JSON.stringify({
    type: "execute_task",
    data: {
        instruction: "open calculator and compute 15 * 23"
    }
}));

// Get system status
ws.send(JSON.stringify({
    type: "get_status"
}));
```

### Health Check
```bash
curl http://127.0.0.1:8001/health
```

## Features Available

✅ **AI Models**: Gemini 2.0 Flash + Groq integration  
✅ **Voice Control**: Wake word detection and speech processing  
✅ **Visual Analysis**: Real-time screen understanding  
✅ **Desktop Automation**: Cross-platform UI control  
✅ **Security Framework**: Multi-level safety controls  
✅ **Task Planning**: Intelligent step-by-step execution  
✅ **Error Recovery**: Automatic adaptation and retry  
✅ **Professional UI**: Modern CustomTkinter interface  

## Troubleshooting

### Common Issues

**1. Display Connection Error**
```bash
# If you see "couldn't connect to display"
export DISPLAY=:0
uv run ai0s

# Or run backend only
uv run python -m Ai0S.backend.main
```

**2. Missing API Keys**
```bash
# Check .env file exists and has keys
cat .env | grep API_KEY
```

**3. Import Errors**
```bash
# Reinstall package
uv pip install -e . --force-reinstall
```

**4. Permission Errors (Linux)**
```bash
# Add user to required groups
sudo usermod -a -G audio,video $USER
```

### Logs Location
```bash
# View logs
tail -f logs/backend.log
tail -f logs/launcher.log
```

## Advanced Usage

### Custom Configuration
```bash
# Override settings
GROQ_MODEL=llama-3.3-70b-versatile uv run ai0s
AI_TEMPERATURE=0.2 uv run ai0s
```

### Multiple Instances
```bash
# Run backend on different port
WS_PORT=8002 uv run python -m Ai0S.backend.main

# Connect desktop app to different backend
WS_HOST=192.168.1.100 WS_PORT=8002 uv run python -m Ai0S.desktop_app.main_window
```

### Integration Examples
```python
# Python integration
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"AI Response: {data}")

ws = websocket.WebSocketApp("ws://127.0.0.1:8001")
ws.on_message = on_message
ws.run_forever()
```

## Production Deployment

### Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/ai0s.service
```

```ini
[Unit]
Description=AI0S Backend Service
After=network.target

[Service]
Type=simple
User=ai0s
WorkingDirectory=/opt/ai0s
ExecStart=/opt/ai0s/.venv/bin/python -m Ai0S.backend.main
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Container
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8001
CMD ["uv", "run", "python", "-m", "Ai0S.backend.main"]
```

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify API keys in `.env` file  
3. Test backend service independently
4. Check system requirements and permissions