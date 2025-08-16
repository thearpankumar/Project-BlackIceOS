from unittest.mock import patch

import pytest

from src.desktop.recognition.template_manager import TemplateManager


class TestTemplateManager:
    """Simple tests for TemplateManager used by DesktopController"""

    @pytest.fixture
    def template_manager(self):
        """Create template manager for testing"""
        return TemplateManager()

    def test_initialization(self, template_manager):
        """Test template manager initializes correctly"""
        assert template_manager is not None
        assert hasattr(template_manager, 'template_cache')

    def test_get_template_path(self, template_manager):
        """Test template path resolution"""
        with patch('os.path.exists', return_value=True):
            path = template_manager.get_template_path("burpsuite", "proxy_tab")
            assert isinstance(path, str)
            assert "proxy_tab" in path

    def test_template_categories(self, template_manager):
        """Test template categories are available"""
        assert hasattr(template_manager, 'categories')
        categories = template_manager.categories
        assert isinstance(categories, dict)
        # Should have some common categories
        expected_categories = ["burpsuite", "common", "terminal", "browser"]
        for category in expected_categories:
            assert category in categories
