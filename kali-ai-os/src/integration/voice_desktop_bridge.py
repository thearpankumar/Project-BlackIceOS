import logging
import re
from typing import Any

import google.generativeai as genai

from auth.auth_client import AuthClient
from desktop.automation.desktop_controller import DesktopController
from voice.recognition.audio_processor import AudioProcessor


class VoiceDesktopBridge:
    """Bridge between voice commands and desktop automation"""

    def __init__(
        self, audio_processor: AudioProcessor, desktop_controller: DesktopController
    ) -> None:
        self.audio_processor = audio_processor
        self.desktop_controller = desktop_controller
        self.auth_client: AuthClient | None = None

        self.logger = logging.getLogger(__name__)

        # Command patterns for different security tools
        self.command_patterns = {
            'burpsuite': [
                r'(?:open|start|launch).*burp\s*suite',
                r'burp.*(?:scan|proxy|configure)',
                r'configure.*proxy.*(?:for|target)',
                r'start.*(?:burp|proxy).*scan',
            ],
            'terminal': [
                r'(?:open|start).*terminal',
                r'run.*(?:nmap|metasploit|msfconsole)',
                r'execute.*(?:command|script)',
                r'(?:nmap|masscan|rustscan).*scan',
            ],
            'wireshark': [
                r'(?:open|start).*wireshark',
                r'capture.*(?:traffic|packets)',
                r'analyze.*(?:network|traffic)',
                r'start.*packet.*capture',
            ],
            'browser': [
                r'(?:open|browse).*(?:website|url|browser)',
                r'navigate.*to.*(?:http|www)',
                r'visit.*(?:site|page|url)',
            ],
            'filemanager': [
                r'(?:open|start).*(?:file|files).*(?:manager|browser|explorer)',
                r'(?:open|browse).*(?:folder|directory)',
                r'(?:show|display).*(?:file|files)',
                r'file.*(?:manager|browser)',
                r'files.*manager',
            ],
            'calculator': [r'(?:open|start).*calculator', r'(?:open|launch).*calc'],
        }

        # VM optimization settings
        self.optimization_settings = {
            'screenshot_quality': 75,
            'animation_delay': 0.2,
            'max_concurrent_actions': 2,
            'template_confidence': 0.75,
            'ocr_confidence': 70,
        }

    def set_auth_client(self, auth_client: AuthClient) -> None:
        """Set the authentication client for API key access"""
        self.auth_client = auth_client

    def _get_auth_client(self) -> AuthClient | None:
        """Get the authentication client"""
        return self.auth_client

    def translate_command_to_actions(self, voice_command: str) -> list[dict[str, Any]]:
        """Translate voice command to desktop automation actions"""
        try:
            command_lower = voice_command.lower()
            actions = []

            # Identify the target tool/application
            target_tool = self._identify_target_tool(command_lower)

            if target_tool == 'burpsuite':
                actions.extend(self._create_burpsuite_actions(command_lower))
            elif target_tool == 'terminal':
                actions.extend(self._create_terminal_actions(command_lower))
            elif target_tool == 'wireshark':
                actions.extend(self._create_wireshark_actions(command_lower))
            elif target_tool == 'browser':
                actions.extend(self._create_browser_actions(command_lower))
            elif target_tool == 'filemanager':
                actions.extend(self._create_filemanager_actions(command_lower))
            elif target_tool == 'calculator':
                actions.extend(self._create_calculator_actions(command_lower))
            else:
                # Generic command processing using AI
                actions.extend(self._create_ai_assisted_actions(voice_command))

            return actions

        except Exception as e:
            self.logger.error(f"Command translation failed: {e}")
            return []

    def _identify_target_tool(self, command: str) -> str:
        """Identify which security tool the command is targeting"""
        for tool, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return tool
        return 'unknown'

    def _create_burpsuite_actions(self, command: str) -> list[dict[str, Any]]:
        """Create action sequence for Burp Suite commands"""
        actions = []

        # Always start by opening Burp Suite
        actions.append({"type": "open_application", "app": "burpsuite"})
        actions.append({"type": "wait_for_startup", "duration": "30"})

        # Check for proxy configuration
        if 'proxy' in command or 'configure' in command:
            actions.append(
                {
                    "type": "click_element",
                    "template": "templates/burpsuite/proxy_tab.png",
                }
            )
            actions.append({"type": "wait", "duration": "1"})

            # Extract target if mentioned
            target_match = re.search(
                r'(?:target|for)\s+([a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?)', command
            )
            if target_match:
                target = target_match.group(1)
                actions.append({"type": "configure_proxy", "target": target})

        # Check for scan commands
        if 'scan' in command:
            actions.append({"type": "start_scan"})
            actions.append({"type": "wait_for_completion"})
            actions.append({"type": "screenshot", "filename": "burp_scan_result.png"})

        return actions

    def _create_terminal_actions(self, command: str) -> list[dict[str, Any]]:
        """Create action sequence for terminal commands"""
        actions = []

        actions.append({"type": "open_application", "app": "terminal"})
        actions.append({"type": "wait", "duration": "2"})

        # Extract and execute command
        if 'nmap' in command:
            # Extract target from command
            target_match = re.search(r'(?:scan|nmap)\s+([a-zA-Z0-9.-]+)', command)
            if target_match:
                target = target_match.group(1)
                nmap_command = f"nmap -sS -A {target}"
                if 'stealth' in command:
                    nmap_command = f"nmap -sS {target}"
                actions.append({"type": "type", "text": nmap_command})
                actions.append({"type": "key_press", "key": "Return"})

        elif 'metasploit' in command or 'msfconsole' in command:
            actions.append({"type": "type", "text": "msfconsole"})
            actions.append({"type": "key_press", "key": "Return"})

        return actions

    def _create_wireshark_actions(self, command: str) -> list[dict[str, Any]]:
        """Create action sequence for Wireshark commands"""
        actions = []

        actions.append({"type": "open_application", "app": "wireshark"})
        actions.append({"type": "wait_for_startup", "duration": "10"})

        if 'capture' in command:
            actions.append(
                {
                    "type": "click_element",
                    "template": "templates/wireshark/start_capture.png",
                }
            )

        return actions

    def _create_browser_actions(self, command: str) -> list[dict[str, Any]]:
        """Create action sequence for browser commands"""
        actions = []

        actions.append({"type": "open_application", "app": "firefox"})
        actions.append({"type": "wait", "duration": "3"})

        # Extract URL if mentioned
        url_match = re.search(r'(?:http[s]?://|www\.)[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?', command)
        if url_match:
            url = url_match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            actions.append(
                {
                    "type": "click_element",
                    "template": "templates/browser/address_bar.png",
                }
            )
            actions.append({"type": "type", "text": url})
            actions.append({"type": "key_press", "key": "Return"})

        return actions

    def _create_filemanager_actions(self, command: str) -> list[dict[str, Any]]:
        """Create action sequence for file manager commands"""
        actions = []

        actions.append({"type": "open_application", "app": "filemanager"})
        actions.append({"type": "wait", "duration": "2"})

        return actions

    def _create_calculator_actions(self, command: str) -> list[dict[str, Any]]:
        """Create action sequence for calculator commands"""
        actions = []

        actions.append({"type": "open_application", "app": "calculator"})
        actions.append({"type": "wait", "duration": "1"})

        return actions

    def _create_ai_assisted_actions(self, voice_command: str) -> list[dict[str, Any]]:
        """Use AI to create actions for complex/unknown commands"""
        if not self.auth_client:
            return []

        try:
            # Get API key for AI processing
            api_key = self.auth_client.get_decrypted_key("google_genai")
            if not api_key:
                return []

            # Use AI to interpret command and generate actions
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            prompt = f"""
            Convert this voice command into desktop automation actions for a cybersecurity VM:
            Command: "{voice_command}"

            Return a JSON list of actions with types like:
            - open_application (app: name)
            - click_element (template: path)
            - type (text: string)
            - wait (duration: seconds)
            - screenshot (filename: string)

            Focus on security tools like Burp Suite, nmap, Wireshark, Metasploit.
            """

            model.generate_content(prompt)

            # Parse AI response (simplified for this implementation)
            # In production, you'd parse the JSON response properly
            actions = [
                {"type": "open_application", "app": "terminal"},
                {"type": "wait", "duration": "2"},
                {"type": "type", "text": f"# AI interpreted command: {voice_command}"},
            ]

            return actions

        except Exception as e:
            self.logger.error(f"AI-assisted action creation failed: {e}")
            return []

    def execute_voice_command(self, command: str | None = None) -> dict[str, Any]:
        """Execute complete voice command pipeline"""
        try:
            # Get voice command if not provided
            if not command:
                if not self.desktop_controller._is_safe_to_act():
                    self.audio_processor.speak_text(
                        "Please wait, user activity detected. I'll try again in a moment."
                    )
                    return {"success": False, "error": "User activity detected"}

                command = self.audio_processor.transcribe_recording()

            if not command or command == "No command processed.":
                self.audio_processor.speak_text(
                    "I didn't understand that command. Please try again."
                )
                return {"success": False, "error": "No valid command received"}

            self.logger.info(f"Processing command: {command}")

            # Translate to actions
            actions = self.translate_command_to_actions(command)

            if not actions:
                self.audio_processor.speak_text("I'm not sure how to execute that command.")
                return {
                    "success": False,
                    "error": "Could not translate command to actions",
                }

            # Execute actions (placeholder - implement action execution logic)
            result = {"success": True, "message": "Actions would be executed"}

            # Provide feedback
            if result["success"]:
                self.provide_voice_feedback(result)
            else:
                error_msg = result.get("error", "Unknown error occurred")
                self.audio_processor.speak_text(f"Command failed: {error_msg}")

            return result

        except Exception as e:
            self.logger.error(f"Voice command execution failed: {e}")
            self.audio_processor.speak_text("An error occurred while processing your command.")
            return {"success": False, "error": str(e)}

    def provide_voice_feedback(self, automation_results: dict[str, Any]) -> None:
        """Provide voice feedback based on automation results"""
        try:
            if not automation_results.get("success"):
                self.audio_processor.speak_text("Command execution failed.")
                return

            completed_actions = automation_results.get("completed_actions", 0)

            # Generate contextual feedback
            feedback_messages = [
                f"Command completed successfully. Executed {completed_actions} actions.",
                "Task completed. The security tool should now be ready for use.",
                "Done! You can check the results on the AI desktop.",
            ]

            # Check for specific results
            results = automation_results.get("results", [])
            for result in results:
                if result.get("type") == "screenshot" and result.get("success"):
                    feedback_messages.append("Screenshot captured for your review.")
                elif "scan" in str(result).lower() and result.get("success"):
                    feedback_messages.append("Security scan initiated successfully.")
                elif "vulnerability" in str(result).lower():
                    feedback_messages.append("Potential security issues detected.")

            # Speak the most relevant feedback
            feedback = feedback_messages[0] if feedback_messages else "Command completed."
            self.audio_processor.speak_text(feedback)

        except Exception as e:
            self.logger.error(f"Voice feedback failed: {e}")

    def get_current_desktop_state(self) -> dict[str, Any]:
        """Get current state of the desktop for context-aware commands"""
        try:
            # This would analyze the current desktop state
            # For now, return a mock state
            return {
                "active_applications": [],
                "current_display": ":1",
                "last_action": "none",
            }
        except Exception as e:
            self.logger.error(f"Failed to get desktop state: {e}")
            return {}

    def get_optimization_settings(self) -> dict[str, Any]:
        """Get current optimization settings for VM"""
        return self.optimization_settings.copy()

    def set_vm_optimization(self, settings: dict[str, Any]) -> None:
        """Update VM optimization settings"""
        self.optimization_settings.update(settings)
        # VM optimization settings updated (no corresponding method in desktop controller)
