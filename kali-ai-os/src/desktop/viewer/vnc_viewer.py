"""
VNC Viewer Implementation
Real-time VNC viewer for AI display
"""

import os
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from typing import Any

from PIL import Image, ImageTk

from ..display.vnc_server import VNCServer
from .base_viewer import BaseViewer
from .vnc_viewer_simple import launch_remmina_simple


class VNCViewer(BaseViewer):
    """VNC-based real-time viewer for AI display"""

    def __init__(self) -> None:
        super().__init__()
        self.vnc_server = VNCServer()
        self.update_thread: threading.Thread | None = None
        self.stop_thread = False
        self.connection_info: dict[str, Any] | None = None
        self.refresh_rate = 2.0  # seconds
        self.image_label: tk.Label | None = None

    def start_viewing(self, display: str) -> bool:
        """Start VNC viewing of the display"""
        try:
            self.logger.info(f"Starting VNC viewer for display {display}")

            # Start VNC server for the display
            if not self.vnc_server.start_vnc_for_display(display):
                self.logger.error("Failed to start VNC server")
                return False

            # Get connection info
            self.connection_info = self.vnc_server.get_vnc_connection_info()
            if not self.connection_info:
                self.logger.error("Failed to get VNC connection info")
                return False

            self.display: str | None = display
            self.is_viewing = True

            self.logger.info(f"VNC viewer started successfully for {display}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting VNC viewer: {e}")
            return False

    def stop_viewing(self) -> bool:
        """Stop VNC viewing"""
        try:
            self.logger.info("Stopping VNC viewer")

            # Stop update thread
            self.stop_thread = True
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=5)

            # Stop VNC server
            self.vnc_server.stop_vnc_server()

            # Reset state
            self.is_viewing = False
            self.display = None
            self.connection_info = None
            self.stop_thread = False

            self.logger.info("VNC viewer stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping VNC viewer: {e}")
            return False

    def get_viewer_widget(self, parent: tk.Widget) -> tk.Widget | None:
        """Get VNC viewer widget for embedding in GUI"""
        try:
            if not self.is_viewing or not self.connection_info:
                return self._create_status_widget(parent, "VNC viewer not active")

            # Create VNC viewer widget
            vnc_frame = tk.Frame(parent, bg='black', relief='sunken', bd=2)

            # Create header with connection info
            header_frame = tk.Frame(vnc_frame, bg='#2d2d2d', height=30)
            header_frame.pack(fill='x', padx=2, pady=2)
            header_frame.pack_propagate(False)

            tk.Label(
                header_frame,
                text=f"🔗 VNC: {self.connection_info['host']}:{self.connection_info['port']}",
                fg='#00ff00',
                bg='#2d2d2d',
                font=('Consolas', 10),
            ).pack(side='left', padx=10, pady=5)

            # Status indicator
            status_color = '#00ff00' if self.vnc_server.is_vnc_running() else '#ff0000'
            status_text = 'Connected' if self.vnc_server.is_vnc_running() else 'Disconnected'

            tk.Label(
                header_frame,
                text=f"● {status_text}",
                fg=status_color,
                bg='#2d2d2d',
                font=('Arial', 10, 'bold'),
            ).pack(side='right', padx=10, pady=5)

            # Create VNC display area with options
            display_frame = tk.Frame(vnc_frame, bg='black')
            display_frame.pack(fill='both', expand=True, padx=2, pady=2)

            # Control buttons frame
            control_frame = tk.Frame(display_frame, bg='#2d2d2d', height=30)
            control_frame.pack(fill='x', padx=2, pady=2)
            control_frame.pack_propagate(False)

            # VNC Client button
            tk.Button(
                control_frame,
                text="🖱️ Launch VNC Client",
                bg='#28a745',
                fg='white',
                font=('Arial', 10, 'bold'),
                command=self._launch_simple_vnc,
                relief='raised',
                bd=2,
            ).pack(side='left', padx=5, pady=2)

            # Focus restore button
            tk.Button(
                control_frame,
                text="🔄 Focus GUI",
                bg='#6c757d',
                fg='white',
                font=('Arial', 9),
                command=self._maintain_tkinter_focus,
                relief='raised',
                bd=2,
            ).pack(side='left', padx=5, pady=2)

            # Info label
            tk.Label(
                control_frame,
                text="For mouse/keyboard control, use VNC client • Click Focus GUI if needed",
                fg='#aaaaaa',
                bg='#2d2d2d',
                font=('Arial', 9),
            ).pack(side='left', padx=10, pady=2)

            # Screenshot display area
            screenshot_frame = tk.Frame(display_frame, bg='black')
            screenshot_frame.pack(fill='both', expand=True, padx=2, pady=2)

            # Image display label
            self.image_label = tk.Label(screenshot_frame, bg='black', text='Loading...', fg='white')
            self.image_label.pack(fill='both', expand=True)

            # Start image update thread
            self._start_image_updates()

            self.widget = vnc_frame
            return vnc_frame

        except Exception as e:
            self.logger.error(f"Error creating VNC widget: {e}")
            return self._create_status_widget(parent, f"VNC error: {e}")

    def _start_image_updates(self) -> None:
        """Start thread to update VNC display with screenshots"""
        if self.update_thread and self.update_thread.is_alive():
            return

        self.stop_thread = False

        def update_loop() -> None:
            while not self.stop_thread and self.is_viewing:
                try:
                    # Take screenshot of AI display using scrot directly
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                        screenshot_path = tmpfile.name

                    # Use scrot directly with the display to avoid context issues
                    import os
                    import subprocess

                    # Set DISPLAY environment for this subprocess
                    env = os.environ.copy()
                    env['DISPLAY'] = self.display or ':0'

                    # Use scrot to capture the virtual display
                    result = subprocess.run(  # noqa: S603
                        [
                            '/usr/bin/scrot',
                            screenshot_path,
                            '--overwrite',  # Overwrite existing file
                        ],
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=True,
                    )

                    if result.returncode == 0 and os.path.exists(screenshot_path):
                        # Load and display image
                        try:
                            image: Image.Image = Image.open(screenshot_path)

                            # Resize to fit widget while maintaining aspect ratio
                            widget_width = 800  # Default width
                            widget_height = 600  # Default height

                            if (
                                hasattr(self, 'image_label')
                                and self.image_label is not None
                                and self.image_label.winfo_exists()
                            ):
                                widget_width = max(self.image_label.winfo_width(), 400)
                                widget_height = max(self.image_label.winfo_height(), 300)

                            # Calculate size maintaining aspect ratio
                            img_ratio = image.width / image.height
                            widget_ratio = widget_width / widget_height

                            if img_ratio > widget_ratio:
                                new_width = widget_width
                                new_height = int(widget_width / img_ratio)
                            else:
                                new_width = int(widget_height * img_ratio)
                                new_height = widget_height

                            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(image)

                            # Update label
                            if (
                                hasattr(self, 'image_label')
                                and self.image_label is not None
                                and self.image_label.winfo_exists()
                            ):
                                self.image_label.configure(image=photo, text="")
                                self.image_label.image = photo  # type: ignore[attr-defined] # noqa: B010

                        except Exception as e:
                            self.logger.debug(f"Image display error: {e}")

                        # Clean up screenshot
                        try:
                            import os

                            os.remove(screenshot_path)
                        except OSError:
                            pass  # noqa: S110

                    # Wait before next update
                    time.sleep(self.refresh_rate)

                except Exception as e:
                    self.logger.error(f"VNC update error: {e}")
                    time.sleep(self.refresh_rate)

        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()

    def _create_status_widget(self, parent: tk.Widget, message: str) -> tk.Widget:
        """Create a status widget showing a message"""
        frame = tk.Frame(parent, bg='#2d2d2d', relief='sunken', bd=2)

        tk.Label(
            frame,
            text=message,
            fg='#ffaa00',
            bg='#2d2d2d',
            font=('Arial', 12),
            wraplength=400,
        ).pack(expand=True, fill='both', padx=20, pady=20)

        return frame

    def _launch_vnc_client(self) -> None:
        """Launch external VNC client for interactive control"""
        try:
            if not self.connection_info:
                self.logger.error("No VNC connection info available")
                return

            host = self.connection_info['host']
            port = self.connection_info['port']

            self.logger.info("=== STARTING VNC CLIENT LAUNCH ===")

            # ONLY try Remmina - force it to be the only choice
            self.logger.info("Checking for Remmina...")
            remmina_result = subprocess.run(['/usr/bin/which', 'remmina'], capture_output=True)

            if remmina_result.returncode == 0:
                self.logger.info("Remmina found! Launching Remmina ONLY...")

                # Try different Remmina launch methods for visibility
                # Method 1: Direct connection
                vnc_cmd = ['/usr/bin/remmina', '-c', f'vnc://{host}:{port}']
                self.logger.info(f"Trying Remmina direct connect: {' '.join(vnc_cmd)}")

                # Set environment to ensure Remmina window is visible
                import time  # Import time here to fix scope issue

                env = os.environ.copy()
                env['DISPLAY'] = ':0'  # Force to user display
                env['G_MESSAGES_DEBUG'] = 'remmina'  # Enable Remmina debug output

                try:
                    process = subprocess.Popen(  # noqa: S603
                        vnc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
                    )

                    time.sleep(3.0)  # Give more time for window to appear

                    # Check if Remmina window actually appeared
                    self.logger.info("Checking for Remmina window...")
                    window_check = subprocess.run(
                        ['/usr/bin/wmctrl', '-l'], capture_output=True, text=True
                    )
                    if window_check.returncode == 0:
                        windows = window_check.stdout
                        self.logger.info(f"Current windows: {windows}")
                        if 'Remmina' in windows or 'remmina' in windows.lower():
                            self.logger.info("Remmina window found in window list!")
                            # Force window to be visible and focused
                            subprocess.run(
                                ['/usr/bin/wmctrl', '-a', 'Remmina'],
                                capture_output=True,
                            )
                            subprocess.run(
                                ['/usr/bin/wmctrl', '-R', 'Remmina'],
                                capture_output=True,
                            )
                        else:
                            self.logger.warning("Remmina window NOT found in window list")

                    if process.poll() is None:
                        self.logger.info(
                            f"SUCCESS: Remmina direct connect launched (PID: {process.pid})"
                        )

                        # Don't try to communicate immediately - let it run
                        self.logger.info("Remmina direct connection running")

                        self._maintain_tkinter_focus()
                        return  # EXIT HERE - Don't try other methods
                    else:
                        stdout, stderr = process.communicate()
                        self.logger.error(f"Remmina process exited: {process.returncode}")
                        if stdout:
                            self.logger.error(f"Stdout: {stdout.decode().strip()}")
                        if stderr:
                            self.logger.error(f"Stderr: {stderr.decode().strip()}")

                except Exception as e:
                    self.logger.error(f"Remmina launch exception: {e}")

                # Method 2: Launch Remmina main window with quick connect (fallback)
                self.logger.info("Trying Remmina main window with quick connect...")
                vnc_cmd = ['/usr/bin/remmina', '--new', f'vnc://{host}:{port}']

                try:
                    process = subprocess.Popen(  # noqa: S603
                        vnc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
                    )

                    time.sleep(2.0)

                    if process.poll() is None:
                        self.logger.info(
                            f"SUCCESS: Remmina new connection launched (PID: {process.pid})"
                        )
                        # Check for window and bring to front
                        window_check = subprocess.run(
                            ['/usr/bin/wmctrl', '-l'], capture_output=True, text=True
                        )
                        if 'Remmina' in window_check.stdout:
                            subprocess.run(
                                ['/usr/bin/wmctrl', '-a', 'Remmina'],
                                capture_output=True,
                            )
                        self._maintain_tkinter_focus()
                        return  # EXIT HERE - Don't try Method 3
                    else:
                        stdout, stderr = process.communicate()
                        self.logger.error(f"Remmina main window failed: {process.returncode}")
                        if stderr:
                            self.logger.error(f"Error: {stderr.decode().strip()}")

                except Exception as e:
                    self.logger.error(f"Remmina main window exception: {e}")

                # Method 3: Simple Remmina launch (last resort)
                self.logger.info("Trying simple Remmina launch...")
                vnc_cmd = ['/usr/bin/remmina']

                process = subprocess.Popen(vnc_cmd, env=env)  # noqa: S603

                if process.poll() is None:
                    self.logger.info(f"SUCCESS: Remmina launched (PID: {process.pid})")
                    self._maintain_tkinter_focus()
                    return  # EXIT - Don't try any other clients
                else:
                    stdout, stderr = process.communicate()
                    self.logger.error("FAILED: Remmina failed to start:")
                    self.logger.error(f"  Return code: {process.returncode}")
                    if stderr:
                        self.logger.error(f"  Error: {stderr.decode().strip()}")
            else:
                self.logger.error("Remmina not found on system!")

            # Show error message - no fallback
            self.logger.error("=== NO VNC CLIENT LAUNCHED ===")

            import tkinter.messagebox as messagebox

            messagebox.showerror(
                "VNC Client Error",
                "Remmina not available. Install with:\nsudo apt install remmina",
            )

        except Exception as e:
            self.logger.error(f"Error launching VNC client: {e}")

    def refresh(self) -> bool:
        """Manually refresh the VNC display"""
        try:
            if not self.is_viewing:
                return False

            # VNC updates are automatic via thread
            # Just verify connection is still good
            if self.vnc_server.is_vnc_running():
                self.logger.debug("VNC refresh: connection healthy")
                return True
            else:
                self.logger.warning("VNC refresh: connection lost")
                return False

        except Exception as e:
            self.logger.error(f"VNC refresh error: {e}")
            return False

    def is_active(self) -> bool:
        """Check if VNC viewer is active"""
        return self.is_viewing and self.vnc_server.is_vnc_running()

    def get_viewer_type(self) -> str:
        """Return viewer type"""
        return "vnc"

    def set_refresh_rate(self, rate: float) -> None:
        """Set the refresh rate in seconds"""
        self.refresh_rate = max(0.5, min(10.0, rate))  # Clamp between 0.5 and 10 seconds
        self.logger.info(f"VNC refresh rate set to {self.refresh_rate}s")

    def _maintain_tkinter_focus(self) -> None:
        """Try to maintain focus on the tkinter main window"""
        try:
            # Try to find the main tkinter window through the widget hierarchy
            if hasattr(self, 'widget') and self.widget:
                root_widget = self.widget

                # Traverse up to find the root window
                while root_widget.master:
                    root_widget = root_widget.master

                # Bring the root window to front and focus
                root_widget.lift()
                root_widget.focus_force()
                root_widget.attributes('-topmost', True)

                # Remove topmost after a brief moment to allow normal interaction
                def remove_topmost() -> None:
                    try:
                        root_widget.attributes('-topmost', False)
                    except Exception as e:
                        self.logger.error(f"Error removing topmost: {e}")

                root_widget.after(1000, remove_topmost)  # Remove topmost after 1 second

                self.logger.debug("Tkinter window focus restored")

        except Exception as e:
            self.logger.debug(f"Could not maintain tkinter focus: {e}")

            # Fallback: try using wmctrl if available
            try:
                subprocess.run(
                    ['/usr/bin/wmctrl', '-a', 'Samsung AI-OS'],
                    capture_output=True,
                    timeout=2,
                )
                self.logger.debug("Used wmctrl to restore focus")
            except Exception as e:
                self.logger.debug(f"wmctrl not available for focus management: {e}")

    def _launch_simple_vnc(self) -> None:
        """Simple VNC client launcher - no multiple methods"""
        if not self.connection_info:
            self.logger.error("No VNC connection info available")
            return

        host = self.connection_info['host']
        port = self.connection_info['port']

        # Use simple launcher - ONLY ONE method
        success = launch_remmina_simple(host, port, self.logger)

        if success:
            self._maintain_tkinter_focus()
        else:
            import tkinter.messagebox as messagebox

            messagebox.showerror(
                "VNC Error",
                "Could not launch Remmina.\nInstall with: sudo apt install remmina",
            )

    def cleanup(self) -> bool:
        """Cleanup VNC viewer resources"""
        return self.stop_viewing()
