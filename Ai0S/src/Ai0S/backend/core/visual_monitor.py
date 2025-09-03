"""
Visual State Monitor - Screenshot capture and AI-powered screen analysis
Real-time screen monitoring with intelligent change detection and analysis.
"""

import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from PIL import Image, ImageGrab
import io
import base64
import numpy as np

# Initialize logger early for import error handling
logger = logging.getLogger(__name__)

try:
    import pyautogui
    import cv2
    HAS_CV2 = True
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_CV2 = False
    HAS_PYAUTOGUI = False
    logger.debug("pyautogui or cv2 not available")
except Exception as e:
    # Handle display connection errors (X authority, missing display, etc.)
    logger.debug(f"Display-related import error: {e}")
    HAS_CV2 = False
    HAS_PYAUTOGUI = False
    
    # For X authority issues, suggest solutions
    if "Xauthority" in str(e) or "DISPLAY" in str(e):
        logger.warning("X11 display access issue detected. To fix:")
        logger.warning("1. Run: xhost +local:")
        logger.warning("2. Or set DISPLAY variable: export DISPLAY=:0")
        logger.warning("3. Or create Xauthority file")
        logger.warning("Visual monitoring will work in headless mode with limited functionality")

from ..models.ai_models import AIModels
from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


@dataclass
class ScreenState:
    """Current state of the screen."""
    timestamp: datetime
    screenshot_hash: str
    screenshot_data: Optional[bytes]
    analysis: Optional[Dict[str, Any]]
    detected_changes: List[str]
    ui_elements: List[Dict[str, Any]]
    active_window: Optional[str]
    mouse_position: Tuple[int, int]
    confidence_score: float


class ScreenCapture:
    """Cross-platform screen capture utility."""
    
    def __init__(self):
        self.system_env = get_system_environment()
        self.capture_method = self._detect_best_capture_method()
        self.last_capture_error = None
        
    def _detect_best_capture_method(self) -> str:
        """Detect the best screen capture method for current platform."""
        
        if self.system_env.os == "Windows":
            return "pil"
        elif self.system_env.os == "Darwin":  # macOS
            return "pil"
        else:  # Linux
            if self.system_env.display_server == "X11":
                return "pil" if HAS_CV2 else "pyautogui"
            elif self.system_env.display_server == "Wayland":
                return "wayland"
            else:
                return "pil"
    
    def capture_screenshot(self) -> Optional[Image.Image]:
        """Capture screenshot using the best available method with robust error handling."""
        
        # Try multiple capture methods in order of preference
        capture_methods = [
            ("pil", self._capture_pil),
            ("pyautogui", self._capture_pyautogui),
            ("wayland", self._capture_wayland),
            ("fallback", self._capture_fallback)
        ]
        
        last_error = None
        for method_name, capture_func in capture_methods:
            try:
                # Skip methods that aren't available
                if method_name == "pyautogui" and not HAS_PYAUTOGUI:
                    continue
                if method_name == "wayland" and self.capture_method != "wayland":
                    continue
                    
                screenshot = capture_func()
                if screenshot:
                    logger.debug(f"Screenshot captured successfully using {method_name}")
                    return screenshot
                    
            except PermissionError as e:
                last_error = f"Permission denied (X11 authority): {e}"
                self.last_capture_error = last_error
                logger.warning(f"Permission error with {method_name}: {e}")
                continue
            except Exception as e:
                last_error = f"Method {method_name} failed: {e}"
                self.last_capture_error = last_error
                logger.debug(f"Screenshot method {method_name} failed: {e}")
                continue
        
        # All methods failed
        if "X11" in str(last_error) or "authority" in str(last_error).lower():
            logger.error(f"X11 display access denied. Try: xhost +local: or set proper DISPLAY variable. Error: {last_error}")
        else:
            logger.error(f"All screenshot capture methods failed. Last error: {last_error}")
            
        return None
    
    def _capture_pil(self) -> Optional[Image.Image]:
        """Capture using PIL ImageGrab."""
        return ImageGrab.grab()
    
    def _capture_pyautogui(self) -> Optional[Image.Image]:
        """Capture using pyautogui."""
        if not HAS_PYAUTOGUI:
            return None
        return pyautogui.screenshot()
    
    def _capture_fallback(self) -> Optional[Image.Image]:
        """Fallback capture method using system tools."""
        try:
            import subprocess
            import tempfile
            import os
            
            # Try using scrot (Linux screenshot tool)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                
            try:
                # Try scrot first
                result = subprocess.run(
                    ['scrot', '-z', tmp_path], 
                    capture_output=True, 
                    timeout=10,
                    check=False
                )
                
                if result.returncode == 0 and os.path.exists(tmp_path):
                    screenshot = Image.open(tmp_path)
                    os.unlink(tmp_path)
                    return screenshot
                    
                # Try gnome-screenshot
                result = subprocess.run(
                    ['gnome-screenshot', '-f', tmp_path], 
                    capture_output=True, 
                    timeout=10,
                    check=False
                )
                
                if result.returncode == 0 and os.path.exists(tmp_path):
                    screenshot = Image.open(tmp_path)
                    os.unlink(tmp_path)
                    return screenshot
                    
            finally:
                # Cleanup temp file if it exists
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
            return None
            
        except Exception as e:
            logger.debug(f"Fallback capture failed: {e}")
            return None
    
    def _capture_wayland(self) -> Optional[Image.Image]:
        """Capture screenshot on Wayland (using grim if available)."""
        
        try:
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                result = subprocess.run(
                    ['grim', tmp.name], 
                    capture_output=True, 
                    timeout=5
                )
                
                if result.returncode == 0:
                    return Image.open(tmp.name)
                else:
                    logger.warning("Grim not available, falling back to PIL")
                    return ImageGrab.grab()
                    
        except Exception as e:
            logger.debug(f"Wayland capture failed: {e}")
            return ImageGrab.grab()
    
    def intelligent_capture(self, quality: int = 85) -> bytes:
        """Capture and compress screenshot intelligently with error handling."""
        
        try:
            screenshot = self.capture_screenshot()
            if not screenshot:
                logger.debug("No screenshot captured - returning empty bytes")
                return b''
            
            # Optimize size for AI analysis
            # Resize large screenshots while maintaining readability
            width, height = screenshot.size
            if width > 1920 or height > 1080:
                # Calculate new size maintaining aspect ratio
                ratio = min(1920/width, 1080/height)
                new_size = (int(width * ratio), int(height * ratio))
                screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Screenshot resized from {width}x{height} to {new_size[0]}x{new_size[1]}")
            
            # Convert to bytes with error handling
            try:
                buffer = io.BytesIO()
                screenshot.save(buffer, format='JPEG', quality=quality, optimize=True)
                screenshot_data = buffer.getvalue()
                
                if len(screenshot_data) == 0:
                    logger.warning("Screenshot saved but resulted in 0 bytes")
                    return b''
                    
                logger.debug(f"Screenshot compressed to {len(screenshot_data)} bytes at quality {quality}")
                return screenshot_data
                
            except Exception as e:
                logger.error(f"Failed to compress screenshot: {e}")
                # Try without optimization
                try:
                    buffer = io.BytesIO()
                    screenshot.save(buffer, format='JPEG', quality=quality)
                    return buffer.getvalue()
                except Exception as e2:
                    logger.error(f"Failed to save screenshot even without optimization: {e2}")
                    return b''
                    
        except Exception as e:
            logger.error(f"Intelligent capture failed: {e}")
            return b''
    
    def diagnose_display_issues(self) -> Dict[str, Any]:
        """Diagnose display and screenshot capture issues."""
        
        import os
        import subprocess
        
        diagnostics = {
            "system_info": {
                "os": self.system_env.os,
                "display_server": self.system_env.display_server,
                "desktop_session": self.system_env.desktop_session
            },
            "environment": {
                "display_var": os.environ.get("DISPLAY"),
                "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
                "xdg_session_type": os.environ.get("XDG_SESSION_TYPE")
            },
            "capture_availability": {
                "has_pyautogui": HAS_PYAUTOGUI,
                "has_cv2": HAS_CV2,
                "preferred_method": self.capture_method
            },
            "last_error": self.last_capture_error,
            "recommendations": []
        }
        
        # Add specific recommendations based on detected issues
        if not os.environ.get("DISPLAY") and self.system_env.display_server == "X11":
            diagnostics["recommendations"].append("Set DISPLAY environment variable (e.g., export DISPLAY=:0)")
        
        if "authority" in str(self.last_capture_error).lower():
            diagnostics["recommendations"].extend([
                "Run 'xhost +local:' to allow local connections",
                "Or run as the same user that started the X session",
                "Check ~/.Xauthority file permissions"
            ])
        
        if self.system_env.display_server == "Wayland":
            diagnostics["recommendations"].extend([
                "Install 'grim' for Wayland screenshots: apt-get install grim",
                "Consider using XWayland compatibility layer"
            ])
        
        # Test basic commands
        test_commands = ["xwininfo", "xrandr", "scrot", "gnome-screenshot", "grim"]
        available_tools = {}
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    ["which", cmd], 
                    capture_output=True, 
                    timeout=2,
                    check=False
                )
                available_tools[cmd] = result.returncode == 0
            except:
                available_tools[cmd] = False
                
        diagnostics["available_tools"] = available_tools
        
        return diagnostics


class ChangeDetector:
    """Intelligent change detection between screen states."""
    
    def __init__(self):
        self.previous_hash = None
        self.previous_analysis = None
        self.change_threshold = 0.05  # 5% change threshold
        
    def detect_changes(self, current_hash: str, current_analysis: Optional[Dict[str, Any]]) -> List[str]:
        """Detect significant changes between screen states."""
        
        changes = []
        
        # Basic hash comparison
        if self.previous_hash and self.previous_hash != current_hash:
            changes.append("screen_content_changed")
        
        # Semantic change detection using AI analysis
        if self.previous_analysis and current_analysis:
            changes.extend(self._detect_semantic_changes(self.previous_analysis, current_analysis))
        
        # Update state
        self.previous_hash = current_hash
        self.previous_analysis = current_analysis
        
        return changes
    
    def _detect_semantic_changes(self, prev_analysis: Dict[str, Any], curr_analysis: Dict[str, Any]) -> List[str]:
        """Detect semantic changes using AI analysis comparison."""
        
        changes = []
        
        # Window changes
        prev_window = prev_analysis.get("active_window")
        curr_window = curr_analysis.get("active_window")
        
        if prev_window != curr_window:
            changes.append(f"window_changed:{prev_window}->{curr_window}")
        
        # UI element changes
        prev_elements = set(el.get("type", "") for el in prev_analysis.get("detected_elements", []))
        curr_elements = set(el.get("type", "") for el in curr_analysis.get("detected_elements", []))
        
        new_elements = curr_elements - prev_elements
        removed_elements = prev_elements - curr_elements
        
        if new_elements:
            changes.append(f"new_elements:{','.join(new_elements)}")
        if removed_elements:
            changes.append(f"removed_elements:{','.join(removed_elements)}")
        
        return changes


class VisualStateMonitor:
    """Main visual state monitoring system."""
    
    def __init__(self, ai_models: AIModels, update_callback: Optional[Callable] = None):
        self.ai_models = ai_models
        self.update_callback = update_callback
        self.settings = get_settings()
        
        # Components
        self.screen_capture = ScreenCapture()
        self.change_detector = ChangeDetector()
        
        # State
        self.current_state: Optional[ScreenState] = None
        self.state_history: List[ScreenState] = []
        self.monitoring_active = False
        
        # Configuration
        self.capture_interval = self.settings.visual_settings.get("capture_interval", 2.0)  # seconds
        self.analysis_enabled = self.settings.visual_settings.get("enable_ai_analysis", True)
        self.change_detection_enabled = self.settings.visual_settings.get("enable_change_detection", True)
        self.max_history_size = self.settings.visual_settings.get("max_history_size", 50)
        
        # Performance optimization
        self.last_analysis_time = 0
        self.analysis_cooldown = 1.0  # Minimum time between AI analyses
        
        # Statistics
        self.stats = {
            "screenshots_captured": 0,
            "ai_analyses_performed": 0,
            "changes_detected": 0,
            "errors": 0,
            "total_monitoring_time": 0
        }
        
        logger.info("Visual state monitor initialized")
    
    async def start_monitoring(self) -> None:
        """Start continuous screen monitoring."""
        
        if self.monitoring_active:
            logger.warning("Visual monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting visual state monitoring")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop screen monitoring."""
        
        self.monitoring_active = False
        logger.info("Visual state monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        
        start_time = time.time()
        
        while self.monitoring_active:
            try:
                # Capture and analyze current state
                await self.capture_and_analyze()
                
                # Wait for next capture
                await asyncio.sleep(self.capture_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(self.capture_interval)
        
        # Update monitoring time
        self.stats["total_monitoring_time"] += time.time() - start_time
    
    async def capture_and_analyze(self, force_analysis: bool = False) -> ScreenState:
        """Capture screenshot and perform AI analysis."""
        
        try:
            # Capture screenshot with improved error handling
            screenshot_data = self.screen_capture.intelligent_capture()
            
            if not screenshot_data:
                logger.debug("Failed to capture screenshot - may be running in headless environment")
                
                # Return a mock state for headless environments to prevent blocking
                if self.current_state is None:
                    return ScreenState(
                        timestamp=datetime.now(),
                        screenshot_hash="no_display",
                        screenshot_data=None,
                        analysis=None,
                        detected_changes=["display_unavailable"],
                        ui_elements=[],
                        active_window=None,
                        mouse_position=(0, 0),
                        confidence_score=0.0
                    )
                else:
                    return self.current_state
            
            self.stats["screenshots_captured"] += 1
            
            # Calculate hash for change detection
            screenshot_hash = hashlib.md5(screenshot_data).hexdigest()
            
            # Get mouse position
            mouse_pos = self._get_mouse_position()
            
            # Create initial state
            current_state = ScreenState(
                timestamp=datetime.now(),
                screenshot_hash=screenshot_hash,
                screenshot_data=screenshot_data,
                analysis=None,
                detected_changes=[],
                ui_elements=[],
                active_window=None,
                mouse_position=mouse_pos,
                confidence_score=0.0
            )
            
            # Detect changes
            if self.change_detection_enabled:
                changes = self.change_detector.detect_changes(screenshot_hash, None)
                current_state.detected_changes = changes
                
                if changes:
                    self.stats["changes_detected"] += 1
            
            # Perform AI analysis (rate limited)
            current_time = time.time()
            should_analyze = (
                self.analysis_enabled and 
                (force_analysis or 
                 current_time - self.last_analysis_time >= self.analysis_cooldown or
                 current_state.detected_changes)
            )
            
            if should_analyze:
                analysis = await self._analyze_screenshot(screenshot_data)
                current_state.analysis = analysis
                current_state.ui_elements = analysis.ui_elements if analysis else []
                current_state.active_window = getattr(analysis, 'active_window', None) if analysis else None
                current_state.confidence_score = analysis.confidence_score if analysis else 0.0
                
                self.last_analysis_time = current_time
                self.stats["ai_analyses_performed"] += 1
                
                # Update change detection with analysis
                if self.change_detection_enabled:
                    # Convert ScreenAnalysis to dictionary for change detector
                    analysis_dict = self._convert_analysis_to_dict(analysis) if analysis else None
                    changes = self.change_detector.detect_changes(screenshot_hash, analysis_dict)
                    current_state.detected_changes = changes
            
            # Update current state
            self.current_state = current_state
            
            # Add to history
            self._add_to_history(current_state)
            
            # Notify callback
            if self.update_callback:
                try:
                    await self.update_callback(current_state)
                except Exception as e:
                    logger.error(f"Update callback error: {e}")
            
            return current_state
            
        except Exception as e:
            logger.error(f"Error in capture_and_analyze: {e}")
            self.stats["errors"] += 1
            return self.current_state
    
    def _get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        
        try:
            if HAS_PYAUTOGUI and hasattr(pyautogui, 'position'):
                pos = pyautogui.position()
                return (pos.x, pos.y)
            else:
                return (0, 0)
        except Exception:
            return (0, 0)
    
    async def _analyze_screenshot(self, screenshot_data: bytes) -> Dict[str, Any]:
        """Analyze screenshot using AI models."""
        
        try:
            # Encode screenshot for AI analysis
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            # Perform AI analysis
            analysis = await self.ai_models.analyze_screen(screenshot_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI screenshot analysis failed: {e}")
            return None
    
    def _convert_analysis_to_dict(self, analysis) -> Dict[str, Any]:
        """Convert ScreenAnalysis object to dictionary format for change detector."""
        if not analysis:
            return {}
        
        try:
            # Convert ScreenAnalysis object to dictionary
            return {
                "active_window": getattr(analysis, 'active_window', None),
                "detected_elements": [
                    {"type": elem.get("type", "unknown")} 
                    for elem in getattr(analysis, 'ui_elements', [])
                ],
                "applications": getattr(analysis, 'applications', []),
                "confidence": getattr(analysis, 'confidence_score', 0.0)
            }
        except Exception as e:
            logger.debug(f"Error converting analysis to dict: {e}")
            return {}
    
    def _add_to_history(self, state: ScreenState) -> None:
        """Add state to history with size management."""
        
        self.state_history.append(state)
        
        # Limit history size
        if len(self.state_history) > self.max_history_size:
            # Remove oldest states
            removed_states = self.state_history[:-self.max_history_size]
            self.state_history = self.state_history[-self.max_history_size:]
            
            # Clean up screenshot data from removed states to save memory
            for old_state in removed_states:
                old_state.screenshot_data = None
    
    def get_current_state(self) -> Optional[ScreenState]:
        """Get current screen state."""
        return self.current_state
    
    async def get_current_screenshot(self) -> Optional[bytes]:
        """Get current screenshot data."""
        
        if self.current_state and self.current_state.screenshot_data:
            return self.current_state.screenshot_data
        
        # Capture new screenshot if none available
        screenshot_data = self.screen_capture.intelligent_capture()
        return screenshot_data if screenshot_data else None
    
    def get_recent_changes(self, minutes: int = 5) -> List[str]:
        """Get changes detected in recent history."""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_changes = []
        
        for state in self.state_history:
            if state.timestamp >= cutoff_time:
                recent_changes.extend(state.detected_changes)
        
        return list(set(recent_changes))  # Remove duplicates
    
    def get_state_history(self, limit: int = 10) -> List[ScreenState]:
        """Get recent state history."""
        
        return self.state_history[-limit:]
    
    async def analyze_region(self, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """Analyze a specific region of the screen."""
        
        try:
            # Capture full screenshot
            screenshot = self.screen_capture.capture_screenshot()
            
            if not screenshot:
                return {"error": "Failed to capture screenshot"}
            
            # Crop to specified region
            region = screenshot.crop((x, y, x + width, y + height))
            
            # Convert to bytes
            buffer = io.BytesIO()
            region.save(buffer, format='JPEG', quality=85)
            region_data = buffer.getvalue()
            
            # Analyze region
            analysis = await self._analyze_screenshot(region_data)
            analysis["region"] = {"x": x, "y": y, "width": width, "height": height}
            
            return analysis
            
        except Exception as e:
            logger.error(f"Region analysis failed: {e}")
            return {"error": str(e)}
    
    async def wait_for_change(self, timeout: int = 30) -> Optional[ScreenState]:
        """Wait for screen state to change."""
        
        if not self.current_state:
            return None
        
        start_hash = self.current_state.screenshot_hash
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.current_state and self.current_state.screenshot_hash != start_hash:
                return self.current_state
            
            await asyncio.sleep(0.5)
        
        return None  # Timeout
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        
        stats = self.stats.copy()
        stats.update({
            "monitoring_active": self.monitoring_active,
            "current_state_available": self.current_state is not None,
            "history_size": len(self.state_history),
            "capture_interval": self.capture_interval,
            "analysis_enabled": self.analysis_enabled,
            "change_detection_enabled": self.change_detection_enabled
        })
        
        return stats


# Global instance and utility functions
_visual_monitor_instance: Optional[VisualStateMonitor] = None


def initialize_visual_monitor(ai_models: AIModels, update_callback: Optional[Callable] = None) -> VisualStateMonitor:
    """Initialize the global visual monitor instance."""
    
    global _visual_monitor_instance
    
    if _visual_monitor_instance is None:
        _visual_monitor_instance = VisualStateMonitor(ai_models, update_callback)
        logger.info("Global visual monitor initialized")
    
    return _visual_monitor_instance


def get_visual_monitor() -> Optional[VisualStateMonitor]:
    """Get the global visual monitor instance."""
    
    return _visual_monitor_instance