"""
Screenshot Preview - Live screenshot display with AI analysis overlay
Real-time visual feedback component showing current screen state and AI observations.
"""

import time
from typing import Optional, Dict, Any, Callable
import logging
from datetime import datetime, timedelta
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io

import customtkinter as ctk
import tkinter as tk

from ..themes.professional_theme import professional_theme


logger = logging.getLogger(__name__)


class ScreenshotPreview(ctk.CTkFrame):
    """Professional screenshot preview with AI analysis overlay."""
    
    def __init__(self, parent, on_screenshot_click: Callable[[Dict[str, float]], None] = None):
        super().__init__(parent)
        
        self.on_screenshot_click = on_screenshot_click
        
        # Screenshot state
        self.current_screenshot: Optional[Image.Image] = None
        self.screenshot_timestamp: Optional[datetime] = None
        self.ai_analysis: Optional[Dict[str, Any]] = None
        
        # Display settings
        self.preview_size = (400, 300)
        self.auto_refresh = True
        self.refresh_interval = 5  # seconds
        
        # Overlay settings
        self.show_analysis_overlay = True
        self.show_clickable_areas = False
        
        # Setup UI
        self._setup_ui()
        
        # Start auto-refresh if enabled
        if self.auto_refresh:
            self._start_auto_refresh()
    
    def _setup_ui(self) -> None:
        """Setup the screenshot preview UI."""
        
        self.configure(
            corner_radius=12,
            fg_color=professional_theme.get_color("bg_secondary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        
        # Main container
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            height=40
        )
        self.header_frame.pack(fill="x", pady=(0, 10))
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Live Screenshot",
            font=professional_theme.get_font("heading_small"),
            text_color=professional_theme.get_color("text_primary")
        )
        self.title_label.pack(side="left")
        
        # Controls
        self.controls_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent"
        )
        self.controls_frame.pack(side="right")
        
        self.refresh_button = professional_theme.create_styled_button(
            self.controls_frame,
            text="📷",
            style="small",
            command=self._take_screenshot,
            width=30
        )
        self.refresh_button.pack(side="left", padx=(0, 5))
        
        self.auto_refresh_var = ctk.BooleanVar(value=self.auto_refresh)
        self.auto_refresh_check = ctk.CTkCheckBox(
            self.controls_frame,
            text="Auto",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
            font=professional_theme.get_font("body_small"),
            width=50
        )
        self.auto_refresh_check.pack(side="left")
        
        # Screenshot display area
        self.screenshot_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=8,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.screenshot_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Canvas for screenshot display
        self.screenshot_canvas = ctk.CTkCanvas(
            self.screenshot_frame,
            bg=professional_theme.get_color("bg_primary"),
            highlightthickness=0,
            cursor="crosshair"
        )
        self.screenshot_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind canvas events
        self.screenshot_canvas.bind("<Button-1>", self._on_canvas_click)
        self.screenshot_canvas.bind("<Motion>", self._on_canvas_motion)
        
        # Info panel
        self.info_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            height=60
        )
        self.info_frame.pack(fill="x")
        self.info_frame.pack_propagate(False)
        
        # Screenshot info
        self.info_container = ctk.CTkFrame(
            self.info_frame,
            fg_color=professional_theme.get_color("bg_primary"),
            corner_radius=6,
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.info_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.timestamp_label = ctk.CTkLabel(
            self.info_container,
            text="No screenshot captured",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.timestamp_label.pack(side="left", padx=10, pady=5)
        
        self.coordinates_label = ctk.CTkLabel(
            self.info_container,
            text="",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.coordinates_label.pack(side="right", padx=10, pady=5)
        
        # Analysis toggle
        self.analysis_var = ctk.BooleanVar(value=self.show_analysis_overlay)
        self.analysis_check = ctk.CTkCheckBox(
            self.info_container,
            text="AI Analysis",
            variable=self.analysis_var,
            command=self._toggle_analysis_overlay,
            font=professional_theme.get_font("body_small")
        )
        self.analysis_check.pack(pady=5)
        
        # Show empty state
        self._show_empty_state()
    
    def _show_empty_state(self) -> None:
        """Show empty state when no screenshot is available."""
        
        canvas_width = self.screenshot_canvas.winfo_width()
        canvas_height = self.screenshot_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            self.screenshot_canvas.delete("all")
            
            # Draw empty state
            self.screenshot_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="No screenshot available\nClick refresh to capture",
                font=professional_theme.get_font("body_medium"),
                fill=professional_theme.get_color("text_muted"),
                justify="center"
            )
    
    def _take_screenshot(self) -> None:
        """Capture a new screenshot."""
        
        try:
            import pyautogui
            
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            self.current_screenshot = screenshot
            self.screenshot_timestamp = datetime.now()
            
            # Update display
            self._update_screenshot_display()
            
            # Update info
            timestamp_str = self.screenshot_timestamp.strftime("%H:%M:%S")
            size_str = f"{screenshot.width}x{screenshot.height}"
            self.timestamp_label.configure(text=f"Captured at {timestamp_str} ({size_str})")
            
            logger.debug(f"Screenshot captured: {size_str}")
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            self.timestamp_label.configure(text="Screenshot capture failed")
    
    def _update_screenshot_display(self) -> None:
        """Update the screenshot display in the canvas."""
        
        if not self.current_screenshot:
            self._show_empty_state()
            return
        
        try:
            # Get canvas dimensions
            canvas_width = self.screenshot_canvas.winfo_width()
            canvas_height = self.screenshot_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready, schedule update
                self.after(100, self._update_screenshot_display)
                return
            
            # Calculate scaled size maintaining aspect ratio
            img_width, img_height = self.current_screenshot.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize screenshot
            resized_screenshot = self.current_screenshot.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )
            
            # Add analysis overlay if enabled
            if self.show_analysis_overlay and self.ai_analysis:
                resized_screenshot = self._add_analysis_overlay(resized_screenshot, scale)
            
            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(resized_screenshot)
            
            # Clear canvas and display image
            self.screenshot_canvas.delete("all")
            
            # Center image in canvas
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.screenshot_canvas.create_image(
                x, y, 
                anchor="nw", 
                image=self.photo_image
            )
            
            # Store display info for coordinate conversion
            self.display_info = {
                "scale": scale,
                "offset_x": x,
                "offset_y": y,
                "display_width": new_width,
                "display_height": new_height
            }
            
        except Exception as e:
            logger.error(f"Failed to update screenshot display: {e}")
            self._show_empty_state()
    
    def _add_analysis_overlay(self, image: Image.Image, scale: float) -> Image.Image:
        """Add AI analysis overlay to screenshot."""
        
        if not self.ai_analysis:
            return image
        
        try:
            # Create overlay image
            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Try to load font
            try:
                font = ImageFont.truetype("arial.ttf", 12)
                small_font = ImageFont.truetype("arial.ttf", 10)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            # Draw detected elements
            elements = self.ai_analysis.get("detected_elements", [])
            for element in elements:
                if "bbox" in element:
                    bbox = element["bbox"]
                    
                    # Scale bounding box
                    x1 = int(bbox["x"] * scale)
                    y1 = int(bbox["y"] * scale)
                    x2 = int((bbox["x"] + bbox["width"]) * scale)
                    y2 = int((bbox["y"] + bbox["height"]) * scale)
                    
                    # Draw bounding box
                    draw.rectangle(
                        [x1, y1, x2, y2],
                        outline=(0, 255, 0, 180),
                        width=2
                    )
                    
                    # Draw label
                    label = element.get("type", "Unknown")
                    confidence = element.get("confidence", 0.0)
                    
                    label_text = f"{label} ({confidence:.1%})"
                    
                    # Background for text
                    text_bbox = draw.textbbox((0, 0), label_text, font=small_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    draw.rectangle(
                        [x1, y1 - text_height - 4, x1 + text_width + 8, y1],
                        fill=(0, 255, 0, 160)
                    )
                    
                    # Draw text
                    draw.text(
                        (x1 + 4, y1 - text_height - 2),
                        label_text,
                        fill=(255, 255, 255, 255),
                        font=small_font
                    )
            
            # Composite overlay onto image
            result = Image.alpha_composite(
                image.convert("RGBA"), overlay
            ).convert("RGB")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add analysis overlay: {e}")
            return image
    
    def _convert_canvas_to_screen_coords(self, canvas_x: int, canvas_y: int) -> Dict[str, float]:
        """Convert canvas coordinates to screen coordinates."""
        
        if not hasattr(self, "display_info") or not self.current_screenshot:
            return {"x": 0, "y": 0}
        
        display_info = self.display_info
        
        # Convert canvas coords to image coords
        img_x = canvas_x - display_info["offset_x"]
        img_y = canvas_y - display_info["offset_y"]
        
        # Convert to screen coords
        screen_x = img_x / display_info["scale"]
        screen_y = img_y / display_info["scale"]
        
        return {
            "x": max(0, min(screen_x, self.current_screenshot.width)),
            "y": max(0, min(screen_y, self.current_screenshot.height))
        }
    
    def _on_canvas_click(self, event) -> None:
        """Handle canvas click events."""
        
        screen_coords = self._convert_canvas_to_screen_coords(event.x, event.y)
        
        logger.debug(f"Screenshot clicked at screen coordinates: {screen_coords}")
        
        if self.on_screenshot_click:
            self.on_screenshot_click(screen_coords)
    
    def _on_canvas_motion(self, event) -> None:
        """Handle canvas mouse motion."""
        
        screen_coords = self._convert_canvas_to_screen_coords(event.x, event.y)
        self.coordinates_label.configure(
            text=f"({int(screen_coords['x'])}, {int(screen_coords['y'])})"
        )
    
    def _toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh functionality."""
        
        self.auto_refresh = self.auto_refresh_var.get()
        
        if self.auto_refresh:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()
    
    def _start_auto_refresh(self) -> None:
        """Start auto-refresh timer."""
        
        if self.auto_refresh:
            self._take_screenshot()
            self.after(self.refresh_interval * 1000, self._start_auto_refresh)
    
    def _stop_auto_refresh(self) -> None:
        """Stop auto-refresh timer."""
        
        # Auto-refresh is controlled by the recursive timer
        pass
    
    def _toggle_analysis_overlay(self) -> None:
        """Toggle AI analysis overlay."""
        
        self.show_analysis_overlay = self.analysis_var.get()
        
        # Refresh display if we have a screenshot
        if self.current_screenshot:
            self._update_screenshot_display()
    
    def update_ai_analysis(self, analysis: Dict[str, Any]) -> None:
        """Update AI analysis data for overlay."""
        
        self.ai_analysis = analysis
        
        # Refresh display if overlay is enabled
        if self.show_analysis_overlay and self.current_screenshot:
            self._update_screenshot_display()
    
    def set_screenshot(self, screenshot: Image.Image, analysis: Optional[Dict[str, Any]] = None) -> None:
        """Set screenshot from external source."""
        
        self.current_screenshot = screenshot
        self.screenshot_timestamp = datetime.now()
        
        if analysis:
            self.ai_analysis = analysis
        
        # Update display
        self._update_screenshot_display()
        
        # Update info
        timestamp_str = self.screenshot_timestamp.strftime("%H:%M:%S")
        size_str = f"{screenshot.width}x{screenshot.height}"
        self.timestamp_label.configure(text=f"Updated at {timestamp_str} ({size_str})")
    
    def get_current_screenshot(self) -> Optional[Image.Image]:
        """Get current screenshot."""
        
        return self.current_screenshot
    
    def save_screenshot(self, filename: str) -> bool:
        """Save current screenshot to file."""
        
        if not self.current_screenshot:
            return False
        
        try:
            self.current_screenshot.save(filename)
            logger.info(f"Screenshot saved to: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return False