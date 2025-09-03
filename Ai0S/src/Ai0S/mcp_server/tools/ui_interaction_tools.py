"""
UI Interaction Tools - Cross-platform user interface automation
Advanced UI interaction with AI-guided element detection.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from PIL import Image

try:
    import pyautogui
    import cv2
    HAS_GUI_TOOLS = True
except (ImportError, Exception):
    # Handle import or display connection errors
    HAS_GUI_TOOLS = False
    pyautogui = None
    cv2 = None

from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class UIInteractionTools:
    """Cross-platform UI interaction and automation tools."""
    
    def __init__(self):
        self.system_env = get_system_environment()
        self.settings = get_settings()
        
        # Configure PyAutoGUI if available
        if HAS_GUI_TOOLS and pyautogui:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1
        
        # Interaction history for learning
        self.interaction_history: List[Dict[str, Any]] = []
        
        # Screen dimensions
        if HAS_GUI_TOOLS and pyautogui:
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            self.screen_width, self.screen_height = 1920, 1080  # Default fallback
        
        # Platform-specific configurations
        self._setup_platform_config()
    
    def _setup_platform_config(self) -> None:
        """Setup platform-specific interaction configurations."""
        
        if self.system_env.os == "Darwin":  # macOS
            self.modifier_key = "cmd"
            self.alt_key = "option"
        else:  # Windows/Linux
            self.modifier_key = "ctrl"
            self.alt_key = "alt"
        
        # Adjust interaction speed based on system performance
        if HAS_GUI_TOOLS and pyautogui:
            if self.system_env.cpu_count < 4:
                pyautogui.PAUSE = 0.2
            elif self.system_env.memory_gb < 8:
                pyautogui.PAUSE = 0.15
    
    async def click_element(
        self, 
        element_description: Optional[str] = None, 
        coordinates: Optional[Dict[str, float]] = None,
        click_type: str = "single"
    ) -> str:
        """
        Click on a UI element by description or coordinates.
        
        Args:
            element_description: Description of element to click
            coordinates: Exact coordinates {"x": x, "y": y}
            click_type: Type of click (single, double, right)
            
        Returns:
            Success message or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            logger.info(f"Clicking element: {element_description}, coords: {coordinates}, type: {click_type}")
            
            # Determine click coordinates
            if coordinates:
                x, y = coordinates["x"], coordinates["y"]
            elif element_description:
                # Use AI-guided element detection (placeholder for future implementation)
                coords = await self._find_element_by_description(element_description)
                if coords:
                    x, y = coords
                else:
                    return f"Could not find element: {element_description}"
            else:
                return "Either element_description or coordinates must be provided"
            
            # Validate coordinates
            if not (0 <= x <= self.screen_width and 0 <= y <= self.screen_height):
                return f"Invalid coordinates: ({x}, {y}). Screen size: {self.screen_width}x{self.screen_height}"
            
            # Record interaction
            interaction_start = time.time()
            
            # Perform click based on type
            if click_type == "single":
                pyautogui.click(x, y)
            elif click_type == "double":
                pyautogui.doubleClick(x, y)
            elif click_type == "right":
                pyautogui.rightClick(x, y)
            else:
                return f"Invalid click type: {click_type}"
            
            # Wait for UI response
            await asyncio.sleep(0.2)
            
            # Record interaction
            self._record_interaction("click", {
                "element_description": element_description,
                "coordinates": {"x": x, "y": y},
                "click_type": click_type,
                "execution_time": time.time() - interaction_start
            })
            
            return f"Successfully clicked {click_type} at ({x}, {y})"
            
        except Exception as e:
            error_msg = f"Failed to click element: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _find_element_by_description(self, description: str) -> Optional[Tuple[float, float]]:
        """
        Find element coordinates by description using AI vision.
        This is a placeholder for future AI-guided element detection.
        """
        # For now, return None to indicate element not found
        # In the future, this would integrate with the visual monitor
        # to use AI to analyze the screen and find elements
        
        logger.debug(f"AI element detection not yet implemented for: {description}")
        return None
    
    async def type_text(
        self, 
        text: str, 
        speed: float = 0.05, 
        clear_first: bool = False
    ) -> str:
        """
        Type text in currently focused element.
        
        Args:
            text: Text to type
            speed: Typing speed (seconds between characters)
            clear_first: Clear field before typing
            
        Returns:
            Success message or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            logger.info(f"Typing text: '{text[:50]}...', speed: {speed}, clear: {clear_first}")
            
            interaction_start = time.time()
            
            # Clear field if requested
            if clear_first:
                # Select all and delete
                pyautogui.hotkey(self.modifier_key, 'a')
                await asyncio.sleep(0.1)
                pyautogui.press('delete')
                await asyncio.sleep(0.1)
            
            # Set typing interval
            original_pause = pyautogui.PAUSE
            pyautogui.PAUSE = speed
            
            # Type text character by character for better reliability
            for char in text:
                if char == '\n':
                    pyautogui.press('enter')
                elif char == '\t':
                    pyautogui.press('tab')
                else:
                    pyautogui.write(char)
                
                # Small delay for special characters
                if char in '!@#$%^&*()_+-=[]{}|;:,.<>?':
                    await asyncio.sleep(0.01)
            
            # Restore original pause
            pyautogui.PAUSE = original_pause
            
            # Record interaction
            self._record_interaction("type", {
                "text": text,
                "length": len(text),
                "speed": speed,
                "clear_first": clear_first,
                "execution_time": time.time() - interaction_start
            })
            
            return f"Successfully typed {len(text)} characters"
            
        except Exception as e:
            error_msg = f"Failed to type text: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def send_key(self, key: str, repeat: int = 1) -> str:
        """
        Send keyboard key or key combination.
        
        Args:
            key: Key to send (e.g., 'enter', 'ctrl+c', 'alt+tab')
            repeat: Number of times to repeat
            
        Returns:
            Success message or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            logger.info(f"Sending key: '{key}', repeat: {repeat}")
            
            interaction_start = time.time()
            
            for _ in range(repeat):
                # Parse key combination
                if '+' in key:
                    # Handle key combinations
                    keys = [k.strip() for k in key.split('+')]
                    
                    # Replace platform-agnostic modifiers
                    keys = [self.modifier_key if k == 'ctrl' else k for k in keys]
                    keys = [self.alt_key if k == 'alt' else k for k in keys]
                    
                    pyautogui.hotkey(*keys)
                else:
                    # Single key
                    pyautogui.press(key)
                
                # Small delay between repeats
                if repeat > 1:
                    await asyncio.sleep(0.1)
            
            # Record interaction
            self._record_interaction("key", {
                "key": key,
                "repeat": repeat,
                "execution_time": time.time() - interaction_start
            })
            
            return f"Successfully sent key '{key}' {repeat} time(s)"
            
        except Exception as e:
            error_msg = f"Failed to send key '{key}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def scroll(
        self, 
        direction: str, 
        amount: int = 3, 
        coordinates: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Scroll in a direction.
        
        Args:
            direction: Scroll direction (up, down, left, right)
            amount: Scroll amount (clicks)
            coordinates: Scroll at specific coordinates
            
        Returns:
            Success message or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            logger.info(f"Scrolling {direction}, amount: {amount}, coords: {coordinates}")
            
            interaction_start = time.time()
            
            # Determine scroll coordinates
            if coordinates:
                x, y = coordinates["x"], coordinates["y"]
            else:
                # Use center of screen
                x, y = self.screen_width // 2, self.screen_height // 2
            
            # Move mouse to scroll position
            pyautogui.moveTo(x, y)
            await asyncio.sleep(0.1)
            
            # Perform scroll based on direction
            if direction == "up":
                pyautogui.scroll(amount)
            elif direction == "down":
                pyautogui.scroll(-amount)
            elif direction == "left":
                # Horizontal scroll (shift + scroll)
                pyautogui.keyDown('shift')
                pyautogui.scroll(amount)
                pyautogui.keyUp('shift')
            elif direction == "right":
                pyautogui.keyDown('shift')
                pyautogui.scroll(-amount)
                pyautogui.keyUp('shift')
            else:
                return f"Invalid scroll direction: {direction}"
            
            # Record interaction
            self._record_interaction("scroll", {
                "direction": direction,
                "amount": amount,
                "coordinates": {"x": x, "y": y},
                "execution_time": time.time() - interaction_start
            })
            
            return f"Successfully scrolled {direction} {amount} clicks at ({x}, {y})"
            
        except Exception as e:
            error_msg = f"Failed to scroll {direction}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def drag_and_drop(
        self, 
        start_coords: Dict[str, float], 
        end_coords: Dict[str, float],
        duration: float = 1.0
    ) -> str:
        """
        Perform drag and drop operation.
        
        Args:
            start_coords: Starting coordinates {"x": x, "y": y}
            end_coords: Ending coordinates {"x": x, "y": y}
            duration: Duration of drag operation in seconds
            
        Returns:
            Success message or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            logger.info(f"Drag and drop from {start_coords} to {end_coords}")
            
            interaction_start = time.time()
            
            start_x, start_y = start_coords["x"], start_coords["y"]
            end_x, end_y = end_coords["x"], end_coords["y"]
            
            # Perform drag and drop
            pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
            
            # Record interaction
            self._record_interaction("drag_drop", {
                "start_coords": start_coords,
                "end_coords": end_coords,
                "duration": duration,
                "execution_time": time.time() - interaction_start
            })
            
            return f"Successfully dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"
            
        except Exception as e:
            error_msg = f"Failed to drag and drop: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def hover_element(
        self, 
        coordinates: Dict[str, float], 
        duration: float = 1.0
    ) -> str:
        """
        Hover over an element.
        
        Args:
            coordinates: Coordinates to hover over {"x": x, "y": y}
            duration: How long to hover in seconds
            
        Returns:
            Success message or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            logger.info(f"Hovering over {coordinates} for {duration}s")
            
            interaction_start = time.time()
            
            x, y = coordinates["x"], coordinates["y"]
            
            # Move mouse to coordinates
            pyautogui.moveTo(x, y, duration=0.5)
            
            # Hover for specified duration
            await asyncio.sleep(duration)
            
            # Record interaction
            self._record_interaction("hover", {
                "coordinates": coordinates,
                "duration": duration,
                "execution_time": time.time() - interaction_start
            })
            
            return f"Successfully hovered at ({x}, {y}) for {duration}s"
            
        except Exception as e:
            error_msg = f"Failed to hover: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def wait_for_element(
        self, 
        element_description: str, 
        timeout: float = 10.0
    ) -> str:
        """
        Wait for an element to appear on screen.
        
        Args:
            element_description: Description of element to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Success message or timeout error
        """
        try:
            logger.info(f"Waiting for element: {element_description}, timeout: {timeout}s")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if element exists (placeholder implementation)
                coords = await self._find_element_by_description(element_description)
                if coords:
                    wait_time = time.time() - start_time
                    return f"Element '{element_description}' appeared after {wait_time:.2f}s at {coords}"
                
                # Wait before next check
                await asyncio.sleep(0.5)
            
            return f"Timeout waiting for element '{element_description}' after {timeout}s"
            
        except Exception as e:
            error_msg = f"Failed to wait for element: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _record_interaction(self, interaction_type: str, details: Dict[str, Any]) -> None:
        """Record interaction for history and learning."""
        
        record = {
            "timestamp": time.time(),
            "type": interaction_type,
            "details": details,
            "system": {
                "os": self.system_env.os,
                "screen_size": f"{self.screen_width}x{self.screen_height}"
            }
        }
        
        self.interaction_history.append(record)
        
        # Limit history size
        if len(self.interaction_history) > 1000:
            self.interaction_history = self.interaction_history[-500:]
    
    async def get_screen_coordinates(self) -> str:
        """Get current screen dimensions and mouse position."""
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            mouse_x, mouse_y = pyautogui.position()
            
            return {
                "screen_size": {
                    "width": self.screen_width,
                    "height": self.screen_height
                },
                "mouse_position": {
                    "x": mouse_x,
                    "y": mouse_y
                },
                "center": {
                    "x": self.screen_width // 2,
                    "y": self.screen_height // 2
                }
            }
            
        except Exception as e:
            return f"Failed to get coordinates: {str(e)}"
    
    async def take_element_screenshot(
        self, 
        coordinates: Dict[str, float], 
        width: int, 
        height: int
    ) -> str:
        """
        Take screenshot of specific element region.
        
        Args:
            coordinates: Top-left coordinates of region
            width: Width of region
            height: Height of region
            
        Returns:
            Screenshot info or error
        """
        if not HAS_GUI_TOOLS or not pyautogui:
            return "UI interaction tools not available - pyautogui not installed or display not accessible"
            
        try:
            x, y = coordinates["x"], coordinates["y"]
            
            # Take screenshot of region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # Save screenshot (optional)
            filename = f"element_{int(time.time())}.png"
            screenshot_path = self.settings.get_data_paths()["screenshots"] / filename
            screenshot.save(screenshot_path)
            
            return f"Element screenshot saved: {screenshot_path}"
            
        except Exception as e:
            return f"Failed to take element screenshot: {str(e)}"
    
    def get_interaction_stats(self) -> Dict[str, Any]:
        """Get UI interaction statistics."""
        if not self.interaction_history:
            return {"total_interactions": 0}
        
        interaction_types = {}
        total_time = 0
        
        for record in self.interaction_history:
            interaction_type = record["type"]
            interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
            total_time += record["details"].get("execution_time", 0)
        
        return {
            "total_interactions": len(self.interaction_history),
            "interaction_types": interaction_types,
            "total_execution_time": round(total_time, 2),
            "average_time_per_interaction": round(total_time / len(self.interaction_history), 3),
            "screen_size": f"{self.screen_width}x{self.screen_height}",
            "os": self.system_env.os
        }