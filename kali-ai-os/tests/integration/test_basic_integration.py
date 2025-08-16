import pytest


class TestBasicIntegration:
    """Integration tests for components actually used together in main.py"""

    def test_auth_client_desktop_controller_integration(self):
        """Test that AuthClient and DesktopController can work together"""
        from src.auth.auth_client import AuthClient
        from src.desktop.automation.desktop_controller import DesktopController

        # Should be able to create both components
        auth_client = AuthClient()
        desktop_controller = DesktopController(display=":1")

        assert auth_client is not None
        assert desktop_controller is not None

        # Both should have required methods used in main.py
        assert hasattr(auth_client, 'cleanup')
        assert hasattr(desktop_controller, 'activity_monitor')
        assert hasattr(desktop_controller.activity_monitor, 'start_monitoring')

    def test_desktop_controller_activity_monitor_integration(self):
        """Test DesktopController integrates with UserActivityMonitor"""
        from src.desktop.automation.desktop_controller import DesktopController

        controller = DesktopController(display=":1")

        # Should have activity monitor
        assert hasattr(controller, 'activity_monitor')

        # Activity monitor should have expected interface
        monitor = controller.activity_monitor
        assert hasattr(monitor, 'start_monitoring')
        assert hasattr(monitor, 'stop_monitoring')
        assert hasattr(monitor, 'get_current_activity_level')

    def test_component_cleanup_integration(self):
        """Test that all components can be cleaned up safely"""
        from src.auth.auth_client import AuthClient
        from src.desktop.automation.desktop_controller import DesktopController

        auth_client = AuthClient()
        desktop_controller = DesktopController(display=":1")

        # Should be able to cleanup without errors
        try:
            if hasattr(desktop_controller, 'activity_monitor'):
                desktop_controller.activity_monitor.stop_monitoring()
            auth_client.cleanup()
        except Exception as e:
            pytest.fail(f"Cleanup failed: {e}")
