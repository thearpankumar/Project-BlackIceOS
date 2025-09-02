"""
Main Window - Professional CustomTkinter Desktop Application
Modern, responsive interface for the Agentic AI OS Control System.
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import queue

from ..config.settings import get_settings
from ..utils.platform_detector import get_system_environment
from .themes.professional_theme import ProfessionalTheme
from .components.voice_input import VoiceInputWidget
from .components.chat_interface import ChatInterface
from .components.execution_visualizer import ExecutionVisualizer
from .components.screenshot_preview import ScreenshotPreview
from .components.status_panel import StatusPanel
from .components.sidebar import Sidebar
from .ipc.ipc_client import IPCClient


logger = logging.getLogger(__name__)


class ProfessionalAIDesktopApp(ctk.CTk):
    """
    Professional CustomTkinter desktop application for AI-powered OS control.
    Features modern UI, voice input, real-time execution tracking, and adaptive theming.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.settings = get_settings()
        self.system_env = get_system_environment()
        self.ui_config = self.settings.get_ui_config()
        
        # Initialize professional theme
        self.theme = ProfessionalTheme()
        
        # Application state
        self.is_listening = False
        self.current_task_id: Optional[str] = None
        self.execution_active = False
        
        # UI update queue for thread-safe updates
        self.ui_update_queue = queue.Queue()
        
        # Backend communication
        self.ipc_client = IPCClient(
            host=self.settings.WS_HOST,
            port=self.settings.WS_PORT
        )
        self.backend_client = None
        self.orchestrator = None
        
        # Initialize UI
        self._setup_professional_window()
        self._setup_theme_system()
        self._setup_main_layout()
        self._setup_component_system()
        self._setup_event_handlers()
        
        # Start UI update processing
        self._start_ui_update_processor()
        
        # Initialize backend communication
        self._setup_backend_communication()
        
        logger.info("Professional AI Desktop App initialized successfully")
    
    def _setup_professional_window(self) -> None:
        """Setup professional window configuration."""
        
        # Window properties
        window_width = self.ui_config["window_size"][0]
        window_height = self.ui_config["window_size"][1]
        
        # Center window on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.title("AI OS Control - Agentic Assistant")
        
        # Window configuration
        self.minsize(1000, 700)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Set window icon (if available)
        try:
            icon_path = self.settings.BASE_DIR / "src/desktop_app/assets/app_icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")
        
        # Make window resizable with proper aspect ratio
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _setup_theme_system(self) -> None:
        """Setup professional theme system."""
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode(self.ui_config["theme"])
        ctk.set_default_color_theme("blue")
        
        # Configure custom colors
        self.configure(fg_color=self.theme.get_color("bg_primary"))
        
        # Font configuration
        self.default_font = ctk.CTkFont(family="Segoe UI", size=12)
        self.heading_font = ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        self.title_font = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
    
    def _setup_main_layout(self) -> None:
        """Setup the main application layout."""
        
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure grid weights
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
        
        # Header section
        self._create_header_section()
        
        # Main content area
        self._create_main_content_area()
        
        # Footer section
        self._create_footer_section()
    
    def _create_header_section(self) -> None:
        """Create professional header with status and controls."""
        
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            height=80,
            fg_color=self.theme.colors["surface"],
            corner_radius=10
        )
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.header_frame.grid_propagate(False)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # App title and logo
        title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # Title
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="🤖 AI OS Control",
            font=self.title_font,
            text_color=self.theme.colors["text_primary"]
        )
        self.title_label.pack(side="left")
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.status_frame.grid(row=0, column=1, pady=15)
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="● Ready",
            font=self.default_font,
            text_color=self.theme.colors["success_color"]
        )
        self.status_indicator.pack()
        
        # Control buttons
        controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=2, sticky="e", padx=20, pady=15)
        
        # Theme toggle button
        self.theme_button = ctk.CTkButton(
            controls_frame,
            text="🌓",
            width=40,
            height=40,
            command=self._toggle_theme,
            font=self.default_font
        )
        self.theme_button.pack(side="right", padx=5)
        
        # Settings button
        self.settings_button = ctk.CTkButton(
            controls_frame,
            text="⚙️",
            width=40,
            height=40,
            command=self._open_settings,
            font=self.default_font
        )
        self.settings_button.pack(side="right", padx=5)
    
    def _create_main_content_area(self) -> None:
        """Create the main content area with panels."""
        
        # Left sidebar
        self.sidebar = Sidebar(
            self.main_container,
            theme=self.theme,
            on_history_select=self._on_history_select,
            on_favorite_select=self._on_favorite_select
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        # Center panel - Chat and execution
        self.center_panel = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme.colors["surface"],
            corner_radius=10
        )
        self.center_panel.grid(row=1, column=1, sticky="nsew", padx=5)
        self.center_panel.grid_rowconfigure(1, weight=1)
        self.center_panel.grid_columnconfigure(0, weight=1)
        
        # Chat interface
        self.chat_interface = ChatInterface(
            self.center_panel,
            theme=self.theme,
            on_message_send=self._on_message_send,
            on_voice_toggle=self._on_voice_toggle
        )
        self.chat_interface.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Execution visualizer
        self.execution_visualizer = ExecutionVisualizer(
            self.center_panel,
            theme=self.theme
        )
        self.execution_visualizer.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Right panel - Screenshots and status
        self.right_panel = ctk.CTkFrame(
            self.main_container,
            width=350,
            fg_color=self.theme.colors["surface"],
            corner_radius=10
        )
        self.right_panel.grid(row=1, column=2, sticky="nsew", padx=(5, 0))
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        # Screenshot preview
        self.screenshot_preview = ScreenshotPreview(
            self.right_panel,
            theme=self.theme
        )
        self.screenshot_preview.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Status panel
        self.status_panel = StatusPanel(
            self.right_panel,
            theme=self.theme
        )
        self.status_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    
    def _create_footer_section(self) -> None:
        """Create footer with voice controls and system status."""
        
        self.footer_frame = ctk.CTkFrame(
            self.main_container,
            height=60,
            fg_color=self.theme.colors["surface"],
            corner_radius=10
        )
        self.footer_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        self.footer_frame.grid_propagate(False)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        
        # Voice input widget
        self.voice_input = VoiceInputWidget(
            self.footer_frame,
            theme=self.theme,
            ipc_client=self.ipc_client,
            on_voice_start=self._on_voice_start,
            on_voice_stop=self._on_voice_stop,
            on_transcript=self._on_voice_transcript
        )
        self.voice_input.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # System info display
        system_info_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        system_info_frame.grid(row=0, column=1, pady=15)
        
        system_info = f"{self.system_env.os} • {self.system_env.architecture} • {self.system_env.memory_gb}GB"
        self.system_info_label = ctk.CTkLabel(
            system_info_frame,
            text=system_info,
            font=ctk.CTkFont(size=10),
            text_color=self.theme.colors["text_secondary"]
        )
        self.system_info_label.pack()
        
        # Emergency stop button
        self.emergency_button = ctk.CTkButton(
            self.footer_frame,
            text="🛑 STOP",
            width=80,
            height=30,
            command=self._emergency_stop,
            font=self.default_font,
            fg_color=self.theme.colors["error_color"],
            hover_color=self.theme.colors.get("error_hover", "#cc0000")
        )
        self.emergency_button.grid(row=0, column=2, sticky="e", padx=20, pady=15)
    
    def _setup_component_system(self) -> None:
        """Initialize component communication system."""
        
        # Set up component callbacks
        self.chat_interface.set_execution_callback(self._update_execution_display)
        self.execution_visualizer.set_screenshot_callback(self._update_screenshot_preview)
        
        # Initialize components
        self.sidebar.initialize()
        self.status_panel.update_system_info(self.system_env.__dict__)
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers and keyboard shortcuts."""
        
        # Keyboard shortcuts
        self.bind_all("<Control-Return>", lambda e: self._on_voice_toggle())
        self.bind_all("<Control-q>", lambda e: self._on_closing())
        self.bind_all("<F1>", lambda e: self._show_help())
        self.bind_all("<F12>", lambda e: self._emergency_stop())
        
        # Window events
        self.bind("<Configure>", self._on_window_configure)
    
    def _start_ui_update_processor(self) -> None:
        """Start processing UI updates from background threads."""
        
        def process_updates():
            try:
                update = self.ui_update_queue.get_nowait()
                self._process_ui_update(update)
            except queue.Empty:
                pass
            
            # Schedule next check
            self.after(50, process_updates)
        
        # Start the update processor
        self.after(100, process_updates)
    
    def _setup_backend_communication(self) -> None:
        """Setup backend IPC communication."""
        
        try:
            # Register IPC event handlers
            self.ipc_client.register_handler("on_execution_state_changed", self._on_backend_execution_state_changed)
            self.ipc_client.register_handler("on_plan_loaded", self._on_backend_plan_loaded)
            self.ipc_client.register_handler("on_step_updated", self._on_backend_step_updated)
            self.ipc_client.register_handler("on_execution_completed", self._on_backend_execution_completed)
            self.ipc_client.register_handler("on_execution_error", self._on_backend_execution_error)
            self.ipc_client.register_handler("on_chat_response", self._on_backend_chat_response)
            self.ipc_client.register_handler("on_approval_request", self._on_backend_approval_request)
            
            # Start IPC client
            self.ipc_client.start()
            
            # Update status
            self._update_status("Connecting to backend...", "warning")
            
            logger.info("Backend communication setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup backend communication: {e}")
            self._update_status("Backend connection failed", "error")
    
    # =========================================================================
    # Backend Event Handlers
    # =========================================================================
    
    async def _on_backend_execution_state_changed(self, data: Dict[str, Any]) -> None:
        """Handle execution state change from backend."""
        state = data.get("state", "unknown")
        
        if state == "started":
            self._update_status("Task started", "info")
            self.execution_active = True
        elif state == "completed":
            self._update_status("Task completed", "success")
            self.execution_active = False
        elif state == "failed":
            self._update_status("Task failed", "error")
            self.execution_active = False
        elif state == "paused":
            self._update_status("Task paused", "warning")
    
    async def _on_backend_plan_loaded(self, data: Dict[str, Any]) -> None:
        """Handle execution plan loaded from backend."""
        plan_data = data.get("plan")
        if plan_data:
            # Update execution visualizer with the plan
            self.execution_visualizer.update_plan(plan_data)
            logger.info(f"Plan loaded: {plan_data.get('title', 'Unknown')}")
    
    async def _on_backend_step_updated(self, data: Dict[str, Any]) -> None:
        """Handle execution step update from backend."""
        step_index = data.get("step_index", 0)
        status = data.get("status", "unknown")
        
        # Update execution visualizer
        self.execution_visualizer.update_step_status(step_index, status)
        
        # Update screenshot if provided
        screenshot = data.get("screenshot")
        if screenshot:
            self.screenshot_preview.update_screenshot_b64(screenshot)
    
    async def _on_backend_execution_completed(self, data: Dict[str, Any]) -> None:
        """Handle execution completion from backend."""
        success = data.get("success", False)
        
        if success:
            self._update_status("Task completed successfully", "success")
            self.chat_interface.add_message("system", "✅ Task completed successfully!")
        else:
            self._update_status("Task failed", "error")
            self.chat_interface.add_message("system", "❌ Task failed")
        
        self.execution_active = False
    
    async def _on_backend_execution_error(self, data: Dict[str, Any]) -> None:
        """Handle execution error from backend."""
        error = data.get("error", "Unknown error")
        self._update_status(f"Error: {error}", "error")
        self.chat_interface.add_message("system", f"❌ Error: {error}")
    
    async def _on_backend_chat_response(self, data: Dict[str, Any]) -> None:
        """Handle chat response from backend."""
        message = data.get("message", "")
        if message:
            self.chat_interface.add_message("assistant", message)
    
    async def _on_backend_approval_request(self, data: Dict[str, Any]) -> None:
        """Handle approval request from backend."""
        step_title = data.get("step_title", "Unknown step")
        step_description = data.get("step_description", "")
        
        # Show approval dialog (placeholder)
        self.chat_interface.add_message("system", f"⚠️ Approval requested: {step_title}")
        logger.info(f"Approval requested: {step_title}")
    
    def _process_ui_update(self, update: Dict[str, Any]) -> None:
        """Process UI update safely in main thread."""
        
        try:
            event_type = update.get("event_type")
            data = update.get("data", {})
            
            if event_type == "task_started":
                self._handle_task_started(data)
            elif event_type == "plan_created":
                self._handle_plan_created(data)
            elif event_type == "step_executing":
                self._handle_step_executing(data)
            elif event_type == "step_completed":
                self._handle_step_completed(data)
            elif event_type == "task_complete":
                self._handle_task_complete(data)
            elif event_type == "execution_error":
                self._handle_execution_error(data)
            elif event_type == "screenshot_update":
                self._handle_screenshot_update(data)
            
        except Exception as e:
            logger.error(f"Error processing UI update: {e}")
    
    # =========================================================================
    # Event Handlers
    # =========================================================================
    
    def _on_message_send(self, message: str) -> None:
        """Handle message send from chat interface."""
        logger.info(f"Sending message: {message}")
        
        # Update status
        self._update_status("Processing...", "warning")
        
        # Send to backend via IPC
        if self.ipc_client and self.ipc_client.is_connected():
            self.ipc_client.execute_request(message, "supervised")
        else:
            self._update_status("Backend not connected", "error")
            self.chat_interface.add_message("system", "❌ Backend service not available")
    
    def _on_voice_toggle(self) -> None:
        """Handle voice input toggle."""
        if self.is_listening:
            self.voice_input.stop_listening()
        else:
            self.voice_input.start_listening()
    
    def _on_voice_start(self) -> None:
        """Handle voice recording start."""
        self.is_listening = True
        self._update_status("Listening...", "info")
    
    def _on_voice_stop(self) -> None:
        """Handle voice recording stop."""
        self.is_listening = False
        self._update_status("Processing voice...", "warning")
    
    def _on_voice_transcript(self, transcript: str) -> None:
        """Handle voice transcript received."""
        logger.info(f"Voice transcript: {transcript}")
        
        # Add to chat and execute
        self.chat_interface.add_message("user", transcript, is_voice=True)
        self._on_message_send(transcript)
    
    def _on_history_select(self, command: str) -> None:
        """Handle history item selection."""
        self.chat_interface.set_input_text(command)
    
    def _on_favorite_select(self, command: str) -> None:
        """Handle favorite command selection."""
        self._on_message_send(command)
    
    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "dark" else "dark"
        
        ctk.set_appearance_mode(new_mode)
        logger.info(f"Theme changed to: {new_mode}")
    
    def _open_settings(self) -> None:
        """Open settings dialog."""
        # Placeholder for settings dialog
        messagebox.showinfo("Settings", "Settings dialog coming soon!")
    
    def _emergency_stop(self) -> None:
        """Emergency stop all execution."""
        logger.warning("Emergency stop triggered!")
        
        # Send cancel to backend
        if self.ipc_client and self.ipc_client.is_connected():
            self.ipc_client.cancel_execution()
        
        self.execution_active = False
        self.current_task_id = None
        
        # Update UI
        self._update_status("Stopped", "error")
        self.execution_visualizer.reset()
        
        # Stop voice if active
        if self.is_listening:
            self.voice_input.stop_listening()
    
    def _show_help(self) -> None:
        """Show help dialog."""
        help_text = """
AI OS Control - Keyboard Shortcuts:

Ctrl+Enter: Toggle voice input
Ctrl+Q: Quit application
F1: Show this help
F12: Emergency stop

Voice Commands:
• "Open browser and search for..."
• "Launch application..."
• "Take a screenshot"
• "List running processes"
• And many more!
        """
        messagebox.showinfo("Help", help_text)
    
    def _on_window_configure(self, event) -> None:
        """Handle window resize/move events."""
        if event.widget == self:
            # Update components on window resize
            self.after_idle(self._update_layout)
    
    def _update_layout(self) -> None:
        """Update layout after window changes."""
        # Force component updates
        self.screenshot_preview.update_size()
    
    def _on_closing(self) -> None:
        """Handle application closing."""
        logger.info("Application closing...")
        
        # Stop any active processes
        self._emergency_stop()
        
        # Close IPC connection
        if self.ipc_client:
            self.ipc_client.stop()
        
        # Save settings/state if needed
        self._save_app_state()
        
        # Close application
        self.destroy()
    
    # =========================================================================
    # Task Execution Handlers
    # =========================================================================
    
    async def _execute_task_async(self, command: str) -> None:
        """Execute task asynchronously."""
        try:
            # This would integrate with the orchestrator
            # For now, simulate task execution
            
            task_id = f"task_{int(time.time())}"
            self.current_task_id = task_id
            self.execution_active = True
            
            # Simulate task execution with updates
            await self._simulate_task_execution(command, task_id)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self._update_status("Error", "error")
    
    async def _simulate_task_execution(self, command: str, task_id: str) -> None:
        """Simulate task execution with UI updates."""
        
        # Add system message to chat
        self.chat_interface.add_message("system", f"Starting task: {command}")
        
        # Simulate planning
        await asyncio.sleep(1)
        plan_data = {
            "task_id": task_id,
            "steps": [
                {"description": "Analyzing request", "status": "pending"},
                {"description": "Capturing screen state", "status": "pending"},
                {"description": "Executing command", "status": "pending"},
                {"description": "Verifying completion", "status": "pending"}
            ]
        }
        self.execution_visualizer.update_plan(plan_data)
        
        # Simulate step execution
        for i, step in enumerate(plan_data["steps"]):
            if not self.execution_active:
                break
                
            step["status"] = "executing"
            self.execution_visualizer.update_step_status(i, "executing")
            
            await asyncio.sleep(2)  # Simulate execution time
            
            step["status"] = "completed"
            self.execution_visualizer.update_step_status(i, "completed")
        
        # Complete task
        if self.execution_active:
            self.chat_interface.add_message("system", "Task completed successfully!")
            self._update_status("Ready", "success")
            self.execution_active = False
    
    # =========================================================================
    # UI Update Methods
    # =========================================================================
    
    def _update_status(self, status: str, status_type: str = "info") -> None:
        """Update status indicator."""
        
        colors = {
            "info": self.theme.colors["primary_color"],
            "success": self.theme.colors["success_color"],
            "warning": self.theme.colors["warning_color"],
            "error": self.theme.colors["error_color"]
        }
        
        symbols = {
            "info": "●",
            "success": "●",
            "warning": "●",
            "error": "●"
        }
        
        color = colors.get(status_type, colors["info"])
        symbol = symbols.get(status_type, "●")
        
        self.status_indicator.configure(text=f"{symbol} {status}", text_color=color)
    
    def _update_execution_display(self, execution_data: Dict[str, Any]) -> None:
        """Update execution visualization."""
        self.execution_visualizer.update_execution(execution_data)
    
    def _update_screenshot_preview(self, screenshot_data: bytes) -> None:
        """Update screenshot preview."""
        self.screenshot_preview.update_screenshot(screenshot_data)
    
    # =========================================================================
    # Task Event Handlers
    # =========================================================================
    
    def _handle_task_started(self, data: Dict[str, Any]) -> None:
        """Handle task started event."""
        self.current_task_id = data.get("task_id")
        self._update_status("Task Started", "info")
        self.chat_interface.add_message("system", f"Task started: {data.get('user_intent', '')}")
    
    def _handle_plan_created(self, data: Dict[str, Any]) -> None:
        """Handle plan created event."""
        self.execution_visualizer.update_plan(data)
        self._update_status("Executing Plan", "info")
    
    def _handle_step_executing(self, data: Dict[str, Any]) -> None:
        """Handle step execution event."""
        step_index = data.get("step_index", 0)
        self.execution_visualizer.update_step_status(step_index, "executing")
        
        # Update screenshot if provided
        screenshot = data.get("screenshot")
        if screenshot:
            self.screenshot_preview.update_screenshot_b64(screenshot)
    
    def _handle_step_completed(self, data: Dict[str, Any]) -> None:
        """Handle step completion event."""
        step_index = data.get("step_index", 0)
        success = data.get("success", False)
        status = "completed" if success else "failed"
        
        self.execution_visualizer.update_step_status(step_index, status)
    
    def _handle_task_complete(self, data: Dict[str, Any]) -> None:
        """Handle task completion event."""
        status = data.get("status", "completed")
        
        if status == "completed":
            self._update_status("Task Completed", "success")
            self.chat_interface.add_message("system", "✅ Task completed successfully!")
        else:
            self._update_status("Task Failed", "error")
            self.chat_interface.add_message("system", "❌ Task failed")
        
        # Add to history
        if self.current_task_id:
            self.sidebar.add_to_history(data.get("command", "Unknown task"))
        
        self.execution_active = False
        self.current_task_id = None
    
    def _handle_execution_error(self, data: Dict[str, Any]) -> None:
        """Handle execution error event."""
        error = data.get("error", "Unknown error")
        self._update_status("Error", "error")
        self.chat_interface.add_message("system", f"❌ Error: {error}")
    
    def _handle_screenshot_update(self, data: Dict[str, Any]) -> None:
        """Handle screenshot update event."""
        screenshot = data.get("screenshot")
        if screenshot:
            self.screenshot_preview.update_screenshot_b64(screenshot)
    
    # =========================================================================
    # Backend Integration
    # =========================================================================
    
    def set_backend_client(self, client) -> None:
        """Set backend client for communication."""
        self.backend_client = client
        logger.info("Backend client connected")
    
    def set_orchestrator(self, orchestrator) -> None:
        """Set orchestrator for task execution."""
        self.orchestrator = orchestrator
        
        # Set UI callback for real-time updates
        orchestrator.set_ui_callback(self._queue_ui_update)
        logger.info("Orchestrator connected")
    
    def _queue_ui_update(self, update: Dict[str, Any]) -> None:
        """Queue UI update for thread-safe processing."""
        self.ui_update_queue.put(update)
    
    def _save_app_state(self) -> None:
        """Save application state before closing."""
        try:
            # Save window size/position, preferences, etc.
            state = {
                "geometry": self.geometry(),
                "theme": ctk.get_appearance_mode(),
                "last_closed": datetime.now().isoformat()
            }
            
            # Save to config file (placeholder)
            logger.debug(f"Saved app state: {state}")
            
        except Exception as e:
            logger.error(f"Failed to save app state: {e}")


def main():
    """Main entry point for the desktop application."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run application
    try:
        app = ProfessionalAIDesktopApp()
        logger.info("Starting AI OS Control Desktop Application")
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()