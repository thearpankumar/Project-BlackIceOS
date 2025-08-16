import logging
import os
import threading
import time
from typing import Any

import psutil
from dotenv import load_dotenv

# Conditional import for GUI libraries (fail gracefully in test environment)
try:
    from pynput import keyboard, mouse

    PYNPUT_AVAILABLE = True
except ImportError:
    # Mock classes for test environment
    class MockMouse:
        class Button:
            left = 'left'
            right = 'right'
            middle = 'middle'

        class Listener:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def start(self) -> None:
                pass

            def stop(self) -> None:
                pass

    class MockKeyboard:
        class Key:
            space = 'space'
            enter = 'enter'
            ctrl = 'ctrl'
            shift = 'shift'
            alt = 'alt'

        class KeyCode:
            def __init__(self, char: str) -> None:
                self.char = char

        class Listener:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def start(self) -> None:
                pass

            def stop(self) -> None:
                pass

    mouse = MockMouse()
    keyboard = MockKeyboard()
    PYNPUT_AVAILABLE = False


class UserActivityMonitor:
    """Monitor user activity in VM to ensure safe automation"""

    def __init__(self) -> None:
        load_dotenv()
        self.logger = logging.getLogger(__name__)

        # Activity tracking
        self.last_activity = time.time()
        self.last_mouse_activity = time.time()
        self.last_keyboard_activity = time.time()

        # Activity thresholds (seconds)
        self.activity_threshold = {
            'idle': 300,  # 5 minutes
            'light': 60,  # 1 minute
            'intensive': 10,  # 10 seconds
        }

        # VM resource monitoring
        self.vm_resource_limits = {
            'max_cpu_percent': 80.0,
            'max_memory_percent': 90.0,
            'max_disk_io_percent': 85.0,
        }

        # Critical processes that should not be interrupted (from environment)
        critical_env = os.getenv(
            "CRITICAL_PROCESSES",
            "zoom,teams,skype,discord,obs-studio,libreoffice-impress",
        )
        self.critical_processes = [proc.strip() for proc in critical_env.split(",")]

        # Monitoring state
        self.monitoring_active = False
        self._mouse_listener = None
        self._keyboard_listener = None
        self._activity_lock = threading.Lock()

    def start_monitoring(self) -> bool:
        """Start monitoring user input activity"""
        try:
            if not PYNPUT_AVAILABLE:
                self.logger.warning("pynput not available, running in mock mode")
                self.monitoring_active = True
                return True

            # Start mouse listener
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )

            # Start keyboard listener
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press, on_release=self._on_key_release
            )

            if self._mouse_listener:
                self._mouse_listener.start()
            if self._keyboard_listener:
                self._keyboard_listener.start()

            self.monitoring_active = True
            self.logger.info("User activity monitoring started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start activity monitoring: {e}")
            return False

    def stop_monitoring(self) -> None:
        """Stop monitoring user input activity"""
        try:
            if not PYNPUT_AVAILABLE:
                self.monitoring_active = False
                self.logger.info("Mock activity monitoring stopped")
                return

            if self._mouse_listener:
                self._mouse_listener.stop()
                self._mouse_listener = None

            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None

            self.monitoring_active = False
            self.logger.info("User activity monitoring stopped")

        except Exception as e:
            self.logger.error(f"Error stopping activity monitoring: {e}")

    def _on_mouse_move(self, x: int, y: int) -> None:
        """Handle mouse movement events"""
        with self._activity_lock:
            self.last_mouse_activity = time.time()
            self.last_activity = time.time()

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Handle mouse click events"""
        with self._activity_lock:
            self.last_mouse_activity = time.time()
            self.last_activity = time.time()

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll events"""
        with self._activity_lock:
            self.last_mouse_activity = time.time()
            self.last_activity = time.time()

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """Handle key press events"""
        with self._activity_lock:
            self.last_keyboard_activity = time.time()
            self.last_activity = time.time()

        # Check for emergency stop key (F12)
        try:
            if key is not None and hasattr(key, 'name') and key.name == 'f12':
                self.logger.warning("Emergency stop key (F12) detected")
                # This would trigger emergency stop in desktop controller
        except AttributeError:
            pass

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """Handle key release events"""
        pass

    def get_current_activity_level(self) -> str:
        """Determine current user activity level"""
        try:
            current_time = time.time()

            # Check recent input activity
            mouse_idle_time = current_time - self.last_mouse_activity
            keyboard_idle_time = current_time - self.last_keyboard_activity

            # Check CPU usage
            cpu_usage = self._get_user_process_cpu()

            # Determine activity level
            if (
                mouse_idle_time > self.activity_threshold['idle']
                and keyboard_idle_time > self.activity_threshold['idle']
                and cpu_usage < 5.0
            ):
                return 'idle'
            elif (
                mouse_idle_time > self.activity_threshold['light']
                or keyboard_idle_time > self.activity_threshold['light']
                or cpu_usage < 20.0
            ):
                return 'light'
            else:
                return 'intensive'

        except Exception as e:
            self.logger.error(f"Error determining activity level: {e}")
            return 'intensive'  # Default to intensive for safety

    def _check_mouse_activity(self) -> bool:
        """Check if there was recent mouse activity"""
        return (time.time() - self.last_mouse_activity) < self.activity_threshold['light']

    def _check_keyboard_activity(self) -> bool:
        """Check if there was recent keyboard activity"""
        return (time.time() - self.last_keyboard_activity) < self.activity_threshold['light']

    def _get_user_process_cpu(self) -> float:
        """Get CPU usage of user processes (excluding system processes)"""
        try:
            user_cpu = 0.0
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent']):
                try:
                    if proc.info['username'] in ['kali', 'user', os.getlogin()]:
                        cpu_percent = proc.info['cpu_percent']
                        if cpu_percent is not None:
                            user_cpu += cpu_percent
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue

            return user_cpu

        except Exception as e:
            self.logger.error(f"Error getting user CPU usage: {e}")
            return 100.0  # Return high value for safety

    def is_user_in_critical_task(self) -> bool:
        """Check if user is running critical processes that shouldn't be interrupted"""
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""

                    # Check against critical process patterns
                    for critical in self.critical_processes:
                        if critical in proc_name or critical in cmdline:
                            self.logger.info(f"Critical process detected: {proc_name}")
                            return True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error checking critical processes: {e}")
            return True  # Assume critical task for safety

    def is_safe_for_ai_activity(self) -> bool:
        """Determine if it's safe for AI to perform automation"""
        # Check activity level
        activity_level = self.get_current_activity_level()
        if activity_level == 'intensive':
            return False

        # Check for critical tasks
        if self.is_user_in_critical_task():
            return False

        # Check VM resources
        if not self.is_vm_resources_available():
            return False

        # Check if user is presenting
        if self.is_user_presenting():
            return False

        return True

    def wait_for_safe_moment(self, timeout: int = 60) -> bool:
        """Wait for a safe moment to perform automation"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.is_safe_for_ai_activity():
                return True

            # Wait a bit before checking again
            time.sleep(2)

        # Timeout reached
        return False

    def check_vm_resources(self) -> dict[str, float]:
        """Check VM resource usage"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_io_busy': (
                    (disk_io := psutil.disk_io_counters()) is not None and disk_io.read_bytes > 0
                ),
            }
        except Exception as e:
            self.logger.error(f"Error checking VM resources: {e}")
            return {'cpu_percent': 100.0, 'memory_percent': 100.0, 'disk_io_busy': True}

    def _get_vm_resource_usage(self) -> dict[str, Any]:
        """Get detailed VM resource usage"""
        return self.check_vm_resources()

    def is_vm_resources_available(self) -> bool:
        """Check if VM has sufficient resources for automation"""
        try:
            resources = self.check_vm_resources()

            if resources['cpu_percent'] > self.vm_resource_limits['max_cpu_percent']:
                return False

            if resources['memory_percent'] > self.vm_resource_limits['max_memory_percent']:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking VM resources: {e}")
            return False

    def set_activity_thresholds(self, thresholds: dict[str, int]) -> None:
        """Set custom activity thresholds"""
        self.activity_threshold.update(thresholds)
        self.logger.info(f"Activity thresholds updated: {self.activity_threshold}")

    def get_active_display(self) -> str:
        """Get the currently active display"""
        try:
            # Try to get the active display from environment variable
            return os.environ.get('DISPLAY', ':0')
        except Exception:
            return ':0'  # Default to main display

    def is_ai_desktop_safe(self) -> bool:
        """Check if AI desktop (:1) is safe to use"""
        active_display = self.get_active_display()
        # AI desktop is safe if user is on different display
        return active_display != ':1'

    def check_for_emergency_intervention(self) -> str | None:
        """Check for emergency user intervention signals"""
        # This would check for various emergency signals
        # For now, return None (no emergency detected)
        return None

    def should_stop_all_automation(self) -> bool:
        """Check if all automation should be stopped immediately"""
        emergency = self.check_for_emergency_intervention()
        return emergency is not None

    def is_user_presenting(self) -> bool:
        """Check if user is in presentation mode"""
        presentation_indicators = [
            'libreoffice-impress',
            'soffice.bin --impress',
            'powerpoint.exe',
            'keynote',
            'zoom --fullscreen',
            'teams --presentation',
        ]

        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""

                    for indicator in presentation_indicators:
                        if indicator in proc_name or indicator in cmdline:
                            return True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error checking presentation mode: {e}")
            return True  # Assume presentation mode for safety

    def __del__(self) -> None:
        """Cleanup when object is destroyed"""
        self.stop_monitoring()
