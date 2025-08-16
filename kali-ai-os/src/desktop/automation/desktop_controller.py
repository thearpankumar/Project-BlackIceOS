"""
Desktop Controller
Clean implementation with proper display isolation and template-based automation
"""

import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from ..display.display_controller import DisplayController
from ..monitoring.user_activity import UserActivityMonitor
from ..recognition.opencv_matcher import OpenCVMatcher
from ..recognition.template_manager import TemplateManager


@dataclass
class AutomationResult:
    """Result of an automation operation"""

    success: bool
    data: Any | None = None
    error_message: str | None = None
    execution_time: float = 0.0


@dataclass
class ClickResult:
    """Result of a click operation - compatibility with old interface"""

    success: bool
    clicked_location: tuple[int, int] | None
    error_message: str | None = None
    execution_time: float = 0.0


class DesktopController:
    """Clean desktop automation controller with proper display isolation"""

    def __init__(self, display: str = ":1") -> None:
        self.logger = logging.getLogger(__name__)

        # Core components
        self.display_controller = DisplayController()
        self.activity_monitor = UserActivityMonitor()
        self.opencv_matcher = OpenCVMatcher()
        self.template_manager = TemplateManager()

        # State
        self.is_initialized = False
        self.automation_active = False
        self.safety_enabled = True
        self._requested_display = display

        # Configuration
        self.config = {
            'click_delay': 0.1,
            'type_interval': 0.01,
            'template_confidence': 0.8,
            'screenshot_timeout': 10,
            'safety_checks': True,
        }

        # Initialize automatically if possible
        try:
            self.initialize(display)
        except Exception as e:
            self.logger.warning(f"Auto-initialization failed: {e}")

    def initialize(self, ai_display: str = ":1") -> bool:
        """Initialize the desktop controller"""
        try:
            self.logger.info("Initializing desktop controller...")

            # Initialize display system
            if not self.display_controller.initialize(ai_display):
                return False

            # Start user activity monitoring
            if not self.activity_monitor.start_monitoring():
                self.logger.warning("User activity monitoring failed to start")

            self.is_initialized = True
            self.logger.info("Desktop controller initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Desktop controller initialization failed: {e}")
            return False

    @property
    def display(self) -> str:
        """Get current AI display for compatibility"""
        ai_display = self.display_controller.get_ai_display()
        return ai_display if ai_display else self._requested_display

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of desktop automation system"""
        return {
            'initialized': self.is_initialized,
            'automation_active': self.automation_active,
            'safety_enabled': self.safety_enabled,
            'display_status': (
                self.display_controller.get_display_status() if self.is_initialized else {}
            ),
            'activity_level': (
                self.activity_monitor.get_current_activity_level()
                if self.is_initialized
                else 'unknown'
            ),
            'config': self.config.copy(),
        }

    def capture_screenshot(self, filename: str | None = None) -> str | None:
        """Capture screenshot from AI display - compatibility interface"""
        if not self.is_initialized:
            self.logger.error("Cannot capture screenshot - system not initialized")
            return None

        if filename is None:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                filename = temp_file.name

        try:
            # Ensure we're in AI display context
            self.display_controller.ensure_ai_display_context()

            # Capture screenshot
            success = self.display_controller.capture_ai_screenshot(filename)

            if success:
                self.logger.debug(f"Screenshot captured: {filename}")
                return filename
            else:
                self.logger.error("Screenshot capture failed")
                return None

        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None

    def get_ai_display(self) -> str | None:
        """Get the AI display identifier"""
        if not self.is_initialized:
            self.logger.error("Cannot get AI display - system not initialized")
            return None

        try:
            return self.display_controller.get_ai_display()
        except Exception as e:
            self.logger.error(f"Error getting AI display: {e}")
            return None

    def test_system(self) -> dict[str, Any]:
        """Test the desktop system functionality"""
        try:
            self.logger.info("Running desktop system test")

            # Test initialization
            init_status = self.is_initialized

            # Test display controller
            display_status = (
                self.display_controller.get_display_status() if self.is_initialized else {}
            )

            # Test activity monitor
            activity_level = (
                self.activity_monitor.get_current_activity_level()
                if self.is_initialized
                else 'unknown'
            )

            # Test screenshot capability
            screenshot_test = False
            if self.is_initialized:
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as temp_screenshot_file:
                    test_screenshot_path = temp_screenshot_file.name
                test_screenshot = self.capture_screenshot(test_screenshot_path)
                screenshot_test = test_screenshot is not None
                if test_screenshot and os.path.exists(test_screenshot):
                    os.remove(test_screenshot)  # Cleanup

            # Determine overall status
            overall_status = 'passed' if (init_status and screenshot_test) else 'failed'

            return {
                'overall_status': overall_status,
                'initialization': init_status,
                'display_status': display_status,
                'activity_level': activity_level,
                'screenshot_test': screenshot_test,
                'timestamp': time.time(),
            }

        except Exception as e:
            self.logger.error(f"System test error: {e}")
            return {
                'overall_status': 'failed',
                'error': str(e),
                'timestamp': time.time(),
            }

    def safe_click(self, x: int, y: int, button: str = 'left') -> ClickResult:
        """Safely perform click on AI display - compatibility interface"""
        start_time = time.time()

        if not self._is_safe_to_act():
            return ClickResult(
                success=False,
                clicked_location=None,
                error_message="User activity detected or safety check failed",
                execution_time=time.time() - start_time,
            )

        try:
            # Ensure AI display context
            self.display_controller.ensure_ai_display_context()

            # Import pyautogui here to ensure proper display context
            import pyautogui

            # Configure for safety
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = self.config['click_delay']

            # Validate coordinates
            screen_size = pyautogui.size()
            if not (0 <= x < screen_size.width and 0 <= y < screen_size.height):
                return ClickResult(
                    success=False,
                    clicked_location=None,
                    error_message=f"Coordinates {x},{y} outside screen bounds {screen_size}",
                    execution_time=time.time() - start_time,
                )

            # Perform click
            pyautogui.click(x, y, button=button)

            self.logger.info(f"Clicked at ({x}, {y}) with {button} button")

            return ClickResult(
                success=True,
                clicked_location=(x, y),
                error_message=None,
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            return ClickResult(
                success=False,
                clicked_location=None,
                error_message=str(e),
                execution_time=time.time() - start_time,
            )

    def safe_type(self, text: str) -> dict[str, Any]:
        """Safely type text on AI display - compatibility interface"""
        if not self._is_safe_to_act():
            return {
                'success': False,
                'text_typed': '',
                'error_message': "User activity detected or safety check failed",
            }

        if not self._validate_text_input(text):
            return {
                'success': False,
                'text_typed': '',
                'error_message': "Text input blocked for security",
            }

        try:
            # Ensure AI display context
            self.display_controller.ensure_ai_display_context()

            import pyautogui

            pyautogui.typewrite(text, interval=self.config['type_interval'])

            self.logger.info(f"Typed text: {text[:50]}...")

            return {'success': True, 'text_typed': text, 'error_message': None}

        except Exception as e:
            return {'success': False, 'text_typed': '', 'error_message': str(e)}

    def find_element(self, template_path: str, confidence: float | None = None) -> dict | None:
        """Find GUI element using template matching - compatibility interface"""
        try:
            # Take screenshot
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_screenshot_file:
                screenshot_path = temp_screenshot_file.name
            if not self.capture_screenshot(screenshot_path):
                return None

            # Use confidence from config if not specified
            if confidence is None:
                confidence = self.config['template_confidence']

            # Find element
            result = self.opencv_matcher.find_template(
                screenshot=screenshot_path,
                template=template_path,
                confidence=confidence,
            )

            # Clean up screenshot
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)

            return result

        except Exception as e:
            self.logger.error(f"Element finding failed: {e}")
            return None

    def open_application(self, app_name: str) -> dict[str, Any]:
        """Open application on AI display - compatibility interface"""
        if not self.is_initialized:
            return {'success': False, 'error': "System not initialized"}

        # Application command mappings for Kali Linux
        app_commands = {
            'terminal': 'x-terminal-emulator',
            'browser': 'firefox-esr',
            'firefox': 'firefox-esr',
            'calculator': 'xcalc',  # Use xcalc instead of galculator
            'filemanager': 'thunar',
            'files': 'thunar',
            'editor': 'mousepad',
            'burpsuite': 'burpsuite',
            'wireshark': 'wireshark',
            'metasploit': 'msfconsole',
            'nmap': 'zenmap',
        }

        command = app_commands.get(app_name.lower(), app_name)

        success = self.display_controller.open_application_on_ai_display(command)

        if success:
            return {'success': True, 'app': app_name, 'command': command}
        else:
            return {
                'success': False,
                'error': f"Failed to open application: {app_name}",
            }

    def _is_safe_to_act(self) -> bool:
        """Check if it's safe to perform automation actions"""
        if not self.safety_enabled:
            return True

        if not self.is_initialized:
            return False

        try:
            # Check user activity
            activity_level = self.activity_monitor.get_current_activity_level()
            if activity_level == 'intensive':
                return False

            # Check for critical processes
            if self.activity_monitor.is_user_in_critical_task():
                return False

            # Check VM resources
            if not self.activity_monitor.is_vm_resources_available():
                return False

            return True

        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            return False  # Fail safe

    def _validate_text_input(self, text: str) -> bool:
        """Validate text input for security"""
        dangerous_patterns = [
            'rm -rf',
            'sudo shutdown',
            'mkfs.',
            'dd if=',
            '; rm ',
            '| rm ',
            '&& rm ',
            'format ',
            'delete *',
        ]

        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                self.logger.warning(f"Blocked dangerous text: {pattern}")
                return False

        return True

    def emergency_stop(self) -> None:
        """Emergency stop all automation"""
        try:
            self.logger.critical("Emergency stop activated")
            self.automation_active = False
            self.safety_enabled = True

            # Switch back to user display
            if self.display_controller:
                self.display_controller.switch_to_user_display()

            self.logger.critical("Emergency stop completed")

        except Exception as e:
            self.logger.critical(f"Error during emergency stop: {e}")

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up desktop controller...")

            # Stop monitoring
            if self.activity_monitor:
                self.activity_monitor.stop_monitoring()

            # Clean up display
            if self.display_controller:
                self.display_controller.cleanup()

            self.is_initialized = False
            self.logger.info("Desktop controller cleanup complete")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.cleanup()
