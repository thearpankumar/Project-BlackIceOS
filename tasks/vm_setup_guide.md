# QEMU/Kali VM Setup Guide for Kali AI-OS

## Overview
This guide provides comprehensive instructions for setting up a QEMU virtual machine running Kali Linux with shared folder access to the Kali AI-OS codebase. This setup enables development and testing of the AI-OS system within an isolated VM environment.

## Prerequisites

### Host System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **CPU**: 8+ cores with virtualization support (Intel VT-x or AMD-V)
- **RAM**: 16GB+ (will allocate 8GB to VM)
- **Storage**: 100GB+ free space
- **Network**: Internet connection for downloads

### Required Software
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y qemu-kvm qemu-utils virt-manager libvirt-daemon-system libvirt-clients bridge-utils

# Enable virtualization
sudo systemctl enable --now libvirtd
sudo usermod -a -G libvirt $USER
sudo usermod -a -G kvm $USER

# Arch Linux
sudo pacman -S qemu-full virt-manager libvirt dnsmasq bridge-utils

# macOS (using Homebrew)
brew install qemu

# Windows (using Chocolatey)
choco install qemu
```

## VM Setup Process

### 1. Download Kali Linux ISO
```bash
# Create VM directory
mkdir -p ~/vm/kali-ai-os
cd ~/vm/kali-ai-os

# Download Kali Linux ISO (latest version)
wget -O kali-linux.iso https://cdimage.kali.org/kali-2024.3/kali-linux-2024.3-installer-amd64.iso

# Verify checksum (optional but recommended)
wget https://cdimage.kali.org/kali-2024.3/SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing
```

### 2. Create VM Disk Image
```bash
# Create 80GB virtual disk
qemu-img create -f qcow2 kali-ai-os.qcow2 80G

# Verify disk creation
qemu-img info kali-ai-os.qcow2
```

### 3. Initial VM Installation
```bash
#!/bin/bash
# scripts/install_kali_vm.sh

VM_NAME="kali-ai-os"
ISO_PATH="$(pwd)/kali-linux.iso"
DISK_PATH="$(pwd)/kali-ai-os.qcow2"
SHARED_DIR="$(dirname $(pwd))/Samsung-AI-os"

qemu-system-x86_64 \
    -name "$VM_NAME" \
    -machine type=q35,accel=kvm \
    -cpu host \
    -smp cores=4,threads=2 \
    -m 8192 \
    -drive file="$DISK_PATH",format=qcow2,if=virtio \
    -cdrom "$ISO_PATH" \
    -boot order=cd \
    -netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:8080 \
    -device virtio-net-pci,netdev=net0 \
    -display gtk \
    -vga virtio \
    -sound-model hda \
    -audiodev pulseaudio,id=audio0 \
    -device intel-hda \
    -device hda-duplex,audiodev=audio0 \
    -usb \
    -device usb-tablet \
    -rtc base=localtime \
    -k en-us

echo "VM started for installation. Follow Kali Linux installation wizard."
echo "Recommended settings:"
echo "  - Username: kali"
echo "  - Hostname: kali-ai-os"
echo "  - Install SSH server"
echo "  - Install desktop environment (XFCE recommended)"
```

### 4. Kali Linux Installation Settings
During installation, configure:

- **Hostname**: kali-ai-os
- **Domain**: (leave blank)
- **Username**: kali
- **Password**: (choose strong password)
- **Partitioning**: Use entire disk, single partition
- **Software**:
  - Desktop environment (XFCE recommended for performance)
  - SSH server
  - Standard system utilities

### 5. Post-Installation VM Startup Script
```bash
#!/bin/bash
# scripts/start_kali_vm.sh

VM_NAME="kali-ai-os"
DISK_PATH="$(pwd)/kali-ai-os.qcow2"
SHARED_DIR="$(dirname $(pwd))/Samsung-AI-os"

# Ensure shared directory exists
mkdir -p "$SHARED_DIR"

echo "Starting Kali AI-OS VM..."
echo "Shared directory: $SHARED_DIR"
echo "SSH: localhost:2222"
echo "Web interface: localhost:8080"

qemu-system-x86_64 \
    -name "$VM_NAME" \
    -machine type=q35,accel=kvm \
    -cpu host \
    -smp cores=4,threads=2 \
    -m 8192 \
    -drive file="$DISK_PATH",format=qcow2,if=virtio \
    -netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:8080,hostfwd=tcp::8000-:8000 \
    -device virtio-net-pci,netdev=net0 \
    -fsdev local,security_model=mapped,id=fsdev0,path="$SHARED_DIR" \
    -device virtio-9p-pci,id=fs0,fsdev=fsdev0,mount_tag=shared \
    -display gtk \
    -vga virtio \
    -sound-model hda \
    -audiodev pulseaudio,id=audio0 \
    -device intel-hda \
    -device hda-duplex,audiodev=audio0 \
    -usb \
    -device usb-tablet \
    -rtc base=localtime \
    -k en-us \
    -enable-kvm \
    -daemonize

echo "VM started successfully!"
echo ""
echo "To connect via SSH:"
echo "  ssh -p 2222 kali@localhost"
echo ""
echo "To access web interface:"
echo "  http://localhost:8080"
```

## Shared Folder Configuration

### 1. Mount Shared Folder in VM
```bash
# Connect to VM via SSH
ssh -p 2222 kali@localhost

# Create mount point
sudo mkdir -p /mnt/shared

# Mount shared folder
sudo mount -t 9p -o trans=virtio,version=9p2000.L shared /mnt/shared

# Verify mount
ls -la /mnt/shared

# Make mount permanent
echo 'shared /mnt/shared 9p trans=virtio,version=9p2000.L,_netdev,rw 0 0' | sudo tee -a /etc/fstab

# Test automatic mount
sudo umount /mnt/shared
sudo mount -a
ls -la /mnt/shared
```

### 2. Create Symbolic Links for Development
```bash
# In the VM, create convenient symlinks
ln -s /mnt/shared ~/kali-ai-os
ln -s /mnt/shared/auth-server ~/auth-server
ln -s /mnt/shared/kali-ai-os ~/kali-ai-os-code

# Verify access
ls -la ~/kali-ai-os
```

## VM Configuration for Kali AI-OS

### 1. Install Required System Packages
```bash
#!/bin/bash
# scripts/setup_vm_environment.sh

echo "Setting up Kali AI-OS development environment..."

# Update system
sudo apt update && sudo apt full-upgrade -y

# Install Python development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential cmake git curl wget

# Install audio support
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y espeak espeak-data libespeak-dev

# Install GUI automation dependencies
sudo apt install -y xvfb x11vnc xdotool wmctrl
sudo apt install -y python3-tk python3-pil python3-pil.imagetk
sudo apt install -y libgtk-3-dev libcairo2-dev libgirepository1.0-dev

# Install security tools (if not already present)
sudo apt install -y nmap nikto dirb gobuster
sudo apt install -y burpsuite zaproxy wireshark
sudo apt install -y metasploit-framework aircrack-ng
sudo apt install -y sqlmap hashcat john

# Install Docker for auth server
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo usermod -a -G docker kali

# Install Node.js for web interface
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

echo "System setup complete!"
```

### 2. Configure Audio System
```bash
#!/bin/bash
# scripts/setup_audio.sh

echo "Configuring audio for voice recognition..."

# Enable PulseAudio
systemctl --user enable pulseaudio.service
systemctl --user start pulseaudio.service

# Configure audio for VM
echo "load-module module-udev-detect" >> ~/.config/pulse/default.pa
echo "load-module module-native-protocol-unix" >> ~/.config/pulse/default.pa

# Test audio
arecord -l  # List recording devices
aplay -l   # List playback devices

# Test microphone (record 5 seconds)
arecord -f cd -t wav -d 5 test.wav && aplay test.wav

echo "Audio configuration complete!"
```

### 3. Setup Development Environment
```bash
#!/bin/bash
# scripts/setup_development.sh

cd /mnt/shared

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install base requirements
pip install --upgrade pip setuptools wheel

# Install development tools
pip install pytest pytest-cov pytest-asyncio
pip install black flake8 mypy
pip install jupyter notebook

# Install Kali AI-OS requirements
pip install -r requirements.txt

echo "Development environment ready!"
echo ""
echo "To activate environment:"
echo "  cd /mnt/shared && source venv/bin/activate"
```

## Network Configuration

### 1. Port Forwarding Setup
The VM startup script includes these port forwards:
- **SSH**: Host port 2222 → VM port 22
- **Web Interface**: Host port 8080 → VM port 8080
- **Auth Server**: Host port 8000 → VM port 8000

### 2. Additional Network Setup
```bash
# In VM: Configure firewall for development
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

# Test network connectivity
ping -c 3 google.com
curl -I http://localhost:8080
```

## Development Workflow

### 1. Starting Development Session
```bash
# On host: Start VM
cd ~/vm/kali-ai-os
bash scripts/start_kali_vm.sh

# Connect to VM
ssh -p 2222 kali@localhost

# In VM: Navigate to project
cd /mnt/shared
source venv/bin/activate

# Start auth server
cd auth-server
docker-compose up -d
cd ..

# Start Kali AI-OS development
cd kali-ai-os
python -m pytest tests/ -v
```

### 2. Code Synchronization
Since the shared folder is mounted from the host, all code changes are automatically synchronized:

- **Edit on host**: Use your preferred IDE/editor on the host system
- **Run in VM**: Execute and test code within the Kali Linux environment
- **No manual copying**: Files are shared in real-time

### 3. Testing Workflow
```bash
# In VM: Run specific task tests
cd /mnt/shared/kali-ai-os

# Test Task 1: Authentication
cd auth-server && python -m pytest tests/ -v

# Test Task 2: Voice Recognition
python -m pytest tests/voice/ -v

# Test Task 3: Desktop Automation
python -m pytest tests/desktop/ -v

# Run full integration tests
python -m pytest tests/integration/ -v
```

## Performance Optimization

### 1. VM Performance Tuning
```bash
# In VM: Optimize for development
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable avahi-daemon

# Optimize SSD performance
echo 'deadline' | sudo tee /sys/block/vda/queue/scheduler
```

### 2. Memory Management
```bash
# Monitor VM memory usage
free -h
top

# Configure swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Backup and Snapshots

### 1. Create VM Snapshot
```bash
# On host: Create snapshot before major changes
cd ~/vm/kali-ai-os

# Stop VM first
sudo pkill qemu-system-x86_64

# Create snapshot
qemu-img snapshot -c "clean-install" kali-ai-os.qcow2

# List snapshots
qemu-img snapshot -l kali-ai-os.qcow2

# Restore snapshot if needed
qemu-img snapshot -a "clean-install" kali-ai-os.qcow2
```

### 2. Backup Development Data
```bash
# In VM: Backup important data
cd /mnt/shared

# Export development environment
pip freeze > requirements-vm.txt

# Backup configurations
cp -r ~/.config ~/kali-ai-os-config-backup
cp ~/.bashrc ~/kali-ai-os-config-backup/

# Create project backup
tar -czf kali-ai-os-backup-$(date +%Y%m%d).tar.gz kali-ai-os/
```

## Troubleshooting

### Common Issues and Solutions

#### 1. VM Won't Start
```bash
# Check KVM support
lscpu | grep Virtualization
ls -la /dev/kvm

# Verify libvirt service
sudo systemctl status libvirtd

# Check QEMU installation
qemu-system-x86_64 --version
```

#### 2. Shared Folder Not Working
```bash
# In VM: Check 9p module
lsmod | grep 9p
sudo modprobe 9pnet_virtio

# Manually mount with debug
sudo mount -t 9p -o trans=virtio,version=9p2000.L,debug=0x04 shared /mnt/shared

# Check host directory permissions
ls -la /path/to/Samsung-AI-os
```

#### 3. Audio Not Working
```bash
# In VM: Check audio devices
arecord -l
aplay -l

# Restart PulseAudio
pulseaudio -k
pulseaudio --start

# Test QEMU audio passthrough
# (Add -audiodev flag to QEMU command)
```

#### 4. Network Issues
```bash
# Check network interface
ip addr show
ping 8.8.8.8

# Test port forwarding
nc -z localhost 2222  # On host
netstat -tlnp | grep 22  # In VM
```

#### 5. Performance Issues
```bash
# Check resource usage
htop
iotop
vmstat 1

# Optimize VM settings
# Reduce allocated RAM if needed
# Enable KVM acceleration
# Use SSD for VM storage
```

## Advanced Configuration

### 1. GPU Passthrough (Optional)
For advanced graphics support:
```bash
# Enable IOMMU
echo 'GRUB_CMDLINE_LINUX="intel_iommu=on"' | sudo tee -a /etc/default/grub
sudo update-grub

# Configure VFIO
echo 'vfio-pci' | sudo tee -a /etc/modules
```

### 2. USB Device Passthrough
```bash
# List USB devices
lsusb

# Add USB passthrough to QEMU command
# -usb -device usb-host,vendorid=0x1234,productid=0x5678
```

### 3. Multiple Monitor Support
```bash
# Configure additional displays
qemu-system-x86_64 \
    ... \
    -display gtk \
    -vga virtio \
    -device virtio-gpu-pci \
    ...
```

## Security Considerations

### 1. VM Isolation
- VM is isolated from host system
- Only specified ports are forwarded
- Shared folder has controlled access

### 2. Network Security
```bash
# In VM: Configure firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw allow 8000/tcp
```

### 3. Data Protection
- Regular snapshots before major changes
- Encrypted VM disk (optional)
- Secure authentication setup

## Automation Scripts

### 1. Complete Setup Script
```bash
#!/bin/bash
# scripts/complete_vm_setup.sh

set -e

echo "=== Kali AI-OS VM Complete Setup ==="

# Check if running on host
if [ -f /.dockerenv ] || [ -f /proc/vz/veinfo ]; then
    echo "Error: This script should run on the host system"
    exit 1
fi

# Create VM directory
mkdir -p ~/vm/kali-ai-os
cd ~/vm/kali-ai-os

# Download Kali ISO if not exists
if [ ! -f "kali-linux.iso" ]; then
    echo "Downloading Kali Linux ISO..."
    wget -O kali-linux.iso https://cdimage.kali.org/kali-2024.3/kali-linux-2024.3-installer-amd64.iso
fi

# Create VM disk if not exists
if [ ! -f "kali-ai-os.qcow2" ]; then
    echo "Creating VM disk..."
    qemu-img create -f qcow2 kali-ai-os.qcow2 80G
fi

# Copy scripts
cp -r $(dirname $0)/../Samsung-AI-os/tasks/scripts/* .

# Make scripts executable
chmod +x *.sh

echo "VM setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: ./install_kali_vm.sh  (for initial installation)"
echo "2. Run: ./start_kali_vm.sh    (to start VM after installation)"
echo "3. Connect: ssh -p 2222 kali@localhost"
```

### 2. Daily Development Script
```bash
#!/bin/bash
# scripts/daily_dev.sh

echo "Starting daily Kali AI-OS development session..."

# Start VM
./start_kali_vm.sh

# Wait for VM to be ready
echo "Waiting for VM to be ready..."
sleep 30

# Connect and setup environment
ssh -p 2222 kali@localhost << 'EOF'
    cd /mnt/shared
    source venv/bin/activate

    # Start auth server
    cd auth-server
    docker-compose up -d
    cd ..

    # Run quick health check
    python -c "
from src.core.health_check import quick_health_check
print('System health:', quick_health_check())
"

    echo "Development environment ready!"
EOF

echo "VM and development environment started successfully!"
echo "Connect with: ssh -p 2222 kali@localhost"
```

This comprehensive VM setup guide provides everything needed to run Kali AI-OS in a virtualized environment with shared folder access for seamless development.
