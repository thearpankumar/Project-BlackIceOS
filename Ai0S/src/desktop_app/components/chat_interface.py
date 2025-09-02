"""
Chat Interface - Real-time messaging with rich formatting and AI integration
Professional chat component with markdown support, typing indicators, and conversation management.
"""

import asyncio
import time
import re
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkFont

from ..themes.professional_theme import professional_theme


logger = logging.getLogger(__name__)


class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    content: str
    message_type: MessageType
    timestamp: datetime
    message_id: str
    metadata: Optional[Dict[str, Any]] = None


class ChatInterface(ctk.CTkFrame):
    """Professional chat interface with real-time updates and rich formatting."""
    
    def __init__(self, parent, on_message_send: Callable[[str], None] = None):
        super().__init__(parent)
        
        self.on_message_send = on_message_send
        
        # Chat state
        self.messages: List[ChatMessage] = []
        self.is_typing = False
        self.typing_indicator_id = None
        
        # UI elements
        self.message_widgets = {}
        self.auto_scroll = True
        
        # Rich text formatting
        self.text_tags = {}
        
        # Setup UI
        self._setup_ui()
        self._setup_text_formatting()
        
        # Add welcome message
        self._add_welcome_message()
    
    def _setup_ui(self) -> None:
        """Setup the chat interface UI."""
        
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
            height=50
        )
        self.header_frame.pack(fill="x", pady=(0, 15))
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="AI Assistant Chat",
            font=professional_theme.get_font("heading_small"),
            text_color=professional_theme.get_color("text_primary")
        )
        self.title_label.pack(side="left", pady=10)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent"
        )
        self.status_frame.pack(side="right", pady=10)
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=("Arial", 14),
            text_color=professional_theme.get_color("success")
        )
        self.status_indicator.pack(side="left", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Connected",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.status_label.pack(side="left")
        
        # Chat container with scrollable area
        self.chat_container = ctk.CTkFrame(
            self.main_container,
            corner_radius=8,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.chat_container.pack(fill="both", expand=True, pady=(0, 15))
        
        # Scrollable text widget for messages
        self.chat_text = ctk.CTkTextbox(
            self.chat_container,
            font=professional_theme.get_font("body_medium"),
            wrap="word",
            state="disabled",
            activate_scrollbars=True
        )
        self.chat_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input container
        self.input_container = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            height=100
        )
        self.input_container.pack(fill="x")
        self.input_container.pack_propagate(False)
        
        # Message input frame
        self.input_frame = ctk.CTkFrame(
            self.input_container,
            corner_radius=8,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.input_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Text input area
        self.message_input = ctk.CTkTextbox(
            self.input_frame,
            height=60,
            font=professional_theme.get_font("body_medium"),
            wrap="word",
            activate_scrollbars=False
        )
        self.message_input.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind events for input
        self.message_input.bind("<Return>", self._on_enter_pressed)
        self.message_input.bind("<Shift-Return>", self._on_shift_enter_pressed)
        self.message_input.bind("<KeyPress>", self._on_typing)
        
        # Input controls
        self.input_controls = ctk.CTkFrame(
            self.input_container,
            fg_color="transparent",
            height=30
        )
        self.input_controls.pack(fill="x")
        
        # Left side controls
        self.left_controls = ctk.CTkFrame(
            self.input_controls,
            fg_color="transparent"
        )
        self.left_controls.pack(side="left", fill="y")
        
        # Auto-scroll toggle
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_check = ctk.CTkCheckBox(
            self.left_controls,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            font=professional_theme.get_font("body_small"),
            command=self._toggle_auto_scroll
        )
        self.auto_scroll_check.pack(side="left", padx=(0, 15))
        
        # Message counter
        self.message_count_label = ctk.CTkLabel(
            self.left_controls,
            text="Messages: 0",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.message_count_label.pack(side="left")
        
        # Right side controls
        self.right_controls = ctk.CTkFrame(
            self.input_controls,
            fg_color="transparent"
        )
        self.right_controls.pack(side="right", fill="y")
        
        # Clear button
        self.clear_button = professional_theme.create_styled_button(
            self.right_controls,
            text="Clear",
            style="small",
            command=self._clear_chat,
            width=60
        )
        self.clear_button.pack(side="left", padx=(0, 10))
        
        # Send button
        self.send_button = professional_theme.create_styled_button(
            self.right_controls,
            text="Send",
            style="primary",
            command=self._send_message,
            width=80
        )
        self.send_button.pack(side="left")
    
    def _setup_text_formatting(self) -> None:
        """Setup text formatting tags for rich content."""
        
        # Configure text widget for rich formatting
        text_widget = self.chat_text._textbox
        
        # User message style
        text_widget.tag_configure(
            "user_message",
            foreground=professional_theme.get_color("text_primary"),
            background=professional_theme.get_color("primary", "light")[:7] + "20",  # Add transparency
            relief="solid",
            borderwidth=1,
            lmargin1=20,
            lmargin2=20,
            rmargin=20,
            spacing1=5,
            spacing3=5
        )
        
        # Assistant message style
        text_widget.tag_configure(
            "assistant_message",
            foreground=professional_theme.get_color("text_primary"),
            background=professional_theme.get_color("bg_tertiary"),
            relief="solid",
            borderwidth=1,
            lmargin1=20,
            lmargin2=20,
            rmargin=20,
            spacing1=5,
            spacing3=5
        )
        
        # System message style
        text_widget.tag_configure(
            "system_message",
            foreground=professional_theme.get_color("text_muted"),
            font=professional_theme.get_font("body_small"),
            justify="center",
            spacing1=10,
            spacing3=10
        )
        
        # Error message style
        text_widget.tag_configure(
            "error_message",
            foreground=professional_theme.get_color("error"),
            background=professional_theme.get_color("error")[:7] + "20",
            relief="solid",
            borderwidth=1,
            lmargin1=20,
            lmargin2=20,
            rmargin=20,
            spacing1=5,
            spacing3=5
        )
        
        # Timestamp style
        text_widget.tag_configure(
            "timestamp",
            foreground=professional_theme.get_color("text_muted"),
            font=professional_theme.get_font("body_small"),
            justify="right"
        )
        
        # Code block style
        text_widget.tag_configure(
            "code_block",
            foreground=professional_theme.get_color("text_primary"),
            background=professional_theme.get_color("bg_tertiary"),
            font=professional_theme.get_font("mono"),
            relief="solid",
            borderwidth=1,
            lmargin1=30,
            lmargin2=30,
            rmargin=30,
            spacing1=5,
            spacing3=5
        )
        
        # Inline code style
        text_widget.tag_configure(
            "inline_code",
            foreground=professional_theme.get_color("primary"),
            background=professional_theme.get_color("bg_tertiary"),
            font=professional_theme.get_font("mono")
        )
        
        # Bold text
        text_widget.tag_configure(
            "bold",
            font=professional_theme.get_font("body_medium")[:-1] + ("bold",)
        )
        
        # Italic text
        text_widget.tag_configure(
            "italic",
            font=professional_theme.get_font("body_medium")[:-1] + ("italic",)
        )
        
        # Typing indicator
        text_widget.tag_configure(
            "typing",
            foreground=professional_theme.get_color("text_muted"),
            font=professional_theme.get_font("body_small") + ("italic",),
            justify="left",
            spacing1=5
        )
    
    def _add_welcome_message(self) -> None:
        """Add welcome message to chat."""
        
        welcome_msg = ChatMessage(
            content="Welcome! I'm your AI assistant. I can help you control your computer, answer questions, and automate tasks. How can I help you today?",
            message_type=MessageType.SYSTEM,
            timestamp=datetime.now(),
            message_id="welcome"
        )
        
        self._add_message_to_display(welcome_msg)
    
    def add_message(self, content: str, message_type: MessageType, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to the chat."""
        
        message = ChatMessage(
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            message_id=f"{message_type.value}_{int(time.time() * 1000)}",
            metadata=metadata
        )
        
        self.messages.append(message)
        self._add_message_to_display(message)
        self._update_message_count()
        
        return message.message_id
    
    def _add_message_to_display(self, message: ChatMessage) -> None:
        """Add message to the display with formatting."""
        
        text_widget = self.chat_text._textbox
        
        # Enable editing temporarily
        text_widget.configure(state="normal")
        
        try:
            # Add timestamp
            timestamp_str = message.timestamp.strftime("%H:%M:%S")
            
            # Determine message style
            if message.message_type == MessageType.USER:
                style_tag = "user_message"
                prefix = f"You ({timestamp_str}):"
            elif message.message_type == MessageType.ASSISTANT:
                style_tag = "assistant_message"
                prefix = f"AI Assistant ({timestamp_str}):"
            elif message.message_type == MessageType.SYSTEM:
                style_tag = "system_message"
                prefix = f"System ({timestamp_str}):"
            else:  # ERROR
                style_tag = "error_message"
                prefix = f"Error ({timestamp_str}):"
            
            # Insert message
            start_pos = text_widget.index("end-1c")
            
            if message.message_type != MessageType.SYSTEM:
                # Add prefix
                text_widget.insert("end", f"\n{prefix}\n", "timestamp")
                
                # Add content with formatting
                formatted_content = self._format_message_content(message.content)
                content_start = text_widget.index("end-1c")
                
                text_widget.insert("end", formatted_content + "\n\n")
                content_end = text_widget.index("end-1c")
                
                # Apply message style to content
                text_widget.tag_add(style_tag, content_start, content_end)
            else:
                # System messages are simpler
                text_widget.insert("end", f"\n--- {message.content} ---\n\n", style_tag)
            
            # Auto-scroll if enabled
            if self.auto_scroll:
                text_widget.see("end")
            
        finally:
            # Disable editing
            text_widget.configure(state="disabled")
    
    def _format_message_content(self, content: str) -> str:
        """Format message content with markdown-like syntax."""
        
        # For now, return content as-is
        # In a more complete implementation, this would parse markdown
        # and apply appropriate text tags
        
        # Basic formatting examples:
        # - **bold** -> apply bold tag
        # - *italic* -> apply italic tag
        # - `code` -> apply inline_code tag
        # - ```code block``` -> apply code_block tag
        
        return content
    
    def _send_message(self) -> None:
        """Send the current message."""
        
        content = self.message_input.get("1.0", "end-1c").strip()
        
        if not content:
            return
        
        # Clear input
        self.message_input.delete("1.0", "end")
        
        # Add user message to chat
        self.add_message(content, MessageType.USER)
        
        # Call callback
        if self.on_message_send:
            self.on_message_send(content)
    
    def _on_enter_pressed(self, event) -> str:
        """Handle Enter key press."""
        
        self._send_message()
        return "break"  # Prevent default behavior
    
    def _on_shift_enter_pressed(self, event) -> str:
        """Handle Shift+Enter key press (new line)."""
        
        return None  # Allow default behavior (new line)
    
    def _on_typing(self, event) -> None:
        """Handle typing events."""
        
        # Could be used to show "user is typing" indicator
        pass
    
    def show_typing_indicator(self, show: bool = True) -> None:
        """Show/hide typing indicator for AI responses."""
        
        text_widget = self.chat_text._textbox
        
        if show and not self.is_typing:
            self.is_typing = True
            
            # Enable editing temporarily
            text_widget.configure(state="normal")
            
            # Add typing indicator
            self.typing_indicator_id = text_widget.index("end-1c")
            text_widget.insert("end", "\nAI Assistant is typing...\n", "typing")
            
            if self.auto_scroll:
                text_widget.see("end")
            
            text_widget.configure(state="disabled")
            
        elif not show and self.is_typing:
            self.is_typing = False
            
            if self.typing_indicator_id:
                # Remove typing indicator
                text_widget.configure(state="normal")
                
                # Find and remove typing indicator text
                try:
                    # This is a simplified removal - in practice you'd need
                    # to track the exact position of the typing indicator
                    current_content = text_widget.get("1.0", "end-1c")
                    if "AI Assistant is typing..." in current_content:
                        new_content = current_content.replace("\nAI Assistant is typing...\n", "")
                        text_widget.delete("1.0", "end")
                        text_widget.insert("1.0", new_content)
                except:
                    pass
                
                text_widget.configure(state="disabled")
                self.typing_indicator_id = None
    
    def _clear_chat(self) -> None:
        """Clear all chat messages."""
        
        self.messages.clear()
        self.chat_text._textbox.configure(state="normal")
        self.chat_text._textbox.delete("1.0", "end")
        self.chat_text._textbox.configure(state="disabled")
        
        self._update_message_count()
        self._add_welcome_message()
    
    def _toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll functionality."""
        
        self.auto_scroll = self.auto_scroll_var.get()
    
    def _update_message_count(self) -> None:
        """Update message counter display."""
        
        count = len([m for m in self.messages if m.message_type != MessageType.SYSTEM])
        self.message_count_label.configure(text=f"Messages: {count}")
    
    def update_status(self, status: str, is_connected: bool = True) -> None:
        """Update connection status display."""
        
        if is_connected:
            self.status_indicator.configure(text_color=professional_theme.get_color("success"))
            self.status_label.configure(text=status)
        else:
            self.status_indicator.configure(text_color=professional_theme.get_color("error"))
            self.status_label.configure(text=status)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        
        self.add_message(content, MessageType.SYSTEM)
    
    def add_error_message(self, content: str) -> None:
        """Add an error message."""
        
        self.add_message(content, MessageType.ERROR)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an assistant message."""
        
        # Hide typing indicator before adding message
        self.show_typing_indicator(False)
        
        self.add_message(content, MessageType.ASSISTANT, metadata)
    
    def get_chat_history(self) -> List[ChatMessage]:
        """Get complete chat history."""
        
        return self.messages.copy()
    
    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation context for AI models."""
        
        context = []
        recent_messages = [m for m in self.messages[-max_messages:] 
                          if m.message_type in [MessageType.USER, MessageType.ASSISTANT]]
        
        for msg in recent_messages:
            context.append({
                "role": "user" if msg.message_type == MessageType.USER else "assistant",
                "content": msg.content
            })
        
        return context
    
    def export_chat(self) -> str:
        """Export chat history as formatted text."""
        
        export_text = f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += "=" * 50 + "\n\n"
        
        for message in self.messages:
            timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            role = message.message_type.value.title()
            
            export_text += f"[{timestamp}] {role}:\n"
            export_text += message.content + "\n\n"
        
        return export_text