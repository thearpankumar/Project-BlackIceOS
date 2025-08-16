import time
from collections import namedtuple
from unittest.mock import patch

import pytest

from src.desktop.automation.desktop_controller import DesktopController

# Mock for pyautogui.size()
Size = namedtuple('Size', ['width', 'height'])


class TestDesktopController:
    """Test suite for desktop automation controller"""

    @pytest.fixture
    def desktop_controller(self):
        """Create desktop controller for testing"""
        with patch(
            'src.desktop.automation.desktop_controller.DisplayController'
        ) as mock_display_controller:
            with patch(
                'src.desktop.automation.desktop_controller.UserActivityMonitor'
            ) as mock_activity_monitor:
                controller = DesktopController(display=":1")
                controller.display_controller = mock_display_controller()
                controller.activity_monitor = mock_activity_monitor()
                controller.is_initialized = True  # Mock initialization
                yield controller

    def test_safe_click_execution(self, desktop_controller):
        """Test click execution with safety validation"""
        with patch('pyautogui.click') as mock_click:
            with patch('pyautogui.size', return_value=Size(1920, 1080)):
                desktop_controller.activity_monitor.get_current_activity_level.return_value = 'low'
                desktop_controller.activity_monitor.is_user_in_critical_task.return_value = False
                desktop_controller.activity_monitor.is_vm_resources_available.return_value = True

                # Should execute click successfully
                result = desktop_controller.safe_click(500, 300)

                assert result.success is True
                assert result.clicked_location == (500, 300)
                assert result.error_message is None
                mock_click.assert_called_once_with(500, 300, button='left')
                desktop_controller.display_controller.ensure_ai_display_context.assert_called_once()

    def test_coordinate_validation(self, desktop_controller):
        """Test click coordinates are validated against screen bounds"""
        with patch('pyautogui.size', return_value=Size(1920, 1080)):
            desktop_controller.activity_monitor.get_current_activity_level.return_value = 'low'
            desktop_controller.activity_monitor.is_user_in_critical_task.return_value = False
            desktop_controller.activity_monitor.is_vm_resources_available.return_value = True

            # Valid coordinates should pass
            result = desktop_controller.safe_click(500, 300)
            assert result.success is True

            # Invalid coordinates should fail with bounds error
            result = desktop_controller.safe_click(-1, 300)
            assert result.success is False
            assert "outside screen bounds" in result.error_message

            result = desktop_controller.safe_click(1920, 300)
            assert result.success is False
            assert "outside screen bounds" in result.error_message

    def test_click_blocked_when_unsafe(self, desktop_controller):
        """Test clicks are blocked when user is active or system is unsafe"""
        desktop_controller.activity_monitor.get_current_activity_level.return_value = 'intensive'

        # Click should be blocked
        result = desktop_controller.safe_click(500, 300)

        assert result.success is False
        assert result.clicked_location is None
        assert "User activity detected" in result.error_message

    def test_safe_typing_execution(self, desktop_controller):
        """Test text typing with safety validation"""
        test_text = "nmap -sS 192.168.1.1"

        with patch('pyautogui.typewrite') as mock_typewrite:
            desktop_controller.activity_monitor.get_current_activity_level.return_value = 'low'
            desktop_controller.activity_monitor.is_user_in_critical_task.return_value = False
            desktop_controller.activity_monitor.is_vm_resources_available.return_value = True

            # Should type text successfully
            result = desktop_controller.safe_type(test_text)

            assert result['success'] is True
            assert result['text_typed'] == test_text
            mock_typewrite.assert_called_once_with(test_text, interval=0.01)
            desktop_controller.display_controller.ensure_ai_display_context.assert_called_once()

    def test_dangerous_text_blocked(self, desktop_controller):
        """Test dangerous text input is blocked"""
        dangerous_text = "rm -rf /"
        desktop_controller.activity_monitor.get_current_activity_level.return_value = 'low'
        desktop_controller.activity_monitor.is_user_in_critical_task.return_value = False
        desktop_controller.activity_monitor.is_vm_resources_available.return_value = True

        result = desktop_controller.safe_type(dangerous_text)

        assert result['success'] is False
        assert "blocked for security" in result['error_message']

    def test_emergency_stop_functionality(self, desktop_controller):
        """Test emergency stop halts all automation"""
        desktop_controller.automation_active = True
        desktop_controller.emergency_stop()
        assert desktop_controller.automation_active is False
        desktop_controller.display_controller.switch_to_user_display.assert_called_once()

    def test_screenshot_capture(self, desktop_controller):
        """Test screenshot capture from AI desktop"""
        desktop_controller.display_controller.capture_ai_screenshot.return_value = True
        result = desktop_controller.capture_screenshot("test.png")
        assert result == "test.png"
        desktop_controller.display_controller.ensure_ai_display_context.assert_called_once()
        desktop_controller.display_controller.capture_ai_screenshot.assert_called_once_with(
            "test.png"
        )

    def test_element_finding_with_template(self, desktop_controller):
        """Test GUI element finding using template matching"""
        template_path = "templates/burpsuite/proxy_tab.png"
        desktop_controller.display_controller.capture_ai_screenshot.return_value = True
        with patch('src.desktop.automation.desktop_controller.OpenCVMatcher') as mock_matcher:
            matcher_instance = mock_matcher.return_value
            matcher_instance.find_template.return_value = {'found': True}
            desktop_controller.opencv_matcher = matcher_instance

            result = desktop_controller.find_element(template_path)
            assert result['found'] is True

    def test_element_not_found_handling(self, desktop_controller):
        """Test graceful handling when GUI element is not found"""
        template_path = "templates/nonexistent/element.png"
        desktop_controller.display_controller.capture_ai_screenshot.return_value = False
        result = desktop_controller.find_element(template_path)
        assert result is None

    def test_performance_timing(self, desktop_controller):
        """Test automation actions meet performance requirements"""
        with patch('pyautogui.click'):
            with patch('pyautogui.size', return_value=Size(1920, 1080)):
                desktop_controller.activity_monitor.get_current_activity_level.return_value = 'low'
                desktop_controller.activity_monitor.is_user_in_critical_task.return_value = False
                desktop_controller.activity_monitor.is_vm_resources_available.return_value = True

                start_time = time.time()
                result = desktop_controller.safe_click(500, 300)
                execution_time = time.time() - start_time

                assert result.success is True
                assert execution_time < 0.5
