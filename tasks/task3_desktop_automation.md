# Task 3: Desktop Automation Core

## What This Task Is About
This task creates the "hands" of the AI system with a hybrid approach evolving toward full agentic automation:
- **Current Phase** - Template-based GUI automation with OpenCV pattern matching for reliable element detection
- **Hybrid Enhancement** - AI vision supplements templates for better recognition and adaptation
- **Future Vision** - Direct screenshot-to-AI decision making where AI autonomously determines actions
- **Dual Desktop System** - AI operates on virtual desktop (:1) while user works on main desktop (:0)
- **Evolution Path** - Template system → Hybrid AI + Templates → Pure AI Vision Decision Making

## Why This Task Is Critical
- **Immediate Value**: Template-based system provides reliable GUI automation today
- **Evolution Strategy**: Hybrid approach bridges current reliability with future AI autonomy
- **Future Vision**: Direct screenshot analysis enables true agentic behavior like Claude Code terminal
- **Tool Integration**: Works with any security tool through visual interface understanding
- **User Productivity**: Complete isolation allows simultaneous human and AI workflows

## How to Complete This Task - Step by Step

### Phase 1: Setup Virtual Desktop Environment (1 hour)
**Foundation for both current templates and future AI vision**
```bash
# 1. Install X11 and virtual desktop tools (in VM)
sudo apt update
sudo apt install -y xvfb x11vnc xdotool wmctrl
sudo apt install -y python3-tk python3-pil python3-pil.imagetk
sudo apt install -y openbox feh  # Lightweight window manager

# 2. Setup Python environment with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv add opencv-python pyautogui pillow
uv add pytest pytest-mock --dev
uv sync --all-extras

# 2. Create AI desktop service
sudo tee /etc/systemd/system/ai-desktop.service << 'EOF'
[Unit]
Description=AI Desktop Virtual Display
After=network.target

[Service]
Type=simple
User=kali
Environment=DISPLAY=:1
ExecStart=/usr/bin/Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 3. Start AI desktop
sudo systemctl enable ai-desktop.service
sudo systemctl start ai-desktop.service

# 4. Test dual desktop setup
DISPLAY=:0 echo "User desktop"    # Should work
DISPLAY=:1 echo "AI desktop"      # Should work
```

### Phase 2: Write Desktop Tests First (1 hour)
**Tests designed to validate current templates and future AI decision-making**
```python
# tests/desktop/test_automation.py
def test_dual_desktop_isolation():
    """Test AI and user desktops don't interfere"""
    # Verify actions on :1 don't affect :0

def test_screen_element_recognition():
    """Test finding GUI elements with OpenCV"""
    # Test finding buttons, text fields in screenshots

def test_safe_click_execution():
    """Test clicks are executed safely"""
    # Test coordinate validation and safety checks

def test_application_automation():
    """Test opening and controlling applications"""
    # Test opening terminal, browser, security tools

def test_user_activity_detection():
    """Test detecting when user is active"""
    # Ensure AI pauses when user is working
```

### Phase 3: Desktop Controller Core (2 hours)
**Flexible architecture supporting templates now, AI vision later**
```python
# src/desktop/automation/pyautogui_controller.py
import pyautogui
import os
import time

class DesktopController:
    def __init__(self, display=":1", mode="hybrid"):  # AI desktop
        self.display = display
        self.mode = mode  # "template", "hybrid", "ai_vision"
        os.environ['DISPLAY'] = display

        # Configure PyAutoGUI for safety
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.1      # Pause between actions

    def safe_click(self, x, y, button='left'):
        """Click with safety validation"""
        # 1. Validate coordinates are on screen
        # 2. Check if safe to perform action
        # 3. Switch to AI display
        # 4. Perform click
        # 5. Return success/failure

    def safe_type(self, text):
        """Type text safely"""
        # 1. Validate text is safe
        # 2. Ensure AI display is active
        # 3. Type character by character
        # 4. Handle special characters

    def find_element(self, target, confidence=0.8):
        """Find GUI element using current mode (template/hybrid/ai_vision)"""
        if self.mode == "template":
            return self._find_with_template(target, confidence)
        elif self.mode == "hybrid":
            return self._find_with_hybrid(target, confidence)
        elif self.mode == "ai_vision":
            return self._find_with_ai_vision(target)

    def _find_with_ai_vision(self, description):
        """FUTURE: Find element using pure AI vision"""
        # 1. Capture current screenshot
        # 2. Send to LLM with description: "find the proxy tab button"
        # 3. AI returns coordinates and confidence
        # 4. No templates needed - AI understands GUI elements
```

### Phase 4: Screen Recognition System (1.5 hours)
**Hybrid system: Templates for reliability + AI vision for adaptability**
```python
# src/desktop/recognition/opencv_matcher.py
import cv2
import numpy as np

class HybridRecognition:
    def __init__(self, ai_model):
        self.ai_model = ai_model
        self.template_matcher = OpenCVMatcher()

    def find_element(self, screenshot, target, method="hybrid"):
        """Find element using best available method"""
        if method == "template" and self._has_template(target):
            return self._find_with_template(screenshot, target)
        elif method == "hybrid":
            # Try template first, fallback to AI
            template_result = self._try_template(screenshot, target)
            if template_result['found']:
                return template_result
            return self._find_with_ai_vision(screenshot, target)
        else:
            return self._find_with_ai_vision(screenshot, target)

    def _find_with_ai_vision(self, screenshot, description):
        """Find element using AI vision - future primary method"""
        # Send screenshot + description to AI
        prompt = f"""Analyze this screenshot and find: {description}
        Return the exact pixel coordinates where I should click.
        Respond with just: x,y,confidence
        """

        response = self.ai_model.generate_content([
            prompt,
            {'mime_type': 'image/png', 'data': screenshot}
        ])

        # Parse AI response: "450,320,0.95"
        # AI directly tells us where to click
        return self._parse_ai_coordinates(response.text)

    def evolve_to_pure_ai(self):
        """FUTURE: Switch to pure AI vision mode"""
        # Phase out templates entirely
        # AI makes all decisions from screenshots
        # Like Claude Code terminal - direct visual understanding
```

### Phase 5: User Activity Monitoring (1 hour)
```python
# src/desktop/monitoring/user_activity.py
import psutil
import time
from pynput import mouse, keyboard

class UserActivityMonitor:
    def __init__(self):
        self.last_activity = time.time()
        self.activity_threshold = 300  # 5 minutes

    def get_current_activity_level(self):
        """Determine if user is active"""
        # Check mouse and keyboard activity on :0
        # Check CPU usage of user processes
        # Return: 'idle', 'light', 'intensive'

    def is_safe_for_ai_activity(self):
        """Check if AI can safely operate"""
        # Don't interfere if user is:
        # - In video call (zoom, teams)
        # - Giving presentation
        # - Actively typing/clicking

    def wait_for_safe_moment(self):
        """Wait until safe to perform AI actions"""
        # Monitor user activity
        # Return when user is idle or gives permission
```

### Phase 6: Application Integration (1.5 hours)
```python
# src/desktop/applications/security_app_controller.py
class SecurityAppController:
    def __init__(self, desktop_controller):
        self.desktop = desktop_controller

    def open_burpsuite(self):
        """Open and setup Burp Suite"""
        # 1. Launch burpsuite application
        # 2. Wait for startup (can take 30+ seconds)
        # 3. Handle license/update dialogs
        # 4. Navigate to proxy tab
        # 5. Return when ready for use

    def configure_burp_proxy(self, target_url, port=8080):
        """Configure Burp Suite proxy for target"""
        # 1. Find proxy tab using template matching
        # 2. Click proxy tab
        # 3. Configure target scope
        # 4. Set proxy port
        # 5. Start intercepting

    def open_terminal(self):
        """Open terminal on AI desktop"""
        # 1. Use keyboard shortcut or application menu
        # 2. Wait for terminal to open
        # 3. Return terminal ready for commands

    def run_command_in_terminal(self, command):
        """Execute command in terminal"""
        # 1. Click in terminal window
        # 2. Type command
        # 3. Press Enter
        # 4. Wait for completion
        # 5. Capture output if needed
```

### Phase 7: Template Management & AI Evolution (45 minutes)
**Current: Template library | Future: AI learning from templates**
```bash
# Current Phase: Create template library for reliable automation
mkdir -p src/desktop/templates/{burpsuite,terminal,browser,nessus}

# Capture template images for common elements:
# - Burp Suite proxy tab, start button, target field
# - Terminal window, command prompt
# - Browser address bar, navigation buttons
# - Common OK/Cancel/Apply buttons

# Test current template system
python -c "
from src.desktop.recognition.hybrid_recognition import HybridRecognition
recognizer = HybridRecognition(ai_model)
result = recognizer.find_element('screenshot.png', 'burpsuite proxy tab', method='template')
print('Element found:', result['found'])
"

# Future Phase: AI learns from templates then operates independently
python -c "
# FUTURE: Pure AI vision mode
result = recognizer.find_element('screenshot.png', 'click the proxy tab in burp suite', method='ai_vision')
# AI directly understands GUI elements without templates
print('AI found element at:', result['coordinates'])
"
```

### Phase 8: Integration & Safety Testing (1 hour)
```python
# src/desktop/safety/isolation_manager.py
class IsolationManager:
    def ensure_ai_desktop_isolation(self):
        """Verify AI operations don't affect user desktop"""
        # 1. Check current DISPLAY environment
        # 2. Verify window manager isolation
        # 3. Test that clicks on :1 don't affect :0
        # 4. Monitor for any cross-desktop interference

    def emergency_stop(self):
        """Stop all desktop automation immediately"""
        # 1. Kill all PyAutoGUI operations
        # 2. Return control to user
        # 3. Log emergency stop event
        # 4. Send notification to user

# Test complete workflow
def test_complete_desktop_workflow():
    controller = DesktopController(display=":1")
    app_controller = SecurityAppController(controller)

    # Test opening and controlling Burp Suite
    app_controller.open_burpsuite()
    app_controller.configure_burp_proxy("https://example.com")

    # Verify user desktop unaffected
    assert_user_desktop_unchanged()
```

## Overview
Build an evolving desktop automation system that transitions from reliable template-based control to autonomous AI decision-making. Current phase uses OpenCV templates with AI vision enhancement, evolving toward pure screenshot-to-action AI like Claude Code terminal.

**Evolution Timeline:**
1. **Phase 1 (Current)**: Template-based automation with OpenCV
2. **Phase 2 (Near Future)**: Hybrid templates + AI vision for adaptation
3. **Phase 3 (Future Vision)**: Pure AI vision - direct screenshot analysis to action decisions

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── desktop/
│   │   │   ├── __init__.py
│   │   │   ├── automation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pyautogui_controller.py
│   │   │   │   ├── screen_capture.py
│   │   │   │   ├── element_recognition.py
│   │   │   │   ├── action_executor.py
│   │   │   │   └── gesture_handler.py
│   │   │   ├── display/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── virtual_desktop.py
│   │   │   │   ├── display_manager.py
│   │   │   │   ├── window_controller.py
│   │   │   │   └── workspace_switcher.py
│   │   │   ├── monitoring/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user_activity.py
│   │   │   │   ├── process_monitor.py
│   │   │   │   ├── resource_tracker.py
│   │   │   │   └── session_coordinator.py
│   │   │   ├── recognition/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── opencv_matcher.py
│   │   │   │   ├── template_manager.py
│   │   │   │   ├── text_recognition.py
│   │   │   │   └── gui_element_finder.py
│   │   │   ├── safety/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── isolation_manager.py
│   │   │   │   ├── permission_guard.py
│   │   │   │   ├── action_validator.py
│   │   │   │   └── emergency_stop.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── desktop_config.py
│   │   │       ├── display_settings.py
│   │   │       └── automation_rules.py
│   │   └── tests/
│   │       ├── desktop/
│   │       │   ├── __init__.py
│   │       │   ├── test_automation.py
│   │       │   ├── test_display_manager.py
│   │       │   ├── test_user_activity.py
│   │       │   ├── test_screen_recognition.py
│   │       │   ├── test_safety_isolation.py
│   │       │   └── test_templates/
│   │       │       ├── burpsuite_elements/
│   │       │       ├── terminal_elements/
│   │       │       ├── browser_elements/
│   │       │       └── nessus_elements/
│   │       └── fixtures/
│   │           ├── test_screenshots/
│   │           └── mock_displays/
│   ├── scripts/
│   │   ├── setup_virtual_desktop.sh
│   │   ├── configure_xorg.sh
│   │   └── test_dual_display.sh
│   └── requirements/
│       ├── desktop_requirements.txt
│       └── system_packages.txt
```

## Technology Stack

### Current Implementation
- **GUI Automation**: PyAutoGUI 0.9.54, pynput 1.7.6
- **Template Recognition**: OpenCV 4.8.1.78, Pillow 10.1.0
- **Display Management**: python-xlib 0.33, xvfbwrapper 0.2.9
- **Process Monitoring**: psutil 5.9.5
- **System Integration**: X11 utilities, wmctrl, xdotool

### Future Enhancement
- **AI Vision**: Google Gemini Vision, GPT-4 Vision, Claude 3.5 Sonnet
- **Direct Screenshot Analysis**: No templates needed
- **Agentic Decision Making**: AI determines actions from visual context
- **Learning System**: AI adapts to new interfaces automatically

### 2. GUI Element Recognition Tests
```python
# tests/desktop/test_screen_recognition.py
def test_hybrid_element_detection():
    """Test hybrid template + AI vision element detection"""
    from src.desktop.recognition.hybrid_recognition import HybridRecognition

    recognizer = HybridRecognition(ai_model)

    # Test template-based detection (current)
    template_cases = [
        {
            'screenshot': 'tests/fixtures/test_screenshots/burpsuite_main.png',
            'target': 'proxy_tab',
            'method': 'template',
            'expected_confidence': 0.85
        }
    ]

    # Test AI vision detection (future)
    ai_vision_cases = [
        {
            'screenshot': 'tests/fixtures/test_screenshots/burpsuite_main.png',
            'target': 'find the proxy tab button in burp suite',
            'method': 'ai_vision',
            'expected_confidence': 0.90
        }
    ]

    for case in template_cases + ai_vision_cases:
        result = recognizer.find_element(
            screenshot=case['screenshot'],
            target=case['target'],
            method=case['method']
        )

        assert result['confidence'] >= case['expected_confidence']
        assert result['location'] is not None

def test_ai_decision_making():
    """Test AI's ability to make autonomous decisions from screenshots"""
    from src.desktop.recognition.hybrid_recognition import HybridRecognition

    recognizer = HybridRecognition(ai_model)

    # Test AI understanding different application states
    test_scenarios = [
        {
            'screenshot': 'tests/fixtures/test_screenshots/burp_startup.png',
            'task': 'configure burp suite for scanning target.com',
            'expected_actions': ['click_proxy_tab', 'set_target_scope']
        },
        {
            'screenshot': 'tests/fixtures/test_screenshots/terminal_ready.png',
            'task': 'run nmap scan on 192.168.1.1',
            'expected_actions': ['click_terminal', 'type_command']
        }
    ]

    for scenario in test_scenarios:
        # AI analyzes screenshot and determines action sequence
        action_plan = recognizer.analyze_and_plan(
            screenshot=scenario['screenshot'],
            task=scenario['task']
        )

        # AI should identify correct sequence of actions
        assert len(action_plan['actions']) > 0

        # AI provides specific coordinates and actions
        for action in action_plan['actions']:
            assert 'type' in action  # click, type, etc.
            assert 'coordinates' in action
            assert 'description' in action
```

## Implementation Requirements

### Core Components

#### 1. Desktop Controller
```python
# src/desktop/automation/pyautogui_controller.py
import pyautogui
import time
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ClickResult:
    success: bool
    clicked_location: Optional[Tuple[int, int]]
    error_message: Optional[str] = None
    execution_time: float = 0.0

class DesktopController:
    def __init__(self, display: str = ":1"):
        self.display = display
        self.safety_enabled = True
        self.automation_active = False

        # Configure PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def safe_click(self, x: int, y: int, button: str = 'left') -> ClickResult:
        """Safely click at coordinates with validation"""
        start_time = time.time()

        # Validate coordinates
        if not self._validate_coordinates(x, y):
            return ClickResult(
                success=False,
                clicked_location=None,
                error_message="Coordinates outside screen bounds"
            )

        # Check if safe to perform action
        if not self._is_safe_to_act():
            return ClickResult(
                success=False,
                clicked_location=None,
                error_message="User activity detected, action blocked"
            )

        try:
            # Switch to AI display
            self._ensure_ai_display()

            # Perform click
            pyautogui.click(x, y, button=button)

            execution_time = time.time() - start_time
            return ClickResult(
                success=True,
                clicked_location=(x, y),
                execution_time=execution_time
            )
        except Exception as e:
            return ClickResult(
                success=False,
                clicked_location=None,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def safe_type(self, text: str, interval: float = 0.01) -> Dict[str, Any]:
        """Safely type text with validation"""
        # Implementation here
        pass

    def find_element(self, template: str, confidence: float = 0.8) -> Optional[Dict]:
        """Find GUI element using template matching"""
        # Implementation here
        pass
```

#### 2. Virtual Desktop Manager
```python
# src/desktop/display/virtual_desktop.py
import subprocess
import os
from typing import List, Dict, Any

class VirtualDesktop:
    def __init__(self, display: str = ":1", resolution: str = "1920x1080"):
        self.display = display
        self.resolution = resolution
        self.is_running = False

    def start_virtual_display(self) -> bool:
        """Start Xvfb virtual display"""
        try:
            # Start Xvfb
            cmd = [
                'Xvfb', self.display,
                '-screen', '0', f'{self.resolution}x24',
                '-ac', '+extension', 'GLX'
            ]

            self.xvfb_process = subprocess.Popen(cmd)

            # Wait for display to be ready
            time.sleep(2)

            # Set DISPLAY environment variable
            os.environ['DISPLAY'] = self.display

            self.is_running = True
            return True

        except Exception as e:
            print(f"Failed to start virtual display: {e}")
            return False

    def stop_virtual_display(self) -> bool:
        """Stop virtual display"""
        # Implementation here
        pass

    def get_display_info(self) -> Dict[str, Any]:
        """Get current display information"""
        # Implementation here
        pass
```

#### 3. User Activity Monitor
```python
# src/desktop/monitoring/user_activity.py
import psutil
import time
from typing import Dict, str
from pynput import mouse, keyboard

class UserActivityMonitor:
    def __init__(self):
        self.last_activity = time.time()
        self.activity_threshold = {
            'idle': 300,      # 5 minutes
            'light': 60,      # 1 minute
            'intensive': 10   # 10 seconds
        }

    def get_current_activity_level(self) -> str:
        """Determine current user activity level"""
        # Check mouse and keyboard activity
        mouse_active = self._check_mouse_activity()
        keyboard_active = self._check_keyboard_activity()

        # Check CPU usage of user processes
        user_cpu = self._get_user_process_cpu()

        # Determine activity level
        if not mouse_active and not keyboard_active and user_cpu < 5:
            return 'idle'
        elif mouse_active or keyboard_active or user_cpu < 20:
            return 'light'
        else:
            return 'intensive'

    def is_user_in_critical_task(self) -> bool:
        """Check if user is in critical task (presentation, call, etc.)"""
        critical_processes = [
            'zoom', 'teams', 'skype', 'discord',
            'obs-studio', 'libreoffice-impress'
        ]

        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and any(cp in proc.info['name'].lower()
                                       for cp in critical_processes):
                return True
        return False

    def _check_mouse_activity(self) -> bool:
        """Check for recent mouse movement"""
        # Implementation here
        pass

    def _check_keyboard_activity(self) -> bool:
        """Check for recent keyboard input"""
        # Implementation here
        pass
```

#### 4. Screen Recognition Engine
```python
# src/desktop/recognition/opencv_matcher.py
import cv2
import numpy as np
from typing import Optional, Tuple, Dict

class OpenCVMatcher:
    def __init__(self):
        self.matching_methods = [
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_CCORR_NORMED,
            cv2.TM_SQDIFF_NORMED
        ]

    def find_template(self, screenshot: str, template: str,
                     confidence: float = 0.8) -> Dict:
        """Find template in screenshot using OpenCV"""
        # Load images
        img = cv2.imread(screenshot, cv2.IMREAD_COLOR)
        template_img = cv2.imread(template, cv2.IMREAD_COLOR)

        if img is None or template_img is None:
            return {'found': False, 'error': 'Could not load images'}

        # Convert to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            return {
                'found': True,
                'confidence': max_val,
                'location': max_loc,
                'size': template_img.shape[:2]
            }
        else:
            return {
                'found': False,
                'confidence': max_val,
                'location': None
            }

    def find_multiple_templates(self, screenshot: str, templates: list) -> list:
        """Find multiple templates in a single screenshot"""
        # Implementation here
        pass
```

### Desktop Isolation & Safety

#### 1. Isolation Manager
```python
# src/desktop/safety/isolation_manager.py
class IsolationManager:
    def __init__(self):
        self.user_display = ":0"
        self.ai_display = ":1"
        self.isolation_active = True

    def ensure_isolation(self) -> bool:
        """Ensure AI operations don't affect user desktop"""
        # Verify AI is operating on correct display
        current_display = os.environ.get('DISPLAY')
        if current_display != self.ai_display:
            self._switch_to_ai_display()

        # Check for any cross-display interference
        return self._verify_no_interference()

    def emergency_isolation(self) -> bool:
        """Emergency isolation of AI activities"""
        # Immediately stop all automation
        # Switch back to safe state
        # Log incident
        pass
```

#### 2. Permission Guard
```python
# src/desktop/safety/permission_guard.py
class PermissionGuard:
    def __init__(self):
        self.allowed_applications = [
            'burpsuite', 'nmap', 'wireshark', 'metasploit',
            'gnome-terminal', 'firefox', 'chromium'
        ]

    def validate_action(self, action: Dict) -> bool:
        """Validate if automation action is allowed"""
        # Check application permissions
        # Validate action safety
        # Ensure within scope
        pass
```

## System Configuration

### Virtual Desktop Setup
```bash
# scripts/setup_virtual_desktop.sh
#!/bin/bash

echo "Setting up virtual desktop for AI automation..."

# Install required packages
sudo apt update
sudo apt install -y xvfb x11vnc xdotool wmctrl
sudo apt install -y python3-tk python3-pil python3-pil.imagetk

# Create AI desktop service
sudo tee /etc/systemd/system/ai-desktop.service << 'EOF'
[Unit]
Description=AI Desktop Virtual Display
After=network.target

[Service]
Type=simple
User=kali
Environment=DISPLAY=:1
ExecStart=/usr/bin/Xvfb :1 -screen 0 1920x1080x24 -ac +extension GLX
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable ai-desktop.service
sudo systemctl start ai-desktop.service

# Configure window manager for AI desktop
DISPLAY=:1 openbox &

echo "Virtual desktop setup complete!"
echo "AI Desktop: :1 (1920x1080)"
echo "User Desktop: :0 (unchanged)"
```

### X11 Configuration
```bash
# scripts/configure_xorg.sh
#!/bin/bash

# Configure X11 for dual desktop support
sudo tee /etc/X11/xorg.conf.d/20-ai-desktop.conf << 'EOF'
Section "ServerFlags"
    Option "AllowEmptyInput" "true"
    Option "DontVTSwitch" "true"
    Option "DontZap" "true"
EndSection

Section "Device"
    Identifier "AI Display Device"
    Driver "dummy"
EndSection

Section "Monitor"
    Identifier "AI Monitor"
    HorizSync 28.0-80.0
    VertRefresh 48.0-75.0
    Modeline "1920x1080" 172.80 1920 2040 2248 2576 1080 1081 1084 1118
EndSection

Section "Screen"
    Identifier "AI Screen"
    Device "AI Display Device"
    Monitor "AI Monitor"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080"
    EndSubSection
EndSection
EOF
```

## Testing Strategy

### Unit Tests (85% coverage minimum)
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-xvfb

# Run desktop automation tests
cd kali-ai-os
python -m pytest tests/desktop/ -v --cov=src.desktop --cov-report=html

# Expected test categories:
# - GUI automation accuracy
# - Display isolation
# - User activity detection
# - Screen recognition
# - Safety mechanisms
# - Performance benchmarks
```

### Integration Tests
```bash
# Test virtual desktop setup
python -m pytest tests/desktop/test_display_manager.py -v

# Test automation pipeline
python -m pytest tests/desktop/test_automation.py -v

# Test safety isolation
python -m pytest tests/desktop/test_safety_isolation.py -v
```

### Performance Tests
```python
def test_automation_speed():
    """Test automation actions meet speed requirements"""
    controller = DesktopController()

    # Test click speed
    start_time = time.time()
    result = controller.safe_click(500, 300)
    click_time = time.time() - start_time

    assert click_time < 0.1  # Click should be under 100ms

    # Test typing speed
    start_time = time.time()
    controller.safe_type("test command")
    type_time = time.time() - start_time

    assert type_time < 0.5  # Typing should be under 500ms

def test_screen_recognition_speed():
    """Test screen recognition meets performance requirements"""
    matcher = OpenCVMatcher()

    start_time = time.time()
    result = matcher.find_template(
        screenshot="test_screenshot.png",
        template="test_template.png"
    )
    recognition_time = time.time() - start_time

    assert recognition_time < 1.0  # Recognition under 1 second
```

## Deployment & Testing

### Setup Commands
```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y xvfb x11vnc xdotool wmctrl
sudo apt install -y python3-tk python3-pil python3-pil.imagetk
sudo apt install -y libgtk-3-dev libcairo2-dev

# 2. Setup virtual desktop
bash scripts/setup_virtual_desktop.sh

# 3. Install Python dependencies
pip install -r requirements/desktop_requirements.txt

# 4. Configure displays
bash scripts/configure_xorg.sh

# 5. Test dual desktop setup
bash scripts/test_dual_display.sh

# 6. Run comprehensive tests
python -m pytest tests/desktop/ -v --cov=src.desktop
```

### Validation Criteria
✅ **Must pass before considering task complete:**

1. **Functionality Tests**
   - Dual desktop isolation working
   - GUI automation accurate (90%+ success rate)
   - Screen recognition functional
   - User activity detection accurate

2. **Performance Tests**
   - Click actions < 100ms
   - Screen recognition < 1 second
   - Memory usage < 512MB
   - CPU usage < 30% during automation

3. **Safety Tests**
   - Complete isolation between desktops
   - Emergency stop working
   - Permission validation active
   - No interference with user activities

4. **Integration Tests**
   - Virtual desktop starts reliably
   - X11 configuration correct
   - All automation components integrated
   - Works with security applications

### Success Metrics

**Current Phase (Template-based)**
- ✅ 90%+ GUI automation success rate with templates
- ✅ <100ms automation response time
- ✅ Complete desktop isolation verified
- ✅ All safety mechanisms functional

**Future Phase (AI Vision)**
- ✅ AI correctly identifies GUI elements from screenshots
- ✅ AI makes autonomous decisions about actions to take
- ✅ AI adapts to new interfaces without template updates
- ✅ Evolution toward Claude Code-style visual understanding

## Configuration Files

### desktop_requirements.txt
```txt
# GUI Automation
pyautogui==0.9.54
pynput==1.7.6

# Screen Recognition
opencv-python==4.8.1.78
Pillow==10.1.0

# LLM Vision Integration
google-generativeai>=0.3.0
openai>=1.0.0

# Display Management
python-xlib==0.33
xvfbwrapper==0.2.9

# Process Monitoring
psutil==5.9.5

# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-mock==3.11.1
pytest-xvfb==2.0.0
```

### Desktop Configuration
```python
# src/desktop/config/desktop_config.py
DESKTOP_CONFIG = {
    'ai_display': ':1',
    'user_display': ':0',
    'resolution': '1920x1080',
    'color_depth': 24,
    'automation_delay': 0.1,
    'safety_enabled': True,
    'isolation_mode': 'strict',
    'emergency_stop_key': 'F12'
}

AUTOMATION_RULES = {
    'max_click_rate': 10,  # clicks per second
    'max_type_speed': 100,  # characters per second
    'screenshot_interval': 1.0,  # seconds
    'activity_check_interval': 5.0  # seconds
}
```

## Next Steps

**Immediate (Template Phase)**
1. Complete template-based automation for reliable GUI control
2. Create comprehensive template library for security tools
3. Test automation workflows with Burp Suite, Nmap, Wireshark

**Near Future (Hybrid Phase)**
1. Integrate AI vision to supplement templates
2. Handle edge cases where templates fail
3. Begin AI learning from template interactions

**Future Vision (Pure AI Phase)**
1. Transition to pure screenshot-to-action AI decision making
2. AI understands GUI context and makes autonomous choices
3. No templates needed - AI operates like Claude Code terminal
4. System becomes truly agentic with visual understanding

## Troubleshooting
Common issues and solutions:
- **Virtual desktop won't start**: Check X11 configuration and permissions
- **Automation not working**: Verify display environment variables
- **Poor recognition accuracy**: Calibrate templates and confidence thresholds
- **User interference**: Check isolation settings and activity monitoring
