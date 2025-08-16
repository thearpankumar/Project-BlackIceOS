# Kali AI OS - Complete Setup Guide

This guide provides comprehensive instructions for setting up the Kali AI OS desktop automation system from development to production deployment.

## Quick Start

### Option 1: Production Installation (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd kali-ai-os

# Run automated service installation
sudo ./scripts/install_service.sh

# Configure environment
sudo nano /opt/kali-ai-os/.env  # Update API keys and settings

# Start and test the service
kali-ai-desktop start
kali-ai-desktop test
```

### Option 2: Development Setup
```bash
# Clone repository  
git clone <repository-url>
cd kali-ai-os

# Install system dependencies
sudo apt update && sudo apt install -y \
  python3 python3-pip python3-venv \
  xvfb x11-utils wmctrl xdotool scrot \
  libgl1-mesa-dri libglx-mesa0 libglib2.0-0 imagemagick dbus-x11 libegl1-mesa mesa-utils \
  libsystemd-dev pkg-config

# Install Python dependencies
uv sync  # or pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Update your API keys and settings

# Run development server
uv run python main.py
```

## System Requirements

### Hardware Requirements
- **CPU**: 4+ cores (for optimal performance)
- **RAM**: 8GB+ (4GB minimum)
- **Disk**: 10GB+ free space
- **Display**: X11 compatible graphics

### Software Requirements
- **OS**: Kali Linux 2023.1+ (or Ubuntu 20.04+ based systems)
- **Python**: 3.9+ (3.11+ recommended)
- **X11**: Virtual display support (Xvfb)
- **Dependencies**: Listed in requirements.txt

### Network Requirements
- **Host Authentication Server**: HTTP access to auth server
- **Internet**: For API calls to Google AI/Gemini and Picovoice
- **Local Network**: For VM-Host communication (if using VM)

## Step-by-Step Installation

### 1. System Dependencies

#### Essential System Packages
```bash
sudo apt update
sudo apt install -y \
  python3 python3-pip python3-venv \
  xvfb x11-utils wmctrl xdotool scrot \
  libgl1-mesa-dri libglx-mesa0 libglib2.0-0 libsm6 \
  libxext6 libxrender-dev libgomp1 \
  libgtk-3-0 libqt5widgets5 \
  imagemagick dbus-x11 libegl1-mesa mesa-utils \
  libsystemd-dev pkg-config
```

#### Optional Enhancements
```bash
# Note: OCR packages no longer needed - using LLM vision instead

# Performance monitoring tools
sudo apt install -y htop iotop nethogs

# Development tools (if needed)
sudo apt install -y git curl wget build-essential
```

### 2. Python Environment Setup

#### Using uv (Recommended)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Sync dependencies from pyproject.toml
cd kali-ai-os
uv sync

# For development with all optional dependencies
uv sync --extra dev

# For production deployment
uv sync --extra production

# Activate virtual environment
source .venv/bin/activate
```

#### Using pip (Alternative)
```bash
cd kali-ai-os
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration

#### Create Configuration File
```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env  # or vim .env
```

#### Required Environment Variables
```bash
# Authentication Server Configuration
AUTH_SERVER_URL=http://192.168.1.100:8000

# AI Service API Keys
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
PICOVOICE_ACCESS_KEY=your_picovoice_access_key_here

# Display Configuration
AI_DISPLAY=:1
USER_DISPLAY=:0

# OCR Configuration
OCR_LANGUAGES=eng
TESSERACT_CONFIG=--oem 3 --psm 6

# Voice Recognition Settings
VOICE_DETECTION_TIMEOUT=30
WAKE_WORD_SENSITIVITY=0.7

# Safety and Security Settings
PERMISSION_STRICT_MODE=true
EMERGENCY_STOP_KEY=F12
DEV_DISABLE_SAFETY_CHECKS=false

# Performance Tuning
MAX_RESPONSE_TIME_MS=100
MAX_MEMORY_USAGE_MB=512
TEMPLATE_CONFIDENCE_THRESHOLD=0.75

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/tmp/kali-ai-desktop.log
```

### 4. Authentication Setup

#### Host Authentication Server
Ensure your host authentication server is running and accessible:

```bash
# Test connection to auth server
curl -X GET http://192.168.1.100:8000/health

# Expected response: {"status": "healthy"}
```

#### API Key Configuration
1. **Google AI (Gemini)**: 
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Create API key
   - Add to `GOOGLE_AI_API_KEY` in `.env`

2. **Picovoice**: 
   - Visit [Picovoice Console](https://console.picovoice.ai/)
   - Create access key
   - Add to `PICOVOICE_ACCESS_KEY` in `.env`

### 5. Virtual Display Setup

#### Automatic Setup (Handled by application)
```bash
# The application automatically creates the virtual display
uv run python main.py
```

#### Manual Setup (for troubleshooting)
```bash
# Start virtual display manually
export DISPLAY=:1
Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &

# Verify display is running
xdpyinfo -display :1 > /dev/null && echo "Display :1 active" || echo "Display :1 failed"

# List all displays
ps aux | grep Xvfb
```

### 6. Template Library Setup

#### Default Templates
The system includes pre-built templates for common applications:

```bash
# View available templates
ls -la templates/
```

#### Custom Templates (Optional)
```bash
# Create custom template directory
mkdir -p templates/custom

# Add your application-specific screenshots
cp /path/to/your/gui_element.png templates/custom/

# Validate templates
uv run python -c "
from src.desktop.recognition.template_manager import TemplateManager
tm = TemplateManager()
print('Template validation:', tm.validate_template('templates/custom/gui_element.png'))
"
```

### 7. Testing Installation

#### Basic Functionality Test
```bash
# Test system components
uv run python -c "
from src.desktop.automation.desktop_controller import DesktopController
controller = DesktopController(':1')
result = controller.capture_screenshot('/tmp/test_screenshot.png')
print('Screenshot test:', 'PASSED' if result else 'FAILED')
"
```

#### Comprehensive Performance Test
```bash
# Run full performance benchmark
./scripts/performance_benchmark.py

# Expected output:
# ✓ DesktopController Init: XX.Xms, XX.XMB
# ✓ Screenshot Capture: XX.Xms, XX.XMB
# ... 
# Task 3 Requirements: ✓ PASSED
```

#### Integration Test
```bash
# Test voice integration (requires microphone)
uv run python -c "
from src.voice.recognition.audio_processor import AudioProcessor
processor = AudioProcessor()
print('Voice processor initialized:', processor is not None)
"

# Test authentication
uv run python -c "
from src.auth.auth_client import AuthClient
client = AuthClient()
# Note: This will fail if auth server is not accessible - that's expected in development
print('Auth client initialized')
"
```

## Production Deployment

### Automated Service Installation
For production environments, use the automated installer:

```bash
# Run as root for system service installation
sudo ./scripts/install_service.sh

# This will:
# 1. Create dedicated service user (ai-automation)
# 2. Install all system dependencies
# 3. Set up Python virtual environment
# 4. Create systemd service
# 5. Configure security settings
# 6. Set up log rotation
# 7. Create management scripts
```

### Service Management
After installation, manage the service using:

```bash
# Service control
kali-ai-desktop start      # Start the service
kali-ai-desktop stop       # Stop the service
kali-ai-desktop restart    # Restart the service
kali-ai-desktop status     # Check service status

# Monitoring
kali-ai-desktop logs       # View system logs (journalctl)
kali-ai-desktop app-logs   # View application logs

# Configuration
kali-ai-desktop enable     # Enable auto-start on boot
kali-ai-desktop disable    # Disable auto-start

# Testing and validation
kali-ai-desktop test       # Test service functionality
```

### Service Configuration
Production configuration files are located at:
- **Service Config**: `/opt/kali-ai-os/.env`
- **Application Code**: `/opt/kali-ai-os/src/`
- **Templates**: `/opt/kali-ai-os/templates/`
- **Logs**: `/opt/kali-ai-os/logs/`

## Troubleshooting

### Common Installation Issues

#### 1. Virtual Display Not Starting
```bash
# Check if Xvfb is installed
which Xvfb

# Check if display is running
ps aux | grep Xvfb

# Manual display start
export DISPLAY=:1
Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX &

# Test display
xdpyinfo -display :1
```

#### 2. Python Dependencies Issues
```bash
# Clear virtual environment and reinstall
rm -rf .venv
uv sync

# Or with pip
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. SystemD Python Package Issues
If you encounter `systemd-python` build errors:
```bash
# Install required system development packages
sudo apt update
sudo apt install -y libsystemd-dev pkg-config

# Error: "Cannot find libsystemd or libsystemd-journal"
# Solution: Install development headers for systemd
sudo apt install -y libsystemd-dev libsystemd-journal-dev pkg-config

# Verify installation
pkg-config --exists libsystemd && echo "✓ libsystemd found" || echo "✗ libsystemd missing"

# Then retry uv sync
uv sync --all-extras
```

#### 3. LLM Vision Integration
```bash
# Test LLM vision functionality 
# Ensure API keys are configured in .env:
# GOOGLE_AI_API_KEY=your_key_here

# Test vision API connectivity
python3 -c "
import google.generativeai as genai
genai.configure(api_key='your_key')
print('LLM Vision API ready')
"
```

#### 4. Permission Issues
```bash
# Check file permissions
ls -la kali-ai-os/

# Fix permissions if needed
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

#### 5. API Connection Issues
```bash
# Test auth server connection
curl -v http://192.168.1.100:8000/health

# Test internet connectivity for AI services
curl -v https://generativelanguage.googleapis.com/
ping -c 3 api.picovoice.ai
```

### Performance Issues

#### 1. High Memory Usage
```bash
# Monitor memory usage
./scripts/performance_benchmark.py --quiet || echo "Memory issues detected"

# Adjust VM optimization settings in code
# Edit src/desktop/automation/desktop_controller.py
# Reduce screenshot_quality, increase animation_delay
```

#### 2. Slow Response Times
```bash
# Run performance benchmark
./scripts/performance_benchmark.py

# Check system resources
htop
iotop

# Optimize for VM environment
# Reduce template confidence thresholds
# Increase automation delays
```

#### 3. Template Recognition Issues
```bash
# Validate templates
uv run python -c "
from src.desktop.recognition.template_manager import TemplateManager
tm = TemplateManager()
for category in tm.get_available_categories():
    print(f'Validating {category} templates...')
    # Add validation logic
"

# Adjust confidence thresholds
# Edit .env file: TEMPLATE_CONFIDENCE_THRESHOLD=0.6
```

### Development Debugging

#### Enable Debug Logging
```bash
# Edit .env file
LOG_LEVEL=DEBUG

# Run with debug output
uv run python main.py
```

#### Manual Component Testing
```bash
# Test individual components
uv run python -c "
from src.desktop.recognition.text_recognizer import TextRecognizer
recognizer = TextRecognizer()
print('OCR test passed:', recognizer._validate_tesseract())
"

# Test safety systems
uv run python -c "
from src.desktop.safety.emergency_stop import EmergencyStop
emergency = EmergencyStop()
print('Emergency stop ready:', not emergency.is_emergency_active())
"
```

## Performance Optimization

### VM-Specific Optimizations
```bash
# Adjust VM settings in .env
VM_SCREENSHOT_QUALITY=60
VM_ANIMATION_DELAY=0.3
VM_MAX_CONCURRENT_ACTIONS=1
VM_TEMPLATE_CONFIDENCE=0.65
```

### Resource Monitoring
```bash
# Monitor system performance
htop  # CPU and memory usage
iotop # Disk I/O
nethogs # Network usage

# Application performance
./scripts/performance_benchmark.py --output benchmark.json
cat benchmark.json | jq '.validation.valid'  # Should be true
```

### Memory Optimization
```bash
# Clear system caches
sudo sync
sudo sysctl vm.drop_caches=3

# Monitor application memory
ps aux | grep python
pmap $(pgrep -f main.py)
```

## Security Considerations

### Service Security
- Service runs as dedicated user `ai-automation`
- Minimal privileges with restricted file access
- Sandboxed execution environment
- Automatic cleanup of sensitive data

### Network Security
- Local authentication server communication
- Encrypted API communications
- No direct network service exposure
- Firewall-friendly architecture

### Desktop Isolation
- Complete separation between user (:0) and AI (:1) displays
- Process isolation monitoring
- Emergency stop capabilities
- Permission validation for all actions

## Maintenance

### Regular Maintenance Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python dependencies
uv sync --upgrade

# Validate performance
./scripts/performance_benchmark.py

# Clean up logs
sudo logrotate -f /etc/logrotate.d/kali-ai-desktop

# Backup configuration
cp /opt/kali-ai-os/.env ~/kali-ai-desktop-config-backup.env
```

### Monitoring
```bash
# Service health check
systemctl is-active kali-ai-desktop

# Performance monitoring
kali-ai-desktop logs | grep -i "performance\|error\|failed"

# Resource usage
journalctl -u kali-ai-desktop --since "1 hour ago" | grep -i "memory\|cpu"
```

## Getting Help

### Log Files
- **System Logs**: `journalctl -u kali-ai-desktop -f`
- **Application Logs**: `/opt/kali-ai-os/logs/` (production) or console output (development)
- **Error Logs**: `/opt/kali-ai-os/logs/kali-ai-desktop.error.log`

### Debug Information
```bash
# System information
./scripts/performance_benchmark.py --output debug_info.json
cat debug_info.json | jq '.system_info'

# Component status
kali-ai-desktop test

# Detailed diagnosis
uv run python -c "
import sys
print('Python version:', sys.version)
from src.desktop.automation.desktop_controller import DesktopController
controller = DesktopController(':1')
print('Desktop controller initialized successfully')
"
```

### Support Resources
- **Performance Benchmark**: `./scripts/performance_benchmark.py`
- **Service Management**: `kali-ai-desktop --help`
- **Template Guide**: `templates/README.md`
- **Deployment Guide**: `scripts/README.md`

This setup guide provides comprehensive instructions for getting the Kali AI OS desktop automation system running in both development and production environments. Follow the appropriate sections based on your use case and environment requirements.