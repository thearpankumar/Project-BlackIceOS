"""
VNC Server Management
Manages VNC servers for AI display viewing
"""

import logging
import subprocess
import time
from typing import Any

import psutil


class VNCServer:
    """Manages VNC server for AI display"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.vnc_process: subprocess.Popen[bytes] | None = None
        self.display: str | None = None
        self.port: int | None = None
        self.is_running = False

    def start_vnc_for_display(self, display: str, port: int = 5900) -> bool:
        """Start VNC server for the specified display"""
        try:
            # Check if VNC server is already running for this display
            if self.is_vnc_running() and self.display == display:
                self.logger.info(f"VNC server already running for {display}")
                return True

            # Stop any existing VNC server
            self.stop_vnc_server()

            # Check if x11vnc is available
            if not self._check_x11vnc_available():
                self.logger.error("x11vnc not found. Install with: sudo apt install x11vnc")
                return False

            # Find available port
            actual_port = self._find_available_port(port)
            if not actual_port:
                self.logger.error(f"No available ports starting from {port}")
                return False

            # Build VNC server command
            vnc_cmd = [
                '/usr/bin/x11vnc',
                '-display',
                display,
                '-rfbport',
                str(actual_port),  # Use -rfbport instead of -port
                '-localhost',  # Security: only local connections
                '-shared',  # Allow multiple clients
                '-forever',  # Keep running after client disconnects
                '-nopw',  # No password for local connections
                '-quiet',  # Reduce log noise
                '-bg',  # Run in background
            ]

            self.logger.info(f"Starting VNC server: {' '.join(vnc_cmd)}")

            # Start VNC server
            result = subprocess.run(  # noqa: S603
                vnc_cmd, capture_output=True, text=True, timeout=10, check=True
            )

            if result.returncode == 0:
                # Wait a moment for server to start
                time.sleep(2)

                # Verify server is running
                if self._verify_vnc_running(actual_port):
                    self.display = display
                    self.port = actual_port
                    self.is_running = True
                    self.logger.info(f"VNC server started successfully on port {actual_port}")
                    return True
                else:
                    self.logger.error("VNC server failed to start properly")
                    return False
            else:
                self.logger.error(f"VNC server failed to start: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("VNC server startup timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error starting VNC server: {e}")
            return False

    def stop_vnc_server(self) -> bool:
        """Stop the VNC server"""
        try:
            if not self.is_running:
                return True

            # Find and kill x11vnc processes for our display/port
            killed = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'x11vnc':
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                        # Check if this is our VNC server
                        display_match = self.display and self.display in cmdline
                        port_match = self.port and str(self.port) in cmdline
                        if display_match or port_match:
                            self.logger.info(f"Terminating VNC server process {proc.info['pid']}")
                            proc.terminate()
                            proc.wait(timeout=5)
                            killed = True

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.TimeoutExpired,
                ):
                    continue

            # Reset state
            self.vnc_process = None
            self.display = None
            self.port = None
            self.is_running = False

            if killed:
                self.logger.info("VNC server stopped successfully")
            else:
                self.logger.info("No VNC server processes found to stop")

            return True

        except Exception as e:
            self.logger.error(f"Error stopping VNC server: {e}")
            return False

    def get_vnc_connection_info(self) -> dict[str, Any] | None:
        """Get VNC connection information"""
        if not self.is_running:
            return None

        return {
            'host': 'localhost',
            'port': self.port,
            'display': self.display,
            'url': f'vnc://localhost:{self.port}',
            'running': self.is_running,
        }

    def is_vnc_running(self) -> bool:
        """Check if VNC server is running"""
        if not self.is_running or not self.port:
            return False

        return self._verify_vnc_running(self.port)

    def _check_x11vnc_available(self) -> bool:
        """Check if x11vnc is installed"""
        try:
            result = subprocess.run(['/usr/bin/which', 'x11vnc'], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def _find_available_port(self, start_port: int) -> int | None:
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 10):
            if self._is_port_available(port):
                return port
        return None

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False

    def _verify_vnc_running(self, port: int) -> bool:
        """Verify VNC server is actually running on the port"""
        try:
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False

    def get_status(self) -> dict[str, Any]:
        """Get VNC server status"""
        return {
            'running': self.is_running,
            'display': self.display,
            'port': self.port,
            'connection_info': self.get_vnc_connection_info(),
        }

    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.stop_vnc_server()
