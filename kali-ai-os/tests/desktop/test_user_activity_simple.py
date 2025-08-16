from unittest.mock import patch

import pytest

from src.desktop.monitoring.user_activity import UserActivityMonitor


class TestUserActivityMonitor:
    """Simple test suite for user activity monitoring"""

    @pytest.fixture
    def activity_monitor(self):
        """Create user activity monitor for testing"""
        return UserActivityMonitor()

    def test_initialization(self, activity_monitor):
        """Test monitor initializes correctly"""
        assert activity_monitor is not None
        assert hasattr(activity_monitor, 'activity_threshold')
        assert hasattr(activity_monitor, 'monitoring_active')

    def test_activity_level_detection(self, activity_monitor):
        """Test activity level detection returns valid values"""
        activity_level = activity_monitor.get_current_activity_level()
        assert activity_level in ['idle', 'light', 'intensive']

    def test_safety_check(self, activity_monitor):
        """Test safety check returns boolean"""
        is_safe = activity_monitor.is_safe_for_ai_activity()
        assert isinstance(is_safe, bool)

    def test_vm_resource_check(self, activity_monitor):
        """Test VM resource checking"""
        with patch('psutil.cpu_percent', return_value=50.0):
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value.percent = 60.0

                resources = activity_monitor.check_vm_resources()
                assert isinstance(resources, dict)
                assert 'cpu_percent' in resources

    def test_critical_process_detection(self, activity_monitor):
        """Test critical process detection"""
        is_critical = activity_monitor.is_user_in_critical_task()
        assert isinstance(is_critical, bool)

    def test_threshold_customization(self, activity_monitor):
        """Test activity threshold setting"""
        new_thresholds = {'idle': 100, 'light': 50, 'intensive': 10}
        activity_monitor.set_activity_thresholds(new_thresholds)

        assert activity_monitor.activity_threshold['idle'] == 100
        assert activity_monitor.activity_threshold['light'] == 50
