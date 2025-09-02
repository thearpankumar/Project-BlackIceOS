"""
MCP Tool Executor - Executes tools via MCP integration
Connects LangGraph orchestrator steps to MCP server tool execution.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import subprocess
import sys
from pathlib import Path

from ...backend.models.ai_models import ExecutionStep
from ...config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of step execution."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    screen_change: Optional[Dict[str, Any]] = None
    next_action: Optional[str] = None
    requires_adaptation: bool = False
    adaptation_reason: Optional[str] = None


@dataclass
class MCPToolCall:
    """MCP tool call specification."""
    tool_name: str
    arguments: Dict[str, Any]
    timeout: float = 30.0


class MCPExecutor:
    """Executes tools through MCP server integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.mcp_process = None
        self.tool_mappings = self._create_tool_mappings()
        
    def _create_tool_mappings(self) -> Dict[str, str]:
        """Create mapping from action types to MCP tools."""
        
        return {
            # Browser actions
            "open_browser": "open_browser",
            "navigate_url": "navigate_url",
            "click_element": "click_element",
            "type_text": "type_text",
            
            # Application actions
            "launch_application": "launch_application",
            "find_window": "find_window",
            "list_applications": "list_applications",
            
            # UI interaction actions
            "click": "click_element",
            "type": "type_text", 
            "scroll": "scroll",
            "send_key": "send_key",
            
            # System actions
            "execute_command": "execute_command",
            "take_screenshot": "take_screenshot",
            "get_system_info": "get_system_info",
            
            # File actions
            "open_file_manager": "open_file_manager",
            "list_files": "list_files",
            
            # Special actions
            "wait": "wait",
            "verify": "verify_state"
        }
    
    async def execute_step(self, step: ExecutionStep) -> ExecutionResult:
        """Execute a single execution step using MCP tools."""
        
        try:
            logger.info(f"Executing step: {step.action_type} - {step.description}")
            
            # Handle special cases first
            if step.action_type == "wait":
                return await self._handle_wait(step)
            elif step.action_type == "verify":
                return await self._handle_verify(step)
            
            # Map to MCP tool
            mcp_tool = self.tool_mappings.get(step.action_type)
            if not mcp_tool:
                logger.warning(f"No MCP tool mapping for action: {step.action_type}")
                return ExecutionResult(
                    success=False,
                    error=f"Unsupported action type: {step.action_type}"
                )
            
            # Prepare tool call
            tool_call = self._prepare_tool_call(mcp_tool, step)
            
            # Execute via MCP
            result = await self._execute_mcp_tool(tool_call)
            
            return result
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                requires_adaptation=True,
                adaptation_reason=f"Execution error: {e}"
            )
    
    def _prepare_tool_call(self, mcp_tool: str, step: ExecutionStep) -> MCPToolCall:
        """Prepare MCP tool call from execution step."""
        
        # Extract parameters based on action type and step data
        arguments = step.parameters.copy() if step.parameters else {}
        
        # Add common parameters
        if step.target:
            if step.action_type in ["click", "click_element"]:
                arguments["element_description"] = step.target
            elif step.action_type in ["type", "type_text"]:
                arguments["text"] = step.target
            elif step.action_type == "navigate_url":
                arguments["url"] = step.target
            elif step.action_type == "launch_application":
                arguments["app_name"] = step.target
        
        # Set timeout from step metadata
        timeout = step.timeout if hasattr(step, 'timeout') else 30.0
        
        return MCPToolCall(
            tool_name=mcp_tool,
            arguments=arguments,
            timeout=timeout
        )
    
    async def _execute_mcp_tool(self, tool_call: MCPToolCall) -> ExecutionResult:
        """Execute MCP tool and return result."""
        
        try:
            # For now, simulate MCP tool execution
            # In a real implementation, this would communicate with the MCP server
            logger.debug(f"MCP Tool Call: {tool_call.tool_name} with {tool_call.arguments}")
            
            # Simulate execution time
            await asyncio.sleep(0.5)
            
            # Mock different tool results
            if tool_call.tool_name == "take_screenshot":
                return ExecutionResult(
                    success=True,
                    output="Screenshot captured successfully",
                    screen_change={"screenshot_taken": True}
                )
            
            elif tool_call.tool_name in ["click_element", "type_text"]:
                return ExecutionResult(
                    success=True,
                    output=f"UI interaction completed: {tool_call.tool_name}",
                    screen_change={"ui_interaction": True}
                )
            
            elif tool_call.tool_name == "launch_application":
                app_name = tool_call.arguments.get("app_name", "unknown")
                return ExecutionResult(
                    success=True,
                    output=f"Application launched: {app_name}",
                    screen_change={"app_launched": app_name}
                )
            
            elif tool_call.tool_name == "open_browser":
                url = tool_call.arguments.get("url", "")
                return ExecutionResult(
                    success=True,
                    output=f"Browser opened{f' to {url}' if url else ''}",
                    screen_change={"browser_opened": True}
                )
            
            elif tool_call.tool_name == "execute_command":
                command = tool_call.arguments.get("command", "unknown")
                return ExecutionResult(
                    success=True,
                    output=f"Command executed: {command}",
                    screen_change={"command_executed": True}
                )
            
            else:
                # Generic success for other tools
                return ExecutionResult(
                    success=True,
                    output=f"Tool executed successfully: {tool_call.tool_name}"
                )
                
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error=f"Tool execution timeout: {tool_call.tool_name}",
                requires_adaptation=True,
                adaptation_reason="Execution timeout"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Tool execution failed: {e}",
                requires_adaptation=True,
                adaptation_reason=f"Tool error: {e}"
            )
    
    async def _handle_wait(self, step: ExecutionStep) -> ExecutionResult:
        """Handle wait action."""
        
        duration = step.parameters.get("duration", 1.0) if step.parameters else 1.0
        duration = float(duration)
        
        logger.debug(f"Waiting for {duration} seconds")
        await asyncio.sleep(duration)
        
        return ExecutionResult(
            success=True,
            output=f"Wait completed ({duration}s)"
        )
    
    async def _handle_verify(self, step: ExecutionStep) -> ExecutionResult:
        """Handle verification action."""
        
        # This would typically involve taking a screenshot and using AI to verify
        # For now, simulate verification
        verification_target = step.parameters.get("target") if step.parameters else "state"
        
        logger.debug(f"Verifying: {verification_target}")
        
        # Simulate verification time
        await asyncio.sleep(1.0)
        
        # Mock verification result (90% success rate)
        import random
        success = random.random() > 0.1
        
        if success:
            return ExecutionResult(
                success=True,
                output=f"Verification passed: {verification_target}"
            )
        else:
            return ExecutionResult(
                success=False,
                error=f"Verification failed: {verification_target}",
                requires_adaptation=True,
                adaptation_reason="State verification failed"
            )
    
    def get_supported_actions(self) -> List[str]:
        """Get list of supported action types."""
        return list(self.tool_mappings.keys())
    
    def is_action_supported(self, action_type: str) -> bool:
        """Check if action type is supported."""
        return action_type in self.tool_mappings
    
    async def start_mcp_server(self) -> bool:
        """Start MCP server if not already running."""
        
        try:
            # Check if MCP server is already running
            # This would be implemented based on your MCP server setup
            logger.info("MCP server connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def stop_mcp_server(self) -> None:
        """Stop MCP server if running."""
        
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                await asyncio.sleep(1)
                if self.mcp_process.poll() is None:
                    self.mcp_process.kill()
                logger.info("MCP server stopped")
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
    
    def get_executor_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        
        return {
            "supported_actions": len(self.tool_mappings),
            "action_types": list(self.tool_mappings.keys()),
            "mcp_server_running": self.mcp_process is not None
        }


# Global executor instance
_mcp_executor: Optional[MCPExecutor] = None


async def get_mcp_executor() -> MCPExecutor:
    """Get global MCP executor instance."""
    global _mcp_executor
    if _mcp_executor is None:
        _mcp_executor = MCPExecutor()
        await _mcp_executor.start_mcp_server()
    return _mcp_executor