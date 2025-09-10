"""
Interactive Terminal Tool - Real-time command execution with history tracking
Like Claude Code and Gemini CLI - provides live command output and iteration capability.
"""

import asyncio
import logging
import json
import time
import os
import subprocess
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from ...config.settings import get_settings
from ...utils.platform_detector import get_system_environment

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a terminal command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    timestamp: str
    working_directory: str
    success: bool
    session_id: str


@dataclass
class TerminalSession:
    """Represents a persistent terminal session."""
    session_id: str
    start_time: str
    working_directory: str
    environment: Dict[str, str]
    command_history: List[CommandResult]
    active: bool = True


class InteractiveTerminal:
    """
    Interactive Terminal Tool - Provides real-time command execution with:
    - Live output streaming
    - Command history tracking
    - Session persistence
    - Cross-platform compatibility
    - Safety controls
    """
    
    def __init__(self, callback: Optional[Callable] = None):
        self.system_env = get_system_environment()
        self.settings = get_settings()
        self.callback = callback  # For real-time output streaming
        
        # Session management
        self.sessions: Dict[str, TerminalSession] = {}
        self.active_session_id: Optional[str] = None
        
        # Safety controls
        self.dangerous_commands = {
            'rm -rf /',
            'del /f /s /q C:\\',
            'format c:',
            'dd if=/dev/zero of=/dev/sda',
            'sudo rm -rf /*',
            ':(){ :|:& };:',  # Fork bomb
        }
        
        # History file
        self.history_file = self.settings.get_data_paths()["logs"] / "terminal_history.json"
        self.history_file.parent.mkdir(exist_ok=True)
        
        # Load existing sessions
        self._load_history()
    
    async def create_session(self, working_directory: Optional[str] = None) -> str:
        """Create a new terminal session."""
        
        session_id = f"term_{int(time.time())}_{len(self.sessions)}"
        
        # Set working directory
        if working_directory is None:
            working_directory = os.getcwd()
        elif not os.path.exists(working_directory):
            logger.warning(f"Directory {working_directory} doesn't exist, using current directory")
            working_directory = os.getcwd()
        
        # Create session
        session = TerminalSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            working_directory=working_directory,
            environment=dict(os.environ),
            command_history=[]
        )
        
        self.sessions[session_id] = session
        self.active_session_id = session_id
        
        logger.info(f"Created terminal session {session_id} in {working_directory}")
        return session_id
    
    async def execute_command(
        self, 
        command: str, 
        session_id: Optional[str] = None,
        stream_output: bool = True,
        timeout: Optional[int] = None
    ) -> CommandResult:
        """
        Execute a command in the specified session with real-time output.
        
        Args:
            command: Command to execute
            session_id: Session ID (uses active session if None)
            stream_output: Whether to stream output in real-time
            timeout: Command timeout in seconds
        """
        
        # Get or create session
        if session_id is None:
            if self.active_session_id is None:
                session_id = await self.create_session()
            else:
                session_id = self.active_session_id
        
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # Safety check
        if self._is_dangerous_command(command):
            logger.error(f"Dangerous command blocked: {command}")
            return CommandResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr="Command blocked for safety",
                execution_time=0.0,
                timestamp=datetime.now().isoformat(),
                working_directory=session.working_directory,
                success=False,
                session_id=session_id
            )
        
        logger.info(f"Executing command in session {session_id}: {command}")
        
        start_time = time.time()
        stdout_lines = []
        stderr_lines = []
        
        try:
            # Prepare command for execution
            if self.system_env.os == "Windows":
                exec_command = ["cmd", "/c", command]
            else:
                exec_command = ["bash", "-c", command]
            
            # Execute with real-time output capture
            process = subprocess.Popen(
                exec_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=session.working_directory,
                env=session.environment,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Real-time output streaming
            if stream_output and self.callback:
                await self._stream_process_output(process, stdout_lines, stderr_lines)
            
            # Wait for completion
            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.to_thread(process.communicate),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                stdout, stderr = await asyncio.to_thread(process.communicate)
                stderr += f"\nCommand timed out after {timeout} seconds"
            
            execution_time = time.time() - start_time
            exit_code = process.returncode
            
            # Combine streamed output with final output
            final_stdout = '\n'.join(stdout_lines) + (stdout if stdout else "")
            final_stderr = '\n'.join(stderr_lines) + (stderr if stderr else "")
            
            # Create result
            result = CommandResult(
                command=command,
                exit_code=exit_code,
                stdout=final_stdout,
                stderr=final_stderr,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                working_directory=session.working_directory,
                success=(exit_code == 0),
                session_id=session_id
            )
            
            # Update session
            session.command_history.append(result)
            
            # Update working directory if command was 'cd'
            if command.strip().startswith('cd '):
                new_dir = self._resolve_cd_command(command, session.working_directory)
                if new_dir and os.path.exists(new_dir):
                    session.working_directory = new_dir
            
            # Save history
            self._save_history()
            
            logger.info(f"Command completed: {command} (exit_code: {exit_code}, time: {execution_time:.2f}s)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Command execution failed: {e}")
            
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                working_directory=session.working_directory,
                success=False,
                session_id=session_id
            )
            
            session.command_history.append(result)
            self._save_history()
            return result
    
    async def _stream_process_output(
        self, 
        process: subprocess.Popen, 
        stdout_lines: List[str], 
        stderr_lines: List[str]
    ):
        """Stream process output in real-time."""
        
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                if line:
                    stdout_lines.append(line.rstrip())
                    if self.callback:
                        asyncio.create_task(self.callback("stdout", line.rstrip()))
        
        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                if line:
                    stderr_lines.append(line.rstrip())
                    if self.callback:
                        asyncio.create_task(self.callback("stderr", line.rstrip()))
        
        # Start threads for real-time streaming
        stdout_thread = threading.Thread(target=read_stdout)
        stderr_thread = threading.Thread(target=read_stderr)
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for threads to complete
        stdout_thread.join()
        stderr_thread.join()
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command is potentially dangerous."""
        command_lower = command.lower().strip()
        
        # Check against known dangerous commands
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return True
        
        # Additional safety checks
        dangerous_patterns = [
            'rm -rf /',
            'sudo rm -rf',
            'del /f /s /q',
            'format ',
            'dd if=',
            'mkfs.',
            '> /dev/sda',
            'wget http' if 'rm -rf' in command_lower else None
        ]
        
        return any(pattern and pattern in command_lower for pattern in dangerous_patterns)
    
    def _resolve_cd_command(self, command: str, current_dir: str) -> Optional[str]:
        """Resolve cd command to absolute path."""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return os.path.expanduser("~")  # cd with no args goes to home
            
            target = " ".join(parts[1:])  # Handle paths with spaces
            
            if os.path.isabs(target):
                return target
            else:
                return os.path.abspath(os.path.join(current_dir, target))
        except Exception:
            return None
    
    def get_session_history(self, session_id: str, limit: Optional[int] = None) -> List[CommandResult]:
        """Get command history for a session."""
        if session_id not in self.sessions:
            return []
        
        history = self.sessions[session_id].command_history
        if limit:
            return history[-limit:]
        return history
    
    def get_active_session(self) -> Optional[TerminalSession]:
        """Get the currently active session."""
        if self.active_session_id and self.active_session_id in self.sessions:
            return self.sessions[self.active_session_id]
        return None
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session."""
        if session_id in self.sessions:
            self.active_session_id = session_id
            logger.info(f"Switched to session {session_id}")
            return True
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions."""
        return [
            {
                "session_id": session.session_id,
                "start_time": session.start_time,
                "working_directory": session.working_directory,
                "command_count": len(session.command_history),
                "active": (session_id == self.active_session_id)
            }
            for session_id, session in self.sessions.items()
        ]
    
    def _save_history(self):
        """Save command history to file."""
        try:
            history_data = {
                session_id: asdict(session) 
                for session_id, session in self.sessions.items()
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save terminal history: {e}")
    
    def _load_history(self):
        """Load command history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                
                for session_id, session_data in history_data.items():
                    # Convert command history back to CommandResult objects
                    command_history = [
                        CommandResult(**cmd_data) 
                        for cmd_data in session_data.get('command_history', [])
                    ]
                    
                    session = TerminalSession(
                        session_id=session_data['session_id'],
                        start_time=session_data['start_time'],
                        working_directory=session_data['working_directory'],
                        environment=session_data.get('environment', {}),
                        command_history=command_history,
                        active=False  # All loaded sessions start as inactive
                    )
                    
                    self.sessions[session_id] = session
                
                logger.info(f"Loaded {len(self.sessions)} terminal sessions from history")
                
        except Exception as e:
            logger.error(f"Failed to load terminal history: {e}")
    
    def get_command_stats(self) -> Dict[str, Any]:
        """Get statistics about command usage."""
        total_commands = sum(len(session.command_history) for session in self.sessions.values())
        successful_commands = sum(
            sum(1 for cmd in session.command_history if cmd.success)
            for session in self.sessions.values()
        )
        
        return {
            "total_sessions": len(self.sessions),
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "success_rate": successful_commands / max(total_commands, 1),
            "active_session": self.active_session_id
        }