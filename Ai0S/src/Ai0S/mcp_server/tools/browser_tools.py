"""
Browser Tools - Cross-platform browser automation
Dynamic browser control with OS-specific implementations.
"""

import asyncio
import logging
import platform
import subprocess
import time
from typing import Dict, List, Optional, Any
import psutil

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except (ImportError, Exception):
    # Handle import or display connection errors
    HAS_PYAUTOGUI = False
    pyautogui = None

from ...utils.platform_detector import get_system_environment, get_os_commands


logger = logging.getLogger(__name__)


class BrowserTools:
    """Cross-platform browser automation tools."""
    
    def __init__(self):
        self.system_env = get_system_environment()
        self.os_commands = get_os_commands()
        
        # Browser executable mapping
        self.browser_executables = self._get_browser_executables()
        
        # Active browser tracking
        self.active_browsers: List[Dict[str, Any]] = []
    
    def _get_browser_executables(self) -> Dict[str, Dict[str, str]]:
        """Get browser executable paths for different OS."""
        
        browsers = {
            "Windows": {
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "default": "start"
            },
            "Darwin": {  # macOS
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "safari": "Safari",
                "edge": "Microsoft Edge",
                "default": "open"
            },
            "Linux": {
                "chrome": "google-chrome",
                "firefox": "firefox",
                "edge": "microsoft-edge",
                "chromium": "chromium-browser",
                "default": "xdg-open"
            }
        }
        
        return browsers.get(self.system_env.os, browsers["Linux"])
    
    async def open_browser(
        self, 
        browser: str = "default", 
        url: Optional[str] = None, 
        new_window: bool = False
    ) -> str:
        """
        Open a web browser with optional URL.
        
        Args:
            browser: Browser name (chrome, firefox, safari, edge, default)
            url: URL to navigate to (optional)
            new_window: Open in new window
            
        Returns:
            Success message or error
        """
        try:
            logger.info(f"Opening browser: {browser}, URL: {url}")
            
            # Get browser executable
            browser_exec = self.browser_executables.get(browser, self.browser_executables["default"])
            
            # Build command based on OS
            command = self._build_browser_command(browser, browser_exec, url, new_window)
            
            if not command:
                return f"Browser {browser} not supported on {self.system_env.os}"
            
            # Execute command
            logger.debug(f"Executing browser command: {command}")
            
            if self.system_env.os == "Windows":
                # Windows-specific execution
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
            else:
                # Unix-like systems
                result = subprocess.run(command, shell=True, capture_output=False)
            
            # Wait a moment for browser to start
            await asyncio.sleep(2)
            
            # Track opened browser
            browser_info = {
                "browser": browser,
                "url": url,
                "opened_at": time.time(),
                "command": command
            }
            self.active_browsers.append(browser_info)
            
            # Verify browser opened
            if self._verify_browser_opened(browser):
                success_msg = f"Successfully opened {browser}"
                if url:
                    success_msg += f" and navigated to {url}"
                return success_msg
            else:
                return f"Browser command executed but verification failed: {command}"
                
        except Exception as e:
            error_msg = f"Failed to open browser {browser}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _build_browser_command(
        self, 
        browser: str, 
        browser_exec: str, 
        url: Optional[str], 
        new_window: bool
    ) -> Optional[str]:
        """Build OS-specific browser command."""
        
        if self.system_env.os == "Windows":
            if browser == "default":
                if url:
                    return f'start "" "{url}"'
                else:
                    return "start"
            else:
                cmd = f"start {browser_exec}"
                if new_window:
                    cmd += " --new-window"
                if url:
                    cmd += f' "{url}"'
                return cmd
        
        elif self.system_env.os == "Darwin":  # macOS
            if browser == "default":
                if url:
                    return f'open "{url}"'
                else:
                    return "open -a Safari"
            else:
                cmd = f'open -a "{browser_exec}"'
                if new_window:
                    cmd += " --new"
                if url:
                    cmd += f' "{url}"'
                return cmd
        
        elif self.system_env.os == "Linux":
            if browser == "default":
                if url:
                    return f'xdg-open "{url}"'
                else:
                    return "xdg-open about:blank"
            else:
                cmd = browser_exec
                if new_window:
                    cmd += " --new-window"
                if url:
                    cmd += f' "{url}"'
                else:
                    cmd += " about:blank"
                return f"{cmd} &"
        
        return None
    
    def _verify_browser_opened(self, browser: str) -> bool:
        """Verify that browser was successfully opened."""
        try:
            # Get list of running processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    process_info = proc.info
                    if process_info and process_info['name']:
                        processes.append(process_info['name'].lower())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check for browser processes
            browser_processes = {
                "chrome": ["chrome", "google-chrome", "chromium"],
                "firefox": ["firefox"],
                "safari": ["safari"],
                "edge": ["msedge", "microsoft-edge"],
                "default": ["chrome", "firefox", "safari", "msedge", "chromium"]
            }
            
            target_processes = browser_processes.get(browser, browser_processes["default"])
            
            for process_name in processes:
                for target in target_processes:
                    if target in process_name:
                        logger.debug(f"Found browser process: {process_name}")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Browser verification failed: {e}")
            return True  # Assume success if verification fails
    
    async def navigate_url(self, url: str, method: str = "address_bar") -> str:
        """
        Navigate to a URL in the active browser.
        
        Args:
            url: URL to navigate to
            method: Navigation method (address_bar, ctrl_l, cmd_l)
            
        Returns:
            Success message or error
        """
        try:
            logger.info(f"Navigating to URL: {url} using method: {method}")
            
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://', 'file://')):
                if '.' in url or url.startswith('localhost'):
                    url = f"https://{url}"
                else:
                    url = f"https://www.google.com/search?q={url}"
            
            # Use keyboard shortcuts to navigate
            if method == "ctrl_l" or (method == "address_bar" and self.system_env.os != "Darwin"):
                # Focus address bar and type URL
                if not HAS_PYAUTOGUI or not pyautogui:
                    return "UI automation not available - pyautogui not installed or display not accessible"
                
                # Ctrl+L to focus address bar (Cmd+L on macOS)
                if self.system_env.os == "Darwin":
                    pyautogui.hotkey('cmd', 'l')
                else:
                    pyautogui.hotkey('ctrl', 'l')
                
                await asyncio.sleep(0.5)
                
                # Type URL
                pyautogui.typewrite(url)
                await asyncio.sleep(0.2)
                
                # Press Enter
                pyautogui.press('enter')
                
            elif method == "cmd_l" or (method == "address_bar" and self.system_env.os == "Darwin"):
                if not HAS_PYAUTOGUI or not pyautogui:
                    return "UI automation not available - pyautogui not installed or display not accessible"
                
                # Cmd+L for macOS
                pyautogui.hotkey('cmd', 'l')
                await asyncio.sleep(0.5)
                pyautogui.typewrite(url)
                await asyncio.sleep(0.2)
                pyautogui.press('enter')
            
            else:
                # Try to open URL in existing browser
                if self.system_env.os == "Windows":
                    subprocess.run(f'start "" "{url}"', shell=True)
                elif self.system_env.os == "Darwin":
                    subprocess.run(['open', url])
                else:
                    subprocess.run(['xdg-open', url])
            
            # Wait for navigation
            await asyncio.sleep(3)
            
            return f"Successfully navigated to {url}"
            
        except Exception as e:
            error_msg = f"Failed to navigate to {url}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def close_browser(self, browser: Optional[str] = None) -> str:
        """
        Close browser or specific browser window.
        
        Args:
            browser: Specific browser to close (optional)
            
        Returns:
            Success message or error
        """
        try:
            if browser:
                # Close specific browser
                browser_processes = {
                    "chrome": ["chrome", "google-chrome"],
                    "firefox": ["firefox"],
                    "safari": ["safari"],
                    "edge": ["msedge", "microsoft-edge"]
                }
                
                target_processes = browser_processes.get(browser, [browser])
                closed_count = 0
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if any(target in proc.info['name'].lower() for target in target_processes):
                            proc.terminate()
                            closed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return f"Closed {closed_count} {browser} processes"
            
            else:
                # Close active browser window using keyboard shortcut
                if not HAS_PYAUTOGUI or not pyautogui:
                    return "UI automation not available - pyautogui not installed or display not accessible"
                
                if self.system_env.os == "Darwin":
                    pyautogui.hotkey('cmd', 'w')
                else:
                    pyautogui.hotkey('ctrl', 'w')
                
                return "Closed active browser window"
                
        except Exception as e:
            error_msg = f"Failed to close browser: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def refresh_page(self) -> str:
        """Refresh the current browser page."""
        if not HAS_PYAUTOGUI or not pyautogui:
            return "UI automation not available - pyautogui not installed or display not accessible"
            
        try:
            
            if self.system_env.os == "Darwin":
                pyautogui.hotkey('cmd', 'r')
            else:
                pyautogui.hotkey('ctrl', 'r')
            
            await asyncio.sleep(1)
            return "Page refreshed"
            
        except Exception as e:
            return f"Failed to refresh page: {str(e)}"
    
    async def go_back(self) -> str:
        """Go back to previous page."""
        if not HAS_PYAUTOGUI or not pyautogui:
            return "UI automation not available - pyautogui not installed or display not accessible"
            
        try:
            
            if self.system_env.os == "Darwin":
                pyautogui.hotkey('cmd', 'left')
            else:
                pyautogui.hotkey('alt', 'left')
            
            await asyncio.sleep(1)
            return "Navigated back"
            
        except Exception as e:
            return f"Failed to go back: {str(e)}"
    
    async def go_forward(self) -> str:
        """Go forward to next page."""
        if not HAS_PYAUTOGUI or not pyautogui:
            return "UI automation not available - pyautogui not installed or display not accessible"
            
        try:
            
            if self.system_env.os == "Darwin":
                pyautogui.hotkey('cmd', 'right')
            else:
                pyautogui.hotkey('alt', 'right')
            
            await asyncio.sleep(1)
            return "Navigated forward"
            
        except Exception as e:
            return f"Failed to go forward: {str(e)}"
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get information about available and active browsers."""
        return {
            "available_browsers": list(self.browser_executables.keys()),
            "active_browsers": self.active_browsers,
            "os": self.system_env.os,
            "capabilities": [cap for cap in self.system_env.capabilities if "browser" in cap.lower()]
        }