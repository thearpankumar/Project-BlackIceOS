import logging
import os
import threading
from collections.abc import Callable

from dotenv import load_dotenv
from pynput import keyboard


class EmergencyStop:
    """Emergency stop system for desktop automation with F12 key trigger"""

    def __init__(self, stop_callback: Callable[[], None] | None = None) -> None:
        load_dotenv()
        self.logger = logging.getLogger(__name__)

        # Emergency stop configuration
        self.emergency_key = os.getenv("EMERGENCY_STOP_KEY", "F12")
        self.stop_callback = stop_callback
        self.is_monitoring = False
        self.emergency_triggered = False

        # Keyboard listener
        self._keyboard_listener: keyboard.Listener | None = None
        self._monitor_thread: threading.Thread | None = None
        self._stop_lock = threading.Lock()

        # Emergency stop handlers
        self.stop_handlers: list[Callable[[], None]] = []

    def add_stop_handler(self, handler: Callable[[], None]) -> None:
        """Add a function to be called during emergency stop"""
        self.stop_handlers.append(handler)

    def remove_stop_handler(self, handler: Callable[[], None]) -> None:
        """Remove a stop handler"""
        if handler in self.stop_handlers:
            self.stop_handlers.remove(handler)

    def start_monitoring(self) -> bool:
        """Start monitoring for emergency stop key"""
        try:
            if self.is_monitoring:
                self.logger.warning("Emergency stop monitoring already active")
                return True

            # Parse emergency key
            emergency_key_obj = self._parse_key(self.emergency_key)
            if not emergency_key_obj:
                self.logger.error(f"Invalid emergency key: {self.emergency_key}")
                return False

            # Start keyboard listener
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press, on_release=self._on_key_release
            )

            self._keyboard_listener.start()
            self.is_monitoring = True
            self.emergency_triggered = False

            self.logger.info(f"Emergency stop monitoring started (Key: {self.emergency_key})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start emergency stop monitoring: {e}")
            return False

    def stop_monitoring(self) -> None:
        """Stop monitoring for emergency stop key"""
        try:
            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None

            self.is_monitoring = False
            self.logger.info("Emergency stop monitoring stopped")

        except Exception as e:
            self.logger.error(f"Error stopping emergency monitoring: {e}")

    def _parse_key(self, key_string: str) -> keyboard.Key | None:
        """Parse key string to keyboard.Key object"""
        try:
            # Handle function keys
            if key_string.upper().startswith('F') and key_string[1:].isdigit():
                func_num = int(key_string[1:])
                if 1 <= func_num <= 12:
                    return getattr(keyboard.Key, f'f{func_num}')

            # Handle special keys
            special_keys = {
                'ESC': keyboard.Key.esc,
                'ESCAPE': keyboard.Key.esc,
                'CTRL': keyboard.Key.ctrl,
                'ALT': keyboard.Key.alt,
                'SHIFT': keyboard.Key.shift,
                'TAB': keyboard.Key.tab,
                'SPACE': keyboard.Key.space,
                'ENTER': keyboard.Key.enter,
                'DELETE': keyboard.Key.delete,
                'BACKSPACE': keyboard.Key.backspace,
            }

            if key_string.upper() in special_keys:
                return special_keys[key_string.upper()]

            # Handle single character keys
            if len(key_string) == 1:
                return keyboard.KeyCode.from_char(key_string.lower())

            return None

        except Exception as e:
            self.logger.error(f"Error parsing key '{key_string}': {e}")
            return None

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """Handle key press events"""
        try:
            # Check if this is our emergency key
            if self._is_emergency_key(key):
                self._trigger_emergency_stop()

        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """Handle key release events"""
        pass  # We only care about key press for emergency stop

    def _is_emergency_key(self, key: keyboard.Key | keyboard.KeyCode | None) -> bool:
        """Check if the pressed key is the emergency stop key"""
        try:
            emergency_key_obj = self._parse_key(self.emergency_key)
            return key == emergency_key_obj

        except Exception as e:
            self.logger.error(f"Error checking emergency key: {e}")
            return False

    def _trigger_emergency_stop(self) -> None:
        """Trigger emergency stop sequence"""
        with self._stop_lock:
            if self.emergency_triggered:
                return  # Already triggered

            self.emergency_triggered = True
            self.logger.critical("EMERGENCY STOP TRIGGERED!")

            try:
                # Execute emergency stop sequence
                self._execute_emergency_stop()

                # Call custom callback if provided
                if self.stop_callback:
                    self.stop_callback()

                # Notify all handlers
                for handler in self.stop_handlers:
                    try:
                        handler()
                    except Exception as e:
                        self.logger.error(f"Error in stop handler: {e}")

                self.logger.critical("Emergency stop sequence completed")

            except Exception as e:
                self.logger.critical(f"Error during emergency stop: {e}")

    def _execute_emergency_stop(self) -> None:
        """Execute the emergency stop sequence"""
        try:
            # Stop all PyAutoGUI operations
            try:
                import pyautogui

                pyautogui.FAILSAFE = True
                # Move mouse to corner to trigger failsafe
                pyautogui.moveTo(0, 0)
            except Exception as e:
                self.logger.error(f"Error in notification: {e}")

            # Kill any automation processes
            self._kill_automation_processes()

            # Reset display environment
            self._reset_display_environment()

            # Send emergency notification
            self._send_emergency_notification()

        except Exception as e:
            self.logger.critical(f"Emergency stop execution failed: {e}")

    def _kill_automation_processes(self) -> None:
        """Kill automation-related processes"""
        try:
            import psutil

            # List of process names to terminate
            automation_processes = ['pyautogui', 'opencv', 'xvfb', 'automation']

            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if not proc_info['name']:
                        continue

                    # Check if this is an automation process
                    is_automation = False
                    for auto_proc in automation_processes:
                        if auto_proc.lower() in proc_info['name'].lower():
                            is_automation = True
                            break

                        # Check command line too
                        if proc_info['cmdline']:
                            cmdline = ' '.join(proc_info['cmdline']).lower()
                            if auto_proc.lower() in cmdline:
                                is_automation = True
                                break

                    if is_automation:
                        proc.terminate()
                        killed_count += 1
                        self.logger.info(
                            f"Terminated automation process: {proc_info['name']}"
                            f" (PID: {proc_info['pid']})"
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    self.logger.debug(f"Error checking process: {e}")

            if killed_count > 0:
                self.logger.info(f"Terminated {killed_count} automation processes")

        except Exception as e:
            self.logger.error(f"Error killing automation processes: {e}")

    def _reset_display_environment(self) -> None:
        """Reset display environment variables"""
        try:
            # Reset to user display
            os.environ['DISPLAY'] = ':0'

            # Clear any automation-related environment variables
            automation_vars = ['AI_DISPLAY', 'AUTOMATION_ACTIVE', 'TEMPLATE_DIR']
            for var in automation_vars:
                os.environ.pop(var, None)

            self.logger.info("Display environment reset to user desktop")

        except Exception as e:
            self.logger.error(f"Error resetting display environment: {e}")

    def _send_emergency_notification(self) -> None:
        """Send emergency stop notification"""
        try:
            # Try to use system notification
            try:
                import subprocess

                subprocess.run(
                    [
                        '/usr/bin/notify-send',
                        'Emergency Stop',
                        'Desktop automation has been stopped',
                        '--urgency=critical',
                    ],
                    timeout=5,
                )
            except Exception as e:
                self.logger.error(f"Error in notification: {e}")

            # Print to console
            print("\n" + "=" * 60)
            print("           EMERGENCY STOP ACTIVATED")
            print("         Desktop automation stopped")
            print("=" * 60 + "\n")

            # Log to system
            self.logger.critical("Emergency stop notification sent")

        except Exception as e:
            self.logger.error(f"Error sending emergency notification: {e}")

    def manual_trigger(self) -> None:
        """Manually trigger emergency stop (for testing)"""
        self.logger.warning("Manual emergency stop triggered")
        self._trigger_emergency_stop()

    def reset_emergency_state(self) -> None:
        """Reset emergency state (call after handling emergency)"""
        with self._stop_lock:
            self.emergency_triggered = False
            self.logger.info("Emergency state reset")

    def is_emergency_active(self) -> bool:
        """Check if emergency stop is currently active"""
        return self.emergency_triggered

    def get_emergency_key(self) -> str:
        """Get the current emergency stop key"""
        return self.emergency_key

    def set_emergency_key(self, new_key: str) -> bool:
        """Set new emergency stop key"""
        try:
            # Validate the new key
            if not self._parse_key(new_key):
                self.logger.error(f"Invalid emergency key: {new_key}")
                return False

            # Stop current monitoring
            was_monitoring = self.is_monitoring
            if was_monitoring:
                self.stop_monitoring()

            # Update key
            self.emergency_key = new_key

            # Restart monitoring if it was active
            if was_monitoring:
                self.start_monitoring()

            self.logger.info(f"Emergency stop key changed to: {new_key}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting emergency key: {e}")
            return False

    def __del__(self) -> None:
        """Cleanup on object destruction"""
        try:
            self.stop_monitoring()
        except Exception as e:
            self.logger.error(f"Error in destructor: {e}")


class AutomationSafetyManager:
    """Manager for automation safety with emergency stop integration"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.emergency_stop = EmergencyStop(self._emergency_callback)
        self.automation_controllers: list[object] = []
        self.safety_enabled = True

    def register_controller(self, controller: object) -> None:
        """Register a controller for emergency stop"""
        self.automation_controllers.append(controller)
        self.emergency_stop.add_stop_handler(lambda: self._stop_controller(controller))

    def unregister_controller(self, controller: object) -> None:
        """Unregister a controller"""
        if controller in self.automation_controllers:
            self.automation_controllers.remove(controller)

    def start_safety_monitoring(self) -> bool:
        """Start safety monitoring"""
        return self.emergency_stop.start_monitoring()

    def stop_safety_monitoring(self) -> None:
        """Stop safety monitoring"""
        self.emergency_stop.stop_monitoring()

    def _emergency_callback(self) -> None:
        """Called when emergency stop is triggered"""
        self.logger.critical("Safety manager handling emergency stop")

        # Stop all registered controllers
        for controller in self.automation_controllers:
            self._stop_controller(controller)

    def _stop_controller(self, controller: object) -> None:
        """Stop a specific controller"""
        try:
            if hasattr(controller, 'emergency_stop'):
                controller.emergency_stop()
            elif hasattr(controller, 'stop'):
                controller.stop()
            elif hasattr(controller, 'automation_active'):
                controller.automation_active = False

            self.logger.info(f"Stopped controller: {type(controller).__name__}")

        except Exception as e:
            self.logger.error(f"Error stopping controller {type(controller).__name__}: {e}")

    def is_emergency_active(self) -> bool:
        """Check if emergency is currently active"""
        return self.emergency_stop.is_emergency_active()

    def reset_emergency(self) -> None:
        """Reset emergency state"""
        self.emergency_stop.reset_emergency_state()

    def manual_emergency_stop(self) -> None:
        """Manually trigger emergency stop"""
        self.emergency_stop.manual_trigger()
