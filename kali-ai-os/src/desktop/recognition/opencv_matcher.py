import logging
import os
import tempfile
from typing import Any

import cv2
import numpy as np


class OpenCVMatcher:
    """OpenCV-based template matching for GUI elements"""

    def __init__(self) -> None:
        self.matching_methods = [
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_CCORR_NORMED,
            cv2.TM_SQDIFF_NORMED,
        ]

        # Element type confidence thresholds
        self.confidence_thresholds = {
            'button': 0.85,
            'text': 0.75,
            'menu': 0.80,
            'tab': 0.82,
            'dialog': 0.78,
            'icon': 0.88,
        }

        self.logger = logging.getLogger(__name__)

    def find_template(
        self, screenshot: str, template: str, confidence: float = 0.8
    ) -> dict[str, Any]:
        """Find template in screenshot using OpenCV"""
        try:
            # Load images
            img = cv2.imread(screenshot, cv2.IMREAD_COLOR)
            template_img = cv2.imread(template, cv2.IMREAD_COLOR)

            if img is None:
                return {
                    'found': False,
                    'error': f'Could not load screenshot: {screenshot}',
                }

            if template_img is None:
                return {'found': False, 'error': f'Could not load template: {template}'}

            # Convert to grayscale for better matching
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

            # Perform template matching
            result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # Check if confidence meets threshold
            if max_val >= confidence:
                return {
                    'found': True,
                    'confidence': float(max_val),
                    'location': max_loc,
                    'size': (
                        template_img.shape[1],
                        template_img.shape[0],
                    ),  # width, height
                    'center': (
                        max_loc[0] + template_img.shape[1] // 2,
                        max_loc[1] + template_img.shape[0] // 2,
                    ),
                }
            else:
                return {
                    'found': False,
                    'confidence': float(max_val),
                    'location': None,
                    'required_confidence': confidence,
                }

        except Exception as e:
            self.logger.error(f"Template matching failed: {e}")
            return {'found': False, 'error': str(e)}

    def find_multiple_templates(
        self, screenshot: str, templates: list[str], confidence: float = 0.8
    ) -> list[dict[str, Any]]:
        """Find multiple templates in a single screenshot"""
        results = []

        for template in templates:
            result = self.find_template(screenshot, template, confidence)
            result['template_path'] = template
            results.append(result)

        return results

    def find_all_instances(
        self, screenshot: str, template: str, confidence: float = 0.8
    ) -> list[dict[str, Any]]:
        """Find all instances of a template in screenshot"""
        try:
            img = cv2.imread(screenshot, cv2.IMREAD_COLOR)
            template_img = cv2.imread(template, cv2.IMREAD_COLOR)

            if img is None or template_img is None:
                return []

            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

            # Template matching
            result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)

            # Find all locations where confidence > threshold
            locations = np.where(result >= confidence)
            instances = []

            for pt in zip(*locations[::-1], strict=False):
                instances.append(
                    {
                        'found': True,
                        'confidence': float(result[pt[1], pt[0]]),
                        'location': pt,
                        'size': (template_img.shape[1], template_img.shape[0]),
                        'center': (
                            pt[0] + template_img.shape[1] // 2,
                            pt[1] + template_img.shape[0] // 2,
                        ),
                    }
                )

            return instances

        except Exception as e:
            self.logger.error(f"Multiple instance matching failed: {e}")
            return []

    def preprocess_screenshot(self, screenshot_path: str) -> np.ndarray | None:
        """Preprocess screenshot for better matching"""
        try:
            img = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
            if img is None:
                return None

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(img, (3, 3), 0)

            # Enhance contrast
            lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)
            enhanced = cv2.merge([l_channel, a_channel, b_channel])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            return enhanced

        except Exception as e:
            self.logger.error(f"Screenshot preprocessing failed: {e}")
            return None

    def find_in_region(
        self,
        screenshot: str,
        template: str,
        region: dict[str, int],
        confidence: float = 0.8,
    ) -> dict[str, Any] | None:
        """Find template in specific screen region"""
        try:
            img = cv2.imread(screenshot, cv2.IMREAD_COLOR)
            if img is None:
                return None

            # Extract region of interest
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            roi = img[y : y + h, x : x + w]

            # Save ROI temporarily
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                roi_path = tmpfile.name
            cv2.imwrite(roi_path, roi)

            # Find template in ROI
            result = self.find_template(roi_path, template, confidence)

            # Adjust coordinates to full screen
            if result.get('found'):
                result['location'] = (
                    result['location'][0] + x,
                    result['location'][1] + y,
                )
                result['center'] = (result['center'][0] + x, result['center'][1] + y)

            # Clean up
            if os.path.exists(roi_path):
                os.remove(roi_path)

            return result

        except Exception as e:
            self.logger.error(f"Region-based matching failed: {e}")
            return None

    def get_adaptive_threshold(self, element_type: str) -> float:
        """Get adaptive confidence threshold based on element type"""
        return self.confidence_thresholds.get(element_type, 0.8)

    def classify_element(self, template_path: str) -> dict[str, Any]:
        """Classify GUI element type based on template filename"""
        filename = os.path.basename(template_path).lower()

        # Simple classification based on filename
        if 'button' in filename:
            element_type = 'button'
        elif 'text' in filename or 'field' in filename:
            element_type = 'text'
        elif 'menu' in filename:
            element_type = 'menu'
        elif 'tab' in filename:
            element_type = 'tab'
        elif 'dialog' in filename:
            element_type = 'dialog'
        elif 'icon' in filename:
            element_type = 'icon'
        else:
            element_type = 'unknown'

        return {
            'element_type': element_type,
            'confidence_threshold': self.get_adaptive_threshold(element_type),
            'found': True,  # Classification always succeeds
        }

    def detect_element_state(self, template_path: str) -> str:
        """Detect element state from template filename or analysis"""
        filename = os.path.basename(template_path).lower()

        if 'disabled' in filename:
            return 'disabled'
        elif 'enabled' in filename:
            return 'enabled'
        elif 'checked' in filename:
            return 'checked'
        elif 'unchecked' in filename:
            return 'unchecked'
        elif 'focused' in filename:
            return 'focused'
        else:
            return 'unknown'

    def find_text_in_image(self, screenshot: str, target_text: str) -> dict[str, Any] | None:
        """Find text in image - OCR functionality removed, use LLM vision instead"""
        # OCR functionality removed - screenshots should be fed directly to LLM
        # for text recognition and element location
        return None

    def compare_templates(self, template1: str, template2: str) -> float:
        """Compare similarity between two templates"""
        try:
            img1 = cv2.imread(template1, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(template2, cv2.IMREAD_GRAYSCALE)

            if img1 is None or img2 is None:
                return 0.0

            # Resize to same dimensions for comparison
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])

            img1_resized = cv2.resize(img1, (width, height))
            img2_resized = cv2.resize(img2, (width, height))

            # Calculate correlation
            result = cv2.matchTemplate(img1_resized, img2_resized, cv2.TM_CCOEFF_NORMED)
            return float(result[0, 0])

        except Exception as e:
            self.logger.error(f"Template comparison failed: {e}")
            return 0.0

    def create_template_from_region(
        self, screenshot: str, region: dict[str, int], output_path: str
    ) -> bool:
        """Create template from screen region"""
        try:
            img = cv2.imread(screenshot, cv2.IMREAD_COLOR)
            if img is None:
                return False

            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            template = img[y : y + h, x : x + w]

            cv2.imwrite(output_path, template)
            return True

        except Exception as e:
            self.logger.error(f"Template creation failed: {e}")
            return False