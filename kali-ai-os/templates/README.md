# GUI Element Templates

This directory contains template images for GUI element recognition using OpenCV template matching.

## Directory Structure

```
templates/
├── burpsuite/          # Burp Suite GUI elements
│   ├── proxy_tab.png
│   ├── scanner_tab.png
│   ├── start_button.png
│   ├── target_field.png
│   └── intercept_button.png
├── wireshark/          # Wireshark GUI elements
│   ├── start_capture.png
│   ├── stop_capture.png
│   ├── interface_list.png
│   └── save_button.png
├── browser/            # Browser GUI elements
│   ├── address_bar.png
│   ├── go_button.png
│   ├── back_button.png
│   ├── forward_button.png
│   └── refresh_button.png
├── terminal/           # Terminal GUI elements
│   ├── prompt.png
│   ├── title_bar.png
│   ├── close_button.png
│   └── maximize_button.png
├── nessus/             # Nessus GUI elements
│   ├── scan_button.png
│   ├── targets_field.png
│   ├── policies_dropdown.png
│   └── launch_button.png
└── common/             # Common GUI elements
    ├── ok_button.png
    ├── cancel_button.png
    ├── close_button.png
    ├── apply_button.png
    └── next_button.png
```

## Template Guidelines

### Image Requirements
- **Format**: PNG preferred (supports transparency)
- **Size**: 10x10 to 500x500 pixels
- **Quality**: High resolution, clear edges
- **Content**: Should contain sufficient detail for matching

### Naming Convention
- Use descriptive names: `proxy_tab.png`, `start_capture.png`
- Use underscores instead of spaces
- Include element state if relevant: `button_enabled.png`, `button_disabled.png`

### Capture Best Practices
1. **Consistent Environment**: Capture on same OS/theme as deployment
2. **Clean Screenshots**: No overlapping windows or artifacts
3. **Minimal Context**: Include just enough surrounding area for uniqueness
4. **Multiple States**: Capture different states (enabled/disabled, focused/unfocused)

## Usage

Templates are automatically managed by the `TemplateManager` class:

```python
from src.desktop.recognition.template_manager import TemplateManager

# Initialize template manager
tm = TemplateManager("templates")

# Get template path
template_path = tm.get_template_path("burpsuite", "proxy_tab")

# Add new template
tm.add_template("burpsuite", "new_button", "/path/to/screenshot.png")

# Create template from screenshot region
tm.create_template_from_screenshot(
    "screenshot.png",
    {"x": 100, "y": 200, "width": 50, "height": 25},
    "burpsuite",
    "custom_button"
)
```

## Template Creation Tools

### From Screenshots
Use the template manager to extract regions from screenshots:

```python
# Capture current screen
screenshot_path = desktop_controller.capture_screenshot()

# Extract template from region
region = {"x": 150, "y": 300, "width": 80, "height": 30}
tm.create_template_from_screenshot(screenshot_path, region, "common", "new_button")
```

### Manual Creation
1. Take screenshot of target application
2. Use image editor to crop exact element
3. Save as PNG in appropriate category folder
4. Validate using `tm.validate_template()`

## Quality Assurance

### Validation
All templates are automatically validated for:
- Minimum size (10x10 pixels)
- Maximum size (500x500 pixels)
- Sufficient edge detail for matching
- Valid image format

### Testing
Test template recognition accuracy:

```python
from src.desktop.recognition.opencv_matcher import OpenCVMatcher

matcher = OpenCVMatcher()
result = matcher.find_template("current_screen.png", template_path)
print(f"Template found: {result['found']}, Confidence: {result['confidence']}")
```

## Maintenance

### Update Templates
- Regularly update templates when applications change
- Test templates after OS/theme updates
- Remove unused or outdated templates

### Performance
- Keep template library size reasonable
- Use appropriate confidence thresholds
- Consider template preprocessing for better matching

### Backup
- Version control template images
- Document template sources and capture conditions
- Maintain metadata for template provenance
