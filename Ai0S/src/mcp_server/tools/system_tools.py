"""
System Tools - Cross-platform system command execution
Safe system automation with security checks and monitoring.
"""

import asyncio
import base64
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil
import pyautogui

from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class SystemTools:
    """Cross-platform system automation tools."""
    
    def __init__(self):
        self.system_env = get_system_environment()
        self.settings = get_settings()
        
        # Command execution history
        self.command_history: List[Dict[str, Any]] = []
        
        # Security settings
        self.security_config = self.settings.get_security_config()
        
        # System monitoring
        self.system_stats = {
            "commands_executed": 0,
            "commands_blocked": 0,
            "screenshots_taken": 0,
            "system_checks": 0
        }
    
    async def execute_command(
        self, 
        command: str, 
        shell: bool = True, 
        timeout: int = 30,
        capture_output: bool = True
    ) -> str:
        """
        Execute system command with safety checks.
        
        Args:
            command: Command to execute
            shell: Execute through shell
            timeout: Timeout in seconds
            capture_output: Capture command output
            
        Returns:
            Command output or error message
        """
        try:
            logger.info(f"Executing command: {command}")
            
            # Security check
            if not self._is_command_safe(command):
                self.system_stats["commands_blocked"] += 1
                return f"Command blocked for security: {command}"
            
            # Record command attempt
            start_time = time.time()
            
            # Execute command
            if shell:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    text=True
                )
            else:
                process = subprocess.Popen(
                    command.split(),
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    text=True
                )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                self._record_command(command, "timeout", f"Command timed out after {timeout}s")
                return f"Command timed out after {timeout} seconds"
            
            execution_time = time.time() - start_time
            
            # Process results
            if return_code == 0:
                result = stdout if capture_output else "Command executed successfully"
                self._record_command(command, "success", result, execution_time)
                self.system_stats["commands_executed"] += 1
                return result if result else "Command completed successfully"
            else:
                error_msg = stderr if capture_output else f"Command failed with code {return_code}"
                self._record_command(command, "error", error_msg, execution_time)
                return f"Command failed (code {return_code}): {error_msg}"
                
        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {str(e)}"
            logger.error(error_msg)
            self._record_command(command, "exception", error_msg)
            return error_msg
    
    def _is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute."""
        
        command_lower = command.lower()
        
        # Check against blocked patterns
        for pattern in self.security_config["blocked_patterns"]:
            if pattern.lower() in command_lower:
                logger.warning(f"Blocked dangerous command pattern: {pattern}")
                return False
        
        # Check for sensitive operations
        sensitive_ops = [
            "rm -rf", "del /f", "format", "mkfs", "dd if=",
            "shutdown", "reboot", "halt", "poweroff",
            "chmod 777", "chown root", "su -", "sudo su",
            "> /dev/", "curl", "wget", "nc -", "netcat"
        ]
        
        for op in sensitive_ops:
            if op in command_lower:
                logger.warning(f"Blocked sensitive operation: {op}")
                return False
        
        return True
    
    def _record_command(
        self, 
        command: str, 
        status: str, 
        result: str, 
        execution_time: float = 0.0
    ) -> None:
        """Record command execution for audit."""
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "status": status,
            "result": result[:1000] if result else "",  # Limit result size
            "execution_time": execution_time,
            "system": {
                "os": self.system_env.os,
                "user": self._get_current_user()
            }
        }
        
        self.command_history.append(record)
        
        # Limit history size
        if len(self.command_history) > 500:
            self.command_history = self.command_history[-250:]
    
    def _get_current_user(self) -> str:
        """Get current system user."""
        try:
            if self.system_env.os == "Windows":
                import os
                return os.environ.get("USERNAME", "unknown")
            else:
                import os
                return os.environ.get("USER", "unknown")
        except:
            return "unknown"
    
    async def take_screenshot(
        self, 
        region: Optional[Dict[str, float]] = None, 
        filename: Optional[str] = None
    ) -> str:
        """
        Capture screenshot of screen or region.
        
        Args:
            region: Screen region to capture {"x": x, "y": y, "width": w, "height": h}
            filename: Save filename (optional)
            
        Returns:
            Screenshot information or error
        """
        try:
            logger.info(f"Taking screenshot, region: {region}, filename: {filename}")
            
            start_time = time.time()
            
            # Take screenshot
            if region:
                x, y = region["x"], region["y"]
                width, height = region["width"], region["height"]
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            else:
                screenshot = pyautogui.screenshot()
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # Save screenshot
            screenshot_dir = self.settings.get_data_paths()["screenshots"]
            screenshot_path = screenshot_dir / filename
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            screenshot.save(screenshot_path)
            
            # Get screenshot info
            file_size = screenshot_path.stat().st_size
            capture_time = time.time() - start_time
            
            self.system_stats["screenshots_taken"] += 1
            
            result = {
                "filename": filename,
                "path": str(screenshot_path),
                "size_bytes": file_size,
                "size_mb": round(file_size / 1024 / 1024, 2),
                "dimensions": screenshot.size,
                "capture_time": round(capture_time, 3),
                "region": region
            }
            
            logger.info(f"Screenshot saved: {screenshot_path} ({file_size} bytes)")
            return str(result)
            
        except Exception as e:
            error_msg = f"Failed to take screenshot: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def get_system_info(self, include_processes: bool = False) -> str:
        """
        Get comprehensive system information.
        
        Args:
            include_processes: Include running processes list
            
        Returns:
            System information dictionary
        """
        try:
            logger.info(f"Getting system info, include_processes: {include_processes}")
            
            self.system_stats["system_checks"] += 1
            
            # Basic system info
            info = {
                "os": {
                    "name": self.system_env.os,
                    "version": self.system_env.os_version,
                    "architecture": self.system_env.architecture
                },
                "display": {
                    "server": self.system_env.display_server,
                    "desktop_environment": self.system_env.desktop_environment,
                    "window_manager": self.system_env.window_manager,
                    "resolution": self.system_env.screen_resolution
                },
                "hardware": {
                    "cpu_count": self.system_env.cpu_count,
                    "memory_gb": self.system_env.memory_gb
                },
                "audio": {
                    "has_output": self.system_env.has_audio,
                    "has_microphone": self.system_env.has_microphone
                },
                "capabilities": self.system_env.capabilities
            }
            
            # Current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info["current_metrics"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / 1024**3, 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024**3, 2),
                "uptime_seconds": time.time() - psutil.boot_time()
            }
            
            # Network interfaces
            network_interfaces = []
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {"name": interface, "addresses": []}
                for addr in addrs:
                    if addr.family.name in ['AF_INET', 'AF_INET6']:
                        interface_info["addresses"].append({
                            "family": addr.family.name,
                            "address": addr.address,
                            "netmask": addr.netmask
                        })
                if interface_info["addresses"]:
                    network_interfaces.append(interface_info)
            
            info["network"] = network_interfaces
            
            # Include processes if requested
            if include_processes:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        process_info = proc.info
                        if process_info and process_info['name']:
                            processes.append({
                                "pid": process_info['pid'],
                                "name": process_info['name'],
                                "cpu_percent": round(process_info.get('cpu_percent', 0), 1),
                                "memory_percent": round(process_info.get('memory_percent', 0), 1)
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Sort by memory usage and limit to top 20
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
                info["top_processes"] = processes[:20]
            
            # Tool statistics
            info["tool_stats"] = self.system_stats.copy()
            
            return str(info)
            
        except Exception as e:
            error_msg = f"Failed to get system info: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def monitor_system_resources(self, duration: int = 10) -> str:
        """
        Monitor system resources for specified duration.
        
        Args:
            duration: Monitoring duration in seconds
            
        Returns:
            Resource monitoring report
        """
        try:
            logger.info(f"Monitoring system resources for {duration} seconds")
            
            measurements = []
            interval = 1.0  # 1 second intervals
            
            for i in range(duration):
                timestamp = time.time()
                
                # Get resource metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                # Get disk I/O
                disk_io = psutil.disk_io_counters()
                
                # Get network I/O
                net_io = psutil.net_io_counters()
                
                measurement = {
                    "timestamp": timestamp,
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": round(memory.used / 1024**3, 2),
                    "disk_read_mb": round(disk_io.read_bytes / 1024**2, 2) if disk_io else 0,
                    "disk_write_mb": round(disk_io.write_bytes / 1024**2, 2) if disk_io else 0,
                    "net_sent_mb": round(net_io.bytes_sent / 1024**2, 2) if net_io else 0,
                    "net_recv_mb": round(net_io.bytes_recv / 1024**2, 2) if net_io else 0
                }
                
                measurements.append(measurement)
                
                # Wait for next measurement (except on last iteration)
                if i < duration - 1:
                    await asyncio.sleep(interval)
            
            # Calculate statistics
            if measurements:
                cpu_values = [m["cpu_percent"] for m in measurements]
                memory_values = [m["memory_percent"] for m in measurements]
                
                report = {
                    "duration_seconds": duration,
                    "measurements_count": len(measurements),
                    "cpu_stats": {
                        "avg": round(sum(cpu_values) / len(cpu_values), 2),
                        "min": min(cpu_values),
                        "max": max(cpu_values)
                    },
                    "memory_stats": {
                        "avg": round(sum(memory_values) / len(memory_values), 2),
                        "min": min(memory_values),
                        "max": max(memory_values)
                    },
                    "measurements": measurements
                }
                
                return str(report)
            else:
                return "No measurements collected"
                
        except Exception as e:
            error_msg = f"Failed to monitor system resources: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def check_system_health(self) -> str:
        """
        Perform comprehensive system health check.
        
        Returns:
            System health report
        """
        try:
            logger.info("Performing system health check")
            
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "checks": {},
                "recommendations": [],
                "warnings": []
            }
            
            # CPU health check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                health_report["checks"]["cpu"] = "critical"
                health_report["warnings"].append(f"High CPU usage: {cpu_percent}%")
                health_report["overall_status"] = "warning"
            elif cpu_percent > 75:
                health_report["checks"]["cpu"] = "warning"
                health_report["warnings"].append(f"Elevated CPU usage: {cpu_percent}%")
                if health_report["overall_status"] == "healthy":
                    health_report["overall_status"] = "warning"
            else:
                health_report["checks"]["cpu"] = "healthy"
            
            # Memory health check
            memory = psutil.virtual_memory()
            if memory.percent > 95:
                health_report["checks"]["memory"] = "critical"
                health_report["warnings"].append(f"Critical memory usage: {memory.percent}%")
                health_report["overall_status"] = "critical"
            elif memory.percent > 85:
                health_report["checks"]["memory"] = "warning"
                health_report["warnings"].append(f"High memory usage: {memory.percent}%")
                if health_report["overall_status"] == "healthy":
                    health_report["overall_status"] = "warning"
            else:
                health_report["checks"]["memory"] = "healthy"
            
            # Disk health check
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                health_report["checks"]["disk"] = "critical"
                health_report["warnings"].append(f"Critical disk usage: {disk.percent}%")
                health_report["overall_status"] = "critical"
            elif disk.percent > 85:
                health_report["checks"]["disk"] = "warning"
                health_report["warnings"].append(f"High disk usage: {disk.percent}%")
                if health_report["overall_status"] == "healthy":
                    health_report["overall_status"] = "warning"
            else:
                health_report["checks"]["disk"] = "healthy"
            
            # Process health check (look for zombie processes)
            zombie_count = len([p for p in psutil.process_iter() 
                               if p.status() == psutil.STATUS_ZOMBIE])
            if zombie_count > 0:
                health_report["checks"]["processes"] = "warning"
                health_report["warnings"].append(f"Found {zombie_count} zombie processes")
            else:
                health_report["checks"]["processes"] = "healthy"
            
            # Generate recommendations
            if health_report["warnings"]:
                if "High CPU usage" in str(health_report["warnings"]):
                    health_report["recommendations"].append("Consider closing resource-intensive applications")
                if "memory usage" in str(health_report["warnings"]):
                    health_report["recommendations"].append("Close unused applications to free memory")
                if "disk usage" in str(health_report["warnings"]):
                    health_report["recommendations"].append("Clean up temporary files and logs")
            
            return str(health_report)
            
        except Exception as e:
            error_msg = f"System health check failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_command_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent command execution history."""
        return self.command_history[-limit:] if self.command_history else []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system tool usage statistics."""
        return {
            "stats": self.system_stats.copy(),
            "command_history_count": len(self.command_history),
            "uptime": time.time() - psutil.boot_time() if psutil else 0
        }