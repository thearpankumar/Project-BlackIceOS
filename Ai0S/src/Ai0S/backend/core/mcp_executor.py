"""
MCP Executor - Bridge between MCP server and execution controller
Manages tool execution with security, monitoring, and error handling.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

from ...mcp_server.server import MCPServer
from ..security.security_framework import SecurityFramework, SecurityLevel, ThreatLevel
from .error_recovery import ErrorRecoverySystem
from .visual_monitor import get_visual_monitor
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of tool execution."""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    execution_time: float
    tool_name: str
    timestamp: datetime


class MCPExecutor:
    """Bridge between MCP server and execution controller with security and monitoring."""
    
    def __init__(self, 
                 mcp_server: MCPServer,
                 security_framework: SecurityFramework,
                 error_recovery: ErrorRecoverySystem):
        
        self.mcp_server = mcp_server
        self.security_framework = security_framework
        self.error_recovery = error_recovery
        self.settings = get_settings()
        
        # Execution tracking
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Tool categorization for security
        self.tool_categories = {
            # System tools - high security
            "system_command": ["system_tools"],
            "process_control": ["system_tools", "application_tools"],
            "admin_privileges": [],
            
            # File operations - medium security  
            "file_read": ["file_tools"],
            "file_write": ["file_tools"],
            "file_execute": ["file_tools", "system_tools"],
            
            # Network operations - medium security
            "network_access": ["browser_tools", "network_tools"],
            
            # UI operations - low security
            "ui_interaction": ["ui_interaction_tools", "application_tools"],
            
            # Safe operations - minimal security
            "data_processing": ["file_tools"],
        }
        
        # Performance monitoring
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "blocked_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
        
        logger.info("MCP Executor initialized")
    
    async def execute_tool(self, 
                          tool_name: str, 
                          parameters: Dict[str, Any],
                          requester: str = "execution_controller",
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute MCP tool with comprehensive security and monitoring.
        
        Returns:
            Dict with execution result, security info, and metadata
        """
        
        execution_id = f"exec_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # Create execution context
            exec_context = {
                "execution_id": execution_id,
                "tool_name": tool_name,
                "parameters": parameters,
                "requester": requester,
                "started_at": datetime.now(),
                "context": context or {}
            }
            
            # Track active execution
            self.active_executions[execution_id] = exec_context
            
            logger.info(f"Starting tool execution: {tool_name} (ID: {execution_id})")
            
            # Step 1: Security check
            security_result = await self._perform_security_check(
                tool_name, parameters, requester, exec_context
            )
            
            if not security_result["allowed"]:
                result = {
                    "success": False,
                    "error": f"Security check failed: {security_result['reason']}",
                    "security_blocked": True,
                    "threat_level": security_result.get("threat_level", "unknown")
                }
                
                self.execution_stats["blocked_executions"] += 1
                await self._record_execution(execution_id, result, time.time() - start_time)
                return result
            
            # Step 2: Pre-execution monitoring
            await self._pre_execution_monitoring(exec_context)
            
            # Step 3: Execute tool with error handling
            execution_result = await self._execute_with_monitoring(
                tool_name, parameters, exec_context
            )
            
            # Step 4: Post-execution analysis
            await self._post_execution_analysis(exec_context, execution_result)
            
            # Step 5: Update statistics
            execution_time = time.time() - start_time
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            if execution_result.get("success", False):
                self.execution_stats["successful_executions"] += 1
            else:
                self.execution_stats["failed_executions"] += 1
            
            # Calculate average
            self.execution_stats["average_execution_time"] = (
                self.execution_stats["total_execution_time"] / 
                self.execution_stats["total_executions"]
            )
            
            # Add execution metadata
            execution_result.update({
                "execution_id": execution_id,
                "execution_time": execution_time,
                "security_level": security_result.get("security_level"),
                "requester": requester
            })
            
            await self._record_execution(execution_id, execution_result, execution_time)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"MCP execution error: {e}")
            
            # Try error recovery
            recovery_result = await self._handle_execution_error(
                execution_id, e, exec_context
            )
            
            execution_time = time.time() - start_time
            self.execution_stats["failed_executions"] += 1
            
            result = {
                "success": False,
                "error": str(e),
                "execution_id": execution_id,
                "execution_time": execution_time,
                "recovery_attempted": recovery_result["attempted"],
                "recovery_successful": recovery_result.get("successful", False)
            }
            
            await self._record_execution(execution_id, result, execution_time)
            return result
            
        finally:
            # Cleanup
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _perform_security_check(self, 
                                    tool_name: str,
                                    parameters: Dict[str, Any],
                                    requester: str,
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security check before execution."""
        
        # Create operation description for security analysis
        operation_desc = f"Execute tool '{tool_name}' with parameters: {json.dumps(parameters)}"
        
        # Add context information
        security_context = {
            "tool_name": tool_name,
            "parameters": parameters,
            "requester": requester,
            "execution_context": context.get("context", {}),
            "estimated_execution_time": self._estimate_execution_time(tool_name, parameters)
        }
        
        # Perform security check
        allowed, reason, threat_level = await self.security_framework.check_security(
            operation_desc, security_context, requester
        )
        
        return {
            "allowed": allowed,
            "reason": reason,
            "threat_level": threat_level,
            "security_level": self.security_framework.security_level.value
        }
    
    def _estimate_execution_time(self, tool_name: str, parameters: Dict[str, Any]) -> int:
        """Estimate execution time for a tool."""
        
        # Simple heuristic-based estimation
        time_estimates = {
            "system_tools": 30,      # System commands can be slow
            "file_tools": 10,        # File operations usually fast
            "browser_tools": 60,     # Browser operations can be slow
            "ui_interaction_tools": 15,  # UI interactions medium speed
            "application_tools": 30,     # Application control medium speed
        }
        
        # Find tool category
        for category, tools in self.tool_categories.items():
            if any(tool_type in tool_name for tool_type in tools):
                return time_estimates.get(tools[0], 20)
        
        return 20  # Default estimate
    
    async def _pre_execution_monitoring(self, context: Dict[str, Any]) -> None:
        """Perform pre-execution monitoring and setup."""
        
        try:
            # Capture screen state before execution
            visual_monitor = get_visual_monitor()
            if visual_monitor:
                current_state = await visual_monitor.capture_and_analyze(force_analysis=True)
                context["pre_execution_screen_state"] = {
                    "screenshot_hash": current_state.screenshot_hash if current_state else None,
                    "active_window": current_state.active_window if current_state else None,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Log execution start
            logger.debug(f"Pre-execution monitoring complete for {context['execution_id']}")
            
        except Exception as e:
            logger.warning(f"Pre-execution monitoring failed: {e}")
    
    async def _execute_with_monitoring(self, 
                                     tool_name: str, 
                                     parameters: Dict[str, Any],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with real-time monitoring."""
        
        try:
            # Set execution timeout based on tool type
            timeout = self._get_execution_timeout(tool_name)
            
            # Execute tool with timeout
            result = await asyncio.wait_for(
                self.mcp_server.call_tool(tool_name, parameters),
                timeout=timeout
            )
            
            # Validate result format
            if not isinstance(result, dict):
                result = {"success": True, "result": result}
            
            # Ensure success field exists
            if "success" not in result:
                result["success"] = True
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Tool execution timeout: {tool_name}")
            return {
                "success": False,
                "error": f"Tool execution timeout after {timeout} seconds",
                "timeout": True
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__
            }
    
    def _get_execution_timeout(self, tool_name: str) -> float:
        """Get execution timeout for tool."""
        
        # Tool-specific timeouts
        timeouts = {
            "system_tools": 120.0,      # System commands - 2 minutes
            "file_tools": 30.0,         # File operations - 30 seconds
            "browser_tools": 180.0,     # Browser operations - 3 minutes
            "ui_interaction_tools": 60.0,  # UI interactions - 1 minute
            "application_tools": 90.0,      # Application control - 1.5 minutes
        }
        
        # Find appropriate timeout
        for category, tools in self.tool_categories.items():
            if any(tool_type in tool_name for tool_type in tools):
                return timeouts.get(tools[0], 60.0)
        
        return 60.0  # Default 1 minute
    
    async def _post_execution_analysis(self, 
                                     context: Dict[str, Any], 
                                     result: Dict[str, Any]) -> None:
        """Perform post-execution analysis and monitoring."""
        
        try:
            # Capture screen state after execution
            visual_monitor = get_visual_monitor()
            if visual_monitor:
                post_state = await visual_monitor.capture_and_analyze(force_analysis=True)
                
                if post_state:
                    context["post_execution_screen_state"] = {
                        "screenshot_hash": post_state.screenshot_hash,
                        "active_window": post_state.active_window,
                        "detected_changes": post_state.detected_changes,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Analyze changes
                    pre_state = context.get("pre_execution_screen_state", {})
                    changes = await self._analyze_execution_changes(pre_state, post_state)
                    context["execution_changes"] = changes
            
            # Validate execution result
            await self._validate_execution_result(context, result)
            
            logger.debug(f"Post-execution analysis complete for {context['execution_id']}")
            
        except Exception as e:
            logger.warning(f"Post-execution analysis failed: {e}")
    
    async def _analyze_execution_changes(self, 
                                       pre_state: Dict[str, Any], 
                                       post_state) -> Dict[str, Any]:
        """Analyze changes between pre and post execution states."""
        
        changes = {
            "screen_changed": False,
            "window_changed": False,
            "ui_changes": [],
            "confidence": 0.0
        }
        
        try:
            # Compare screenshot hashes
            pre_hash = pre_state.get("screenshot_hash")
            post_hash = post_state.screenshot_hash
            
            if pre_hash and post_hash and pre_hash != post_hash:
                changes["screen_changed"] = True
            
            # Compare active windows
            pre_window = pre_state.get("active_window")
            post_window = post_state.active_window
            
            if pre_window != post_window:
                changes["window_changed"] = True
                changes["window_change"] = f"{pre_window} -> {post_window}"
            
            # Analyze UI changes
            if post_state.detected_changes:
                changes["ui_changes"] = post_state.detected_changes
            
            # Calculate confidence based on detected changes
            change_count = len([c for c in changes.values() if c])
            changes["confidence"] = min(change_count * 0.3, 1.0)
            
        except Exception as e:
            logger.debug(f"Change analysis error: {e}")
        
        return changes
    
    async def _validate_execution_result(self, 
                                       context: Dict[str, Any], 
                                       result: Dict[str, Any]) -> None:
        """Validate execution result and detect anomalies."""
        
        try:
            # Check for expected result format
            if not isinstance(result, dict):
                logger.warning(f"Invalid result format from tool {context['tool_name']}")
                return
            
            # Check for success indicators
            success = result.get("success", True)
            error = result.get("error")
            
            if not success and error:
                logger.info(f"Tool execution reported failure: {error}")
            
            # Validate result consistency with screen changes
            execution_changes = context.get("execution_changes", {})
            screen_changed = execution_changes.get("screen_changed", False)
            
            # Some tools should cause screen changes
            screen_change_expected = self._should_cause_screen_change(context["tool_name"])
            
            if screen_change_expected and not screen_changed:
                logger.debug(f"Expected screen change not detected for {context['tool_name']}")
            
        except Exception as e:
            logger.debug(f"Result validation error: {e}")
    
    def _should_cause_screen_change(self, tool_name: str) -> bool:
        """Check if tool should cause visible screen changes."""
        
        ui_tools = [
            "ui_interaction_tools",
            "browser_tools", 
            "application_tools"
        ]
        
        return any(ui_tool in tool_name for ui_tool in ui_tools)
    
    async def _handle_execution_error(self, 
                                    execution_id: str,
                                    error: Exception, 
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution error with recovery strategies."""
        
        try:
            # Prepare error context for recovery system
            error_context = {
                "execution_id": execution_id,
                "tool_name": context["tool_name"],
                "parameters": context["parameters"],
                "requester": context["requester"],
                "error": str(error),
                "error_type": type(error).__name__,
                "execution_context": context
            }
            
            # Attempt recovery
            recovery_success, recovery_message, adapted_plan = await self.error_recovery.handle_error(
                error, error_context
            )
            
            return {
                "attempted": True,
                "successful": recovery_success,
                "message": recovery_message,
                "adapted_plan": adapted_plan
            }
            
        except Exception as e:
            logger.error(f"Error recovery failed: {e}")
            return {
                "attempted": True,
                "successful": False,
                "message": f"Recovery system error: {e}"
            }
    
    async def _record_execution(self, 
                              execution_id: str, 
                              result: Dict[str, Any], 
                              execution_time: float) -> None:
        """Record execution for history and analysis."""
        
        try:
            execution_record = {
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
                "success": result.get("success", False),
                "tool_name": self.active_executions.get(execution_id, {}).get("tool_name"),
                "requester": self.active_executions.get(execution_id, {}).get("requester"),
                "error": result.get("error"),
                "security_blocked": result.get("security_blocked", False),
                "recovery_attempted": result.get("recovery_attempted", False)
            }
            
            self.execution_history.append(execution_record)
            
            # Limit history size
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]
            
        except Exception as e:
            logger.error(f"Failed to record execution: {e}")
    
    # Tool management methods
    
    async def list_available_tools(self) -> List[str]:
        """Get list of available MCP tools."""
        
        try:
            # Get tools from MCP server
            tools = await self.mcp_server.list_tools()
            return [tool["name"] for tool in tools]
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool."""
        
        try:
            tools = await self.mcp_server.list_tools()
            
            for tool in tools:
                if tool["name"] == tool_name:
                    return tool
            
            return {"error": f"Tool '{tool_name}' not found"}
            
        except Exception as e:
            logger.error(f"Failed to get tool info: {e}")
            return {"error": str(e)}
    
    def get_active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active executions."""
        
        return self.active_executions.copy()
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        
        stats = self.execution_stats.copy()
        
        # Add derived statistics
        total = stats["total_executions"]
        if total > 0:
            stats["success_rate"] = stats["successful_executions"] / total
            stats["failure_rate"] = stats["failed_executions"] / total
            stats["block_rate"] = stats["blocked_executions"] / total
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
            stats["block_rate"] = 0.0
        
        stats["active_executions"] = len(self.active_executions)
        stats["history_size"] = len(self.execution_history)
        
        return stats
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        
        return self.execution_history[-limit:]


# Global instance and utility functions
_mcp_executor_instance: Optional[MCPExecutor] = None


def initialize_mcp_executor(mcp_server: MCPServer,
                           security_framework: SecurityFramework,
                           error_recovery: ErrorRecoverySystem) -> MCPExecutor:
    """Initialize the global MCP executor instance."""
    
    global _mcp_executor_instance
    
    if _mcp_executor_instance is None:
        _mcp_executor_instance = MCPExecutor(mcp_server, security_framework, error_recovery)
        logger.info("Global MCP executor initialized")
    
    return _mcp_executor_instance


def get_mcp_executor() -> Optional[MCPExecutor]:
    """Get the global MCP executor instance."""
    
    return _mcp_executor_instance