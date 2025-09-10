"""
Sidebar - Navigation, history, and favorites panel
Professional sidebar component with task history, favorites, and quick actions.
"""

import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

import customtkinter as ctk
import tkinter as tk

from ..themes.professional_theme import professional_theme


logger = logging.getLogger(__name__)


@dataclass
class HistoryItem:
    """Represents a history item."""
    id: str
    title: str
    description: str
    timestamp: datetime
    success: bool
    execution_time: float
    user_request: str


@dataclass
class FavoriteItem:
    """Represents a favorite item."""
    id: str
    title: str
    description: str
    command: str
    category: str
    created_at: datetime
    usage_count: int = 0


class Sidebar(ctk.CTkFrame):
    """Professional sidebar with navigation, history, and favorites."""
    
    def __init__(self, parent, theme=None, on_history_select: Callable[[str], None] = None,
                 on_favorite_select: Callable[[str], None] = None,
                 on_history_item_click: Callable[[str], None] = None,
                 on_favorite_click: Callable[[str], None] = None):
        super().__init__(parent)
        
        # Store theme (use provided theme or fallback)
        self.theme = theme if theme else professional_theme
        
        # Store callbacks (use new names if provided, fallback to old names)
        self.on_history_item_click = on_history_select or on_history_item_click
        self.on_favorite_click = on_favorite_select or on_favorite_click
        
        # Data storage
        self.history_items: List[HistoryItem] = []
        self.favorite_items: List[FavoriteItem] = []
        
        # UI state
        self.active_section = "history"
        self.history_widgets = []
        self.favorite_widgets = []
        
        # Settings
        self.max_history_items = 50
        self.max_display_items = 10
        
        # Setup UI
        self._setup_ui()
        
        # Load saved data
        self._load_data()
    
    def _setup_ui(self) -> None:
        """Setup the sidebar UI."""
        
        self.configure(
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_tertiary"),
            border_width=0,
            width=300
        )
        
        # Main container
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header with navigation tabs
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            height=50
        )
        self.header_frame.pack(fill="x", pady=(0, 15))
        self.header_frame.pack_propagate(False)
        
        # Tab buttons
        self.tab_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color=professional_theme.get_color("bg_primary"),
            corner_radius=0,
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.tab_frame.pack(fill="both", expand=True)
        
        self.history_tab = professional_theme.create_styled_button(
            self.tab_frame,
            text="History",
            style="secondary",
            command=lambda: self._switch_section("history")
        )
        self.history_tab.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        
        self.favorites_tab = professional_theme.create_styled_button(
            self.tab_frame,
            text="Favorites",
            style="secondary", 
            command=lambda: self._switch_section("favorites")
        )
        self.favorites_tab.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        
        # Quick actions section
        self.actions_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border"),
            height=80
        )
        self.actions_frame.pack(fill="x", pady=(0, 15))
        self.actions_frame.pack_propagate(False)
        
        # Quick action buttons
        actions_container = ctk.CTkFrame(
            self.actions_frame,
            fg_color="transparent"
        )
        actions_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Row 1
        action_row1 = ctk.CTkFrame(actions_container, fg_color="transparent")
        action_row1.pack(fill="x", pady=(0, 5))
        
        self.clear_button = professional_theme.create_styled_button(
            action_row1,
            text="🗑️ Clear",
            style="small",
            command=self._clear_current_section,
            width=70
        )
        self.clear_button.pack(side="left", padx=(0, 5))
        
        self.export_button = professional_theme.create_styled_button(
            action_row1,
            text="📤 Export", 
            style="small",
            command=self._export_data,
            width=70
        )
        self.export_button.pack(side="left")
        
        # Row 2
        action_row2 = ctk.CTkFrame(actions_container, fg_color="transparent")
        action_row2.pack(fill="x")
        
        self.refresh_button = professional_theme.create_styled_button(
            action_row2,
            text="🔄 Refresh",
            style="small",
            command=self._refresh_current_section,
            width=70
        )
        self.refresh_button.pack(side="left", padx=(0, 5))
        
        self.settings_button = professional_theme.create_styled_button(
            action_row2,
            text="⚙️ Settings",
            style="small",
            command=self._show_settings,
            width=70
        )
        self.settings_button.pack(side="left")
        
        # Content area (scrollable)
        self.content_frame = ctk.CTkScrollableFrame(
            self.main_container,
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.content_frame.pack(fill="both", expand=True)
        
        # Initialize with history section
        self._switch_section("history")
    
    def _switch_section(self, section: str) -> None:
        """Switch between sidebar sections."""
        
        self.active_section = section
        
        # Update tab appearance
        if section == "history":
            self.history_tab.configure(fg_color=professional_theme.get_color("primary"))
            self.favorites_tab.configure(fg_color=professional_theme.get_color("bg_tertiary"))
        else:
            self.history_tab.configure(fg_color=professional_theme.get_color("bg_tertiary"))
            self.favorites_tab.configure(fg_color=professional_theme.get_color("primary"))
        
        # Clear and populate content
        self._clear_content()
        
        if section == "history":
            self._populate_history()
        elif section == "favorites":
            self._populate_favorites()
    
    def _clear_content(self) -> None:
        """Clear content area."""
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.history_widgets.clear()
        self.favorite_widgets.clear()
    
    def _populate_history(self) -> None:
        """Populate history section."""
        
        if not self.history_items:
            self._show_empty_state("No execution history", "History of task executions will appear here")
            return
        
        # Section header
        header_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            height=30
        )
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text=f"Recent Tasks ({len(self.history_items)})",
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_primary")
        )
        header_label.pack(side="left")
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        filter_frame.pack(side="right")
        
        # Show recent history items
        recent_items = sorted(self.history_items, key=lambda x: x.timestamp, reverse=True)
        display_items = recent_items[:self.max_display_items]
        
        for item in display_items:
            item_widget = self._create_history_item_widget(item)
            self.history_widgets.append(item_widget)
    
    def _populate_favorites(self) -> None:
        """Populate favorites section."""
        
        if not self.favorite_items:
            self._show_empty_state("No favorites", "Save frequently used commands as favorites")
            return
        
        # Section header  
        header_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            height=30
        )
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text=f"Favorites ({len(self.favorite_items)})",
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_primary")
        )
        header_label.pack(side="left")
        
        add_button = professional_theme.create_styled_button(
            header_frame,
            text="➕",
            style="small",
            command=self._add_favorite,
            width=25
        )
        add_button.pack(side="right")
        
        # Group favorites by category
        categories = {}
        for item in self.favorite_items:
            category = item.category or "Uncategorized"
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Display categories
        for category_name, items in categories.items():
            category_widget = self._create_favorites_category(category_name, items)
    
    def _create_history_item_widget(self, item: HistoryItem) -> Dict[str, Any]:
        """Create widget for history item."""
        
        item_frame = ctk.CTkFrame(
            self.content_frame,
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_secondary"),
            border_width=1,
            border_color=professional_theme.get_color("border"),
            height=70
        )
        item_frame.pack(fill="x", padx=10, pady=3)
        item_frame.pack_propagate(False)
        
        # Make clickable
        item_frame.bind("<Button-1>", lambda e: self._on_history_item_clicked(item.id))
        
        # Main content
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Title and status
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 2))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=item.title,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_primary"),
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True)
        
        # Status indicator
        status_color = professional_theme.get_color("success" if item.success else "error")
        status_label = ctk.CTkLabel(
            title_frame,
            text="●",
            font=("Arial", 12),
            text_color=status_color,
            width=20
        )
        status_label.pack(side="right")
        
        # Description (truncated)
        desc_text = item.description[:60] + "..." if len(item.description) > 60 else item.description
        desc_label = ctk.CTkLabel(
            content_frame,
            text=desc_text,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted"),
            anchor="w"
        )
        desc_label.pack(fill="x", pady=(0, 2))
        
        # Timestamp and duration
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x")
        
        time_ago = self._format_time_ago(item.timestamp)
        time_label = ctk.CTkLabel(
            info_frame,
            text=time_ago,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        time_label.pack(side="left")
        
        duration_label = ctk.CTkLabel(
            info_frame,
            text=f"{item.execution_time:.1f}s",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        duration_label.pack(side="right")
        
        return {
            "frame": item_frame,
            "item_id": item.id,
            "title": title_label,
            "description": desc_label,
            "status": status_label
        }
    
    def _create_favorites_category(self, category_name: str, items: List[FavoriteItem]) -> None:
        """Create a favorites category section."""
        
        # Category header
        category_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            height=25
        )
        category_frame.pack(fill="x", padx=10, pady=(10, 5))
        category_frame.pack_propagate(False)
        
        category_label = ctk.CTkLabel(
            category_frame,
            text=f"📁 {category_name}",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_secondary")
        )
        category_label.pack(side="left")
        
        # Category items
        for item in items:
            self._create_favorite_item_widget(item)
    
    def _create_favorite_item_widget(self, item: FavoriteItem) -> None:
        """Create widget for favorite item."""
        
        item_frame = ctk.CTkFrame(
            self.content_frame,
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_secondary"),
            border_width=1,
            border_color=professional_theme.get_color("border"),
            height=50
        )
        item_frame.pack(fill="x", padx=15, pady=2)
        item_frame.pack_propagate(False)
        
        # Make clickable
        item_frame.bind("<Button-1>", lambda e: self._on_favorite_item_clicked(item.id))
        
        # Content
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=6)
        
        # Title and usage count
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 2))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=item.title,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_primary"),
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True)
        
        if item.usage_count > 0:
            usage_label = ctk.CTkLabel(
                title_frame,
                text=f"×{item.usage_count}",
                font=professional_theme.get_font("body_small"),
                text_color=professional_theme.get_color("text_muted")
            )
            usage_label.pack(side="right")
        
        # Description (truncated)
        desc_text = item.description[:50] + "..." if len(item.description) > 50 else item.description
        desc_label = ctk.CTkLabel(
            content_frame,
            text=desc_text,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted"),
            anchor="w"
        )
        desc_label.pack(fill="x")
        
        self.favorite_widgets.append({
            "frame": item_frame,
            "item_id": item.id,
            "title": title_label,
            "description": desc_label
        })
    
    def _show_empty_state(self, title: str, message: str) -> None:
        """Show empty state message."""
        
        empty_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            height=100
        )
        empty_frame.pack(fill="x", padx=10, pady=30)
        empty_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            empty_frame,
            text=title,
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_muted")
        )
        title_label.pack(pady=(0, 5))
        
        message_label = ctk.CTkLabel(
            empty_frame,
            text=message,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted"),
            justify="center"
        )
        message_label.pack()
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as time ago."""
        
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    
    def _on_history_item_clicked(self, item_id: str) -> None:
        """Handle history item click."""
        
        if self.on_history_item_click:
            self.on_history_item_click(item_id)
        
        logger.debug(f"History item clicked: {item_id}")
    
    def _on_favorite_item_clicked(self, item_id: str) -> None:
        """Handle favorite item click."""
        
        # Update usage count
        for item in self.favorite_items:
            if item.id == item_id:
                item.usage_count += 1
                break
        
        if self.on_favorite_click:
            self.on_favorite_click(item_id)
        
        # Refresh display to show updated usage count
        if self.active_section == "favorites":
            self._populate_favorites()
        
        logger.debug(f"Favorite item clicked: {item_id}")
    
    def _clear_current_section(self) -> None:
        """Clear current section data."""
        
        if self.active_section == "history":
            self.history_items.clear()
            self._populate_history()
            logger.info("History cleared")
        elif self.active_section == "favorites":
            self.favorite_items.clear()
            self._populate_favorites()
            logger.info("Favorites cleared")
    
    def _export_data(self) -> None:
        """Export current section data."""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.active_section == "history":
                filename = f"ai_os_history_{timestamp}.json"
                data = [asdict(item) for item in self.history_items]
            else:
                filename = f"ai_os_favorites_{timestamp}.json"
                data = [asdict(item) for item in self.favorite_items]
            
            # Convert datetime objects to strings for JSON serialization
            def datetime_converter(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=datetime_converter)
            
            logger.info(f"Data exported to: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
    
    def _refresh_current_section(self) -> None:
        """Refresh current section display."""
        
        self._switch_section(self.active_section)
    
    def _show_settings(self) -> None:
        """Show sidebar settings dialog."""
        
        # Create settings dialog
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Sidebar Settings")
        settings_window.geometry("300x200")
        settings_window.transient(self.winfo_toplevel())
        settings_window.grab_set()
        
        # Settings content
        label = ctk.CTkLabel(
            settings_window,
            text="Sidebar Settings",
            font=professional_theme.get_font("heading_medium")
        )
        label.pack(pady=20)
        
        # Max items setting
        max_items_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        max_items_frame.pack(pady=10)
        
        max_items_label = ctk.CTkLabel(max_items_frame, text="Max display items:")
        max_items_label.pack(side="left", padx=(0, 10))
        
        max_items_entry = ctk.CTkEntry(max_items_frame, width=60)
        max_items_entry.pack(side="left")
        max_items_entry.insert(0, str(self.max_display_items))
        
        # Close button
        close_btn = professional_theme.create_styled_button(
            settings_window,
            text="Close",
            command=settings_window.destroy
        )
        close_btn.pack(pady=20)
    
    def _add_favorite(self) -> None:
        """Show add favorite dialog."""
        
        # Create add favorite dialog
        add_window = ctk.CTkToplevel(self)
        add_window.title("Add Favorite")
        add_window.geometry("400x300")
        add_window.transient(self.winfo_toplevel())
        add_window.grab_set()
        
        # Form fields
        fields = {}
        
        # Title
        title_label = ctk.CTkLabel(add_window, text="Title:")
        title_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        fields["title"] = ctk.CTkEntry(add_window, width=360)
        fields["title"].pack(padx=20, pady=(0, 10))
        
        # Description
        desc_label = ctk.CTkLabel(add_window, text="Description:")
        desc_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        fields["description"] = ctk.CTkTextbox(add_window, width=360, height=60)
        fields["description"].pack(padx=20, pady=(0, 10))
        
        # Command
        cmd_label = ctk.CTkLabel(add_window, text="Command:")
        cmd_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        fields["command"] = ctk.CTkEntry(add_window, width=360)
        fields["command"].pack(padx=20, pady=(0, 10))
        
        # Category
        cat_label = ctk.CTkLabel(add_window, text="Category:")
        cat_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        fields["category"] = ctk.CTkEntry(add_window, width=360)
        fields["category"].pack(padx=20, pady=(0, 20))
        fields["category"].insert(0, "General")
        
        # Buttons
        button_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        button_frame.pack(pady=10)
        
        cancel_btn = professional_theme.create_styled_button(
            button_frame,
            text="Cancel",
            style="secondary",
            command=add_window.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        save_btn = professional_theme.create_styled_button(
            button_frame,
            text="Save",
            command=lambda: self._save_favorite(fields, add_window)
        )
        save_btn.pack(side="left")
    
    def _save_favorite(self, fields: Dict[str, Any], window) -> None:
        """Save a new favorite item."""
        
        try:
            title = fields["title"].get().strip()
            description = fields["description"].get("1.0", "end-1c").strip()
            command = fields["command"].get().strip()
            category = fields["category"].get().strip()
            
            if not title or not command:
                return
            
            favorite = FavoriteItem(
                id=f"fav_{int(datetime.now().timestamp())}",
                title=title,
                description=description,
                command=command,
                category=category,
                created_at=datetime.now(),
                usage_count=0
            )
            
            self.favorite_items.append(favorite)
            
            # Refresh if showing favorites
            if self.active_section == "favorites":
                self._populate_favorites()
            
            window.destroy()
            logger.info(f"Added favorite: {title}")
            
        except Exception as e:
            logger.error(f"Failed to save favorite: {e}")
    
    def _load_data(self) -> None:
        """Load saved data from storage."""
        
        # This would load from persistent storage in a real implementation
        # For now, it's a placeholder
        
        logger.debug("Loading sidebar data...")
    
    def _save_data(self) -> None:
        """Save data to persistent storage."""
        
        # This would save to persistent storage in a real implementation
        # For now, it's a placeholder
        
        logger.debug("Saving sidebar data...")
    
    # Public API methods
    
    def add_history_item(self, title: str, description: str, success: bool, 
                        execution_time: float, user_request: str) -> None:
        """Add a new history item."""
        
        item = HistoryItem(
            id=f"hist_{int(datetime.now().timestamp())}",
            title=title,
            description=description,
            timestamp=datetime.now(),
            success=success,
            execution_time=execution_time,
            user_request=user_request
        )
        
        self.history_items.append(item)
        
        # Limit history size
        if len(self.history_items) > self.max_history_items:
            self.history_items = self.history_items[-self.max_history_items:]
        
        # Refresh if showing history
        if self.active_section == "history":
            self._populate_history()
        
        logger.debug(f"Added history item: {title}")
    
    def get_history_item(self, item_id: str) -> Optional[HistoryItem]:
        """Get history item by ID."""
        
        for item in self.history_items:
            if item.id == item_id:
                return item
        
        return None
    
    def get_favorite_item(self, item_id: str) -> Optional[FavoriteItem]:
        """Get favorite item by ID."""
        
        for item in self.favorite_items:
            if item.id == item_id:
                return item
        
        return None
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get history summary statistics."""
        
        if not self.history_items:
            return {"total": 0, "successful": 0, "failed": 0, "avg_time": 0}
        
        successful = len([item for item in self.history_items if item.success])
        failed = len(self.history_items) - successful
        avg_time = sum(item.execution_time for item in self.history_items) / len(self.history_items)
        
        return {
            "total": len(self.history_items),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.history_items) if self.history_items else 0,
            "avg_execution_time": avg_time
        }
    
    def initialize(self) -> None:
        """Initialize the sidebar component."""
        # Load any saved data
        self._load_data()
        # Set default section to history
        self.active_section = "history"