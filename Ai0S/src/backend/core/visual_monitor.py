"""
Visual State Monitor - Screenshot capture and LLM analysis
Provides real-time screen analysis and change detection using AI vision.
"""

import asyncio
import base64
import hashlib
import io
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyautogui
import cv2

from ...backend.models.ai_models import ScreenAnalysis, get_ai_models
from ...utils.platform_detector import get_system_environment, get_automation_config
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class ScreenState:
    """Complete screen state information."""
    timestamp: datetime
    screenshot_data: bytes
    screenshot_hash: str
    analysis: Optional[ScreenAnalysis] = None
    change_score: float = 0.0
    previous_state_hash: Optional[str] = None
    detected_changes: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class ChangeDetection:
    """Screen change detection results."""
    has_significant_change: bool
    change_score: float
    changed_regions: List[Dict[str, Any]]
    change_type: str  # "minor", "major", "application_change", "popup", "dialog"
    description: str


class OptimizedScreenCapture:
    """Optimized screenshot capturing with change detection."""
    
    def __init__(self):
        self.settings = get_settings()
        self.automation_config = get_automation_config()
        self.cache = {}
        self.last_full_capture = None
        self.last_capture_time = 0
        self.capture_count = 0
        
        # Configure PyAutoGUI for cross-platform support
        pyautogui.FAILSAFE = False  # Disable failsafe for automation
        
        # Platform-specific optimizations
        self._setup_platform_capture()
    
    def _setup_platform_capture(self) -> None:
        """Setup platform-specific screenshot optimizations."""
        system_env = get_system_environment()
        
        if system_env.os == "Linux":
            if system_env.display_server == "wayland":
                logger.info("Using Wayland-compatible screenshot method")
                # Wayland requires special handling
                self.use_wayland = True
            else:
                logger.info("Using X11 screenshot method")
                self.use_wayland = False
        elif system_env.os == "Windows":
            logger.info("Using Windows native screenshot method")
        elif system_env.os == "Darwin":
            logger.info("Using macOS screenshot method")
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> bytes:
        """
        Capture screenshot with platform-specific optimizations.
        
        Args:
            region: (x, y, width, height) region to capture, None for full screen
            
        Returns:
            Screenshot data as bytes
        """
        try:
            self.capture_count += 1
            start_time = time.time()
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to bytes with quality optimization
            img_buffer = io.BytesIO()
            screenshot.save(
                img_buffer,
                format='PNG',
                optimize=True,
                compress_level=int((1 - self.settings.SCREENSHOT_QUALITY) * 9)
            )
            screenshot_data = img_buffer.getvalue()
            
            capture_time = time.time() - start_time
            logger.debug(f"Screenshot captured in {capture_time:.3f}s, size: {len(screenshot_data)} bytes")
            
            self.last_full_capture = screenshot_data
            self.last_capture_time = time.time()
            
            return screenshot_data
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            raise
    
    def intelligent_capture(self, force_full: bool = False) -> bytes:
        """
        Smart screenshot capturing with change detection optimization.
        
        Args:
            force_full: Force a full screenshot regardless of cache
            
        Returns:
            Screenshot data as bytes
        """
        current_time = time.time()
        
        # Check if we need a new capture
        if (force_full or 
            self.last_full_capture is None or 
            current_time - self.last_capture_time > 1.0 or  # Max 1 second cache
            self.should_capture_full()):
            
            return self.capture_screen()
        else:
            # Return cached screenshot
            logger.debug("Using cached screenshot")
            return self.last_full_capture
    
    def should_capture_full(self) -> bool:
        """
        Determine if a full capture is needed using quick pixel sampling.
        
        Returns:
            True if significant screen change detected
        """
        try:
            if self.capture_count % 10 == 0:  # Force full capture every 10 calls
                return True
            
            # Quick pixel sampling to detect changes
            sample_pixels = self._sample_screen_pixels()
            if not hasattr(self, '_last_sample'):
                self._last_sample = sample_pixels
                return True
            
            # Compare with previous sample
            change_detected = self._detect_significant_change(sample_pixels)
            self._last_sample = sample_pixels
            
            return change_detected
            
        except Exception as e:
            logger.debug(f"Change detection failed, forcing full capture: {e}")
            return True
    
    def _sample_screen_pixels(self) -> np.ndarray:
        """Sample a small grid of pixels for change detection."""
        try:
            # Capture a small region for sampling
            small_screenshot = pyautogui.screenshot(region=(0, 0, 200, 200))
            return np.array(small_screenshot)
        except:
            # Fallback to empty array if sampling fails
            return np.array([])
    
    def _detect_significant_change(self, current_sample: np.ndarray) -> bool:
        """Detect if there's a significant change in the sampled pixels."""
        try:
            if self._last_sample.size == 0 or current_sample.size == 0:
                return True
            
            if self._last_sample.shape != current_sample.shape:
                return True
            
            # Calculate pixel difference
            diff = np.abs(current_sample.astype(float) - self._last_sample.astype(float))
            change_percentage = np.mean(diff) / 255.0
            
            # Threshold for significant change
            threshold = 0.05  # 5% change threshold
            return change_percentage > threshold
            
        except Exception as e:
            logger.debug(f"Change calculation failed: {e}")
            return True


class VisualStateMonitor:
    """Advanced visual state monitoring with AI analysis."""
    
    def __init__(self):
        self.settings = get_settings()
        self.screen_capture = OptimizedScreenCapture()
        self.previous_state: Optional[ScreenState] = None
        self.state_history: List[ScreenState] = []
        self.change_threshold = 0.1
        
        # AI models for analysis
        self.ai_models = None
        
        # Performance tracking
        self.analysis_times = []
        self.capture_times = []
    
    async def initialize(self) -> None:
        """Initialize the visual monitor with AI models."""
        try:
            self.ai_models = await get_ai_models()
            logger.info("Visual State Monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Visual State Monitor: {e}")
            raise
    
    async def capture_and_analyze(self, force_analysis: bool = False) -> ScreenState:
        """
        Capture screenshot and perform AI analysis.
        
        Args:
            force_analysis: Force AI analysis even if screen hasn't changed much
            
        Returns:
            ScreenState with analysis results
        """
        start_time = time.time()
        
        try:
            # Capture screenshot
            screenshot_data = self.screen_capture.intelligent_capture()
            screenshot_hash = hashlib.md5(screenshot_data).hexdigest()
            
            # Create initial screen state
            current_state = ScreenState(
                timestamp=datetime.now(),
                screenshot_data=screenshot_data,
                screenshot_hash=screenshot_hash,
                previous_state_hash=self.previous_state.screenshot_hash if self.previous_state else None
            )
            
            # Detect changes
            if self.previous_state:
                change_detection = await self._detect_changes(current_state, self.previous_state)
                current_state.change_score = change_detection.change_score
                current_state.detected_changes = change_detection.changed_regions
            
            # Perform AI analysis if needed
            should_analyze = (
                force_analysis or
                self.previous_state is None or
                current_state.change_score > self.change_threshold or
                len(current_state.detected_changes) > 0
            )
            
            if should_analyze and self.ai_models:
                logger.debug("Performing AI screen analysis")
                analysis_start = time.time()
                
                current_state.analysis = await self.ai_models.analyze_screen(screenshot_data)
                current_state.confidence_score = current_state.analysis.confidence_score
                
                analysis_time = time.time() - analysis_start
                self.analysis_times.append(analysis_time)
                logger.debug(f"AI analysis completed in {analysis_time:.3f}s")
            
            # Update state history
            self.previous_state = current_state
            self.state_history.append(current_state)
            
            # Limit history size
            if len(self.state_history) > 100:
                self.state_history = self.state_history[-50:]
            
            capture_time = time.time() - start_time
            self.capture_times.append(capture_time)
            
            logger.debug(f"Screen capture and analysis completed in {capture_time:.3f}s")
            return current_state
            
        except Exception as e:
            logger.error(f"Screen capture and analysis failed: {e}")
            # Return basic state without analysis
            return ScreenState(
                timestamp=datetime.now(),
                screenshot_data=b"",
                screenshot_hash="error",
                change_score=1.0  # Indicate significant change due to error
            )
    
    async def _detect_changes(self, current: ScreenState, previous: ScreenState) -> ChangeDetection:
        """
        Detect changes between current and previous screen states.
        
        Args:
            current: Current screen state
            previous: Previous screen state
            
        Returns:
            ChangeDetection results
        """
        try:
            # Hash-based change detection
            if current.screenshot_hash == previous.screenshot_hash:
                return ChangeDetection(
                    has_significant_change=False,
                    change_score=0.0,
                    changed_regions=[],
                    change_type="none",
                    description="No changes detected"
                )
            
            # Image-based change detection using OpenCV
            current_img = self._bytes_to_cv2(current.screenshot_data)
            previous_img = self._bytes_to_cv2(previous.screenshot_data)
            
            if current_img is None or previous_img is None:
                return ChangeDetection(
                    has_significant_change=True,
                    change_score=1.0,
                    changed_regions=[],
                    change_type="unknown",
                    description="Could not compare images"
                )
            
            # Resize images if necessary for comparison
            if current_img.shape != previous_img.shape:
                min_height = min(current_img.shape[0], previous_img.shape[0])
                min_width = min(current_img.shape[1], previous_img.shape[1])
                current_img = cv2.resize(current_img, (min_width, min_height))
                previous_img = cv2.resize(previous_img, (min_width, min_height))
            
            # Calculate difference
            diff = cv2.absdiff(current_img, previous_img)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Calculate change score
            change_score = np.mean(gray_diff) / 255.0
            
            # Find significant change regions
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            changed_regions = []
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Filter small changes
                    x, y, w, h = cv2.boundingRect(contour)
                    changed_regions.append({
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                        "area": int(cv2.contourArea(contour))
                    })
            
            # Classify change type
            change_type = self._classify_change_type(change_score, changed_regions)
            
            return ChangeDetection(
                has_significant_change=change_score > self.change_threshold,
                change_score=change_score,
                changed_regions=changed_regions,
                change_type=change_type,
                description=f"{change_type.title()} change detected with score {change_score:.3f}"
            )
            
        except Exception as e:
            logger.error(f"Change detection failed: {e}")
            return ChangeDetection(
                has_significant_change=True,
                change_score=1.0,
                changed_regions=[],
                change_type="error",
                description=f"Change detection failed: {e}"
            )
    
    def _bytes_to_cv2(self, image_data: bytes) -> Optional[np.ndarray]:
        """Convert bytes to OpenCV image."""
        try:
            if not image_data:
                return None
            
            # Convert bytes to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            # Convert to OpenCV format (BGR)
            cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return cv2_image
            
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            return None
    
    def _classify_change_type(self, change_score: float, regions: List[Dict]) -> str:
        """Classify the type of change based on score and regions."""
        if change_score < 0.05:
            return "minor"
        elif change_score < 0.2:
            return "moderate"
        elif change_score < 0.5:
            return "major"
        else:
            return "significant"
    
    async def detect_plan_disruption(self, expected_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect if something unexpected appeared that might disrupt the plan.
        
        Args:
            expected_state: What was expected to be on screen
            
        Returns:
            List of disruptions found
        """
        if not self.previous_state or not self.previous_state.analysis:
            return []
        
        disruptions = []
        analysis = self.previous_state.analysis
        
        # Check for unexpected elements
        for element in analysis.unexpected_elements:
            disruption_type = element.get("type", "unknown")
            if disruption_type in ["popup", "dialog", "notification", "error"]:
                disruptions.append({
                    "type": disruption_type,
                    "action": "handle_" + disruption_type,
                    "description": element.get("description", "Unexpected element detected"),
                    "suggested_response": self._get_disruption_response(disruption_type)
                })
        
        return disruptions
    
    def _get_disruption_response(self, disruption_type: str) -> str:
        """Get suggested response for disruption type."""
        responses = {
            "popup": "Click close button or press Escape",
            "dialog": "Read dialog and take appropriate action",
            "notification": "Dismiss notification if not critical",
            "error": "Handle error message and retry or adapt plan"
        }
        return responses.get(disruption_type, "Manual intervention required")
    
    def save_screenshot(self, filename: Optional[str] = None) -> Path:
        """
        Save the current screenshot to file.
        
        Args:
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to saved screenshot
        """
        if not self.previous_state or not self.previous_state.screenshot_data:
            raise ValueError("No screenshot data available to save")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        screenshot_path = Path(self.settings.SCREENSHOT_DIR) / filename
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(screenshot_path, "wb") as f:
            f.write(self.previous_state.screenshot_data)
        
        logger.info(f"Screenshot saved to {screenshot_path}")
        return screenshot_path
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the monitor."""
        return {
            "total_captures": len(self.capture_times),
            "avg_capture_time": np.mean(self.capture_times) if self.capture_times else 0,
            "avg_analysis_time": np.mean(self.analysis_times) if self.analysis_times else 0,
            "total_analyses": len(self.analysis_times),
            "states_in_history": len(self.state_history),
            "last_change_score": self.previous_state.change_score if self.previous_state else 0
        }
    
    async def get_current_screen_info(self) -> Dict[str, Any]:
        """Get comprehensive information about current screen state."""
        current_state = await self.capture_and_analyze(force_analysis=True)
        
        info = {
            "timestamp": current_state.timestamp.isoformat(),
            "has_analysis": current_state.analysis is not None,
            "change_score": current_state.change_score,
            "confidence_score": current_state.confidence_score,
        }
        
        if current_state.analysis:
            info.update({
                "applications": current_state.analysis.applications,
                "ui_elements_count": len(current_state.analysis.ui_elements),
                "clickable_elements_count": len(current_state.analysis.clickable_elements),
                "text_content_lines": len(current_state.analysis.text_content),
                "unexpected_elements": current_state.analysis.unexpected_elements,
                "recommendations": current_state.analysis.recommendations
            })
        
        return info


# Global visual monitor instance
_visual_monitor: Optional[VisualStateMonitor] = None


async def get_visual_monitor() -> VisualStateMonitor:
    """Get global visual monitor instance."""
    global _visual_monitor
    if _visual_monitor is None:
        _visual_monitor = VisualStateMonitor()
        await _visual_monitor.initialize()
    return _visual_monitor


if __name__ == "__main__":
    # Test the visual monitor
    async def test_monitor():
        monitor = await get_visual_monitor()
        
        print("=== Testing Visual State Monitor ===")
        state = await monitor.capture_and_analyze(force_analysis=True)
        
        print(f"Timestamp: {state.timestamp}")
        print(f"Screenshot size: {len(state.screenshot_data)} bytes")
        print(f"Change score: {state.change_score}")
        print(f"Confidence: {state.confidence_score}")
        
        if state.analysis:
            print(f"Applications: {state.analysis.applications}")
            print(f"UI elements: {len(state.analysis.ui_elements)}")
            print(f"Clickable elements: {len(state.analysis.clickable_elements)}")
        
        # Save screenshot for testing
        screenshot_path = monitor.save_screenshot()
        print(f"Screenshot saved: {screenshot_path}")
        
        # Performance stats
        stats = monitor.get_performance_stats()
        print(f"Performance: {stats}")
    
    asyncio.run(test_monitor())