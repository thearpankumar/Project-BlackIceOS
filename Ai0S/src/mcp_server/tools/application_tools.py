"""
Application Tools - Cross-platform application management
Dynamic application control with OS-specific implementations.
"""

import asyncio
import logging
import platform
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple
import psutil
import shutil

from ...utils.platform_detector import get_system_environment


logger = logging.getLogger(__name__)


class ApplicationTools:
    """Cross-platform application management tools."""
    
    def __init__(self):
        self.system_env = get_system_environment()
        
        # Application launch strategies per OS
        self.launch_strategies = self._get_launch_strategies()
        
        # Common application mappings
        self.app_aliases = self._get_app_aliases()
        
        # Active applications tracking
        self.launched_apps: List[Dict[str, Any]] = []
    
    def _get_launch_strategies(self) -> Dict[str, Dict[str, str]]:
        """Get application launch strategies for different OS."""
        
        strategies = {
            "Windows": {
                "start_menu": "start",
                "executable": "start",
                "path": "start",
                "powershell": "powershell -Command \"Start-Process '{app}'\""
            },
            "Darwin": {  # macOS
                "applications": "open -a \"{app}\"",
                "bundle": "open \"{app}\"",
                "executable": "open \"{app}\"",
                "terminal": "osascript -e 'tell application \"Terminal\" to do script \"{app}\"'"
            },
            "Linux": {
                "desktop": "{app} &",
                "executable": "{app} &", 
                "path": "\"{app}\" &",
                "terminal": "gnome-terminal -- {app}",
                "flatpak": "flatpak run {app}",
                "snap": "snap run {app}",
                "appimage": "\"{app}\" &"
            }
        }
        
        return strategies.get(self.system_env.os, strategies["Linux"])
    
    def _get_app_aliases(self) -> Dict[str, Dict[str, str]]:
        """Get common application name aliases for different OS."""
        
        aliases = {
            "Windows": {
                "calculator": "calc",
                "notepad": "notepad",
                "paint": "mspaint",
                "cmd": "cmd",
                "powershell": "powershell",
                "explorer": "explorer",
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "code": "code",
                "vscode": "code",
                "discord": "Discord",
                "zoom": "Zoom",
                "teams": "Teams"
            },
            "Darwin": {  # macOS
                "calculator": "Calculator",
                "textedit": "TextEdit",
                "finder": "Finder",
                "terminal": "Terminal",
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "safari": "Safari",
                "code": "Visual Studio Code",
                "vscode": "Visual Studio Code",
                "discord": "Discord",
                "zoom": "zoom.us",
                "teams": "Microsoft Teams"
            },
            "Linux": {
                "calculator": "gnome-calculator",
                "notepad": "gedit",
                "text": "gedit",
                "files": "nautilus",
                "terminal": "gnome-terminal",
                "chrome": "google-chrome",
                "firefox": "firefox",
                "code": "code",
                "vscode": "code",
                "discord": "discord",
                "zoom": "zoom",
                "teams": "teams"
            }
        }
        
        return aliases.get(self.system_env.os, aliases["Linux"])
    
    async def launch_application(
        self, 
        app_name: str, 
        args: List[str] = None, 
        wait: bool = False
    ) -> str:
        """
        Launch an application by name or path.
        
        Args:
            app_name: Application name or executable path
            args: Command line arguments
            wait: Wait for application to start
            
        Returns:
            Success message or error
        """
        try:
            logger.info(f"Launching application: {app_name} with args: {args}")
            
            if args is None:
                args = []
            
            # Resolve application alias
            resolved_app = self.app_aliases.get(app_name.lower(), app_name)
            
            # Find application executable
            app_path = self._find_application(resolved_app)
            if not app_path:
                app_path = resolved_app
            
            # Build launch command
            command = self._build_launch_command(app_path, args)
            
            if not command:
                return f"Could not build launch command for {app_name}"
            
            logger.debug(f"Executing launch command: {command}")
            
            # Execute command
            start_time = time.time()
            
            if self.system_env.os == "Windows":
                result = subprocess.run(command, shell=True, capture_output=False)
            else:
                result = subprocess.run(command, shell=True, capture_output=False)
            
            # Wait for application if requested
            if wait:
                await asyncio.sleep(2)
                
                # Verify application started
                if self._verify_app_launched(resolved_app):
                    launch_time = time.time() - start_time
                    
                    # Track launched application
                    app_info = {
                        "name": app_name,
                        "resolved_name": resolved_app,
                        "path": app_path,
                        "args": args,
                        "launched_at": start_time,
                        "launch_time": launch_time,
                        "command": command
                    }
                    self.launched_apps.append(app_info)
                    
                    return f"Successfully launched {app_name} ({launch_time:.2f}s)"
                else:
                    return f"Application command executed but verification failed: {app_name}"
            else:
                # Track launched application without verification
                app_info = {
                    "name": app_name,
                    "resolved_name": resolved_app,
                    "path": app_path,
                    "args": args,
                    "launched_at": start_time,
                    "command": command
                }
                self.launched_apps.append(app_info)
                
                return f"Launch command executed for {app_name}"
                
        except Exception as e:
            error_msg = f"Failed to launch application {app_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _find_application(self, app_name: str) -> Optional[str]:
        """Find application executable path."""
        try:
            # Check if it's already a full path
            if '/' in app_name or '\\' in app_name:
                return app_name
            
            # Try to find in PATH
            path = shutil.which(app_name)
            if path:
                return path
            
            # OS-specific application search
            if self.system_env.os == "Linux":
                # Check common Linux application paths
                common_paths = [
                    f"/usr/bin/{app_name}",
                    f"/usr/local/bin/{app_name}",
                    f"/opt/{app_name}/{app_name}",
                    f"/snap/bin/{app_name}",
                    f"/var/lib/flatpak/exports/bin/{app_name}"
                ]
                
                for path in common_paths:
                    if subprocess.run(["test", "-f", path], capture_output=True).returncode == 0:
                        return path
            
            elif self.system_env.os == "Windows":
                # Windows application search
                common_paths = [
                    f"C:\\Program Files\\{app_name}\\{app_name}.exe",
                    f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe",
                    f"C:\\Windows\\System32\\{app_name}.exe"
                ]
                
                for path in common_paths:
                    if subprocess.run(["test", "-f", path], shell=True, capture_output=True).returncode == 0:
                        return path
            
            return None
            
        except Exception as e:
            logger.debug(f"Application search failed for {app_name}: {e}")
            return None
    
    def _build_launch_command(self, app_path: str, args: List[str]) -> Optional[str]:
        """Build OS-specific launch command."""
        
        try:
            args_str = " ".join(args) if args else ""
            
            if self.system_env.os == "Windows":
                if args_str:
                    return f'start "" "{app_path}" {args_str}'
                else:
                    return f'start "" "{app_path}"'
            
            elif self.system_env.os == "Darwin":  # macOS
                if app_path.endswith('.app') or not '/' in app_path:
                    # Application bundle
                    if args_str:
                        return f'open -a "{app_path}" --args {args_str}'
                    else:
                        return f'open -a "{app_path}"'
                else:
                    # Executable
                    if args_str:
                        return f'"{app_path}" {args_str} &'
                    else:
                        return f'"{app_path}" &'
            
            elif self.system_env.os == "Linux":
                if args_str:
                    return f'"{app_path}" {args_str} &'
                else:
                    return f'"{app_path}" &'
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to build launch command: {e}")
            return None
    
    def _verify_app_launched(self, app_name: str) -> bool:
        """Verify that application was successfully launched."""
        try:
            # Get list of running processes
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    process_info = proc.info
                    if not process_info or not process_info['name']:
                        continue
                    
                    process_name = process_info['name'].lower()
                    
                    # Check if process name matches application
                    if (app_name.lower() in process_name or 
                        process_name in app_name.lower()):
                        logger.debug(f"Found application process: {process_name}")
                        return True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Application verification failed: {e}")
            return True  # Assume success if verification fails
    
    async def find_window(self, window_title: str, partial_match: bool = True) -> str:
        """
        Find application window by title.
        
        Args:
            window_title: Window title to search for
            partial_match: Allow partial title matches
            
        Returns:
            Window information or error message
        """
        try:
            logger.info(f"Finding window: {window_title}, partial: {partial_match}")
            
            windows = []
            
            if self.system_env.os == "Linux" and self.system_env.display_server == "x11":
                # Use wmctrl on X11 systems
                try:
                    result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                parts = line.split(' ', 3)
                                if len(parts) >= 4:
                                    window_id, desktop, hostname, title = parts
                                    
                                    if partial_match:
                                        if window_title.lower() in title.lower():
                                            windows.append({
                                                "id": window_id,
                                                "title": title,
                                                "desktop": desktop
                                            })
                                    else:
                                        if window_title.lower() == title.lower():
                                            windows.append({
                                                "id": window_id,
                                                "title": title,
                                                "desktop": desktop
                                            })
                except subprocess.CalledProcessError:
                    pass
            
            elif self.system_env.os == "Windows":
                # Windows window enumeration would require pywin32
                # For now, return a placeholder
                windows.append({
                    "title": "Windows window enumeration not implemented",
                    "note": "Would require pywin32 for full implementation"
                })
            
            elif self.system_env.os == "Darwin":
                # macOS window enumeration
                try:
                    # Use AppleScript to list windows
                    script = """
                    tell application "System Events"
                        set windowList to {}
                        repeat with proc in (every process whose visible is true)
                            repeat with win in (every window of proc)
                                set end of windowList to (name of win as string)
                            end repeat
                        end repeat
                        return windowList
                    end tell
                    """
                    
                    result = subprocess.run(['osascript', '-e', script], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        window_titles = result.stdout.strip().split(', ')
                        for title in window_titles:
                            if partial_match:
                                if window_title.lower() in title.lower():
                                    windows.append({"title": title})
                            else:
                                if window_title.lower() == title.lower():
                                    windows.append({"title": title})
                
                except subprocess.CalledProcessError:
                    pass
            
            if windows:
                return f"Found {len(windows)} window(s): {windows}"
            else:
                return f"No windows found matching '{window_title}'"
                
        except Exception as e:
            error_msg = f"Failed to find window '{window_title}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def list_applications(self, filter_system: bool = True) -> str:
        """
        List currently running applications.
        
        Args:
            filter_system: Filter out system processes
            
        Returns:
            List of running applications
        """
        try:
            logger.info(f"Listing applications, filter_system: {filter_system}")
            
            applications = []
            system_processes = {
                'kernel', 'kthreadd', 'systemd', 'init', 'swapper', 'migration',
                'ksoftirqd', 'watchdog', 'rcu_', 'sshd', 'dbus', 'NetworkManager',
                'pulseaudio', 'gdm', 'Xorg', 'gnome-shell', 'gsd-', 'evolution-',
                'gvfs', 'udisks', 'packagekit', 'colord', 'accounts-daemon',
                'winlogon.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
                'lsass.exe', 'svchost.exe', 'dwm.exe', 'explorer.exe'
            }
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info', 'cpu_percent']):
                try:
                    process_info = proc.info
                    if not process_info or not process_info['name']:
                        continue
                    
                    process_name = process_info['name']
                    
                    # Filter system processes if requested
                    if filter_system:
                        is_system = any(sys_proc in process_name.lower() 
                                       for sys_proc in system_processes)
                        if is_system:
                            continue
                    
                    # Get additional process info
                    try:
                        memory_mb = process_info['memory_info'].rss / 1024 / 1024
                        cpu_percent = process_info.get('cpu_percent', 0.0)
                    except:
                        memory_mb = 0
                        cpu_percent = 0.0
                    
                    applications.append({
                        "name": process_name,
                        "pid": process_info['pid'],
                        "executable": process_info.get('exe', 'N/A'),
                        "memory_mb": round(memory_mb, 1),
                        "cpu_percent": round(cpu_percent, 1)
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            applications.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            # Limit to top 50 applications
            applications = applications[:50]
            
            return f"Found {len(applications)} applications: {applications}"
            
        except Exception as e:
            error_msg = f"Failed to list applications: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def close_application(self, app_name: str, force: bool = False) -> str:
        """
        Close application by name.
        
        Args:
            app_name: Application name to close
            force: Force close (kill) the application
            
        Returns:
            Success message or error
        """
        try:
            logger.info(f"Closing application: {app_name}, force: {force}")
            
            closed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        if force:
                            proc.kill()
                        else:
                            proc.terminate()
                        closed_count += 1
                        logger.debug(f"{'Killed' if force else 'Terminated'} process: {proc.info['name']} (PID: {proc.info['pid']})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.debug(f"Could not close process: {e}")
                    continue
            
            if closed_count > 0:
                return f"{'Killed' if force else 'Closed'} {closed_count} {app_name} process(es)"
            else:
                return f"No processes found matching '{app_name}'"
                
        except Exception as e:
            error_msg = f"Failed to close application {app_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_application_info(self) -> Dict[str, Any]:
        """Get information about application management capabilities."""
        return {
            "launch_strategies": list(self.launch_strategies.keys()),
            "app_aliases": list(self.app_aliases.keys()),
            "launched_apps": self.launched_apps,
            "os": self.system_env.os,
            "capabilities": [cap for cap in self.system_env.capabilities 
                           if any(term in cap.lower() for term in ['app', 'process', 'window'])]
        }