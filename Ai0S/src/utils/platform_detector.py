"""
Platform detection and OS environment identification module.
Provides dynamic OS detection and environment analysis for cross-platform compatibility.
"""

import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Optional, List
import psutil


@dataclass
class SystemEnvironment:
    """Complete system environment information."""
    os: str
    os_version: str
    architecture: str
    display_server: Optional[str]
    desktop_environment: Optional[str]
    window_manager: Optional[str]
    python_version: str
    has_audio: bool
    has_microphone: bool
    screen_resolution: tuple
    cpu_count: int
    memory_gb: float
    capabilities: List[str]


class PlatformDetector:
    """Advanced platform detection with OS-specific capability analysis."""
    
    def __init__(self):
        self.system_info = None
        self._detect_environment()
    
    def _detect_environment(self) -> None:
        """Detect complete system environment."""
        os_name = platform.system()
        
        self.system_info = SystemEnvironment(
            os=os_name,
            os_version=platform.version(),
            architecture=platform.machine(),
            display_server=self._detect_display_server(),
            desktop_environment=self._detect_desktop_environment(),
            window_manager=self._detect_window_manager(),
            python_version=sys.version,
            has_audio=self._detect_audio_support(),
            has_microphone=self._detect_microphone_support(),
            screen_resolution=self._get_screen_resolution(),
            cpu_count=psutil.cpu_count(),
            memory_gb=round(psutil.virtual_memory().total / (1024**3), 2),
            capabilities=self._detect_capabilities()
        )
    
    def _detect_display_server(self) -> Optional[str]:
        """Detect the display server (X11, Wayland, or Windows/macOS native)."""
        if self.system_info and self.system_info.os == "Windows":
            return "win32"
        elif self.system_info and self.system_info.os == "Darwin":
            return "quartz"
        
        # Linux display server detection
        if os.environ.get('WAYLAND_DISPLAY'):
            return "wayland"
        elif os.environ.get('DISPLAY'):
            return "x11"
        elif os.environ.get('XDG_SESSION_TYPE') == 'wayland':
            return "wayland"
        elif os.environ.get('XDG_SESSION_TYPE') == 'x11':
            return "x11"
        
        return None
    
    def _detect_desktop_environment(self) -> Optional[str]:
        """Detect the desktop environment."""
        # Check common environment variables
        desktop_vars = [
            'XDG_CURRENT_DESKTOP',
            'XDG_SESSION_DESKTOP', 
            'DESKTOP_SESSION',
            'GDMSESSION'
        ]
        
        for var in desktop_vars:
            if var in os.environ:
                return os.environ[var].lower()
        
        # Platform-specific detection
        if platform.system() == "Windows":
            return "windows_desktop"
        elif platform.system() == "Darwin":
            return "macos_desktop"
        
        return None
    
    def _detect_window_manager(self) -> Optional[str]:
        """Detect the window manager."""
        try:
            if platform.system() == "Linux":
                # Try to detect window manager
                wm_check_commands = [
                    "wmctrl -m",
                    "xprop -root _NET_WM_NAME",
                    "ps aux | grep -i gnome-shell",
                    "ps aux | grep -i kwin",
                    "ps aux | grep -i openbox"
                ]
                
                for cmd in wm_check_commands:
                    try:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        if result.returncode == 0 and result.stdout:
                            # Parse window manager from output
                            output = result.stdout.lower()
                            if "gnome" in output:
                                return "gnome"
                            elif "kwin" in output:
                                return "kwin"
                            elif "openbox" in output:
                                return "openbox"
                    except:
                        continue
        except:
            pass
        
        return None
    
    def _detect_audio_support(self) -> bool:
        """Detect if audio output is available."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            return len([d for d in devices if d['max_outputs'] > 0]) > 0
        except:
            return False
    
    def _detect_microphone_support(self) -> bool:
        """Detect if microphone input is available."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            return len([d for d in devices if d['max_inputs'] > 0]) > 0
        except:
            return False
    
    def _get_screen_resolution(self) -> tuple:
        """Get primary screen resolution."""
        try:
            if platform.system() == "Windows":
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()
                return (width, height)
            
            elif platform.system() == "Darwin":
                # macOS
                import subprocess
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                      capture_output=True, text=True)
                # Parse resolution from output (simplified)
                return (1920, 1080)  # Default fallback
            
            elif platform.system() == "Linux":
                try:
                    # Try xrandr first
                    result = subprocess.run(['xrandr'], capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if '*' in line and 'x' in line:
                                # Parse resolution from xrandr output
                                parts = line.strip().split()
                                for part in parts:
                                    if 'x' in part and part.replace('x', '').replace('.', '').isdigit():
                                        w, h = part.split('x')
                                        return (int(float(w)), int(float(h)))
                except:
                    pass
                
                # Fallback to tkinter
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()
                return (width, height)
                
        except Exception as e:
            print(f"Could not detect screen resolution: {e}")
            return (1920, 1080)  # Default fallback
    
    def _detect_capabilities(self) -> List[str]:
        """Detect system capabilities for automation."""
        capabilities = []
        
        # Basic capabilities
        capabilities.append("screenshot")
        capabilities.append("keyboard_input")
        capabilities.append("mouse_input")
        
        # Audio capabilities
        if self.system_info and self.system_info.has_audio:
            capabilities.append("audio_output")
        if self.system_info and self.system_info.has_microphone:
            capabilities.append("audio_input")
        
        # OS-specific capabilities
        if platform.system() == "Windows":
            capabilities.extend([
                "windows_automation",
                "powershell",
                "win32_api",
                "system_tray"
            ])
        elif platform.system() == "Darwin":
            capabilities.extend([
                "macos_automation", 
                "applescript",
                "accessibility_api",
                "dock_integration"
            ])
        elif platform.system() == "Linux":
            capabilities.extend([
                "linux_automation",
                "bash",
                "dbus"
            ])
            
            # Display server specific
            if self.system_info and self.system_info.display_server == "x11":
                capabilities.extend(["xdotool", "wmctrl", "xprop"])
            elif self.system_info and self.system_info.display_server == "wayland":
                capabilities.extend(["wayland_automation", "dbus_desktop"])
        
        # Check for specific tools availability
        tools_to_check = {
            "git": "git_integration",
            "docker": "docker_support", 
            "code": "vscode_integration",
            "firefox": "firefox_automation",
            "chrome": "chrome_automation"
        }
        
        for tool, capability in tools_to_check.items():
            if self._check_command_available(tool):
                capabilities.append(capability)
        
        return capabilities
    
    def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            subprocess.run([command, '--version'], 
                         capture_output=True, 
                         timeout=5)
            return True
        except:
            return False
    
    def get_os_commands(self) -> Dict[str, Dict[str, str]]:
        """Get OS-specific command templates."""
        if not self.system_info:
            return {}
        
        commands = {
            "Windows": {
                "open_browser": 'start {browser} "{url}"',
                "open_application": 'start {app}',
                "take_screenshot": 'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds"',
                "list_processes": 'tasklist',
                "kill_process": 'taskkill /IM {process} /F',
                "open_file_manager": 'explorer',
                "system_info": 'systeminfo'
            },
            "Darwin": {
                "open_browser": 'open -a "{browser}" "{url}"',
                "open_application": 'open -a "{app}"',
                "take_screenshot": 'screencapture -x {filename}',
                "list_processes": 'ps aux',
                "kill_process": 'killall {process}',
                "open_file_manager": 'open .',
                "system_info": 'system_profiler SPHardwareDataType'
            },
            "Linux": {
                "open_browser": 'xdg-open "{url}"',
                "open_application": '{app} &',
                "take_screenshot": 'gnome-screenshot -f {filename}',
                "list_processes": 'ps aux',
                "kill_process": 'killall {process}',
                "open_file_manager": 'xdg-open .',
                "system_info": 'uname -a && lscpu'
            }
        }
        
        return commands.get(self.system_info.os, {})
    
    def get_automation_config(self) -> Dict[str, any]:
        """Get recommended automation configuration based on platform."""
        if not self.system_info:
            return {}
        
        base_config = {
            "screenshot_method": "pyautogui",
            "mouse_method": "pyautogui", 
            "keyboard_method": "pyautogui",
            "delay_between_actions": 0.1,
            "screenshot_quality": 0.8
        }
        
        # Platform-specific optimizations
        if self.system_info.os == "Linux":
            if self.system_info.display_server == "wayland":
                base_config.update({
                    "wayland_mode": True,
                    "delay_between_actions": 0.2,
                    "use_dbus": True
                })
            elif self.system_info.display_server == "x11":
                base_config.update({
                    "x11_mode": True,
                    "use_xdotool": True
                })
        
        elif self.system_info.os == "Windows":
            base_config.update({
                "use_win32": True,
                "screenshot_method": "win32gui"
            })
        
        elif self.system_info.os == "Darwin":
            base_config.update({
                "use_applescript": True,
                "screenshot_method": "screencapture"
            })
        
        return base_config
    
    def print_system_info(self) -> None:
        """Print comprehensive system information."""
        if not self.system_info:
            print("System information not available")
            return
        
        print("=== System Environment Information ===")
        print(f"OS: {self.system_info.os} {self.system_info.os_version}")
        print(f"Architecture: {self.system_info.architecture}")
        print(f"Display Server: {self.system_info.display_server}")
        print(f"Desktop Environment: {self.system_info.desktop_environment}")
        print(f"Window Manager: {self.system_info.window_manager}")
        print(f"Screen Resolution: {self.system_info.screen_resolution}")
        print(f"CPU Cores: {self.system_info.cpu_count}")
        print(f"Memory: {self.system_info.memory_gb} GB")
        print(f"Audio Support: {self.system_info.has_audio}")
        print(f"Microphone Support: {self.system_info.has_microphone}")
        print(f"Capabilities: {', '.join(self.system_info.capabilities)}")


# Global platform detector instance
platform_detector = PlatformDetector()


def get_system_environment() -> SystemEnvironment:
    """Get the current system environment."""
    return platform_detector.system_info


def get_os_commands() -> Dict[str, Dict[str, str]]:
    """Get OS-specific command templates."""
    return platform_detector.get_os_commands()


def get_automation_config() -> Dict[str, any]:
    """Get automation configuration for current platform."""
    return platform_detector.get_automation_config()


if __name__ == "__main__":
    # Test the platform detection
    detector = PlatformDetector()
    detector.print_system_info()
    
    print("\n=== OS Commands ===")
    commands = detector.get_os_commands()
    for action, command in commands.items():
        print(f"{action}: {command}")
    
    print("\n=== Automation Config ===")
    config = detector.get_automation_config()
    for key, value in config.items():
        print(f"{key}: {value}")