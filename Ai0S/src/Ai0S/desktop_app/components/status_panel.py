"""
Status Panel - System status and metrics display
Professional system monitoring panel with real-time updates and health indicators.
"""

import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

import customtkinter as ctk

from ..themes.professional_theme import professional_theme
from ...utils.platform_detector import get_system_environment


logger = logging.getLogger(__name__)


class StatusPanel(ctk.CTkFrame):
    """Professional status panel with system metrics and health monitoring."""
    
    def __init__(self, parent, theme=None):
        super().__init__(parent)
        
        # Store theme (use provided theme or fallback)
        self.theme = theme if theme else professional_theme
        
        self.system_env = get_system_environment()
        
        # Status data
        self.system_metrics = {}
        self.ai_status = {"status": "disconnected", "last_response_time": 0}
        self.mcp_status = {"status": "disconnected", "tools_available": 0}
        self.execution_status = {"state": "idle", "current_plan": None}
        
        # Update settings
        self.update_interval = 5  # seconds
        self.auto_update = True
        
        # Setup UI
        self._setup_ui()
        
        # Start auto-updates
        if self.auto_update:
            self._start_auto_update()
    
    def _setup_ui(self) -> None:
        """Setup the status panel UI."""
        
        self.configure(
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_secondary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        
        # Main container
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            height=30
        )
        self.header_frame.pack(fill="x", pady=(0, 15))
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="System Status",
            font=professional_theme.get_font("heading_small"),
            text_color=professional_theme.get_color("text_primary")
        )
        self.title_label.pack(side="left")
        
        # System overview section
        self.system_section = self._create_status_section("System Overview")
        self.system_section.pack(fill="x", pady=(0, 15))
        
        # System metrics
        self.cpu_frame = self._create_metric_row(self.system_section, "CPU Usage", "0%", "info")
        self.memory_frame = self._create_metric_row(self.system_section, "Memory", "0%", "info")
        self.disk_frame = self._create_metric_row(self.system_section, "Disk", "0%", "info")
        
        # AI Services section
        self.ai_section = self._create_status_section("AI Services")
        self.ai_section.pack(fill="x", pady=(0, 15))
        
        self.ai_models_frame = self._create_status_row(self.ai_section, "AI Models", "Disconnected", "error")
        self.mcp_server_frame = self._create_status_row(self.ai_section, "MCP Server", "Disconnected", "error")
        
        # Execution section
        self.execution_section = self._create_status_section("Execution Status")
        self.execution_section.pack(fill="x", pady=(0, 15))
        
        self.execution_state_frame = self._create_status_row(self.execution_section, "State", "Idle", "success")
        self.current_task_frame = self._create_info_row(self.execution_section, "Current Task", "None")
        
        # Network section
        self.network_section = self._create_status_section("Network")
        self.network_section.pack(fill="x")
        
        # Get network interfaces
        self.network_interfaces = self._get_network_interfaces()
        self.network_widgets = []
        
        for interface in self.network_interfaces:
            interface_frame = self._create_info_row(
                self.network_section, 
                interface["name"], 
                interface["status"]
            )
            self.network_widgets.append({
                "name": interface["name"],
                "frame": interface_frame
            })
    
    def _create_status_section(self, title: str) -> ctk.CTkFrame:
        """Create a status section with title."""
        
        section_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        
        # Section header
        header = ctk.CTkFrame(
            section_frame,
            fg_color="transparent",
            height=30
        )
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_primary")
        )
        title_label.pack(side="left")
        
        return section_frame
    
    def _create_metric_row(self, parent: ctk.CTkFrame, label: str, value: str, status_type: str) -> Dict[str, Any]:
        """Create a metric row with progress bar."""
        
        row_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=40
        )
        row_frame.pack(fill="x", padx=10, pady=2)
        row_frame.pack_propagate(False)
        
        # Label
        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_primary"),
            width=80
        )
        label_widget.pack(side="left", padx=(0, 10))
        
        # Progress bar
        progress_bar = ctk.CTkProgressBar(
            row_frame,
            height=15,
            corner_radius=0,
            width=150
        )
        progress_bar.pack(side="left", padx=(0, 10))
        progress_bar.set(0)
        
        # Value label
        value_label = ctk.CTkLabel(
            row_frame,
            text=value,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_secondary"),
            width=50
        )
        value_label.pack(side="left")
        
        return {
            "frame": row_frame,
            "label": label_widget,
            "progress": progress_bar,
            "value": value_label
        }
    
    def _create_status_row(self, parent: ctk.CTkFrame, label: str, status: str, status_type: str) -> Dict[str, Any]:
        """Create a status row with indicator."""
        
        row_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=30
        )
        row_frame.pack(fill="x", padx=10, pady=2)
        row_frame.pack_propagate(False)
        
        # Label
        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_primary")
        )
        label_widget.pack(side="left", padx=(0, 10))
        
        # Status indicator
        indicator_color = self._get_status_color(status_type)
        
        indicator_label = ctk.CTkLabel(
            row_frame,
            text="●",
            font=("Arial", 14),
            text_color=indicator_color,
            width=20
        )
        indicator_label.pack(side="left", padx=(0, 5))
        
        # Status text
        status_label = ctk.CTkLabel(
            row_frame,
            text=status,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_secondary")
        )
        status_label.pack(side="left")
        
        return {
            "frame": row_frame,
            "label": label_widget,
            "indicator": indicator_label,
            "status": status_label
        }
    
    def _create_info_row(self, parent: ctk.CTkFrame, label: str, info: str) -> Dict[str, Any]:
        """Create an info row without status indicator."""
        
        row_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=25
        )
        row_frame.pack(fill="x", padx=10, pady=2)
        row_frame.pack_propagate(False)
        
        # Label
        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_primary")
        )
        label_widget.pack(side="left", padx=(0, 10))
        
        # Info text
        info_label = ctk.CTkLabel(
            row_frame,
            text=info,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        info_label.pack(side="right")
        
        return {
            "frame": row_frame,
            "label": label_widget,
            "info": info_label
        }
    
    def _get_status_color(self, status_type: str) -> str:
        """Get color for status type."""
        
        colors = {
            "success": professional_theme.get_color("success"),
            "warning": professional_theme.get_color("warning"),
            "error": professional_theme.get_color("error"),
            "info": professional_theme.get_color("info")
        }
        
        return colors.get(status_type, professional_theme.get_color("text_muted"))
    
    def _get_network_interfaces(self) -> list:
        """Get network interface information."""
        
        try:
            interfaces = []
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, addresses in net_if_addrs.items():
                if interface_name.startswith("lo"):  # Skip loopback
                    continue
                
                # Get interface status
                stats = net_if_stats.get(interface_name)
                is_up = stats.isup if stats else False
                
                # Get IP addresses
                ip_addresses = []
                for addr in addresses:
                    if addr.family.name in ['AF_INET', 'AF_INET6']:
                        ip_addresses.append(addr.address)
                
                status = "Connected" if is_up and ip_addresses else "Disconnected"
                
                interfaces.append({
                    "name": interface_name,
                    "status": status,
                    "is_up": is_up,
                    "addresses": ip_addresses
                })
            
            return interfaces[:3]  # Limit to 3 interfaces
            
        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")
            return []
    
    def _start_auto_update(self) -> None:
        """Start automatic status updates."""
        
        if self.auto_update:
            self._update_all_status()
            self.after(self.update_interval * 1000, self._start_auto_update)
    
    def _update_all_status(self) -> None:
        """Update all status information."""
        
        try:
            # Update system metrics
            self._update_system_metrics()
            
            # Update UI elements
            self._update_system_ui()
            
        except Exception as e:
            logger.error(f"Status update error: {e}")
    
    def _update_system_metrics(self) -> None:
        """Update system performance metrics."""
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            self.system_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk_percent,
                "disk_free_gb": disk.free / (1024**3),
                "net_bytes_sent": net_io.bytes_sent if net_io else 0,
                "net_bytes_recv": net_io.bytes_recv if net_io else 0,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def _update_system_ui(self) -> None:
        """Update system status UI elements."""
        
        if not self.system_metrics:
            return
        
        # Update CPU
        cpu_percent = self.system_metrics.get("cpu_percent", 0)
        self.cpu_frame["progress"].set(cpu_percent / 100)
        self.cpu_frame["value"].configure(text=f"{cpu_percent:.1f}%")
        
        # Update Memory
        memory_percent = self.system_metrics.get("memory_percent", 0)
        self.memory_frame["progress"].set(memory_percent / 100)
        memory_available = self.system_metrics.get("memory_available_gb", 0)
        self.memory_frame["value"].configure(text=f"{memory_percent:.1f}% ({memory_available:.1f}GB free)")
        
        # Update Disk
        disk_percent = self.system_metrics.get("disk_percent", 0)
        self.disk_frame["progress"].set(disk_percent / 100)
        disk_free = self.system_metrics.get("disk_free_gb", 0)
        self.disk_frame["value"].configure(text=f"{disk_percent:.1f}% ({disk_free:.1f}GB free)")
    
    def update_ai_status(self, status: str, response_time: Optional[float] = None) -> None:
        """Update AI services status."""
        
        self.ai_status["status"] = status
        if response_time is not None:
            self.ai_status["last_response_time"] = response_time
        
        # Update UI
        status_type = "success" if status == "connected" else "error"
        status_text = status.title()
        
        if response_time:
            status_text += f" ({response_time:.0f}ms)"
        
        self.ai_models_frame["status"].configure(text=status_text)
        self.ai_models_frame["indicator"].configure(
            text_color=self._get_status_color(status_type)
        )
    
    def update_mcp_status(self, status: str, tools_available: int = 0) -> None:
        """Update MCP server status."""
        
        self.mcp_status["status"] = status
        self.mcp_status["tools_available"] = tools_available
        
        # Update UI
        status_type = "success" if status == "connected" else "error"
        status_text = status.title()
        
        if tools_available > 0:
            status_text += f" ({tools_available} tools)"
        
        self.mcp_server_frame["status"].configure(text=status_text)
        self.mcp_server_frame["indicator"].configure(
            text_color=self._get_status_color(status_type)
        )
    
    def update_execution_status(self, state: str, current_task: Optional[str] = None) -> None:
        """Update execution status."""
        
        self.execution_status["state"] = state
        self.execution_status["current_plan"] = current_task
        
        # Update UI
        state_colors = {
            "idle": "success",
            "planning": "info",
            "executing": "warning",
            "completed": "success",
            "failed": "error",
            "cancelled": "warning"
        }
        
        status_type = state_colors.get(state.lower(), "info")
        
        self.execution_state_frame["status"].configure(text=state.title())
        self.execution_state_frame["indicator"].configure(
            text_color=self._get_status_color(status_type)
        )
        
        # Update current task
        task_text = current_task if current_task else "None"
        self.current_task_frame["info"].configure(text=task_text)
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        
        if not self.system_metrics:
            return {"status": "unknown", "details": "No metrics available"}
        
        # Calculate overall health
        cpu_healthy = self.system_metrics.get("cpu_percent", 0) < 80
        memory_healthy = self.system_metrics.get("memory_percent", 0) < 85
        disk_healthy = self.system_metrics.get("disk_percent", 0) < 90
        
        ai_healthy = self.ai_status["status"] == "connected"
        mcp_healthy = self.mcp_status["status"] == "connected"
        
        health_checks = [cpu_healthy, memory_healthy, disk_healthy, ai_healthy, mcp_healthy]
        health_score = sum(health_checks) / len(health_checks)
        
        if health_score >= 0.8:
            status = "healthy"
        elif health_score >= 0.6:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "score": health_score,
            "checks": {
                "cpu": cpu_healthy,
                "memory": memory_healthy,
                "disk": disk_healthy,
                "ai_services": ai_healthy,
                "mcp_server": mcp_healthy
            },
            "metrics": self.system_metrics.copy()
        }
    
    def export_status_report(self) -> str:
        """Export detailed status report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"System Status Report - {timestamp}\n"
        report += "=" * 50 + "\n\n"
        
        # System Information
        report += f"Operating System: {self.system_env.os} {self.system_env.os_version}\n"
        report += f"Architecture: {self.system_env.architecture}\n"
        report += f"Desktop Environment: {self.system_env.desktop_environment}\n\n"
        
        # System Metrics
        if self.system_metrics:
            report += "System Metrics:\n"
            report += f"  CPU Usage: {self.system_metrics.get('cpu_percent', 0):.1f}%\n"
            report += f"  Memory Usage: {self.system_metrics.get('memory_percent', 0):.1f}%\n"
            report += f"  Disk Usage: {self.system_metrics.get('disk_percent', 0):.1f}%\n"
            report += f"  Available Memory: {self.system_metrics.get('memory_available_gb', 0):.1f} GB\n"
            report += f"  Free Disk Space: {self.system_metrics.get('disk_free_gb', 0):.1f} GB\n\n"
        
        # Service Status
        report += "Service Status:\n"
        report += f"  AI Models: {self.ai_status['status']}\n"
        report += f"  MCP Server: {self.mcp_status['status']} ({self.mcp_status['tools_available']} tools)\n"
        report += f"  Execution State: {self.execution_status['state']}\n\n"
        
        # Health Summary
        health = self.get_system_health_summary()
        report += f"Overall Health: {health['status'].upper()} ({health['score']:.1%})\n"
        
        return report
    
    def update_system_info(self, *args, **kwargs) -> None:
        """Update system information display."""
        # This method would update the displayed system information
        # For now, just call the auto-update functionality
        self._update_system_metrics()