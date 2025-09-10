"""
Web Element Detector - Dynamic website element detection using Playwright
Provides AI with real-time access to DOM elements for intelligent clicking and interaction.
"""

import asyncio
import logging
import json
import time
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, ElementHandle
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    async_playwright = None

from ...config.settings import get_settings
from ...utils.platform_detector import get_system_environment

logger = logging.getLogger(__name__)


@dataclass
class WebElement:
    """Represents a detectable web element."""
    element_id: str
    tag_name: str
    text_content: str
    inner_text: str
    href: Optional[str]
    src: Optional[str]
    alt: Optional[str]
    title: Optional[str]
    role: Optional[str]
    aria_label: Optional[str]
    class_list: List[str]
    bounding_box: Dict[str, float]  # {x, y, width, height}
    clickable: bool
    visible: bool
    element_type: str  # button, link, video, image, form, etc.
    confidence_score: float


@dataclass
class PageAnalysis:
    """Complete analysis of a web page."""
    url: str
    title: str
    timestamp: str
    elements: List[WebElement]
    total_elements: int
    clickable_elements: int
    interactive_elements: int
    screenshot_path: Optional[str]
    page_type: str  # youtube, github, social, ecommerce, etc.


class WebElementDetector:
    """
    Web Element Detector using Playwright for universal website interaction.
    
    Features:
    - Real-time DOM element detection
    - Smart element classification (videos, buttons, links, forms)
    - Screenshot capture with element overlay
    - Context-aware element selection
    - Cross-browser support
    """
    
    def __init__(self):
        self.system_env = get_system_environment()
        self.settings = get_settings()
        
        # Playwright instances
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Session tracking
        self.current_url: Optional[str] = None
        self.page_history: List[PageAnalysis] = []
        
        # Element detection configuration
        self.element_selectors = {
            'video': ['video', '[data-testid*="video"]', '.video-thumbnail', '[href*="watch"]'],
            'button': ['button', '[role="button"]', '.btn', '.button', 'input[type="submit"]'],
            'link': ['a[href]', '[role="link"]'],
            'image': ['img', '[role="img"]'],
            'form': ['form', '[role="form"]'],
            'input': ['input', 'textarea', 'select', '[role="textbox"]'],
            'navigation': ['nav', '[role="navigation"]', '.nav', '.navbar'],
            'content': ['article', '[role="article"]', '.content', '.post']
        }
        
        # Page type detection patterns
        self.page_patterns = {
            'youtube': ['youtube.com', 'youtu.be'],
            'github': ['github.com', 'githubusercontent.com'],
            'social': ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com'],
            'ecommerce': ['amazon.com', 'ebay.com', 'shopify', 'store', 'shop'],
            'news': ['news', 'bbc.com', 'cnn.com', 'reuters.com'],
            'search': ['google.com/search', 'bing.com', 'duckduckgo.com']
        }
        
        # Screenshots directory
        self.screenshots_dir = self.settings.get_data_paths()["screenshots"]
        self.screenshots_dir.mkdir(exist_ok=True)
    
    async def initialize_browser(self, headless: bool = False) -> bool:
        """Initialize Playwright browser instance."""
        if not HAS_PLAYWRIGHT:
            logger.error("Playwright not available - install with: pip install playwright && playwright install chromium")
            return False
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            # Create context
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            logger.info("Playwright browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {e}")
            return False
    
    async def navigate_to_url(self, url: str, wait_for: str = "load") -> bool:
        """Navigate to a URL and wait for page load."""
        if not self.page:
            if not await self.initialize_browser():
                return False
        
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            
            logger.info(f"Navigating to: {url}")
            
            # Navigate with timeout
            await self.page.goto(url, wait_until=wait_for, timeout=30000)
            
            # Wait for dynamic content
            await asyncio.sleep(2)
            
            self.current_url = url
            logger.info(f"Successfully navigated to: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    async def analyze_current_page(self, take_screenshot: bool = True) -> Optional[PageAnalysis]:
        """Analyze the current page and detect all interactive elements."""
        if not self.page or not self.current_url:
            logger.error("No active page to analyze")
            return None
        
        try:
            logger.info(f"Analyzing page: {self.current_url}")
            
            # Get page info
            page_title = await self.page.title()
            page_type = self._detect_page_type(self.current_url)
            
            # Detect all elements
            elements = await self._detect_elements()
            
            # Take screenshot if requested
            screenshot_path = None
            if take_screenshot:
                screenshot_path = await self._take_screenshot_with_overlay(elements)
            
            # Create analysis
            analysis = PageAnalysis(
                url=self.current_url,
                title=page_title,
                timestamp=datetime.now().isoformat(),
                elements=elements,
                total_elements=len(elements),
                clickable_elements=len([e for e in elements if e.clickable]),
                interactive_elements=len([e for e in elements if e.clickable or e.element_type in ['input', 'form']]),
                screenshot_path=screenshot_path,
                page_type=page_type
            )
            
            # Store in history
            self.page_history.append(analysis)
            
            logger.info(f"Page analysis complete: {len(elements)} elements found ({analysis.clickable_elements} clickable)")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze page: {e}")
            return None
    
    async def _detect_elements(self) -> List[WebElement]:
        """Detect all interactive elements on the current page."""
        elements = []
        
        try:
            # Get all potentially interactive elements
            selectors_to_check = [
                'a', 'button', 'input', 'textarea', 'select', 'video', 'img',
                '[role="button"]', '[role="link"]', '[onclick]', '[href]',
                '.video-thumbnail', '[data-testid*="video"]',
                '.btn', '.button', '.clickable'
            ]
            
            for selector in selectors_to_check:
                try:
                    page_elements = await self.page.query_selector_all(selector)
                    
                    for i, element in enumerate(page_elements):
                        web_element = await self._analyze_element(element, f"{selector}_{i}")
                        if web_element:
                            elements.append(web_element)
                            
                except Exception as e:
                    logger.debug(f"Error processing selector {selector}: {e}")
                    continue
            
            # Remove duplicates based on position
            elements = self._deduplicate_elements(elements)
            
            # Sort by relevance/visibility
            elements.sort(key=lambda x: (-x.confidence_score, -x.bounding_box['width'] * x.bounding_box['height']))
            
            return elements
            
        except Exception as e:
            logger.error(f"Error detecting elements: {e}")
            return []
    
    async def _analyze_element(self, element: ElementHandle, element_id: str) -> Optional[WebElement]:
        """Analyze a single DOM element."""
        try:
            # Get element properties
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            text_content = (await element.text_content() or "").strip()
            inner_text = (await element.inner_text() or "").strip()
            
            # Get attributes
            href = await element.get_attribute('href')
            src = await element.get_attribute('src')
            alt = await element.get_attribute('alt')
            title = await element.get_attribute('title')
            role = await element.get_attribute('role')
            aria_label = await element.get_attribute('aria-label')
            class_attr = await element.get_attribute('class')
            
            # Get bounding box
            bbox = await element.bounding_box()
            if not bbox:
                return None  # Element not visible
            
            # Check visibility and clickability
            visible = await element.is_visible()
            enabled = await element.is_enabled()
            
            # Determine element type and clickability
            element_type, clickable = self._classify_element(
                tag_name, href, src, role, class_attr, text_content
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                element_type, visible, enabled, text_content, bbox
            )
            
            return WebElement(
                element_id=element_id,
                tag_name=tag_name,
                text_content=text_content[:200],  # Limit text length
                inner_text=inner_text[:200],
                href=href,
                src=src,
                alt=alt,
                title=title,
                role=role,
                aria_label=aria_label,
                class_list=class_attr.split() if class_attr else [],
                bounding_box={
                    'x': bbox['x'],
                    'y': bbox['y'], 
                    'width': bbox['width'],
                    'height': bbox['height']
                },
                clickable=clickable and enabled,
                visible=visible,
                element_type=element_type,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.debug(f"Error analyzing element {element_id}: {e}")
            return None
    
    def _classify_element(
        self, 
        tag_name: str, 
        href: Optional[str], 
        src: Optional[str], 
        role: Optional[str], 
        class_attr: Optional[str],
        text_content: str
    ) -> Tuple[str, bool]:
        """Classify element type and determine if it's clickable."""
        
        # Video elements
        if (tag_name == 'video' or 
            'video' in (class_attr or '') or 
            'thumbnail' in (class_attr or '') or
            (href and 'watch' in href)):
            return 'video', True
        
        # Button elements
        if (tag_name == 'button' or 
            role == 'button' or 
            'btn' in (class_attr or '') or
            'button' in (class_attr or '')):
            return 'button', True
        
        # Link elements
        if tag_name == 'a' and href:
            return 'link', True
        
        # Form inputs
        if tag_name in ['input', 'textarea', 'select']:
            return 'input', True
        
        # Images
        if tag_name == 'img' or role == 'img':
            return 'image', bool(href)  # Clickable if has href
        
        # Generic clickable elements
        if (role in ['button', 'link'] or 
            'click' in (class_attr or '') or
            'interactive' in (class_attr or '')):
            return 'interactive', True
        
        return 'element', False
    
    def _calculate_confidence_score(
        self, 
        element_type: str, 
        visible: bool, 
        enabled: bool, 
        text_content: str,
        bbox: Dict[str, float]
    ) -> float:
        """Calculate confidence score for element relevance."""
        
        score = 0.0
        
        # Base scores by type
        type_scores = {
            'video': 0.9,
            'button': 0.8,
            'link': 0.7,
            'image': 0.6,
            'input': 0.7,
            'interactive': 0.6,
            'element': 0.3
        }
        score += type_scores.get(element_type, 0.1)
        
        # Visibility bonus
        if visible:
            score += 0.2
        
        # Enabled bonus
        if enabled:
            score += 0.1
        
        # Text content bonus
        if text_content and len(text_content.strip()) > 0:
            score += 0.1
            if len(text_content.strip()) > 5:
                score += 0.05
        
        # Size bonus (reasonable size elements)
        area = bbox['width'] * bbox['height']
        if 100 < area < 50000:  # Not too small, not too large
            score += 0.1
        
        return min(score, 1.0)
    
    def _deduplicate_elements(self, elements: List[WebElement]) -> List[WebElement]:
        """Remove duplicate elements based on position overlap."""
        unique_elements = []
        
        for element in elements:
            is_duplicate = False
            
            for existing in unique_elements:
                # Check if bounding boxes overlap significantly
                overlap = self._calculate_bbox_overlap(
                    element.bounding_box, 
                    existing.bounding_box
                )
                
                if overlap > 0.8:  # 80% overlap threshold
                    # Keep the one with higher confidence
                    if element.confidence_score > existing.confidence_score:
                        unique_elements.remove(existing)
                        unique_elements.append(element)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_elements.append(element)
        
        return unique_elements
    
    def _calculate_bbox_overlap(self, bbox1: Dict[str, float], bbox2: Dict[str, float]) -> float:
        """Calculate overlap ratio between two bounding boxes."""
        
        # Calculate intersection
        x_overlap = max(0, min(bbox1['x'] + bbox1['width'], bbox2['x'] + bbox2['width']) - 
                          max(bbox1['x'], bbox2['x']))
        y_overlap = max(0, min(bbox1['y'] + bbox1['height'], bbox2['y'] + bbox2['height']) - 
                          max(bbox1['y'], bbox2['y']))
        
        intersection_area = x_overlap * y_overlap
        
        # Calculate union
        area1 = bbox1['width'] * bbox1['height']
        area2 = bbox2['width'] * bbox2['height']
        union_area = area1 + area2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
    
    def _detect_page_type(self, url: str) -> str:
        """Detect the type of website based on URL."""
        url_lower = url.lower()
        
        for page_type, patterns in self.page_patterns.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return page_type
        
        return 'general'
    
    async def _take_screenshot_with_overlay(self, elements: List[WebElement]) -> Optional[str]:
        """Take screenshot with element overlay for AI visualization."""
        try:
            timestamp = int(time.time())
            screenshot_path = self.screenshots_dir / f"page_analysis_{timestamp}.png"
            
            # Take full page screenshot
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            
            logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    async def click_element_by_coordinates(self, x: float, y: float) -> bool:
        """Click element at specific coordinates."""
        if not self.page:
            return False
        
        try:
            await self.page.mouse.click(x, y)
            await asyncio.sleep(1)  # Wait for potential navigation
            logger.info(f"Clicked coordinates ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click coordinates ({x}, {y}): {e}")
            return False
    
    async def click_element_by_text(self, text: str, exact: bool = False) -> bool:
        """Click element by visible text."""
        if not self.page:
            return False
        
        try:
            if exact:
                await self.page.click(f'text="{text}"')
            else:
                await self.page.click(f'text={text}')
            
            await asyncio.sleep(1)
            logger.info(f"Clicked element with text: {text}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click element with text '{text}': {e}")
            return False
    
    async def get_clickable_elements_by_type(self, element_type: str) -> List[WebElement]:
        """Get all clickable elements of a specific type."""
        analysis = await self.analyze_current_page(take_screenshot=False)
        
        if not analysis:
            return []
        
        return [
            elem for elem in analysis.elements 
            if elem.element_type == element_type and elem.clickable
        ]
    
    async def close_browser(self):
        """Close the browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("Browser closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def get_page_history(self) -> List[PageAnalysis]:
        """Get history of analyzed pages."""
        return self.page_history.copy()
    
    def get_current_page_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of current page state."""
        if not self.page_history:
            return None
        
        latest = self.page_history[-1]
        
        return {
            "url": latest.url,
            "title": latest.title,
            "page_type": latest.page_type,
            "total_elements": latest.total_elements,
            "clickable_elements": latest.clickable_elements,
            "top_elements": [
                {
                    "type": elem.element_type,
                    "text": elem.inner_text[:50],
                    "confidence": elem.confidence_score
                }
                for elem in latest.elements[:5]
            ]
        }