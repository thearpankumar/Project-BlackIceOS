#!/usr/bin/env python3
"""
Samsung AI-OS - Simplified GUI Interface
Clean implementation with proper desktop automation separation
"""

import logging
import os
import queue
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import google.generativeai as genai
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from scipy.io.wavfile import write

from src.auth.auth_client import AuthClient
from src.desktop.automation.desktop_controller import DesktopController
from src.desktop.viewer.viewer_manager import ViewerManager


class SamsungAIOSGUI:
    def __init__(self: "SamsungAIOSGUI", root: tk.Tk) -> None:
        self.root = root
        self.root.title("Samsung AI-OS - Voice-Controlled Cybersecurity Platform")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')

        # Create a temporary log file
        self._log_file = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
        self.log_file_path = self._log_file.name
        self._log_file.close()

        # Configure logging for the instance
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.log_file_path),
            ],
        )

        # State
        self.is_recording = False
        self.components_initialized = False

        # Queue for thread-safe GUI updates
        self.message_queue = queue.Queue()

        # Initialize components
        self.desktop_controller = None
        self.auth_client = None
        self.viewer_manager = None

        # Viewer state
        self.current_viewer_panel = None
        self.viewer_operation_in_progress = False

        # Voice setup
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.llm_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        else:
            self.llm_model = None

        # Audio config
        self.sample_rate = 16000
        self.recording_data = []

        # Setup
        self.logger = logging.getLogger(__name__)
        self.create_gui()
        self.start_initialization()
        self.process_message_queue()

    def create_gui(self: "SamsungAIOSGUI") -> None:
        """Create simplified GUI interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#1a1a1a')
        header_frame.pack(fill='x', padx=20, pady=10)

        title_label = tk.Label(
            header_frame,
            text="Samsung AI-OS",
            font=('Arial', 24, 'bold'),
            fg='#1e7ce8',
            bg='#1a1a1a',
        )
        title_label.pack(side='left')

        # Status
        self.status_frame = tk.Frame(header_frame, bg='#1a1a1a')
        self.status_frame.pack(side='right')

        tk.Label(
            self.status_frame,
            text="System:",
            font=('Arial', 12),
            fg='white',
            bg='#1a1a1a',
        ).pack(side='left', padx=(0, 5))

        self.status_label = tk.Label(
            self.status_frame,
            text="Initializing...",
            font=('Arial', 12, 'bold'),
            fg='orange',
            bg='#1a1a1a',
        )
        self.status_label.pack(side='left')

        # Main content
        main_frame = tk.Frame(self.root, bg='#2d2d2d')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Control buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d2d')
        button_frame.pack(fill='x', pady=(0, 20))

        # Voice button
        self.voice_button = tk.Button(
            button_frame,
            text="🎤 Voice Command",
            font=('Arial', 14, 'bold'),
            bg='#1e7ce8',
            fg='white',
            command=self.toggle_voice_recording,
            height=2,
            width=20,
            relief='raised',
            bd=3,
            state='disabled',
        )
        self.voice_button.pack(side='left', padx=(0, 20))

        # Test button
        self.test_button = tk.Button(
            button_frame,
            text="🧪 Test System",
            font=('Arial', 14, 'bold'),
            bg='#28a745',
            fg='white',
            command=self.run_system_test,
            height=2,
            width=20,
            relief='raised',
            bd=3,
            state='disabled',
        )
        self.test_button.pack(side='left', padx=(0, 20))

        # Screenshot button
        self.screenshot_button = tk.Button(
            button_frame,
            text="📸 AI Screenshot",
            font=('Arial', 14, 'bold'),
            bg='#6f42c1',
            fg='white',
            command=self.take_ai_screenshot,
            height=2,
            width=20,
            relief='raised',
            bd=3,
            state='disabled',
        )
        self.screenshot_button.pack(side='left', padx=(0, 20))

        # Viewer control buttons
        self.vnc_button = tk.Button(
            button_frame,
            text="📺 VNC View",
            font=('Arial', 14, 'bold'),
            bg='#17a2b8',
            fg='white',
            command=self.start_vnc_viewer,
            height=2,
            width=20,
            relief='raised',
            bd=3,
            state='disabled',
        )
        self.vnc_button.pack(side='left', padx=(0, 20))

        self.stop_viewer_button = tk.Button(
            button_frame,
            text="❌ Stop View",
            font=('Arial', 14, 'bold'),
            bg='#dc3545',
            fg='white',
            command=self.stop_viewer,
            height=2,
            width=20,
            relief='raised',
            bd=3,
            state='disabled',
        )
        self.stop_viewer_button.pack(side='left', padx=(0, 20))

        # Content area - split for viewer
        content_frame = tk.Frame(main_frame, bg='#2d2d2d')
        content_frame.pack(fill='both', expand=True)

        # Create paned window for resizable layout
        self.paned_window = ttk.PanedWindow(content_frame, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True, padx=5, pady=5)

        # Left panel - logs and status
        left_panel = tk.Frame(self.paned_window, bg='#2d2d2d')
        self.paned_window.add(left_panel, weight=1)

        # Right panel - AI display viewer (initially hidden)
        self.viewer_panel = tk.Frame(self.paned_window, bg='#1a1a1a', width=400)
        # Don't add to paned window initially - will add when viewer starts

        # Status log (in left panel now)
        log_frame = tk.Frame(left_panel, bg='#1a1a1a', relief='sunken', bd=2)
        log_frame.pack(fill='both', expand=True)

        tk.Label(
            log_frame,
            text="System Status & Logs",
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#1a1a1a',
        ).pack(anchor='w', padx=10, pady=(10, 5))

        self.status_text = tk.Text(
            log_frame,
            font=('Consolas', 10),
            bg='#1a1a1a',
            fg='#00ff00',
            height=20,
            wrap='word',
            state='disabled',
        )
        self.status_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Status bar
        status_bar = tk.Frame(self.root, bg='#333333', height=30)
        status_bar.pack(fill='x', side='bottom')

        self.status_bar_label = tk.Label(
            status_bar,
            text="Ready - Clean architecture implementation",
            font=('Arial', 10),
            fg='white',
            bg='#333333',
        )
        self.status_bar_label.pack(side='left', padx=10, pady=5)

    def log_message(self: "SamsungAIOSGUI", message: str, level: str = 'INFO') -> None:
        """Log message to GUI and console"""
        if level == 'ERROR':
            self.logger.error(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'SUCCESS':
            self.logger.info(f"✓ {message}")
        else:
            self.logger.info(message)

        self.message_queue.put(('log', level, message))

    def update_status(self: "SamsungAIOSGUI", status: str, color: str = 'white') -> None:
        """Update system status"""
        self.message_queue.put(('status', status, color))

    def process_message_queue(self: "SamsungAIOSGUI") -> None:
        """Process messages from background threads"""
        try:
            while True:
                msg_type, *args = self.message_queue.get_nowait()

                if msg_type == 'log':
                    level, message = args
                    timestamp = time.strftime("%H:%M:%S")

                    self.status_text.config(state='normal')

                    if level == 'ERROR':
                        self.status_text.insert('end', f"[{timestamp}] ❌ {message}\n", 'error')
                    elif level == 'WARNING':
                        self.status_text.insert('end', f"[{timestamp}] ⚠️ {message}\n", 'warning')
                    elif level == 'SUCCESS':
                        self.status_text.insert('end', f"[{timestamp}] ✅ {message}\n", 'success')
                    else:
                        self.status_text.insert('end', f"[{timestamp}] ℹ️ {message}\n", 'info')

                    # Configure colors
                    self.status_text.tag_config('error', foreground='#ff4444')
                    self.status_text.tag_config('warning', foreground='#ffaa00')
                    self.status_text.tag_config('success', foreground='#00ffaa')
                    self.status_text.tag_config('info', foreground='#00ff00')

                    self.status_text.config(state='disabled')
                    self.status_text.see('end')

                elif msg_type == 'status':
                    status, color = args
                    self.status_label.config(text=status, fg=color)
                    self.status_bar_label.config(text=f"{status} - Logs displayed above")

                elif msg_type == 'enable_buttons':
                    self.voice_button.config(state='normal')
                    self.test_button.config(state='normal')
                    self.screenshot_button.config(state='normal')
                    self.vnc_button.config(state='normal')
                    self.stop_viewer_button.config(state='normal')

                elif msg_type == 'reset_voice_button':
                    self.is_recording = False
                    self.voice_button.config(text="🎤 Voice Command", bg='#1e7ce8')

                elif msg_type == 'show_viewer_panel':
                    self._show_viewer_panel()

                elif msg_type == 'hide_viewer_panel':
                    self._hide_viewer_panel()

        except queue.Empty:
            pass

        self.root.after(100, self.process_message_queue)

    def start_initialization(self: "SamsungAIOSGUI") -> None:
        """Initialize system components in background"""

        def initialize() -> None:
            try:
                self.log_message("Starting Samsung AI-OS initialization...")

                # Initialize desktop controller
                self.update_status("Initializing desktop automation...", 'orange')
                self.desktop_controller = DesktopController()

                # Initialize viewer manager
                self.update_status("Initializing display viewers...", 'orange')
                self.viewer_manager = ViewerManager()

                if self.desktop_controller.is_initialized:
                    self.log_message("Desktop controller initialized successfully", 'SUCCESS')
                    self.log_message("Display viewers ready", 'SUCCESS')
                else:
                    self.log_message("Desktop controller initialization failed", 'WARNING')

                # Initialize auth client
                self.update_status("Connecting to auth server...", 'orange')
                try:
                    self.auth_client = AuthClient()
                    self.log_message("Authentication client connected", 'SUCCESS')
                except Exception as e:
                    self.log_message(f"Auth client failed: {e}", 'WARNING')

                # Check voice setup
                if self.llm_model:
                    self.log_message("Voice processing ready (Gemini)", 'SUCCESS')
                else:
                    self.log_message("No API key - voice features disabled", 'WARNING')

                # Log system status
                if self.desktop_controller:
                    status = self.desktop_controller.get_status()
                    self.log_message(f"Display status: {status['display_status']}")

                self.components_initialized = True
                self.update_status("Ready", 'green')
                self.log_message("Samsung AI-OS initialization complete!", 'SUCCESS')

                # Enable controls
                self.message_queue.put(('enable_buttons',))

            except Exception as e:
                self.log_message(f"Initialization failed: {e}", 'ERROR')
                self.update_status("Failed", 'red')

        init_thread = threading.Thread(target=initialize, daemon=True)
        init_thread.start()

    def toggle_voice_recording(self: "SamsungAIOSGUI") -> None:
        """Handle voice recording"""
        if not self.components_initialized:
            messagebox.showwarning("Not Ready", "System is still initializing.")
            return

        if not self.llm_model:
            messagebox.showwarning("API Key Missing", "No Google AI API key found.")
            return

        if not self.is_recording:
            # Start recording
            self.is_recording = True
            self.voice_button.config(text="🛑 Stop Recording", bg='#dc3545')
            self.log_message("Voice recording started - speak your command")
            self.recording_data = []

            def record_audio() -> None:
                try:

                    def audio_callback(
                        indata: np.ndarray,
                        frames: int,
                        time: sd.CallbackFlags,
                        status: sd.CallbackFlags,
                    ) -> None:
                        if self.is_recording:
                            self.recording_data.append(indata.copy())

                    with sd.InputStream(
                        samplerate=self.sample_rate,
                        channels=1,
                        callback=audio_callback,
                        dtype=np.float32,
                    ):
                        while self.is_recording:
                            time.sleep(0.1)

                except Exception as e:
                    self.log_message(f"Recording error: {e}", 'ERROR')
                    self.message_queue.put(('reset_voice_button',))

            threading.Thread(target=record_audio, daemon=True).start()

        else:
            # Stop and process
            self.is_recording = False
            self.log_message("Processing recorded audio...")

            def process_audio() -> None:
                try:
                    if self.recording_data:
                        # Save audio
                        audio_data = np.concatenate(self.recording_data, axis=0)
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".wav"
                        ) as tmp_audio_file:
                            audio_file = tmp_audio_file.name
                        audio_int16 = (audio_data * 32767).astype(np.int16)
                        write(audio_file, self.sample_rate, audio_int16)

                        # Transcribe
                        with open(audio_file, 'rb') as f:
                            audio_content = f.read()

                        response = self.llm_model.generate_content(
                            [
                                "Transcribe this audio to English text only. "
                                "Return just the transcribed text.",
                                {"mime_type": "audio/wav", "data": audio_content},
                            ]
                        )

                        transcribed_text = response.text.strip()
                        self.log_message(f"Transcribed: '{transcribed_text}'", 'SUCCESS')

                        # Execute command
                        self.execute_voice_command(transcribed_text)

                        # Cleanup
                        os.remove(audio_file)
                    else:
                        self.log_message("No audio recorded", 'WARNING')

                except Exception as e:
                    self.log_message(f"Audio processing error: {e}", 'ERROR')

                finally:
                    self.message_queue.put(('reset_voice_button',))

            threading.Thread(target=process_audio, daemon=True).start()

    def execute_voice_command(self: "SamsungAIOSGUI", command_text: str) -> None:
        """Execute voice commands using desktop controller"""
        try:
            command_text = command_text.lower().strip()
            self.log_message(f"Executing command: '{command_text}'")

            if not self.desktop_controller:
                self.log_message("No desktop controller available", 'ERROR')
                return

            # Command mappings
            if any(word in command_text for word in ['terminal', 'command line']):
                result = self.desktop_controller.open_application('terminal')
            elif any(word in command_text for word in ['browser', 'firefox']):
                result = self.desktop_controller.open_application('browser')
            elif any(word in command_text for word in ['calculator', 'calc']):
                result = self.desktop_controller.open_application('calculator')
            elif any(word in command_text for word in ['file', 'files']):
                result = self.desktop_controller.open_application('files')
            elif any(word in command_text for word in ['screenshot', 'capture']):
                self.take_ai_screenshot()
                return
            else:
                self.log_message(f"Command not recognized: {command_text}", 'WARNING')
                return

            if result['success']:
                self.log_message(f"Successfully executed: {command_text}", 'SUCCESS')
            else:
                self.log_message(f"Command failed: {result.get('error', 'Unknown error')}", 'ERROR')

        except Exception as e:
            self.log_message(f"Voice command execution error: {e}", 'ERROR')

    def run_system_test(self: "SamsungAIOSGUI") -> None:
        """Run comprehensive system test"""
        if not self.components_initialized:
            messagebox.showwarning("Not Ready", "System is still initializing.")
            return

        self.log_message("Starting system test...")

        def test_system() -> None:
            try:
                test_results = {}

                # Test desktop controller
                if self.desktop_controller:
                    test_results['desktop'] = self.desktop_controller.test_system()

                    if test_results['desktop']['overall_status'] == 'passed':
                        self.log_message("✓ Desktop automation tests passed", 'SUCCESS')
                    else:
                        self.log_message("✗ Desktop automation tests failed", 'ERROR')
                        self.log_message(f"Details: {test_results['desktop']}")
                else:
                    self.log_message("✗ No desktop controller", 'ERROR')

                # Test auth client
                if self.auth_client:
                    self.log_message("✓ Auth client available", 'SUCCESS')
                else:
                    self.log_message("✗ No auth client", 'WARNING')

                # Test voice
                if self.llm_model:
                    self.log_message("✓ Voice processing available", 'SUCCESS')
                else:
                    self.log_message("✗ Voice processing unavailable", 'WARNING')

                self.log_message("System test completed", 'SUCCESS')

            except Exception as e:
                self.log_message(f"System test error: {e}", 'ERROR')

        threading.Thread(target=test_system, daemon=True).start()

    def take_ai_screenshot(self: "SamsungAIOSGUI") -> None:
        """Take screenshot from AI display"""
        if not self.desktop_controller:
            self.log_message("No desktop controller available", 'ERROR')
            return

        def capture() -> None:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png"
                ) as tmp_screenshot_file:
                    filename = tmp_screenshot_file.name

                result = self.desktop_controller.capture_screenshot(filename)

                if result:
                    self.log_message(f"Screenshot saved: {filename}", 'SUCCESS')
                else:
                    self.log_message("Screenshot capture failed", 'ERROR')

            except Exception as e:
                self.log_message(f"Screenshot error: {e}", 'ERROR')

        threading.Thread(target=capture, daemon=True).start()

    def start_vnc_viewer(self: "SamsungAIOSGUI") -> None:
        """Start VNC viewer for AI display"""
        if not self.components_initialized:
            messagebox.showwarning("Not Ready", "System is still initializing.")
            return

        if self.viewer_operation_in_progress:
            self.log_message("Viewer operation already in progress", 'WARNING')
            return

        if not self.desktop_controller or not self.desktop_controller.is_initialized:
            messagebox.showerror("Error", "Desktop controller not available.")
            return

        def start_vnc() -> None:
            try:
                self.viewer_operation_in_progress = True
                self.log_message("Starting VNC viewer...")

                ai_display = self.desktop_controller.get_ai_display()
                if not ai_display:
                    self.log_message("No AI display available", 'ERROR')
                    return

                if self.viewer_manager.start_viewing(ai_display, "vnc"):
                    self.log_message("VNC viewer started successfully", 'SUCCESS')
                    self.message_queue.put(('show_viewer_panel',))
                else:
                    self.log_message("Failed to start VNC viewer", 'ERROR')

            except Exception as e:
                self.log_message(f"VNC viewer error: {e}", 'ERROR')
            finally:
                self.viewer_operation_in_progress = False

        threading.Thread(target=start_vnc, daemon=True).start()

    def stop_viewer(self: "SamsungAIOSGUI") -> None:
        """Stop current viewer"""
        if not self.viewer_manager:
            return

        if self.viewer_operation_in_progress:
            self.log_message("Viewer operation already in progress", 'WARNING')
            return

        def stop() -> None:
            try:
                self.viewer_operation_in_progress = True
                if self.viewer_manager.is_viewing():
                    viewer_type = self.viewer_manager.get_current_viewer_type()
                    self.log_message(f"Stopping {viewer_type} viewer...")

                    if self.viewer_manager.stop_viewing():
                        self.log_message("Viewer stopped successfully", 'SUCCESS')
                        self.message_queue.put(('hide_viewer_panel',))
                    else:
                        self.log_message("Failed to stop viewer", 'ERROR')
                else:
                    self.log_message("No viewer currently active", 'WARNING')

            except Exception as e:
                self.log_message(f"Stop viewer error: {e}", 'ERROR')
            finally:
                self.viewer_operation_in_progress = False

        threading.Thread(target=stop, daemon=True).start()

    def _show_viewer_panel(self: "SamsungAIOSGUI") -> None:
        """Show the viewer panel"""
        try:
            # Clear existing content in viewer panel
            for widget in self.viewer_panel.winfo_children():
                widget.destroy()

            # Create new viewer widget
            self.current_viewer_panel = self.viewer_manager.get_current_viewer_widget(
                self.viewer_panel
            )
            if self.current_viewer_panel:
                self.current_viewer_panel.pack(fill='both', expand=True)

            # Add viewer panel to paned window if not already added
            try:
                if self.viewer_panel not in self.paned_window.panes():
                    self.paned_window.add(self.viewer_panel, weight=1)
            except tk.TclError as e:
                if "already added" in str(e):
                    # Panel already added, just ensure it's visible
                    pass
                else:
                    raise e

        except Exception as e:
            self.log_message(f"Error showing viewer panel: {e}", 'ERROR')

    def _hide_viewer_panel(self: "SamsungAIOSGUI") -> None:
        """Hide the viewer panel"""
        try:
            if self.viewer_panel in self.paned_window.panes():
                self.paned_window.remove(self.viewer_panel)

            if self.current_viewer_panel:
                self.current_viewer_panel.destroy()
                self.current_viewer_panel = None

        except Exception as e:
            self.log_message(f"Error hiding viewer panel: {e}", 'ERROR')

    def on_closing(self: "SamsungAIOSGUI") -> None:
        """Handle window closing"""
        self.log_message("Shutting down Samsung AI-OS...")

        try:
            if self.viewer_manager:
                self.viewer_manager.cleanup()

            if self.desktop_controller:
                self.desktop_controller.cleanup()

            if self.auth_client:
                self.auth_client.cleanup()

            # Clean up the temporary log file
            if os.path.exists(self.log_file_path):
                os.remove(self.log_file_path)

            self.log_message("Shutdown complete")

        except Exception as e:
            self.log_message(f"Cleanup error: {e}", 'ERROR')

        self.root.destroy()


def main() -> None:
    """Main entry point"""
    root = tk.Tk()
    app = SamsungAIOSGUI(root)

    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
