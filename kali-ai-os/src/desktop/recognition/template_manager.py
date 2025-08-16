import json
import logging
import os
from pathlib import Path
from typing import Any

import cv2


class TemplateManager:
    """Manage GUI element templates for screen recognition"""

    def __init__(self, template_base_dir: str = "templates") -> None:
        self.template_base_dir = Path(template_base_dir)
        self.logger = logging.getLogger(__name__)

        # Template metadata cache
        self.template_cache: dict[str, Any] = {}
        self.metadata_file = self.template_base_dir / "templates_metadata.json"

        # Supported template categories
        self.categories = {
            'burpsuite': [
                'proxy_tab',
                'scanner_tab',
                'start_button',
                'target_field',
                'intercept_button',
            ],
            'wireshark': [
                'start_capture',
                'stop_capture',
                'interface_list',
                'save_button',
            ],
            'browser': [
                'address_bar',
                'go_button',
                'back_button',
                'forward_button',
                'refresh_button',
            ],
            'terminal': ['prompt', 'title_bar', 'close_button', 'maximize_button'],
            'nessus': [
                'scan_button',
                'targets_field',
                'policies_dropdown',
                'launch_button',
            ],
            'common': [
                'ok_button',
                'cancel_button',
                'close_button',
                'apply_button',
                'next_button',
            ],
        }

        # Initialize template directories
        self._ensure_template_structure()
        self._load_metadata()

    def _ensure_template_structure(self) -> None:
        """Ensure all template directories exist"""
        try:
            self.template_base_dir.mkdir(parents=True, exist_ok=True)

            for category in self.categories.keys():
                category_dir = self.template_base_dir / category
                category_dir.mkdir(exist_ok=True)

                # Create placeholder files for expected templates
                for template_name in self.categories[category]:
                    placeholder_file = category_dir / f"{template_name}.png"
                    if not placeholder_file.exists():
                        # Create a simple placeholder image
                        self._create_placeholder_template(str(placeholder_file), template_name)

        except Exception as e:
            self.logger.error(f"Failed to create template structure: {e}")

    def _create_placeholder_template(self, filepath: str, name: str) -> None:
        """Create a placeholder template image"""
        try:
            import numpy as np

            # Create a simple 100x30 placeholder image
            placeholder = np.ones((30, 100, 3), dtype=np.uint8) * 200
            cv2.putText(
                placeholder,
                name[:10],
                (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 0, 0),
                1,
            )
            cv2.imwrite(filepath, placeholder)

        except Exception as e:
            self.logger.debug(f"Could not create placeholder for {name}: {e}")

    def _load_metadata(self) -> None:
        """Load template metadata from file"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file) as f:
                    self.template_cache = json.load(f)
            else:
                self.template_cache = {}
                self._save_metadata()

        except Exception as e:
            self.logger.error(f"Failed to load template metadata: {e}")
            self.template_cache = {}

    def _save_metadata(self) -> None:
        """Save template metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.template_cache, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save template metadata: {e}")

    def get_template_path(self, category: str, template_name: str) -> str | None:
        """Get full path to a template"""
        template_path = self.template_base_dir / category / f"{template_name}.png"

        if template_path.exists():
            return str(template_path)

        # Try alternative extensions
        for ext in ['.jpg', '.jpeg', '.bmp']:
            alt_path = self.template_base_dir / category / f"{template_name}{ext}"
            if alt_path.exists():
                return str(alt_path)

        self.logger.warning(f"Template not found: {category}/{template_name}")
        return None

    def add_template(
        self,
        category: str,
        template_name: str,
        image_path: str,
        metadata: dict | None = None,
    ) -> bool:
        """Add a new template to the library"""
        try:
            # Validate category
            if category not in self.categories:
                self.logger.error(f"Unknown category: {category}")
                return False

            # Copy template to appropriate directory
            target_dir = self.template_base_dir / category
            target_path = target_dir / f"{template_name}.png"

            # Load and save the image (this validates it's a valid image)
            img = cv2.imread(image_path)
            if img is None:
                self.logger.error(f"Could not load image: {image_path}")
                return False

            cv2.imwrite(str(target_path), img)

            # Update metadata
            template_key = f"{category}/{template_name}"
            self.template_cache[template_key] = {
                'category': category,
                'name': template_name,
                'path': str(target_path),
                'size': img.shape[:2],  # height, width
                'added_date': str(Path(image_path).stat().st_mtime),
                'metadata': metadata or {},
            }

            self._save_metadata()
            self.logger.info(f"Added template: {template_key}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add template {category}/{template_name}: {e}")
            return False

    def get_templates_for_category(self, category: str) -> list[dict[str, Any]]:
        """Get all templates for a specific category"""
        templates = []

        for _key, metadata in self.template_cache.items():
            if metadata['category'] == category:
                templates.append(metadata)

        return templates

    def get_all_templates(self) -> dict[str, list[str]]:
        """Get all available templates organized by category"""
        result = {}

        for category in self.categories.keys():
            category_dir = self.template_base_dir / category
            if category_dir.exists():
                templates = []
                for template_file in category_dir.glob("*.png"):
                    template_name = template_file.stem
                    templates.append(template_name)
                result[category] = templates

        return result

    def validate_template(self, template_path: str) -> dict[str, Any]:
        """Validate a template image"""
        try:
            img = cv2.imread(template_path)
            if img is None:
                return {'valid': False, 'error': 'Could not load image'}

            height, width = img.shape[:2]

            # Check size constraints
            if width < 10 or height < 10:
                return {'valid': False, 'error': 'Template too small (minimum 10x10)'}

            if width > 500 or height > 500:
                return {'valid': False, 'error': 'Template too large (maximum 500x500)'}

            # Check if image has sufficient detail for matching
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_count = cv2.countNonZero(edges)

            if edge_count < 50:
                return {
                    'valid': False,
                    'error': 'Template lacks sufficient detail for matching',
                }

            return {
                'valid': True,
                'size': (width, height),
                'edge_count': edge_count,
                'channels': img.shape[2] if len(img.shape) == 3 else 1,
            }

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def create_template_from_screenshot(
        self,
        screenshot_path: str,
        region: dict[str, int],
        category: str,
        template_name: str,
    ) -> bool:
        """Create template from a region of a screenshot"""
        try:
            img = cv2.imread(screenshot_path)
            if img is None:
                self.logger.error(f"Could not load screenshot: {screenshot_path}")
                return False

            # Extract region
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            template = img[y : y + h, x : x + w]

            # Validate extracted template
            validation = self.validate_template_array(template)
            if not validation['valid']:
                self.logger.error(f"Invalid template region: {validation['error']}")
                return False

            # Save template
            target_dir = self.template_base_dir / category
            target_dir.mkdir(exist_ok=True)
            template_path = target_dir / f"{template_name}.png"

            cv2.imwrite(str(template_path), template)

            # Update metadata
            template_key = f"{category}/{template_name}"
            self.template_cache[template_key] = {
                'category': category,
                'name': template_name,
                'path': str(template_path),
                'size': template.shape[:2],
                'created_from': screenshot_path,
                'region': region,
                'metadata': {},
            }

            self._save_metadata()
            self.logger.info(f"Created template from screenshot: {template_key}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create template from screenshot: {e}")
            return False

    def validate_template_array(self, img_array: cv2.typing.MatLike) -> dict[str, Any]:
        """Validate a template image array"""
        try:
            if img_array is None or img_array.size == 0:
                return {'valid': False, 'error': 'Empty image array'}

            height, width = img_array.shape[:2]

            if width < 10 or height < 10:
                return {'valid': False, 'error': 'Template too small'}

            if width > 500 or height > 500:
                return {'valid': False, 'error': 'Template too large'}

            return {'valid': True, 'size': (width, height)}

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def find_similar_templates(
        self, template_path: str, threshold: float = 0.8
    ) -> list[dict[str, Any]]:
        """Find templates similar to the given one"""
        similar: list[dict[str, Any]] = []

        try:
            base_img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if base_img is None:
                return similar

            for template_key, metadata in self.template_cache.items():
                other_path = metadata['path']
                if other_path == template_path:
                    continue

                other_img = cv2.imread(other_path, cv2.IMREAD_GRAYSCALE)
                if other_img is None:
                    continue

                # Resize to same size for comparison
                min_height = min(base_img.shape[0], other_img.shape[0])
                min_width = min(base_img.shape[1], other_img.shape[1])

                base_resized = cv2.resize(base_img, (min_width, min_height))
                other_resized = cv2.resize(other_img, (min_width, min_height))

                # Calculate correlation
                result = cv2.matchTemplate(base_resized, other_resized, cv2.TM_CCOEFF_NORMED)
                similarity = result[0, 0]

                if similarity >= threshold:
                    similar.append(
                        {
                            'template': template_key,
                            'similarity': float(similarity),
                            'metadata': metadata,
                        }
                    )

            # Sort by similarity
            similar.sort(key=lambda x: x['similarity'], reverse=True)

        except Exception as e:
            self.logger.error(f"Error finding similar templates: {e}")

        return similar

    def get_template_stats(self) -> dict[str, Any]:
        """Get statistics about the template library"""
        stats: dict[str, Any] = {
            'total_templates': len(self.template_cache),
            'categories': {},
            'template_sizes': [],
            'missing_templates': [],
        }
        missing_templates: list[str] = stats['missing_templates']
        template_sizes: list[Any] = stats['template_sizes']

        # Count templates per category
        for category in self.categories.keys():
            category_templates = self.get_templates_for_category(category)
            stats['categories'][category] = {
                'count': len(category_templates),
                'expected': len(self.categories[category]),
                'templates': [t['name'] for t in category_templates],
            }

        # Find missing templates
        for category, expected_templates in self.categories.items():
            for template_name in expected_templates:
                template_path = self.get_template_path(category, template_name)
                if not template_path or not os.path.exists(template_path):
                    missing_templates.append(f"{category}/{template_name}")

        # Collect template sizes
        for metadata in self.template_cache.values():
            if 'size' in metadata:
                template_sizes.append(metadata['size'])

        return stats

    def cleanup_invalid_templates(self) -> int:
        """Remove invalid template entries and files"""
        removed_count = 0
        invalid_keys = []

        for template_key, metadata in self.template_cache.items():
            template_path = metadata.get('path')
            if not template_path or not os.path.exists(template_path):
                invalid_keys.append(template_key)
                continue

            validation = self.validate_template(template_path)
            if not validation['valid']:
                invalid_keys.append(template_key)
                try:
                    os.remove(template_path)
                except OSError:
                    pass  # noqa: S110

        # Remove invalid entries
        for key in invalid_keys:
            del self.template_cache[key]
            removed_count += 1

        if removed_count > 0:
            self._save_metadata()
            self.logger.info(f"Cleaned up {removed_count} invalid templates")

        return removed_count
