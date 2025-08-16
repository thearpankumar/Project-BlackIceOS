"""
Viewer Manager
Manages VNC viewer for AI display
"""

import logging
import tkinter as tk
from typing import Any

from .vnc_viewer import VNCViewer


class ViewerManager:
    """Manages VNC viewer for AI display viewing"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # Available viewers
        self.vnc_viewer = VNCViewer()

        # State
        self.current_viewer: Any = None
        self.current_viewer_type: str | None = None
        self.display: str | None = None
        self.preferred_viewer = "vnc"  # Only VNC available

        # Viewer registry
        self.viewers = {"vnc": self.vnc_viewer}

    def start_viewing(self, display: str, viewer_type: str | None = None) -> bool:
        """Start viewing with specified or preferred viewer type"""
        try:
            # Use specified type or fall back to preferred
            if viewer_type is None:
                viewer_type = self.preferred_viewer

            self.logger.info(f"Starting {viewer_type} viewer for display {display}")

            # Stop any current viewing
            self.stop_viewing()

            # Only VNC is available, so force viewer_type to vnc
            viewer_type = "vnc"

            # Try to start the VNC viewer
            if self._start_viewer(viewer_type, display):
                self.display = display
                self.current_viewer_type = viewer_type
                self.logger.info(f"Successfully started {viewer_type} viewer")
                return True

            self.logger.error("VNC viewer failed to start")
            return False

        except Exception as e:
            self.logger.error(f"Error starting viewer: {e}")
            return False

    def stop_viewing(self) -> bool:
        """Stop current viewing"""
        try:
            if self.current_viewer:
                self.logger.info(f"Stopping {self.current_viewer_type} viewer")
                success = self.current_viewer.stop_viewing()

                if success:
                    self.current_viewer = None
                    self.current_viewer_type = None
                    self.display = None
                    self.logger.info("Viewer stopped successfully")
                else:
                    self.logger.warning("Viewer stop may have failed")

                return bool(success)

            return True  # Nothing to stop

        except Exception as e:
            self.logger.error(f"Error stopping viewer: {e}")
            return False

    def switch_viewer(self, new_viewer_type: str) -> bool:
        """Switch to a different viewer type"""
        try:
            if not self.display:
                self.logger.error("No display currently being viewed")
                return False

            if self.current_viewer_type == new_viewer_type:
                self.logger.info(f"Already using {new_viewer_type} viewer")
                return True

            self.logger.info(f"Switching from {self.current_viewer_type} to {new_viewer_type}")

            # Save current display
            current_display = self.display

            # Stop current viewer
            self.stop_viewing()

            # Start new viewer
            return self.start_viewing(current_display, new_viewer_type)

        except Exception as e:
            self.logger.error(f"Error switching viewer: {e}")
            return False

    def get_current_viewer_widget(self, parent: tk.Widget) -> tk.Widget | None:
        """Get the current viewer's widget for embedding in GUI"""
        try:
            if self.current_viewer:
                widget = self.current_viewer.get_viewer_widget(parent)
                return widget if widget is not None else None
            else:
                return self._create_no_viewer_widget(parent)

        except Exception as e:
            self.logger.error(f"Error getting viewer widget: {e}")
            return self._create_error_widget(parent, str(e))

    def refresh_current_viewer(self) -> bool:
        """Refresh the current viewer"""
        if self.current_viewer:
            result = self.current_viewer.refresh()
            return bool(result) if result is not None else False
        return False

    def is_viewing(self) -> bool:
        """Check if currently viewing"""
        return self.current_viewer is not None and self.current_viewer.is_active()

    def get_current_viewer_type(self) -> str | None:
        """Get the current viewer type"""
        return self.current_viewer_type

    def get_available_viewers(self) -> list[str]:
        """Get list of available viewer types"""
        return list(self.viewers.keys())

    def set_preferred_viewer(self, viewer_type: str) -> None:
        """Set the preferred viewer type"""
        if viewer_type in self.viewers:
            self.preferred_viewer = viewer_type
            self.logger.info(f"Preferred viewer set to {viewer_type}")
        else:
            self.logger.warning(f"Unknown viewer type: {viewer_type}")

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive status"""
        status: dict[str, Any] = {
            'viewing': self.is_viewing(),
            'current_viewer': self.current_viewer_type,
            'display': self.display,
            'preferred_viewer': self.preferred_viewer,
            'available_viewers': self.get_available_viewers(),
        }

        # Add individual viewer statuses
        for viewer_type, viewer in self.viewers.items():
            status[f'{viewer_type}_status'] = viewer.get_status()

        return status

    def _start_viewer(self, viewer_type: str, display: str) -> bool:
        """Start a specific viewer type"""
        try:
            if viewer_type not in self.viewers:
                self.logger.error(f"Unknown viewer type: {viewer_type}")
                return False

            viewer = self.viewers[viewer_type]

            if viewer.start_viewing(display):
                self.current_viewer = viewer
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error starting {viewer_type} viewer: {e}")
            return False

    def _create_no_viewer_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create widget shown when no viewer is active"""
        frame = tk.Frame(parent, bg='#2d2d2d', relief='sunken', bd=2)

        # Header
        header_frame = tk.Frame(frame, bg='#1a1a1a', height=50)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="📺 AI Display Viewer",
            fg='#1e7ce8',
            bg='#1a1a1a',
            font=('Arial', 16, 'bold'),
        ).pack(expand=True)

        # Content
        content_frame = tk.Frame(frame, bg='#2d2d2d')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(
            content_frame,
            text="""No AI display viewer is currently active.

Available viewing mode:
• VNC Viewer - Real-time streaming with interaction

Use the VNC viewer button to start viewing the AI display.""",
            fg='white',
            bg='#2d2d2d',
            font=('Arial', 12),
            justify='center',
        ).pack(expand=True)

        return frame

    def _create_error_widget(self, parent: tk.Widget, error_msg: str) -> tk.Widget:
        """Create widget shown when there's an error"""
        frame = tk.Frame(parent, bg='#2d2d2d', relief='sunken', bd=2)

        tk.Label(
            frame,
            text=f"Viewer Error\n\n{error_msg}",
            fg='#ff4444',
            bg='#2d2d2d',
            font=('Arial', 12),
            justify='center',
        ).pack(expand=True, padx=20, pady=20)

        return frame

    def cleanup(self) -> bool:
        """Cleanup all viewers"""
        try:
            self.logger.info("Cleaning up viewer manager")

            # Stop current viewing
            self.stop_viewing()

            # Cleanup all viewers
            success = True
            for viewer_type, viewer in self.viewers.items():
                try:
                    if not viewer.cleanup():
                        success = False
                        self.logger.warning(f"Failed to cleanup {viewer_type} viewer")
                except Exception as e:
                    self.logger.error(f"Error cleaning up {viewer_type} viewer: {e}")
                    success = False

            if success:
                self.logger.info("Viewer manager cleanup completed successfully")
            else:
                self.logger.warning("Viewer manager cleanup completed with some errors")

            return success

        except Exception as e:
            self.logger.error(f"Error during viewer manager cleanup: {e}")
            return False

    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.cleanup()
