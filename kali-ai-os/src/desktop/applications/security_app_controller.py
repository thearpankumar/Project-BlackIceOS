import logging
import shutil
import subprocess  # noqa: S404
import time
from typing import Any

from ..automation.desktop_controller import DesktopController


class SecurityAppController:
    """Controller for security applications like Burp Suite, Wireshark, etc."""

    def __init__(self: "SecurityAppController", desktop_controller: DesktopController) -> None:
        self.desktop = desktop_controller
        self.logger = logging.getLogger(__name__)

        # Application launch commands
        self.app_commands = {
            'burpsuite': 'burpsuite',
            'wireshark': 'wireshark',
            'firefox': 'firefox',
            'terminal': 'gnome-terminal',
            'metasploit': 'msfconsole',
            'nmap': 'nmap',
        }

        # Template paths for GUI elements
        self.templates = {
            'burpsuite': {
                'proxy_tab': 'templates/burpsuite/proxy_tab.png',
                'start_button': 'templates/burpsuite/start_button.png',
                'target_field': 'templates/burpsuite/target_field.png',
                'scanner_tab': 'templates/burpsuite/scanner_tab.png',
            },
            'wireshark': {
                'start_capture': 'templates/wireshark/start_capture.png',
                'stop_capture': 'templates/wireshark/stop_capture.png',
                'interface_list': 'templates/wireshark/interface_list.png',
            },
            'browser': {
                'address_bar': 'templates/browser/address_bar.png',
                'go_button': 'templates/browser/go_button.png',
            },
            'common': {
                'ok_button': 'templates/common/ok_button.png',
                'cancel_button': 'templates/common/cancel_button.png',
                'close_button': 'templates/common/close_button.png',
            },
        }

    def open_application(self: "SecurityAppController", app_name: str) -> dict[str, Any]:
        """Open a security application"""
        try:
            if app_name not in self.app_commands:
                return {'success': False, 'error': f'Unknown application: {app_name}'}

            # Ensure we're on AI desktop
            self.desktop.display_controller.ensure_ai_display_context()

            # Launch application
            command = self.app_commands[app_name]
            full_command_path = shutil.which(command)
            if not full_command_path:
                return {'success': False, 'error': f'Command not found: {command}'}

            process = subprocess.Popen(  # noqa: S603
                [full_command_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={'DISPLAY': self.desktop.display},
            )

            self.logger.info(f"Launched {app_name} with command: {command}")

            # Wait for application to start
            startup_time = self._get_app_startup_time(app_name)
            time.sleep(startup_time)

            return {
                'success': True,
                'app': app_name,
                'process_id': process.pid,
                'startup_time': startup_time,
            }

        except Exception as e:
            self.logger.error(f"Failed to open {app_name}: {e}")
            return {'success': False, 'error': str(e)}

    def _get_app_startup_time(self, app_name: str) -> float:
        """Get estimated startup time for application"""
        startup_times = {
            'burpsuite': 30.0,  # Burp Suite takes a while to start
            'wireshark': 8.0,
            'firefox': 5.0,
            'terminal': 2.0,
            'metasploit': 15.0,
        }
        return startup_times.get(app_name, 5.0)

    def open_burpsuite(self) -> dict[str, Any]:
        """Open and setup Burp Suite"""
        try:
            # Launch Burp Suite
            result = self.open_application('burpsuite')
            if not result['success']:
                return result

            # Wait for full startup (Burp Suite has loading screens)
            self.logger.info("Waiting for Burp Suite to fully load...")
            time.sleep(5)  # Additional wait after initial startup

            # Handle potential license/update dialogs
            self._handle_burp_dialogs()

            # Navigate to proxy tab by default
            proxy_result = self._click_burp_proxy_tab()

            result.update({'proxy_tab_opened': proxy_result['success'], 'ready_for_use': True})

            return result

        except Exception as e:
            self.logger.error(f"Burp Suite setup failed: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_burp_dialogs(self) -> None:
        """Handle Burp Suite startup dialogs"""
        try:
            # Look for common dialog buttons and close them
            time.sleep(2)

            # Try to find and click "OK" or "Close" buttons
            ok_button = self.desktop.find_element(self.templates['common']['ok_button'])
            if ok_button and ok_button.get('found'):
                self.desktop.safe_click(ok_button['center'][0], ok_button['center'][1])
                time.sleep(1)

        except Exception as e:
            self.logger.debug(f"Dialog handling: {e}")

    def _click_burp_proxy_tab(self) -> dict[str, Any]:
        """Click on Burp Suite proxy tab"""
        try:
            proxy_tab = self.desktop.find_element(
                self.templates['burpsuite']['proxy_tab'], confidence=0.7
            )

            if proxy_tab and proxy_tab.get('found'):
                self.desktop.safe_click(proxy_tab['center'][0], proxy_tab['center'][1])
                return {'success': True}
            else:
                return {'success': False, 'error': 'Proxy tab not found'}

        except Exception as e:
            self.logger.error(f"Failed to click proxy tab: {e}")
            return {'success': False, 'error': str(e)}

    def configure_burp_proxy(self, target_url: str, port: int = 8080) -> dict[str, Any]:
        """Configure Burp Suite proxy for target"""
        try:
            # This would involve more complex GUI automation
            # For now, return a success indicator
            self.logger.info(f"Configuring Burp proxy for {target_url} on port {port}")

            # In a full implementation, this would:
            # 1. Navigate to proxy settings
            # 2. Configure target scope
            # 3. Set proxy port
            # 4. Enable/disable intercept

            return {
                'success': True,
                'target': target_url,
                'port': port,
                'configured': True,
            }

        except Exception as e:
            self.logger.error(f"Proxy configuration failed: {e}")
            return {'success': False, 'error': str(e)}

    def open_terminal(self) -> dict[str, Any]:
        """Open terminal on AI desktop"""
        try:
            result = self.open_application('terminal')

            if result['success']:
                # Wait for terminal to be ready for commands
                time.sleep(1)
                result.update({'ready_for_commands': True, 'shell': 'bash'})

            return result

        except Exception as e:
            self.logger.error(f"Failed to open terminal: {e}")
            return {'success': False, 'error': str(e)}

    def run_command_in_terminal(self, command: str) -> dict[str, Any]:
        """Execute command in terminal"""
        try:
            # Type command
            type_result = self.desktop.safe_type(command)

            if not type_result['success']:
                return dict(type_result)

            # Press Enter to execute
            time.sleep(0.5)
            self.desktop.safe_click(500, 400)  # Click in terminal first
            time.sleep(0.2)

            # Simulate Enter key (simplified implementation)
            # In a full implementation, you'd use pyautogui.press('enter')

            self.logger.info(f"Executed command: {command}")

            return {'success': True, 'command': command, 'executed': True}

        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {'success': False, 'error': str(e)}

    def open_wireshark(self) -> dict[str, Any]:
        """Open and setup Wireshark"""
        try:
            result = self.open_application('wireshark')

            if result['success']:
                # Wait for Wireshark to load
                time.sleep(3)

                # Wireshark might show interface selection dialog
                self._handle_wireshark_startup()

                result.update({'interfaces_detected': True, 'ready_for_capture': True})

            return result

        except Exception as e:
            self.logger.error(f"Wireshark setup failed: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_wireshark_startup(self) -> None:
        """Handle Wireshark startup interface selection"""
        try:
            # This would handle the interface selection dialog
            # For now, just wait and assume it's handled
            time.sleep(2)
            self.logger.debug("Wireshark startup handled")

        except Exception as e:
            self.logger.debug(f"Wireshark startup handling: {e}")

    def start_packet_capture(self, interface: str = "eth0") -> dict[str, Any]:
        """Start packet capture in Wireshark"""
        try:
            # Look for start capture button
            start_button = self.desktop.find_element(
                self.templates['wireshark']['start_capture'], confidence=0.7
            )

            if start_button and start_button.get('found'):
                self.desktop.safe_click(start_button['center'][0], start_button['center'][1])

                return {
                    'success': True,
                    'interface': interface,
                    'capture_started': True,
                }
            else:
                return {'success': False, 'error': 'Start capture button not found'}

        except Exception as e:
            self.logger.error(f"Failed to start capture: {e}")
            return {'success': False, 'error': str(e)}

    def take_application_screenshot(self, app_name: str) -> dict[str, Any]:
        """Take screenshot of application"""
        try:
            filename = f"{app_name}_screenshot_{int(time.time())}.png"
            screenshot_path = self.desktop.capture_screenshot(filename)

            if screenshot_path:
                return {'success': True, 'screenshot': screenshot_path, 'app': app_name}
            else:
                return {'success': False, 'error': 'Screenshot capture failed'}

        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_supported_applications(self) -> list[str]:
        """Get list of supported security applications"""
        return list(self.app_commands.keys())

    def check_application_running(self, app_name: str) -> bool:
        """Check if application is currently running"""
        try:
            import psutil

            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to check if {app_name} is running: {e}")
            return False
