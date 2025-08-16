#!/bin/bash
# Cleanup script for X display :1 lock files

echo "=== Cleaning up X display :1 ==="

# Kill any existing Xvfb processes for :1
echo "1. Killing existing Xvfb :1 processes..."
pkill -f "Xvfb :1" 2>/dev/null || echo "   No Xvfb :1 processes found"

# Wait a moment
sleep 1

# Remove lock files
echo "2. Removing lock files..."
if [ -f "/tmp/.X1-lock" ]; then
    echo "   Removing /tmp/.X1-lock"
    sudo rm -f /tmp/.X1-lock || rm -f /tmp/.X1-lock
else
    echo "   /tmp/.X1-lock does not exist"
fi

if [ -e "/tmp/.X11-unix/X1" ]; then
    echo "   Removing /tmp/.X11-unix/X1"
    sudo rm -f /tmp/.X11-unix/X1 || rm -f /tmp/.X11-unix/X1
else
    echo "   /tmp/.X11-unix/X1 does not exist"
fi

echo "3. Cleanup complete!"
echo ""
echo "Now you can run the main application:"
echo "python3 main.py"
