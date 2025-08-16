"""
Virtual Display Manager
Handles creation, management, and cleanup of virtual displays for AI automation
"""

import logging
import os
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass


@dataclass
class DisplayInfo:
    """Information about a display"""

    display: str
    resolution: str
    process: subprocess.Popen | None
    is_running: bool
    creation_time: float


class VirtualDisplayManager:
    """Manages virtual displays for isolated AI automation"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.displays: dict[str, DisplayInfo] = {}  # Only tracks displays WE created
        self.ai_display: str | None = None
        self.user_display = ":0"  # Default user display
        self._cleanup_lock = threading.Lock()
        self._created_by_us: set[str] = set()  # Track which displays we created

    def create_ai_display(
        self, preferred_display: str = ":1", resolution: str = "1920x1080"
    ) -> str | None:
        """Create a virtual display for AI automation"""
        self.logger.info("Creating AI virtual display...")

        # Find available display
        display = self._find_available_display(preferred_display)
        if not display:
            self.logger.error("No available display found")
            return None

        # Create the virtual display
        if self._create_virtual_display(display, resolution):
            self.ai_display = display
            self.logger.info(f"AI display created: {display}")
            return display
        else:
            self.logger.error(f"Failed to create virtual display {display}")
            return None

    def _find_available_display(self, preferred: str) -> str | None:
        """Find an available display number"""
        current_display = os.environ.get('DISPLAY', ':0')
        current_num = self._extract_display_number(current_display)

        # Try alternative displays first to avoid conflicts
        alternatives = [":10", ":20", ":30", ":99", ":1"]
        for display in alternatives:
            display_num = self._extract_display_number(display)
            if display_num != current_num and self._is_display_available(display):
                return display

        # Try preferred display last
        preferred_num = self._extract_display_number(preferred)
        if preferred_num != current_num and self._is_display_available(preferred):
            return preferred

        return None

    def _extract_display_number(self, display: str) -> str:
        """Extract display number from display string"""
        return display.split(':')[1].split('.')[0] if ':' in display else '0'

    def _is_display_available(self, display: str) -> bool:
        """Check if a display is available (not in use)"""
        try:
            result = subprocess.run(  # noqa: S603,S607
                ['/usr/bin/xdpyinfo', '-display', display],
                capture_output=True,
                timeout=2,
            )
            is_available = result.returncode != 0  # Available if /usr/bin/xdpyinfo fails

            if not is_available:
                self.logger.debug(f"Display {display} is already in use")

            return is_available
        except Exception:
            return True  # Assume available if can't check

    def _create_virtual_display(self, display: str, resolution: str) -> bool:
        """Create a single virtual display"""
        try:
            # Only clean up if WE created this display before
            if display in self._created_by_us:
                self.logger.info(f"Cleaning up our previous display {display}")
                self._cleanup_display(display)
            else:
                self.logger.debug(f"Display {display} not created by us, checking availability")

            # Remove lock files
            display_num = self._extract_display_number(display)
            lock_files = [
                os.path.join(tempfile.gettempdir(), f'.X{display_num}-lock'),
                os.path.join(tempfile.gettempdir(), '.X11-unix', f'X{display_num}'),
            ]

            for lock_file in lock_files:
                try:
                    if os.path.exists(lock_file):
                        os.remove(lock_file)
                        self.logger.debug(f"Removed lock file: {lock_file}")
                except Exception as e:
                    self.logger.warning(f"Could not remove {lock_file}: {e}")

            # Create Xvfb command
            xvfb_cmd = [
                'Xvfb',
                display,
                '-screen',
                '0',
                f'{resolution}x24',
                '-ac',
                '+extension',
                'GLX',
                '+render',
                '-noreset',
                '-nolisten',
                'tcp',  # Security: disable TCP connections
            ]

            self.logger.info(f"Starting virtual display: {' '.join(xvfb_cmd)}")

            # Start Xvfb process
            process = subprocess.Popen(  # noqa: S603
                xvfb_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,  # Create new process group for cleanup
            )

            # Wait for display to be ready
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(0.5)

                if process.poll() is not None:
                    # Process died
                    stdout, stderr = process.communicate()
                    self.logger.error(f"Xvfb died: {stderr.decode()}")
                    return False

                # Test if display is accessible
                try:
                    result = subprocess.run(  # noqa: S603,S607
                        ['/usr/bin/xdpyinfo', '-display', display],
                        capture_output=True,
                        timeout=2,
                    )
                    if result.returncode == 0:
                        # Success!
                        display_info = DisplayInfo(
                            display=display,
                            resolution=resolution,
                            process=process,
                            is_running=True,
                            creation_time=time.time(),
                        )
                        self.displays[display] = display_info
                        self._created_by_us.add(display)  # Track that WE created this

                        # Setup display content
                        self._setup_display_content(display)

                        self.logger.info(f"Virtual display {display} ready (created by us)")
                        return True

                except subprocess.TimeoutExpired:
                    continue
                except Exception as e:
                    self.logger.debug(f"Display test attempt {attempt}: {e}")
                    continue

            # Failed to become ready
            self.logger.error(f"Display {display} failed to become ready")
            process.terminate()
            return False

        except Exception as e:
            self.logger.error(f"Exception creating virtual display: {e}")
            return False

    def _setup_display_content(self, display: str) -> None:
        """Setup initial content on virtual display"""
        try:
            # Set a background color
            subprocess.run(  # noqa: S603,S607
                ['/usr/bin/xsetroot', '-display', display, '-solid', '#2d2d2d'],
                timeout=5,
                capture_output=True,
            )

            # Start a simple window manager
            env = os.environ.copy()
            env['DISPLAY'] = display

            subprocess.Popen(  # noqa: S603,S607
                ['/usr/bin/openbox', '--replace'],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            self.logger.debug(f"Set up content for display {display}")

        except Exception as e:
            self.logger.warning(f"Could not setup display content: {e}")

    def _cleanup_display(self, display: str) -> None:
        """Clean up existing display processes"""
        try:
            # Kill any existing Xvfb processes for this display
            subprocess.run(  # noqa: S603,S607
                ['/usr/bin/pkill', '-f', f'Xvfb {display}'],
                capture_output=True,
                timeout=5,
            )

            time.sleep(1)  # Wait for processes to die

        except Exception as e:
            self.logger.debug(f"Cleanup display error: {e}")

    def get_ai_display(self) -> str | None:
        """Get the current AI display"""
        return self.ai_display

    def get_user_display(self) -> str:
        """Get the user's display"""
        return self.user_display

    def is_display_running(self, display: str) -> bool:
        """Check if a display is running"""
        if display not in self.displays:
            return False

        display_info = self.displays[display]
        if not display_info.process:
            return False

        # Check if process is still alive
        if display_info.process.poll() is not None:
            # Process died
            display_info.is_running = False
            return False

        return True

    def take_screenshot(self, display: str, output_path: str) -> bool:
        """Take screenshot of specific display"""
        try:
            # Method 1: scrot with display specification
            result = subprocess.run(  # noqa: S603,S607
                ['/usr/bin/scrot', '--display', display, output_path],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0 and os.path.exists(output_path):
                return True

            # Method 2: import with display specification
            result = subprocess.run(  # noqa: S603,S607
                [
                    '/usr/bin/import',
                    '-display',
                    display,
                    '-window',
                    'root',
                    output_path,
                ],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0 and os.path.exists(output_path):
                return True

            self.logger.error(f"Screenshot failed for display {display}")
            return False

        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return False

    def open_application(self, display: str, app_command: str) -> bool:
        """Open application on specific display"""
        try:
            if display == self.user_display:
                self.logger.warning("Refusing to open app on user display")
                return False

            env = os.environ.copy()
            env['DISPLAY'] = display
            env.pop('WAYLAND_DISPLAY', None)  # Remove Wayland

            # For applications that might use DBus activation (like file managers),
            # we need to explicitly disable DBus activation
            if app_command == 'thunar':
                # Use thunar with --no-daemon to prevent DBus issues
                full_command = ['thunar', '--no-daemon']
            elif app_command == 'firefox-esr':
                # For Firefox, use new instance flag to prevent existing instance issues
                full_command = ['firefox-esr', '--new-instance', '--no-remote']
            else:
                full_command = [app_command]

            # Start application with explicit display
            subprocess.Popen(  # noqa: S603
                full_command,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            self.logger.info(f"Opened {' '.join(full_command)} on display {display}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to open {app_command}: {e}")
            return False

    def cleanup_all_displays(self) -> None:
        """Clean up ONLY virtual displays WE created, leave existing ones alone"""
        with self._cleanup_lock:
            if not self._created_by_us:
                self.logger.info("No displays created by us to clean up")
                return

            self.logger.info(f"Cleaning up displays we created: {list(self._created_by_us)}")

            # Only clean up displays WE created
            for display in list(self._created_by_us):
                if display in self.displays:
                    display_info = self.displays[display]
                    if display_info.process and display_info.process.poll() is None:
                        try:
                            self.logger.info(f"Terminating our display {display}")
                            # Try graceful termination first
                            display_info.process.terminate()
                            display_info.process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            # Force kill if needed
                            try:
                                self.logger.warning(f"Force killing display {display}")
                                os.killpg(os.getpgid(display_info.process.pid), 9)
                            except Exception:
                                display_info.process.kill()
                        except Exception as e:
                            self.logger.warning(f"Error terminating {display}: {e}")

                    # Clean up lock files for OUR displays only
                    display_num = self._extract_display_number(display)
                    lock_files = [
                        os.path.join(tempfile.gettempdir(), f'.X{display_num}-lock'),
                        os.path.join(tempfile.gettempdir(), '.X11-unix', f'X{display_num}'),
                    ]

                    for lock_file in lock_files:
                        try:
                            if os.path.exists(lock_file):
                                os.remove(lock_file)
                                self.logger.debug(f"Removed lock file: {lock_file}")
                        except Exception as e:
                            self.logger.debug(f"Could not remove {lock_file}: {e}")

            # Clear our tracking
            self.displays.clear()
            self._created_by_us.clear()
            self.ai_display = None

            self.logger.info("Cleanup complete - only removed displays we created")

    def get_display_info(self, display: str) -> DisplayInfo | None:
        """Get information about a display"""
        return self.displays.get(display)

    def list_displays(self) -> list[str]:
        """List all managed displays"""
        return list(self.displays.keys())

    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.cleanup_all_displays()
