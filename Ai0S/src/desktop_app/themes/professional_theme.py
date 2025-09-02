"""
Professional Theme Configuration for CustomTkinter
Modern, clean theme with customizable colors and styling.
"""

import customtkinter as ctk
from typing import Dict, Tuple, Optional
from enum import Enum


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ProfessionalTheme:
    """Professional theme configuration for the AI desktop application."""
    
    def __init__(self):
        # Primary color palette
        self.colors = {
            "primary": "#2B5CE6",      # Professional blue
            "primary_hover": "#1E40AF",
            "primary_disabled": "#93C5FD",
            
            "secondary": "#4F46E5",     # Indigo accent
            "secondary_hover": "#3730A3",
            
            "success": "#10B981",       # Green
            "success_hover": "#059669",
            
            "warning": "#F59E0B",       # Amber
            "warning_hover": "#D97706",
            
            "error": "#EF4444",         # Red
            "error_hover": "#DC2626",
            
            "info": "#3B82F6",          # Blue
            "info_hover": "#2563EB",
        }
        
        # Light theme colors
        self.light_colors = {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8FAFC",
            "bg_tertiary": "#F1F5F9",
            "bg_hover": "#E2E8F0",
            
            "text_primary": "#1E293B",
            "text_secondary": "#475569",
            "text_muted": "#64748B",
            "text_disabled": "#94A3B8",
            
            "border": "#E2E8F0",
            "border_hover": "#CBD5E1",
            
            "shadow": "#00000010",
            "overlay": "#00000040",
        }
        
        # Dark theme colors
        self.dark_colors = {
            "bg_primary": "#0F172A",
            "bg_secondary": "#1E293B",
            "bg_tertiary": "#334155",
            "bg_hover": "#475569",
            
            "text_primary": "#F8FAFC",
            "text_secondary": "#CBD5E1",
            "text_muted": "#94A3B8",
            "text_disabled": "#64748B",
            
            "border": "#334155",
            "border_hover": "#475569",
            
            "shadow": "#00000030",
            "overlay": "#00000080",
        }
        
        # Font configuration
        self.fonts = {
            "heading_large": ("Segoe UI", 24, "bold"),
            "heading_medium": ("Segoe UI", 20, "bold"),
            "heading_small": ("Segoe UI", 16, "bold"),
            
            "body_large": ("Segoe UI", 14, "normal"),
            "body_medium": ("Segoe UI", 12, "normal"),
            "body_small": ("Segoe UI", 10, "normal"),
            
            "mono": ("Consolas", 11, "normal"),
            "mono_bold": ("Consolas", 11, "bold"),
        }
        
        # Component-specific styling
        self.button_styles = {
            "primary": {
                "corner_radius": 8,
                "height": 36,
                "font": self.fonts["body_large"],
            },
            "secondary": {
                "corner_radius": 6,
                "height": 32,
                "font": self.fonts["body_medium"],
            },
            "small": {
                "corner_radius": 4,
                "height": 28,
                "font": self.fonts["body_small"],
            }
        }
        
        self.input_styles = {
            "default": {
                "corner_radius": 6,
                "height": 36,
                "font": self.fonts["body_medium"],
                "border_width": 1,
            },
            "large": {
                "corner_radius": 8,
                "height": 44,
                "font": self.fonts["body_large"],
                "border_width": 1,
            }
        }
        
        self.panel_styles = {
            "sidebar": {
                "corner_radius": 0,
                "border_width": 0,
            },
            "main": {
                "corner_radius": 12,
                "border_width": 1,
            },
            "card": {
                "corner_radius": 8,
                "border_width": 1,
            }
        }
        
        # Animation settings
        self.animations = {
            "hover_duration": 200,
            "fade_duration": 300,
            "slide_duration": 400,
        }
    
    def apply_theme(self, mode: ThemeMode = ThemeMode.SYSTEM) -> None:
        """Apply the professional theme to CustomTkinter."""
        
        # Set appearance mode
        if mode == ThemeMode.SYSTEM:
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(mode.value)
        
        # Create custom theme
        theme_dict = self._create_theme_dict()
        ctk.set_default_color_theme(theme_dict)
    
    def _create_theme_dict(self) -> Dict:
        """Create CustomTkinter theme dictionary."""
        
        theme = {
            "CTk": {
                "fg_color": [self.light_colors["bg_primary"], self.dark_colors["bg_primary"]]
            },
            "CTkToplevel": {
                "fg_color": [self.light_colors["bg_primary"], self.dark_colors["bg_primary"]]
            },
            
            # Buttons
            "CTkButton": {
                "corner_radius": 8,
                "border_width": 0,
                "fg_color": [self.colors["primary"], self.colors["primary"]],
                "hover_color": [self.colors["primary_hover"], self.colors["primary_hover"]],
                "border_color": [self.colors["primary"], self.colors["primary"]],
                "text_color": ["white", "white"],
                "text_color_disabled": [self.light_colors["text_disabled"], self.dark_colors["text_disabled"]]
            },
            
            # Frames
            "CTkFrame": {
                "corner_radius": 12,
                "border_width": 1,
                "fg_color": [self.light_colors["bg_secondary"], self.dark_colors["bg_secondary"]],
                "border_color": [self.light_colors["border"], self.dark_colors["border"]]
            },
            
            # Labels
            "CTkLabel": {
                "text_color": [self.light_colors["text_primary"], self.dark_colors["text_primary"]]
            },
            
            # Entry fields
            "CTkEntry": {
                "corner_radius": 6,
                "border_width": 1,
                "fg_color": [self.light_colors["bg_primary"], self.dark_colors["bg_primary"]],
                "border_color": [self.light_colors["border"], self.dark_colors["border"]],
                "text_color": [self.light_colors["text_primary"], self.dark_colors["text_primary"]],
                "placeholder_text_color": [self.light_colors["text_muted"], self.dark_colors["text_muted"]]
            },
            
            # Text boxes
            "CTkTextbox": {
                "corner_radius": 8,
                "border_width": 1,
                "fg_color": [self.light_colors["bg_primary"], self.dark_colors["bg_primary"]],
                "border_color": [self.light_colors["border"], self.dark_colors["border"]],
                "text_color": [self.light_colors["text_primary"], self.dark_colors["text_primary"]]
            },
            
            # Scrollbars
            "CTkScrollbar": {
                "corner_radius": 4,
                "border_spacing": 2,
                "fg_color": [self.light_colors["bg_tertiary"], self.dark_colors["bg_tertiary"]],
                "button_color": [self.light_colors["text_muted"], self.dark_colors["text_muted"]],
                "button_hover_color": [self.light_colors["text_secondary"], self.dark_colors["text_secondary"]]
            }
        }
        
        return theme
    
    def get_color(self, color_name: str, mode: Optional[str] = None) -> str:
        """Get color value for current theme mode."""
        
        if color_name in self.colors:
            return self.colors[color_name]
        
        # Auto-detect mode if not specified
        if mode is None:
            mode = "dark" if ctk.get_appearance_mode() == "Dark" else "light"
        
        color_dict = self.dark_colors if mode == "dark" else self.light_colors
        return color_dict.get(color_name, "#FFFFFF")
    
    def get_font(self, font_name: str) -> Tuple:
        """Get font tuple for specified font style."""
        return self.fonts.get(font_name, self.fonts["body_medium"])
    
    def get_button_style(self, style_name: str) -> Dict:
        """Get button styling dictionary."""
        return self.button_styles.get(style_name, self.button_styles["primary"])
    
    def get_input_style(self, style_name: str) -> Dict:
        """Get input field styling dictionary."""
        return self.input_styles.get(style_name, self.input_styles["default"])
    
    def get_panel_style(self, style_name: str) -> Dict:
        """Get panel styling dictionary."""
        return self.panel_styles.get(style_name, self.panel_styles["main"])
    
    def create_gradient_frame(self, parent, width: int, height: int, 
                            start_color: str, end_color: str) -> ctk.CTkFrame:
        """Create a frame with gradient background effect."""
        
        frame = ctk.CTkFrame(
            parent,
            width=width,
            height=height,
            fg_color=start_color,
            corner_radius=8
        )
        
        # Note: CustomTkinter doesn't support true gradients,
        # but we can simulate with layered frames or custom drawing
        return frame
    
    def create_styled_button(self, parent, text: str, style: str = "primary", 
                           command=None, **kwargs) -> ctk.CTkButton:
        """Create a button with specified style."""
        
        style_config = self.get_button_style(style)
        
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            corner_radius=style_config["corner_radius"],
            height=style_config["height"],
            font=style_config["font"],
            **kwargs
        )
        
        return button
    
    def create_styled_entry(self, parent, placeholder: str = "", 
                           style: str = "default", **kwargs) -> ctk.CTkEntry:
        """Create an entry field with specified style."""
        
        style_config = self.get_input_style(style)
        
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            corner_radius=style_config["corner_radius"],
            height=style_config["height"],
            font=style_config["font"],
            border_width=style_config["border_width"],
            **kwargs
        )
        
        return entry
    
    def create_styled_frame(self, parent, style: str = "main", **kwargs) -> ctk.CTkFrame:
        """Create a frame with specified style."""
        
        style_config = self.get_panel_style(style)
        
        frame = ctk.CTkFrame(
            parent,
            corner_radius=style_config["corner_radius"],
            border_width=style_config["border_width"],
            **kwargs
        )
        
        return frame


# Global theme instance
professional_theme = ProfessionalTheme()