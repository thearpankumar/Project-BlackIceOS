import logging
import os
import re
import time
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv


class PermissionGuard:
    """Validate and control AI automation permissions with security checks"""

    def __init__(self) -> None:
        load_dotenv()
        self.logger = logging.getLogger(__name__)

        # Permission configuration
        self.permissions_enabled = True
        self.strict_mode = os.getenv("PERMISSION_STRICT_MODE", "true").lower() == "true"

        # Allowed applications for AI automation
        self.allowed_applications = {
            'security_tools': [
                'burpsuite',
                'burp',
                'wireshark',
                'nmap',
                'masscan',
                'rustscan',
                'metasploit',
                'msfconsole',
                'msfvenom',
                'sqlmap',
                'nikto',
                'dirb',
                'dirbuster',
                'gobuster',
                'ffuf',
                'wfuzz',
            ],
            'system_tools': [
                'gnome-terminal',
                'x-terminal-emulator',
                'xterm',
                'konsole',
                'qterminal',
                'lxterminal',
                'terminator',
            ],
            'browsers': [
                'firefox',
                'firefox-esr',
                'chromium',
                'google-chrome',
                'brave-browser',
                'tor-browser',
            ],
            'utilities': [
                'galculator',
                'mousepad',
                'thunar',
                'nautilus',
                'pcmanfm',
                'gedit',
                'nano',
                'vim',
                'emacs',
            ],
            'analysis_tools': [
                'volatility',
                'autopsy',
                'sleuthkit',
                'binwalk',
                'strings',
                'hexdump',
                'xxd',
                'objdump',
                'readelf',
            ],
        }

        # Blocked dangerous commands and patterns
        self.blocked_patterns = self._load_blocked_patterns()

        # Allowed action types
        self.allowed_action_types = {
            'click',
            'type',
            'move',
            'scroll',
            'wait',
            'screenshot',
            'find_element',
            'open_application',
            'key_press',
            'drag_drop',
        }

        # Dangerous file paths to protect
        self.protected_paths = {
            '/etc',
            '/bin',
            '/sbin',
            '/usr/bin',
            '/usr/sbin',
            '/boot',
            '/dev',
            '/proc',
            '/sys',
            '/root',
            '/home/*/.ssh',
            '/home/*/.gnupg',
        }

        # Action rate limiting
        self.action_history: list[float] = []
        self.max_actions_per_minute = 100
        self.max_actions_per_second = 10

        # Permission callbacks
        self.permission_callbacks: list[Callable] = []

    def _load_blocked_patterns(self) -> list[str]:
        """Load blocked command patterns from environment"""
        blocked_env = os.getenv(
            "BLOCKED_PATTERNS",
            "rm -rf,sudo shutdown,mkfs.,dd if=,format ,delete *,chmod 777,passwd",
        )

        patterns = [pattern.strip() for pattern in blocked_env.split(",")]

        # Add additional dangerous patterns
        patterns.extend(
            [
                r'rm\s+.*\*',  # rm with wildcards
                r'sudo\s+.*',  # sudo commands (with exceptions)
                r'chmod\s+[67]\d\d',  # dangerous chmod permissions
                r'chown\s+.*',  # ownership changes
                r'mount\s+.*',  # filesystem mounting
                r'umount\s+.*',  # filesystem unmounting
                r'fdisk\s+.*',  # disk partitioning
                r'parted\s+.*',  # disk partitioning
                r'mkfs\.\w+',  # filesystem creation
                r'cryptsetup\s+.*',  # encryption setup
                r'iptables\s+.*',  # firewall changes
                r'systemctl\s+(stop|disable|mask)',  # dangerous systemctl
                r'service\s+\w+\s+(stop|disable)',  # service control
                r'kill\s+-9\s+.*',  # force kill
                r'killall\s+.*',  # kill all processes
                r'reboot|shutdown|halt',  # system shutdown
                r'echo\s+.*>\s*/etc/',  # writing to /etc
                r'wget\s+.*\|\s*sh',  # download and execute
                r'curl\s+.*\|\s*sh',  # download and execute
                r'nc\s+.*-e',  # netcat with execute
                r'python\s+.*-c.*exec',  # python exec
            ]
        )

        return patterns

    def validate_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Validate if automation action is allowed"""
        try:
            # Check if permissions are enabled
            if not self.permissions_enabled:
                return {'allowed': True, 'reason': 'Permissions disabled'}

            # Check action type
            if not self._validate_action_type(action):
                return {'allowed': False, 'reason': 'Invalid action type'}

            # Check rate limiting
            if not self._validate_rate_limit():
                return {'allowed': False, 'reason': 'Rate limit exceeded'}

            # Validate specific action
            validation_result = self._validate_specific_action(action)
            if not validation_result['allowed']:
                return validation_result

            # Record successful validation
            self._record_action(action)

            # Call permission callbacks
            for callback in self.permission_callbacks:
                try:
                    callback(action, True)
                except Exception as e:
                    self.logger.error(f"Permission callback error: {e}")

            return {'allowed': True, 'reason': 'Action validated'}

        except Exception as e:
            self.logger.error(f"Action validation failed: {e}")
            return {'allowed': False, 'reason': f'Validation error: {e}'}

    def _validate_action_type(self, action: dict[str, Any]) -> bool:
        """Validate action type is allowed"""
        action_type = action.get('type')

        if not action_type:
            self.logger.warning("Action missing type field")
            return False

        if action_type not in self.allowed_action_types:
            self.logger.warning(f"Action type not allowed: {action_type}")
            return False

        return True

    def _validate_rate_limit(self) -> bool:
        """Check if action rate limits are respected"""
        current_time = time.time()

        # Clean old entries
        self.action_history = [
            timestamp
            for timestamp in self.action_history
            if current_time - timestamp < 60  # Keep last minute
        ]

        # Check per-minute limit
        if len(self.action_history) >= self.max_actions_per_minute:
            self.logger.warning("Per-minute action rate limit exceeded")
            return False

        # Check per-second limit
        recent_actions = [
            timestamp
            for timestamp in self.action_history
            if current_time - timestamp < 1  # Last second
        ]

        if len(recent_actions) >= self.max_actions_per_second:
            self.logger.warning("Per-second action rate limit exceeded")
            return False

        return True

    def _validate_specific_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Validate specific action based on type"""
        action_type = action.get('type')

        if action_type == 'open_application':
            return self._validate_application_action(action)
        elif action_type == 'type':
            return self._validate_type_action(action)
        elif action_type == 'click':
            return self._validate_click_action(action)
        elif action_type == 'key_press':
            return self._validate_key_action(action)
        elif action_type in ['move', 'scroll', 'wait', 'screenshot', 'find_element']:
            return {'allowed': True, 'reason': f'{action_type} action allowed'}
        else:
            return {'allowed': False, 'reason': f'Unknown action type: {action_type}'}

    def _validate_application_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Validate application opening action"""
        app_name = action.get('app', '').lower()

        if not app_name:
            return {'allowed': False, 'reason': 'Application name missing'}

        # Check if application is in allowed list
        for _category, apps in self.allowed_applications.items():
            if any(allowed_app in app_name for allowed_app in apps):
                return {'allowed': True, 'reason': f'Application allowed ({_category})'}

        # In strict mode, block unknown applications
        if self.strict_mode:
            return {
                'allowed': False,
                'reason': f'Application not in allowed list: {app_name}',
            }

        # In non-strict mode, warn but allow
        self.logger.warning(f"Unknown application being opened: {app_name}")
        return {'allowed': True, 'reason': 'Application allowed (non-strict mode)'}

    def _validate_type_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Validate text typing action"""
        text = action.get('text', '')

        if not text:
            return {'allowed': True, 'reason': 'Empty text allowed'}

        # Check for dangerous command patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    'allowed': False,
                    'reason': f'Blocked pattern detected: {pattern}',
                }

        # Check for suspicious scripts
        if self._contains_suspicious_script(text):
            return {'allowed': False, 'reason': 'Suspicious script content detected'}

        # Check for file operations on protected paths
        if self._contains_protected_path_operation(text):
            return {'allowed': False, 'reason': 'Protected path operation detected'}

        return {'allowed': True, 'reason': 'Text content validated'}

    def _validate_click_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Validate click action"""
        x = action.get('x')
        y = action.get('y')

        if x is None or y is None:
            return {'allowed': False, 'reason': 'Click coordinates missing'}

        # Validate coordinates are reasonable
        if not (0 <= x <= 3840 and 0 <= y <= 2160):  # Max 4K resolution
            return {'allowed': False, 'reason': 'Click coordinates out of bounds'}

        # Check click rate (prevent click spam)
        button = action.get('button', 'left')
        if button not in ['left', 'right', 'middle']:
            return {'allowed': False, 'reason': f'Invalid mouse button: {button}'}

        return {'allowed': True, 'reason': 'Click action validated'}

    def _validate_key_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Validate key press action"""
        key = action.get('key', '')

        if not key:
            return {'allowed': False, 'reason': 'Key specification missing'}

        # Block dangerous key combinations
        dangerous_keys = [
            'ctrl+alt+del',
            'alt+f4',
            'ctrl+shift+esc',
            'alt+sysrq',
            'ctrl+alt+backspace',
        ]

        if key.lower() in dangerous_keys:
            return {
                'allowed': False,
                'reason': f'Dangerous key combination blocked: {key}',
            }

        return {'allowed': True, 'reason': 'Key action validated'}

    def _contains_suspicious_script(self, text: str) -> bool:
        """Check if text contains suspicious script content"""
        suspicious_patterns = [
            r'eval\s*\(',  # eval functions
            r'exec\s*\(',  # exec functions
            r'system\s*\(',  # system calls
            r'shell_exec\s*\(',  # shell execution
            r'passthru\s*\(',  # passthru functions
            r'base64_decode\s*\(',  # base64 decoding
            r'\$\(\(',  # command substitution
            r'`[^`]*`',  # backtick execution
            r'<script[^>]*>',  # script tags
            r'javascript:',  # javascript URIs
            r'vbscript:',  # vbscript URIs
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _contains_protected_path_operation(self, text: str) -> bool:
        """Check if text contains operations on protected paths"""
        # Look for file operations on protected paths
        file_operations = [
            r'>\s*/etc/',  # redirect to /etc
            r'rm\s+/etc/',  # remove from /etc
            r'cp\s+.*\s+/etc/',  # copy to /etc
            r'mv\s+.*\s+/etc/',  # move to /etc
            r'chmod\s+.*\s+/etc/',  # chmod /etc
            r'chown\s+.*\s+/etc/',  # chown /etc
        ]

        for operation in file_operations:
            if re.search(operation, text, re.IGNORECASE):
                return True

        return False

    def _record_action(self, action: dict[str, Any]) -> None:
        """Record action for rate limiting and auditing"""
        current_time = time.time()
        self.action_history.append(current_time)

        # Log action for audit trail
        action_type = action.get('type')
        self.logger.debug(f"Action validated: {action_type}")

    def add_permission_callback(self, callback: Callable) -> None:
        """Add callback for permission events"""
        self.permission_callbacks.append(callback)

    def remove_permission_callback(self, callback: Callable) -> None:
        """Remove permission callback"""
        if callback in self.permission_callbacks:
            self.permission_callbacks.remove(callback)

    def check_application_permission(self, app_name: str) -> bool:
        """Check if application is allowed"""
        app_lower = app_name.lower()

        for _category, apps in self.allowed_applications.items():
            if any(allowed_app in app_lower for allowed_app in apps):
                return True

        return not self.strict_mode  # Allow in non-strict mode

    def add_allowed_application(self, app_name: str, category: str = 'custom') -> bool:
        """Add application to allowed list"""
        try:
            if category not in self.allowed_applications:
                self.allowed_applications[category] = []

            if app_name not in self.allowed_applications[category]:
                self.allowed_applications[category].append(app_name)
                self.logger.info(f"Added application to allowed list: {app_name} ({category})")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error adding allowed application: {e}")
            return False

    def remove_allowed_application(self, app_name: str) -> bool:
        """Remove application from allowed list"""
        try:
            for _category, apps in self.allowed_applications.items():
                if app_name in apps:
                    apps.remove(app_name)
                    self.logger.info(f"Removed application from allowed list: {app_name}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error removing allowed application: {e}")
            return False

    def get_permission_status(self) -> dict[str, Any]:
        """Get current permission system status"""
        return {
            'enabled': self.permissions_enabled,
            'strict_mode': self.strict_mode,
            'allowed_applications': dict(self.allowed_applications),
            'blocked_patterns_count': len(self.blocked_patterns),
            'action_history_size': len(self.action_history),
            'rate_limits': {
                'per_minute': self.max_actions_per_minute,
                'per_second': self.max_actions_per_second,
            },
        }

    def enable_permissions(self) -> None:
        """Enable permission checking"""
        self.permissions_enabled = True
        self.logger.info("Permission checking enabled")

    def disable_permissions(self) -> None:
        """Disable permission checking (dangerous!)"""
        self.permissions_enabled = False
        self.logger.warning("Permission checking disabled - security risk!")

    def set_strict_mode(self, enabled: bool) -> None:
        """Enable/disable strict mode"""
        self.strict_mode = enabled
        self.logger.info(f"Strict mode {'enabled' if enabled else 'disabled'}")

    def clear_action_history(self) -> None:
        """Clear action history (reset rate limits)"""
        self.action_history.clear()
        self.logger.info("Action history cleared")

    def validate_command_safety(self, command: str) -> dict[str, Any]:
        """Validate command safety (for terminal commands)"""
        try:
            # Check against blocked patterns
            for pattern in self.blocked_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return {
                        'safe': False,
                        'reason': f'Blocked pattern detected: {pattern}',
                        'severity': 'high',
                    }

            # Check for suspicious content
            if self._contains_suspicious_script(command):
                return {
                    'safe': False,
                    'reason': 'Suspicious script content detected',
                    'severity': 'high',
                }

            # Check for protected path operations
            if self._contains_protected_path_operation(command):
                return {
                    'safe': False,
                    'reason': 'Protected path operation detected',
                    'severity': 'medium',
                }

            return {'safe': True, 'reason': 'Command appears safe', 'severity': 'low'}

        except Exception as e:
            return {
                'safe': False,
                'reason': f'Validation error: {e}',
                'severity': 'high',
            }
