"""
Display Controller
High-level interface for display management and automation
"""

import logging
import os
import subprocess
import tempfile
from typing import Any

from .virtual_display import VirtualDisplayManager


class DisplayController:
    """High-level controller for display management"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.display_manager = VirtualDisplayManager()
        self.ai_display: str | None = None
        self.is_initialized = False

    def initialize(self, preferred_ai_display: str = ":1") -> bool:
        """Initialize display system"""
        try:
            self.logger.info("Initializing display controller...")

            # Create AI display
            self.ai_display = self.display_manager.create_ai_display(
                preferred_display=preferred_ai_display
            )

            if self.ai_display:
                self.is_initialized = True
                self.logger.info(
                    f"Display controller initialized with AI display: {self.ai_display}"
                )
                return True
            else:
                self.logger.error("Failed to create AI display")
                return False

        except Exception as e:
            self.logger.error(f"Display controller initialization failed: {e}")
            return False

    def get_ai_display(self) -> str | None:
        """Get the AI display identifier"""
        return self.ai_display

    def get_user_display(self) -> str:
        """Get the user display identifier"""
        return self.display_manager.get_user_display()

    def is_ai_display_running(self) -> bool:
        """Check if AI display is running"""
        if not self.ai_display:
            return False
        return self.display_manager.is_display_running(self.ai_display)

    def capture_ai_screenshot(self, output_path: str) -> bool:
        """Capture screenshot from AI display"""
        if not self.ai_display:
            self.logger.error("No AI display available for screenshot")
            return False

        return self.display_manager.take_screenshot(self.ai_display, output_path)

    def open_application_on_ai_display(self, app_command: str) -> bool:
        """Open application on AI display only"""
        if not self.ai_display:
            self.logger.error("No AI display available for application")
            return False

        return self.display_manager.open_application(self.ai_display, app_command)

    def switch_to_ai_display(self) -> None:
        """Switch environment to AI display"""
        if self.ai_display:
            os.environ['DISPLAY'] = self.ai_display
            # Remove Wayland to ensure X11
            os.environ.pop('WAYLAND_DISPLAY', None)
            self.logger.debug(f"Switched to AI display: {self.ai_display}")
        else:
            self.logger.warning("No AI display to switch to")

    def switch_to_user_display(self) -> None:
        """Switch environment back to user display"""
        user_display = self.display_manager.get_user_display()
        os.environ['DISPLAY'] = user_display
        self.logger.debug(f"Switched to user display: {user_display}")

    def ensure_ai_display_context(self) -> None:
        """Ensure we're operating in AI display context"""
        current_display = os.environ.get('DISPLAY', ':0')
        if current_display != self.ai_display:
            self.switch_to_ai_display()

    def get_display_status(self) -> dict[str, Any]:
        """Get comprehensive display status"""
        status: dict[str, Any] = {
            'initialized': self.is_initialized,
            'ai_display': self.ai_display,
            'user_display': self.display_manager.get_user_display(),
            'ai_display_running': (self.is_ai_display_running() if self.ai_display else False),
            'current_environment_display': os.environ.get('DISPLAY', 'unknown'),
            'managed_displays': self.display_manager.list_displays(),
        }

        # Add detailed info for AI display
        if self.ai_display:
            display_info = self.display_manager.get_display_info(self.ai_display)
            if display_info:
                status['ai_display_info'] = {
                    'resolution': display_info.resolution,
                    'creation_time': display_info.creation_time,
                    'uptime': display_info.creation_time,
                    'process_running': (
                        display_info.process.poll() is None if display_info.process else False
                    ),
                }

        return status

    def test_ai_display(self) -> dict[str, Any]:
        """Test AI display functionality"""
        test_results: dict[str, Any] = {
            'display_accessible': False,
            'screenshot_working': False,
            'environment_correct': False,
            'isolation_verified': False,
        }

        if not self.ai_display:
            test_results['error'] = 'No AI display available'
            return test_results

        try:
            # Test 1: Display accessibility
            result = subprocess.run(  # noqa: S603
                ['/usr/bin/xdpyinfo', '-display', self.ai_display],
                capture_output=True,
                timeout=5,
                check=True,
            )
            test_results['display_accessible'] = result.returncode == 0

            # Test 2: Screenshot capability
            test_screenshot = os.path.join(tempfile.gettempdir(), 'test_ai_display.png')
            test_results['screenshot_working'] = self.capture_ai_screenshot(test_screenshot)

            # Clean up test screenshot
            if os.path.exists(test_screenshot):
                os.remove(test_screenshot)

            # Test 3: Environment setup
            self.switch_to_ai_display()
            current_display = os.environ.get('DISPLAY')
            test_results['environment_correct'] = current_display == self.ai_display

            # Test 4: Isolation verification
            user_display = self.display_manager.get_user_display()
            test_results['isolation_verified'] = self.ai_display != user_display

        except Exception as e:
            test_results['error'] = str(e)
            self.logger.error(f"AI display test failed: {e}")

        return test_results

    def cleanup(self) -> None:
        """Clean up display resources"""
        try:
            self.logger.info("Cleaning up display controller...")
            self.display_manager.cleanup_all_displays()
            self.ai_display = None
            self.is_initialized = False
            self.logger.info("Display controller cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during display cleanup: {e}")

    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.cleanup()
