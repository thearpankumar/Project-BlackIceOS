# Kali Linux Setup Guide

This guide provides specific instructions for setting up Kali AI OS on Kali Linux.

## Kali Linux Package Names

Kali Linux (Debian-based) uses different package names than Ubuntu:

### Graphics Libraries (Kali/Debian)
```bash
# Kali Linux specific packages
libgl1-mesa-dri      # DRI drivers
libgl1-mesa-glx      # GLX library (still available in Debian/Kali)
libegl1-mesa0        # EGL library (note the '0' suffix)
mesa-utils-extra     # Extended Mesa utilities
```

### Quick Installation (Kali Linux)
```bash
# Clone repository
git clone <repository-url>
cd kali-ai-os

# Run the automated installer (now Kali-compatible)
sudo ./scripts/install_service.sh

# The installer automatically detects Kali and uses correct packages
```

### Manual Installation (Kali Linux)
```bash
# Install system dependencies for Kali Linux
sudo apt update && sudo apt install -y \
  python3 python3-pip python3-venv \
  xvfb x11-utils wmctrl xdotool scrot \
  tesseract-ocr tesseract-ocr-eng \
  libgl1-mesa-dri libgl1-mesa-glx \
  libegl1-mesa0 mesa-utils-extra \
  libglib2.0-0 libsm6 libxext6 \
  libxrender-dev libgomp1 \
  libgtk-3-0 libqt5widgets5 \
  imagemagick dbus-x11

# Install Python dependencies
uv sync  # or pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Run development server
uv run python main.py
```

## Kali-Specific Notes

### Package Differences
| Component | Ubuntu 24.04 | Kali Linux |
|-----------|---------------|------------|
| GLX Library | `libglx-mesa0` | `libgl1-mesa-glx` |
| EGL Library | `libegl1-mesa` | `libegl1-mesa0` |
| Mesa Utils | `mesa-utils` | `mesa-utils-extra` |

### Virtual Display Setup
```bash
# Kali Linux supports both methods
export DISPLAY=:1
Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &

# Verify
DISPLAY=:1 xrandr --listmonitors
```

### Security Tools Integration
Kali Linux comes with security tools pre-installed:

```bash
# Verify security tools are available
which burpsuite    # /usr/bin/burpsuite
which wireshark    # /usr/bin/wireshark
which nmap         # /usr/bin/nmap
which metasploit   # /usr/bin/msfconsole
```

### Kali-Specific Optimizations
```bash
# Add to .env for Kali optimization
VM_SCREENSHOT_QUALITY=80
VM_ANIMATION_DELAY=0.15
VM_TEMPLATE_CONFIDENCE=0.8
```

## Troubleshooting Kali Linux

### Package Not Found Issues
If you encounter package issues:

```bash
# Update package lists
sudo apt update

# Search for alternative package names
apt search mesa | grep -i gl
apt search egl
```

### Graphics Issues
```bash
# Install additional graphics support
sudo apt install -y \
  mesa-vulkan-drivers \
  libvulkan1 \
  vulkan-tools

# Test OpenGL
glxinfo | grep "OpenGL version"
```

### Permission Issues
```bash
# Add user to necessary groups
sudo usermod -a -G video,audio,input $USER

# Logout and login again for groups to take effect
```

### X11 Issues
```bash
# Install additional X11 packages if needed
sudo apt install -y \
  xorg-dev \
  xserver-xorg-core \
  xserver-xorg-video-dummy
```

## Kali Rolling Updates

Kali Linux uses rolling releases, so packages may change:

```bash
# Keep system updated
sudo apt update && sudo apt upgrade

# If packages are removed/renamed, check:
apt list --upgradable
```

## Performance on Kali Linux

Kali Linux typically performs well for this application:

### Expected Performance
- **Response Time**: <80ms (better than Ubuntu in VMs)
- **Memory Usage**: <400MB (efficient Debian base)
- **CPU Usage**: <25% during automation

### Kali VM Optimization
```bash
# Optimize for VM usage
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=5' | sudo tee -a /etc/sysctl.conf
```

## Service Management on Kali

After installation:

```bash
# Service management (same as other systems)
kali-ai-desktop start
kali-ai-desktop status
kali-ai-desktop test

# View logs
journalctl -u kali-ai-desktop -f
```

## Integration with Kali Tools

The system integrates seamlessly with Kali's pre-installed tools:

### Voice Commands Examples
```
"Computer, open Burp Suite and configure proxy"
"Computer, run nmap stealth scan on 192.168.1.0/24"
"Computer, start Wireshark on eth0"
"Computer, launch Metasploit and search for apache exploits"
```

All Kali security tools are automatically detected and integrated with the voice control system.
