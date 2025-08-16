"""
Desktop Display Management
Handles virtual displays and isolation for AI automation
"""

from .display_controller import DisplayController
from .virtual_display import VirtualDisplayManager

__all__ = ['VirtualDisplayManager', 'DisplayController']
