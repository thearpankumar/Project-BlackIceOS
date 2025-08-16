"""
Base Viewer Interface
Abstract base class for all AI display viewers
"""

import logging
import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any


class BaseViewer(ABC):
    """Abstract base class for AI display viewers"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_viewing = False
        self.display: str | None = None
        self.widget: Any = None

    @abstractmethod
    def start_viewing(self, display: str) -> bool:
        """Start viewing the specified display"""
        pass

    @abstractmethod
    def stop_viewing(self) -> bool:
        """Stop viewing and cleanup resources"""
        pass

    @abstractmethod
    def get_viewer_widget(self, parent: tk.Widget) -> tk.Widget | None:
        """Get the tkinter widget that shows the display"""
        pass

    @abstractmethod
    def refresh(self) -> bool:
        """Manually refresh the display view"""
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """Check if viewer is currently active"""
        pass

    @abstractmethod
    def get_viewer_type(self) -> str:
        """Return the type of viewer (vnc, pip, etc.)"""
        pass

    def get_status(self) -> dict[str, Any]:
        """Get viewer status information"""
        return {
            'type': self.get_viewer_type(),
            'active': self.is_active(),
            'display': self.display,
            'viewing': self.is_viewing,
        }

    def cleanup(self) -> bool:
        """Cleanup resources - called during shutdown"""
        try:
            if self.is_viewing:
                self.stop_viewing()
            return True
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            return False
