import logging
import os
import subprocess
import time
from typing import Any

import psutil
from dotenv import load_dotenv


class IsolationManager:
    """Ensure AI operations don't affect user desktop with strict isolation"""

    def __init__(self) -> None:
        load_dotenv()
        self.logger = logging.getLogger(__name__)

        # Display configuration
        self.user_display = ":0"
        self.ai_display = os.getenv("AI_DISPLAY", ":1")
        self.isolation_active = True

        # Process monitoring
        self.monitored_processes: set[str] = set()
        self.ai_processes: set[str] = set()
        self.user_processes: set[str] = set()

        # Isolation violations
        self.violation_count = 0
        self.max_violations = 5
        self.violation_history: list[dict[str, Any]] = []

        # Allowed AI operations
        self.allowed_ai_applications = {
            'automation_tools': ['burpsuite', 'wireshark', 'nmap', 'metasploit'],
            'system_tools': ['gnome-terminal', 'x-terminal-emulator', 'xterm'],
            'browsers': ['firefox', 'firefox-esr', 'chromium'],
            'utilities': ['galculator', 'mousepad', 'thunar'],
        }

    def ensure_isolation(self) -> bool:
        """Ensure AI operations don't affect user desktop"""
        try:
            # Check current display
            if not self._verify_display_isolation():
                return False

            # Check process isolation
            if not self._verify_process_isolation():
                return False

            # Check window manager isolation
            if not self._verify_window_isolation():
                return False

            # Check resource usage
            if not self._verify_resource_isolation():
                return False

            return True

        except Exception as e:
            self.logger.error(f"Isolation verification failed: {e}")
            return False

    def _verify_display_isolation(self) -> bool:
        """Verify AI is operating on correct display"""
        try:
            current_display = os.environ.get('DISPLAY')

            if current_display != self.ai_display:
                self.logger.error(
                    f"Display isolation violation: AI on {current_display}, should be"
                    f" {self.ai_display}"
                )
                self._record_violation('display', f'Wrong display: {current_display}')

                # Try to fix automatically
                self._switch_to_ai_display()

                # Verify fix
                if os.environ.get('DISPLAY') != self.ai_display:
                    return False

            # Verify AI display exists and is functional
            if not self._verify_ai_display_functional():
                self.logger.error("AI display not functional")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Display isolation verification failed: {e}")
            return False

    def _verify_process_isolation(self) -> bool:
        """Verify processes are properly isolated"""
        try:
            current_ai_processes = self._get_ai_processes()
            current_user_processes = self._get_user_processes()

            # Check for process interference
            interference = current_ai_processes.intersection(current_user_processes)
            if interference:
                self.logger.error(f"Process isolation violation: {interference}")
                self._record_violation('process', f'Interfering processes: {interference}')
                return False

            # Update tracked processes
            self.ai_processes = current_ai_processes
            self.user_processes = current_user_processes

            return True

        except Exception as e:
            self.logger.error(f"Process isolation verification failed: {e}")
            return False

    def _verify_window_isolation(self) -> bool:
        """Verify window manager isolation"""
        try:
            # Check if AI windows are on correct display
            ai_windows = self._get_windows_on_display(self.ai_display)
            user_windows = self._get_windows_on_display(self.user_display)

            # Verify no window overlap
            if not self._verify_no_window_overlap(ai_windows, user_windows):
                self.logger.error("Window isolation violation detected")
                self._record_violation('window', 'Window overlap detected')
                return False

            return True

        except Exception as e:
            self.logger.error(f"Window isolation verification failed: {e}")
            return False

    def _verify_resource_isolation(self) -> bool:
        """Verify resource usage isolation"""
        try:
            # Check CPU usage by AI processes
            ai_cpu_usage = self._get_ai_cpu_usage()
            if ai_cpu_usage > 80.0:  # 80% CPU threshold
                self.logger.warning(f"High AI CPU usage: {ai_cpu_usage}%")
                self._record_violation('resource', f'High CPU usage: {ai_cpu_usage}%')

            # Check memory usage
            ai_memory_usage = self._get_ai_memory_usage()
            if ai_memory_usage > 2048:  # 2GB memory threshold
                self.logger.warning(f"High AI memory usage: {ai_memory_usage}MB")
                self._record_violation('resource', f'High memory usage: {ai_memory_usage}MB')

            return True

        except Exception as e:
            self.logger.error(f"Resource isolation verification failed: {e}")
            return False

    def _switch_to_ai_display(self) -> bool:
        """Switch to AI display"""
        try:
            os.environ['DISPLAY'] = self.ai_display

            # Verify the switch worked
            if os.environ.get('DISPLAY') == self.ai_display:
                self.logger.info(f"Switched to AI display: {self.ai_display}")
                return True
            else:
                self.logger.error("Failed to switch to AI display")
                return False

        except Exception as e:
            self.logger.error(f"Error switching to AI display: {e}")
            return False

    def _verify_ai_display_functional(self) -> bool:
        """Verify AI display is functional"""
        try:
            # Try to run a simple X11 command on the AI display
            result = subprocess.run(
                ['/usr/bin/xrandr', '--listmonitors'],
                env={'DISPLAY': self.ai_display},
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.returncode == 0

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            return False
        except Exception as e:
            self.logger.error(f"Error verifying AI display: {e}")
            return False

    def _get_ai_processes(self) -> set[str]:
        """Get processes associated with AI display"""
        ai_processes = set()

        try:
            for proc in psutil.process_iter(['pid', 'name', 'environ']):
                try:
                    proc_info = proc.info
                    if not proc_info['name']:
                        continue

                    # Check if process uses AI display
                    if proc_info['environ']:
                        display = proc_info['environ'].get('DISPLAY', '')
                        if display == self.ai_display:
                            ai_processes.add(proc_info['name'])

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error getting AI processes: {e}")

        return ai_processes

    def _get_user_processes(self) -> set[str]:
        """Get processes associated with user display"""
        user_processes = set()

        try:
            for proc in psutil.process_iter(['pid', 'name', 'environ']):
                try:
                    proc_info = proc.info
                    if not proc_info['name']:
                        continue

                    # Check if process uses user display
                    if proc_info['environ']:
                        display = proc_info['environ'].get('DISPLAY', '')
                        if display == self.user_display or display == '':
                            user_processes.add(proc_info['name'])

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error getting user processes: {e}")

        return user_processes

    def _get_windows_on_display(self, display: str) -> list[dict[str, Any]]:
        """Get windows on specific display"""
        windows = []

        try:
            # Use wmctrl to list windows
            result = subprocess.run(
                ['/usr/bin/wmctrl', '-l'],
                env={'DISPLAY': display},
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            windows.append(
                                {
                                    'id': parts[0],
                                    'desktop': parts[1],
                                    'pid': parts[2],
                                    'title': parts[3],
                                }
                            )

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            pass
        except Exception as e:
            self.logger.error(f"Error getting windows for {display}: {e}")

        return windows

    def _verify_no_window_overlap(self, ai_windows: list, user_windows: list) -> bool:
        """Verify no window overlap between displays"""
        try:
            # For now, just verify we have different window lists
            # In a more sophisticated implementation, we'd check window positions

            ai_titles = {w['title'] for w in ai_windows}
            user_titles = {w['title'] for w in user_windows}

            # Check for identical windows (potential overlap)
            overlap = ai_titles.intersection(user_titles)

            if overlap:
                self.logger.warning(f"Potential window overlap: {overlap}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error verifying window overlap: {e}")
            return False

    def _get_ai_cpu_usage(self) -> float:
        """Get CPU usage by AI processes"""
        total_cpu = 0.0

        try:
            for proc in psutil.process_iter(['pid', 'name', 'environ', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    if not proc_info['environ']:
                        continue

                    display = proc_info['environ'].get('DISPLAY', '')
                    if display == self.ai_display:
                        total_cpu += proc_info['cpu_percent'] or 0.0

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error getting AI CPU usage: {e}")

        return total_cpu

    def _get_ai_memory_usage(self) -> float:
        """Get memory usage by AI processes in MB"""
        total_memory = 0.0

        try:
            for proc in psutil.process_iter(['pid', 'name', 'environ', 'memory_info']):
                try:
                    proc_info = proc.info
                    if not proc_info['environ']:
                        continue

                    display = proc_info['environ'].get('DISPLAY', '')
                    if display == self.ai_display:
                        memory_info = proc_info['memory_info']
                        if memory_info:
                            total_memory += memory_info.rss / (1024 * 1024)  # Convert to MB

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error getting AI memory usage: {e}")

        return total_memory

    def _record_violation(self, violation_type: str, details: str) -> None:
        """Record isolation violation"""
        violation = {
            'type': violation_type,
            'details': details,
            'timestamp': time.time(),
            'count': self.violation_count + 1,
        }

        self.violation_history.append(violation)
        self.violation_count += 1

        self.logger.warning(
            f"Isolation violation #{self.violation_count}: {violation_type} - {details}"
        )

        # Check if we've exceeded max violations
        if self.violation_count >= self.max_violations:
            self.logger.critical(f"Maximum isolation violations reached ({self.max_violations})")
            self.emergency_isolation()

    def emergency_isolation(self) -> bool:
        """Emergency isolation of AI activities"""
        try:
            self.logger.critical("EMERGENCY ISOLATION ACTIVATED")

            # Stop all AI processes
            self._terminate_ai_processes()

            # Reset display environment
            os.environ['DISPLAY'] = self.user_display

            # Clear AI window states
            self._clear_ai_windows()

            # Reset isolation state
            self.isolation_active = False

            self.logger.critical("Emergency isolation completed")
            return True

        except Exception as e:
            self.logger.critical(f"Emergency isolation failed: {e}")
            return False

    def _terminate_ai_processes(self) -> None:
        """Terminate all AI-related processes"""
        try:
            terminated_count = 0

            for proc in psutil.process_iter(['pid', 'name', 'environ']):
                try:
                    proc_info = proc.info
                    if not proc_info['environ']:
                        continue

                    display = proc_info['environ'].get('DISPLAY', '')
                    if display == self.ai_display:
                        proc.terminate()
                        terminated_count += 1
                        self.logger.info(
                            f"Terminated AI process: {proc_info['name']} (PID: {proc_info['pid']})"
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self.logger.info(f"Terminated {terminated_count} AI processes")

        except Exception as e:
            self.logger.error(f"Error terminating AI processes: {e}")

    def _clear_ai_windows(self) -> None:
        """Clear AI windows from display"""
        try:
            # Close all windows on AI display
            subprocess.run(
                ['/usr/bin/wmctrl', '-c', ':ACTIVE:'],
                env={'DISPLAY': self.ai_display},
                capture_output=True,
                timeout=5,
            )

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            pass
        except Exception as e:
            self.logger.error(f"Error clearing AI windows: {e}")

    def get_isolation_status(self) -> dict[str, Any]:
        """Get current isolation status"""
        return {
            'active': self.isolation_active,
            'user_display': self.user_display,
            'ai_display': self.ai_display,
            'violation_count': self.violation_count,
            'ai_processes': len(self.ai_processes),
            'user_processes': len(self.user_processes),
            'recent_violations': (self.violation_history[-5:] if self.violation_history else []),
        }

    def reset_isolation_state(self) -> None:
        """Reset isolation violation state"""
        self.violation_count = 0
        self.violation_history.clear()
        self.isolation_active = True
        self.logger.info("Isolation state reset")

    def check_application_permission(self, app_name: str) -> bool:
        """Check if application is allowed for AI use"""
        app_lower = app_name.lower()

        for _category, apps in self.allowed_ai_applications.items():
            if any(allowed_app in app_lower for allowed_app in apps):
                return True

        self.logger.warning(f"Application not in allowed list: {app_name}")
        return False
