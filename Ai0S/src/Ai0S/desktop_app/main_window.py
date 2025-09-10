"""
Simplified Main Window - Clean and Minimal AI OS Control Interface
A streamlined, user-friendly interface focusing on core functionality.
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
import pyaudio
import wave
import io
import base64
import concurrent.futures
import numpy as np

from ..config.settings import get_settings
from ..utils.platform_detector import get_system_environment
from .themes.professional_theme import ProfessionalTheme
from ..backend.models.ai_models import create_ai_models
from ..agents.orchestrator.intelligent_orchestrator import get_intelligent_orchestrator
from ..mcp_server.tools.system_tools import SystemTools

logger = logging.getLogger(__name__)


class SimpleAIDesktopApp(ctk.CTk):
    """
    Simplified AI Desktop Application with clean, minimal interface.
    Focuses on essential features: chat, voice input, and basic status.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.settings = get_settings()
        self.system_env = get_system_environment()
        self.theme = ProfessionalTheme()
        
        # Application state
        self.is_listening = False
        self.is_connected = False
        self.execution_active = False
        
        # AI models for voice transcription
        self.ai_models = None
        
        # Direct AI orchestration (no IPC needed)
        self.orchestrator = None
        self.system_tools = None
        
        # Task tracking
        self.current_task_id = None
        
        # Shared asyncio event loop for all async operations
        self.async_executor = None
        self.event_loop = None
        self._setup_async_infrastructure()
        
        # Chat history
        self.chat_history = []
        
        # Voice recording state
        self.is_recording = False
        self.audio_buffer = []
        self.audio_thread = None
        
        # Audio configuration
        self.audio_config = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": 16000,
            "chunk": 1024,
            "record_seconds": 30
        }
        
        # PyAudio instance
        self.audio = None
        
        # Initialize UI
        self._setup_window()
        self._create_interface()
        self._initialize_ai_models()
        self._initialize_orchestrator()
        
        # Initial status update
        self.after(1000, self._update_connection_status)
        
        logger.info("Simple AI Desktop App initialized")
    
    def _setup_async_infrastructure(self) -> None:
        """Setup shared asyncio event loop infrastructure to avoid conflicts."""
        try:
            # Create a thread pool executor for async operations
            self.async_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            
            # Start dedicated event loop thread
            self.async_loop_thread = threading.Thread(
                target=self._run_async_loop, 
                daemon=True
            )
            self.async_loop_thread.start()
            
            logger.info("✅ Async infrastructure initialized with dedicated event loop")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup async infrastructure: {e}")
            self.async_executor = None
            self.event_loop = None
    
    def _run_async_loop(self) -> None:
        """Run dedicated asyncio event loop in background thread."""
        try:
            # Create and set event loop for this thread
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            logger.info("🔄 Dedicated async event loop started")
            
            # Run forever
            self.event_loop.run_forever()
            
        except Exception as e:
            logger.error(f"❌ Async event loop failed: {e}")
        finally:
            if self.event_loop:
                self.event_loop.close()
    
    def _run_async_task(self, coro) -> concurrent.futures.Future:
        """Schedule async task on the dedicated event loop."""
        if not self.event_loop or self.event_loop.is_closed():
            logger.error("❌ Event loop not available")
            return None
            
        # Schedule coroutine on the dedicated loop
        return asyncio.run_coroutine_threadsafe(coro, self.event_loop)
    
    def _setup_window(self) -> None:
        """Setup clean window configuration."""
        
        # Window properties - Bigger frame for better usability
        window_width = 1200
        window_height = 800
        
        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.title("AI OS Control")
        self.minsize(1000, 700)
        
        # Configure appearance using professional theme
        self.theme.apply_theme()
        self.configure(fg_color=self.theme.get_color("bg_primary"))
        
        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Grid configuration
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _create_interface(self) -> None:
        """Create the simplified interface."""
        
        # Header with title and status
        self._create_header()
        
        # Main chat area
        self._create_chat_area()
        
        # Input area with voice controls
        self._create_input_area()
    
    def _create_header(self) -> None:
        """Create simple header with title and connection status."""
        
        header_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=self.theme.get_color("bg_secondary"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # App title
        title_label = ctk.CTkLabel(
            header_frame,
            text="AI OS Control",
            font=self.theme.get_font("heading_medium"),
            text_color=self.theme.get_color("text_primary")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # Connection status
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Starting...",
            font=self.theme.get_font("body_medium"),
            text_color=self.theme.get_color("warning")
        )
        self.status_label.grid(row=0, column=2, sticky="e", padx=20, pady=15)
    
    def _create_chat_area(self) -> None:
        """Create main chat/conversation area."""
        
        # Chat container
        chat_container = ctk.CTkFrame(self, fg_color=self.theme.get_color("bg_secondary"), corner_radius=0)
        chat_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        chat_container.grid_rowconfigure(0, weight=1)
        chat_container.grid_columnconfigure(0, weight=1)
        
        # Scrollable chat area
        self.chat_scrollable = ctk.CTkScrollableFrame(
            chat_container,
            fg_color="transparent",
            scrollbar_button_color=self.theme.get_color("border"),
            scrollbar_button_hover_color=self.theme.get_color("primary_hover")
        )
        self.chat_scrollable.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.chat_scrollable.grid_columnconfigure(0, weight=1)
        
        # Welcome message
        self._add_welcome_message()
    
    def _create_input_area(self) -> None:
        """Create input area with text input and voice controls."""
        
        input_container = ctk.CTkFrame(self, height=170, corner_radius=0, fg_color=self.theme.get_color("bg_secondary"))
        input_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_container.grid_propagate(False)
        input_container.grid_columnconfigure(1, weight=1)
        input_container.grid_rowconfigure(0, weight=1)
        
        # Left side - Voice input widget (simplified)
        voice_frame = ctk.CTkFrame(input_container, width=200)
        voice_frame.grid(row=0, column=0, sticky="ns", padx=(15, 10), pady=15)
        voice_frame.grid_propagate(False)
        
        # Voice button
        self.voice_button = ctk.CTkButton(
            voice_frame,
            text="Voice Command",
            width=180,
            height=40,
            font=self.theme.get_font("body_medium"),
            command=self._toggle_voice,
            fg_color=self.theme.get_color("primary"),
            hover_color=self.theme.get_color("primary_hover")
        )
        self.voice_button.pack(pady=(15, 10))
        
        # Voice status
        self.voice_status = ctk.CTkLabel(
            voice_frame,
            text="Ready",
            font=self.theme.get_font("mono"),
            text_color=self.theme.get_color("text_muted")
        )
        self.voice_status.pack()
        
        # Right side - Text input
        text_frame = ctk.CTkFrame(input_container, fg_color=self.theme.get_color("bg_tertiary"))
        text_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 15), pady=15)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(1, weight=1)  # Give more space to input
        
        # Text input - make it much more visible
        self.text_input = ctk.CTkEntry(
            text_frame,
            placeholder_text="Type your command here...",
            font=self.theme.get_font("body_large"),
            height=60,
            corner_radius=0,
            border_width=2,
            fg_color=self.theme.get_color("bg_primary"),
            text_color=self.theme.get_color("text_primary"),
            border_color=self.theme.get_color("border"),
            placeholder_text_color=self.theme.get_color("text_muted")
        )
        self.text_input.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        self.text_input.bind("<Return>", self._on_text_submit)
        
        # Send button - make it more prominent
        self.send_button = ctk.CTkButton(
            text_frame,
            text="Send Message",
            width=140,
            height=45,
            command=self._send_text_message,
            fg_color=self.theme.get_color("primary"),
            hover_color=self.theme.get_color("primary_hover"),
            font=self.theme.get_font("body_medium"),
            corner_radius=0
        )
        self.send_button.grid(row=1, column=0, pady=(0, 20))
        
        # Status info
        status_info = ctk.CTkLabel(
            text_frame,
            text=f"Ready • {self.system_env.os}",
            font=self.theme.get_font("body_small"),
            text_color=self.theme.get_color("text_muted")
        )
        status_info.grid(row=2, column=0, pady=(0, 15))
    
    def _add_welcome_message(self) -> None:
        """Add welcome message to chat."""
        
        welcome_text = """Welcome to AI OS Control!

I'm your AI assistant. I can help you:
- Control your computer with voice or text commands
- Open applications and files
- Take screenshots and analyze your screen
- Automate tasks and workflows

Try saying or typing commands like:
- "Open a web browser"
- "Take a screenshot"
- "Show me running processes"
- "Create a new folder on desktop"

How can I help you today?"""
        
        self._add_chat_message("assistant", welcome_text, show_timestamp=False)
    
    def _add_chat_message(self, sender: str, message: str, show_timestamp: bool = True) -> None:
        """Add message to chat area."""
        
        # Message container
        msg_frame = ctk.CTkFrame(self.chat_scrollable, fg_color="transparent")
        msg_frame.grid(row=len(self.chat_history), column=0, sticky="ew", pady=5)
        msg_frame.grid_columnconfigure(1, weight=1)
        
        # Sender colors and prefixes
        sender_config = {
            "user": {"color": self.theme.get_color("primary"), "prefix": "You", "align": "e"},
            "assistant": {"color": self.theme.get_color("secondary"), "prefix": "AI", "align": "w"},
            "system": {"color": self.theme.get_color("warning"), "prefix": "System", "align": "w"},
            "error": {"color": self.theme.get_color("error"), "prefix": "Error", "align": "w"}
        }
        
        config = sender_config.get(sender, sender_config["assistant"])
        
        # Message bubble
        if sender == "user":
            # User messages align right
            bubble_frame = ctk.CTkFrame(
                msg_frame,
                fg_color=config["color"],
                corner_radius=0
            )
            bubble_frame.grid(row=0, column=1, sticky="e", padx=(50, 0), pady=2)
        else:
            # Assistant/system messages align left
            bubble_frame = ctk.CTkFrame(
                msg_frame,
                fg_color=self.theme.get_color("bg_tertiary"),
                corner_radius=0,
                border_width=1,
                border_color=self.theme.get_color("border")
            )
            bubble_frame.grid(row=0, column=0, sticky="w", padx=(0, 50), pady=2)
        
        # Prefix and sender label
        if sender != "user":
            sender_label = ctk.CTkLabel(
                bubble_frame,
                text=f"{config['prefix']}",
                font=self.theme.get_font("body_small"),
                text_color=config["color"]
            )
            sender_label.pack(anchor="w", padx=15, pady=(10, 0))
        
        # Message text
        msg_label = ctk.CTkLabel(
            bubble_frame,
            text=message,
            font=self.theme.get_font("body_medium"),
            text_color="white" if sender == "user" else self.theme.get_color("text_primary"),
            justify="left",
            wraplength=400
        )
        msg_label.pack(anchor="w", padx=15, pady=(5 if sender != "user" else 10, 10))
        
        # Timestamp
        if show_timestamp:
            timestamp = datetime.now().strftime("%H:%M")
            time_label = ctk.CTkLabel(
                bubble_frame,
                text=timestamp,
                font=self.theme.get_font("body_small"),
                text_color=self.theme.get_color("text_muted")
            )
            time_label.pack(anchor="e" if sender == "user" else "w", padx=15, pady=(0, 8))
        
        # Store message in history
        self.chat_history.append({
            "sender": sender,
            "message": message,
            "timestamp": datetime.now()
        })
        
        # Auto-scroll to bottom
        self.after(100, lambda: self.chat_scrollable._parent_canvas.yview_moveto(1.0))
    
    def _initialize_ai_models(self) -> None:
        """Initialize AI models for voice transcription."""
        
        try:
            # Initialize AI models in a thread since we don't have an event loop yet
            threading.Thread(target=self._setup_ai_models_sync, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self._add_chat_message("system", "Warning: Voice transcription may not work - AI models initialization failed")
    
    def _setup_ai_models_sync(self) -> None:
        """Setup AI models synchronously in a thread."""
        
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize AI models
            self.ai_models = loop.run_until_complete(create_ai_models())
            
            logger.info("AI models initialized successfully")
            
            # Update UI from main thread
            self.after(0, lambda: self._add_chat_message("system", "Voice transcription ready (powered by Gemini 2.5 Pro)"))
            self.after(0, self._setup_voice_transcription)
            self.after(0, self._setup_orchestrator_with_models)
            self.after(100, self._update_connection_status)
            
        except Exception as e:
            logger.error(f"AI models setup failed: {e}")
            self.after(0, lambda: self._add_chat_message("system", f"Error: AI models setup failed: {str(e)}"))
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _setup_voice_transcription(self) -> None:
        """Setup voice transcription functionality."""
        
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            logger.info("Audio system initialized")
            
        except Exception as e:
            logger.error(f"Audio system initialization failed: {e}")
            self._add_chat_message("system", "Warning: Audio system not available")
    
    def _initialize_orchestrator(self) -> None:
        """Initialize orchestrator and system tools in a thread."""
        
        try:
            # Initialize in thread since it doesn't need async
            threading.Thread(target=self._setup_orchestrator_sync, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self._add_chat_message("system", "Warning: AI orchestrator initialization failed")
    
    def _setup_orchestrator_sync(self) -> None:
        """Setup intelligent orchestrator using shared event loop."""
        
        try:
            # Wait for event loop to be ready
            max_wait = 10  # 10 seconds
            wait_count = 0
            while (not self.event_loop or self.event_loop.is_closed()) and wait_count < max_wait:
                time.sleep(1)
                wait_count += 1
            
            if not self.event_loop or self.event_loop.is_closed():
                raise RuntimeError("Shared event loop not available")
            
            # Initialize system tools first (sync operation)
            self.system_tools = SystemTools()
            logger.info("System tools initialized successfully")
            
            # Initialize intelligent orchestrator using shared event loop
            future = self._run_async_task(get_intelligent_orchestrator())
            if future:
                self.orchestrator = future.result(timeout=30)  # 30 second timeout
                logger.info("✅ Intelligent Multi-Agent orchestrator initialized successfully")
            
            # Set UI callback for real-time updates
            self.orchestrator.set_ui_callback(self._handle_orchestrator_update)
            
            # Update UI
            self.after(0, lambda: self._add_chat_message("system", "🧠 Intelligent Multi-Agent AI ready - advanced recursive execution enabled"))
            self.after(0, lambda: setattr(self, 'is_connected', True))  # Set connected status
            self.after(0, self._update_connection_status)
            
        except Exception as e:
            logger.error(f"Orchestrator setup failed: {e}")
            self.after(0, lambda: self._add_chat_message("system", f"Error: Orchestrator setup failed: {str(e)}"))
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _handle_orchestrator_update(self, update: Dict[str, Any]) -> None:
        """Handle real-time updates from intelligent orchestrator - sync version."""
        try:
            event_type = update.get("event_type", "unknown")
            task_id = update.get("task_id", "unknown")
            
            logger.info(f"🔔 UI callback received: {event_type} for task {task_id[:8]}...")
            
            if event_type == "task_started":
                user_intent = update.get("user_intent", "unknown task")
                self.after(0, lambda: self._add_chat_message("assistant", f"🚀 Starting: {user_intent}"))
                
            elif event_type == "status_update":
                data = update.get("data", {})
                status = data.get("status", "unknown")
                step = data.get("current_step", 0)
                confidence = data.get("confidence_score", 0.0)
                
                if status == "completed":
                    reason = data.get("completion_reason", "Task completed")
                    self.after(0, lambda: self._add_chat_message("assistant", f"✅ Completed: {reason}"))
                    self.after(0, lambda: setattr(self, 'execution_active', False))
                elif status == "failed":
                    reason = data.get("completion_reason", "Task failed")
                    self.after(0, lambda: self._add_chat_message("assistant", f"❌ Failed: {reason}"))
                    self.after(0, lambda: setattr(self, 'execution_active', False))
                else:
                    self.after(0, lambda: self._add_chat_message("system", f"📊 Step {step}: {status} (confidence: {confidence:.2f})"))
                    
            elif event_type == "task_cancelled":
                self.after(0, lambda: self._add_chat_message("system", f"⏹️ Task {task_id[:8]}... cancelled"))
                self.after(0, lambda: setattr(self, 'execution_active', False))
                
        except Exception as e:
            logger.error(f"Orchestrator update handler failed: {e}")
    
    def _setup_orchestrator_with_models(self) -> None:
        """Setup orchestrator after AI models are ready."""
        
        # This is called after AI models are initialized
        # The orchestrator may need the AI models, so we trigger setup here too
        if hasattr(self, 'ai_models') and self.ai_models and not self.orchestrator:
            self._initialize_orchestrator()
    
    def _toggle_voice(self) -> None:
        """Toggle voice input recording."""
        
        if not self.audio:
            self._add_chat_message("system", "Warning: Audio system not available")
            return
        
        if self.is_recording:
            self._stop_voice_recording()
        else:
            self._start_voice_recording()
    
    def _start_voice_recording(self) -> None:
        """Start voice recording."""
        
        if not self.ai_models:
            self._add_chat_message("system", "Warning: AI models not ready for transcription")
            return
        
        try:
            self.is_recording = True
            self.audio_buffer = []
            
            # Update UI
            self.voice_button.configure(
                text="Stop Recording",
                fg_color=self.theme.get_color("error"),
                hover_color=self.theme.get_color("error_hover")
            )
            self.voice_status.configure(
                text="Recording...",
                text_color=self.theme.get_color("error")
            )
            
            # Start recording in thread
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            logger.info("Voice recording started")
            
        except Exception as e:
            logger.error(f"Failed to start voice recording: {e}")
            self._add_chat_message("system", f"Error: Recording failed: {str(e)}")
            self.is_recording = False
    
    def _stop_voice_recording(self) -> None:
        """Stop voice recording and transcribe."""
        
        if not self.is_recording:
            return
        
        try:
            self.is_recording = False
            
            # Update UI
            self.voice_button.configure(
                text="🎤 Voice",
                fg_color=self.theme.get_color("primary"),
                hover_color=self.theme.get_color("primary_hover")
            )
            self.voice_status.configure(
                text="Processing...",
                text_color=self.theme.get_color("warning")
            )
            
            # Wait for recording thread
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2)
            
            # Process the recorded audio in a separate thread
            threading.Thread(target=self._transcribe_audio_sync, daemon=True).start()
            
            logger.info("Voice recording stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            self._add_chat_message("system", f"Error: Processing failed: {str(e)}")
    
    def _record_audio(self) -> None:
        """Record audio in background thread."""
        
        try:
            stream = self.audio.open(
                format=self.audio_config["format"],
                channels=self.audio_config["channels"],
                rate=self.audio_config["rate"],
                input=True,
                frames_per_buffer=self.audio_config["chunk"]
            )
            
            while self.is_recording:
                data = stream.read(self.audio_config["chunk"])
                self.audio_buffer.append(data)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logger.error(f"Audio recording error: {e}")
            self.is_recording = False
    
    def _transcribe_audio_sync(self) -> None:
        """Transcribe recorded audio using Gemini in a separate thread."""
        
        try:
            if not self.audio_buffer:
                self.after(0, lambda: self.voice_status.configure(text="No audio recorded", text_color=self.theme.get_color("error")))
                return
            
            # Use shared event loop instead of creating new one
            
            # Convert audio buffer to WAV format
            audio_data = b''.join(self.audio_buffer)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.audio_config["channels"])
                wav_file.setsampwidth(self.audio.get_sample_size(self.audio_config["format"]))
                wav_file.setframerate(self.audio_config["rate"])
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            audio_bytes = wav_buffer.getvalue()
            
            # Transcribe using Gemini via shared event loop
            future = self._run_async_task(self.ai_models.transcribe_audio(audio_bytes, "wav"))
            if future:
                transcript = future.result(timeout=15)  # 15 second timeout
            else:
                transcript = None
            
            if transcript and transcript.strip():
                # Clean up transcript
                clean_transcript = transcript.strip()
                
                # Update UI from main thread
                self.after(0, lambda: self._add_chat_message("user", f"Voice: {clean_transcript}"))
                self.after(0, lambda: self.voice_status.configure(text="Ready", text_color=self.theme.get_color("success")))
                self.after(0, lambda: self._send_command(clean_transcript))
                
            else:
                self.after(0, lambda: self.voice_status.configure(text="No speech detected", text_color=self.theme.get_color("error")))
                self.after(0, lambda: self._add_chat_message("system", "Warning: No speech detected in recording"))
            
        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            self.after(0, lambda: self.voice_status.configure(text="Transcription failed", text_color=self.theme.get_color("error")))
            self.after(0, lambda: self._add_chat_message("system", f"Error: Transcription failed: {str(e)}"))
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _on_text_submit(self, event) -> None:
        """Handle text input submit via Enter key."""
        self._send_text_message()
        return "break"
    
    def _send_text_message(self) -> None:
        """Send text message from input field."""
        
        message = self.text_input.get().strip()
        if not message:
            return
        
        # Clear input
        self.text_input.delete(0, "end")
        
        # Add to chat
        self._add_chat_message("user", message)
        
        # Send command
        self._send_command(message)
    
    def _send_command(self, command: str) -> None:
        """Send command directly to orchestrator for execution."""
        
        if not self.orchestrator:
            # Not ready yet
            self._add_chat_message("system", f" Received: {command}")
            self._add_chat_message("assistant", " AI orchestrator not ready yet, please wait...")
            return
        
        # Execute directly via orchestrator
        try:
            logger.info(f"Executing command via orchestrator: {command}")
            self._add_chat_message("system", f" Processing: {command}")
            
            # Update status
            self.execution_active = True
            self._update_connection_status()
            
            # Execute command directly in a separate thread
            threading.Thread(target=self._execute_command_sync, args=(command,), daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            self._add_chat_message("error", f"Error: Failed to execute command: {str(e)}")
            self.execution_active = False
            self._update_connection_status()
    
    def _execute_command_sync(self, command: str) -> None:
        """Execute command using shared event loop."""
        
        try:
            
            # Execute command via orchestrator using shared event loop
            future = self._run_async_task(self.orchestrator.execute_task(command))
            if future:
                task_id = future.result(timeout=10)  # 10 second timeout
            else:
                raise RuntimeError("Failed to schedule task on event loop")
            
            # Store current task ID for monitoring
            self.current_task_id = task_id
            
            # Update UI from main thread
            self.after(0, lambda: self._add_chat_message("assistant", f" Task started: {task_id[:8]}..."))
            self.after(0, lambda: self._add_chat_message("assistant", " Executing your request..."))
            
            # Start monitoring task status
            self.after(0, self._start_task_monitoring)
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            self.after(0, lambda: self._add_chat_message("error", f"Error: Execution failed: {str(e)}"))
            self.after(0, lambda: setattr(self, 'execution_active', False))
            self.after(0, self._update_connection_status)
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _start_task_monitoring(self) -> None:
        """Start monitoring the current task status."""
        if self.current_task_id and self.orchestrator:
            self._check_task_status()
    
    def _check_task_status(self) -> None:
        """Check current task status and update UI."""
        if not self.current_task_id or not self.orchestrator:
            return
            
        try:
            # Run async method in thread to avoid blocking Tkinter
            threading.Thread(target=self._check_task_status_async, daemon=True).start()
        except Exception as e:
            logger.error(f"Error starting task status check: {e}")
            # Continue monitoring despite error
            self.after(5000, self._check_task_status)
    
    def _check_task_status_async(self) -> None:
        """Check task status using shared event loop."""
        try:
            # Get status from orchestrator using shared event loop
            future = self._run_async_task(self.orchestrator.get_task_status(self.current_task_id))
            if future:
                status = future.result(timeout=5)  # 5 second timeout
            else:
                status = None
            
            # Schedule UI updates on main thread
            if status:
                task_status = status.get("status", "unknown")
                current_step = status.get("current_step", 0)
                total_steps = status.get("total_steps", 0)
                errors = status.get("error_messages", [])
                
                logger.info(f"Task {self.current_task_id[:8]}... status: {task_status}, step: {current_step}/{total_steps}")
                
                if task_status == "completed":
                    self.after(0, lambda: self._add_chat_message("assistant", "✅ Task completed successfully!"))
                    self.after(0, lambda: setattr(self, 'current_task_id', None))
                    self.after(0, lambda: setattr(self, 'execution_active', False))
                    self.after(0, self._update_connection_status)
                elif task_status == "failed":
                    error_msg = errors[-1] if errors else "Unknown error"
                    self.after(0, lambda: self._add_chat_message("error", f"❌ Task failed: {error_msg}"))
                    self.after(0, lambda: setattr(self, 'current_task_id', None))
                    self.after(0, lambda: setattr(self, 'execution_active', False))
                    self.after(0, self._update_connection_status)
                elif task_status == "in_progress":
                    self.after(0, lambda: self._add_chat_message("system", f"📊 Step {current_step}: {task_status}"))
                    # Continue monitoring from main thread
                    self.after(3000, self._check_task_status)  # Check again in 3 seconds
            else:
                # Task not found, might be completed
                self.after(0, lambda: self._add_chat_message("assistant", "🏁 Task execution finished"))
                self.after(0, lambda: setattr(self, 'current_task_id', None))
                self.after(0, lambda: setattr(self, 'execution_active', False))
                self.after(0, self._update_connection_status)
                
        except Exception as e:
            logger.error(f"Error checking task status: {e}")
            # Continue monitoring despite error from main thread
            self.after(0, lambda: self.after(5000, self._check_task_status))
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _update_connection_status(self) -> None:
        """Update connection status display."""
        
        if self.is_listening:
            return  # Don't update while listening
        
        if self.is_connected:
            if self.execution_active:
                self.status_label.configure(
                    text=" Executing...",
                    text_color=self.theme.get_color("warning")
                )
            else:
                self.status_label.configure(
                    text=" Ready (AI enabled)",
                    text_color=self.theme.get_color("success")
                )
        elif hasattr(self, 'ai_models') and self.ai_models:
            self.status_label.configure(
                text=" Voice only",
                text_color=self.theme.get_color("warning")
            )
        else:
            self.status_label.configure(
                text=" Starting up...",
                text_color=self.theme.get_color("warning")
            )
    
    
    def _on_closing(self) -> None:
        """Handle application closing."""
        
        logger.info("Closing Simple AI Desktop App...")
        
        # Stop recording if active
        if self.is_recording:
            self.is_recording = False
        
        # Cleanup audio
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        
        # Cleanup shared event loop
        if self.event_loop and not self.event_loop.is_closed():
            try:
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            except:
                pass
        
        # Cleanup executor
        if self.async_executor:
            try:
                self.async_executor.shutdown(wait=False)
            except:
                pass
        
        # Close application
        self.destroy()


def main():
    """Main entry point for the simplified desktop application."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        app = SimpleAIDesktopApp()
        logger.info("Starting Simple AI OS Control Desktop Application")
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()