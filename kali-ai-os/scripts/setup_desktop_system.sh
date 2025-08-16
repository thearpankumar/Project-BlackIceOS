#!/bin/bash
# Setup Script for Samsung AI-OS Desktop System
# Run this first to install dependencies

echo "🚀 Setting up Samsung AI-OS Desktop System"
echo "=========================================="

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y \
    xvfb \
    x11-utils \
    scrot \
    imagemagick \
    openbox \
    xsetroot \
    wmctrl \
    xdotool \
    galculator \
    xcalc \
    x11vnc \
    tigervnc-viewer \
    tigervnc-common

# Install additional VNC clients for mouse/keyboard control
echo "🖱️  Installing VNC clients for interactive control..."
sudo apt install -y \
    tigervnc-viewer \
    xtightvncviewer \
    vinagre \
    krdc \
    remmina \
    gvncviewer || echo "⚠️  Some VNC clients may not be available"

# Install Python packages if not already installed
echo "🐍 Installing Python packages..."
cd "$(dirname "$0")/.."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv for Python packages..."
    uv sync --all-extras
    PYTHON_CMD="uv run python"
else
    echo "Using pip for Python packages..."
    pip3 install -e ".[desktop,dev]"
    PYTHON_CMD="python3"
fi

# Make scripts executable
echo "🔑 Making scripts executable..."
chmod +x scripts/*.py
chmod +x scripts/*.sh

# Test basic X11 functionality
echo "🖥️  Testing X11 functionality..."
if command -v xdpyinfo &> /dev/null; then
    echo "✅ X11 tools available"
    echo "Current DISPLAY: $DISPLAY"

    # Test if we can run X commands
    if xdpyinfo &> /dev/null; then
        echo "✅ X11 display accessible"
    else
        echo "⚠️  X11 display not accessible - make sure you're in a graphical environment"
    fi
else
    echo "❌ X11 tools not found"
fi

# Test Xvfb
echo "🖼️  Testing Xvfb..."
if command -v Xvfb &> /dev/null; then
    echo "✅ Xvfb available"

    # Quick test
    echo "Testing Xvfb startup..."
    Xvfb :99 -screen 0 800x600x24 &
    XVFB_PID=$!
    sleep 2

    if kill -0 $XVFB_PID 2>/dev/null; then
        echo "✅ Xvfb test successful"
        kill $XVFB_PID
    else
        echo "⚠️  Xvfb test failed"
    fi
else
    echo "❌ Xvfb not found"
fi

# Test VNC components
echo "📺 Testing VNC components..."
if command -v x11vnc &> /dev/null; then
    echo "✅ x11vnc available"
else
    echo "❌ x11vnc not found"
fi

# Test for available VNC clients (for mouse/keyboard control)
echo "🖱️  Checking available VNC clients for interactive control..."
VNC_CLIENTS_FOUND=0

for client in vncviewer xtightvncviewer vinagre krdc remmina gvncviewer; do
    if command -v "$client" &> /dev/null; then
        echo "✅ $client available"
        VNC_CLIENTS_FOUND=$((VNC_CLIENTS_FOUND + 1))
    fi
done

if [ $VNC_CLIENTS_FOUND -eq 0 ]; then
    echo "⚠️  No VNC clients found - install with: sudo apt install tigervnc-viewer"
    echo "   VNC clients are needed for mouse/keyboard control of AI display"
else
    echo "✅ $VNC_CLIENTS_FOUND VNC client(s) available for interactive control"
fi

# Test Python packages
echo "🐍 Testing Python packages..."
$PYTHON_CMD -c "
# Core GUI framework
try:
    import tkinter
    print('✅ tkinter available')
except ImportError:
    print('❌ tkinter missing')

# Image processing (for screenshots)
try:
    import PIL
    print('✅ Pillow available')
except ImportError:
    print('❌ Pillow missing')

# Audio processing (for voice commands)
try:
    import sounddevice
    print('✅ sounddevice available')
except ImportError:
    print('❌ sounddevice missing')

try:
    import soundfile
    print('✅ soundfile available')
except ImportError:
    print('❌ soundfile missing')

# Desktop automation
try:
    import pyautogui
    print('✅ pyautogui available')
except ImportError:
    print('❌ pyautogui missing')

try:
    import pynput
    print('✅ pynput available')
except ImportError:
    print('❌ pynput missing')

# System monitoring (for VNC/process management)
try:
    import psutil
    print('✅ psutil available')
except ImportError:
    print('❌ psutil missing')

# AI/Voice processing
try:
    import google.generativeai
    print('✅ google-generativeai available')
except ImportError:
    print('❌ google-generativeai missing')

# Environment configuration
try:
    import dotenv
    print('✅ python-dotenv available')
except ImportError:
    print('❌ python-dotenv missing')

# Security/encryption (for auth)
try:
    import cryptography
    print('✅ cryptography available')
except ImportError:
    print('❌ cryptography missing')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
if command -v uv &> /dev/null; then
    echo "1. Run the test script: uv run python scripts/test_new_desktop_system.py"
    echo "2. If tests pass, run: uv run python main.py"
else
    echo "1. Run the test script: python3 scripts/test_new_desktop_system.py"
    echo "2. If tests pass, run: python3 main.py"
fi
echo "3. Check logs if you encounter issues"
echo ""
echo "Troubleshooting:"
echo "- Make sure you're running in a VM with graphical interface"
echo "- Ensure DISPLAY variable is set (echo \$DISPLAY)"
echo "- Check /tmp/samsung_ai_os.log for detailed logs"
