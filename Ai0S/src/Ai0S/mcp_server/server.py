"""
MCP Server - Model Context Protocol Server
Cross-platform tool execution server for agentic OS control.
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import platform
import psutil

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    LoggingLevel
)

from ..utils.platform_detector import get_system_environment, get_os_commands
from ..config.settings import get_settings
from .tools.browser_tools import BrowserTools
from .tools.application_tools import ApplicationTools  
from .tools.ui_interaction_tools import UIInteractionTools
from .tools.system_tools import SystemTools
from .tools.file_tools import FileTools


logger = logging.getLogger(__name__)


class MCPServer:
    """Advanced MCP Server for cross-platform OS automation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.system_env = get_system_environment()
        self.server = Server("agentic-os-control")
        
        # Initialize tool modules
        self.browser_tools = BrowserTools()
        self.application_tools = ApplicationTools()
        self.ui_tools = UIInteractionTools()
        self.system_tools = SystemTools()
        self.file_tools = FileTools()
        
        # Command history and safety tracking
        self.command_history: List[Dict[str, Any]] = []
        self.blocked_commands = 0
        self.executed_commands = 0
        
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self) -> None:
        """Setup all available tools based on platform capabilities."""
        
        # Browser Control Tools
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools."""
            tools = []
            
            # Browser tools
            if "browser_automation" in self.system_env.capabilities:
                tools.extend([
                    Tool(
                        name="open_browser",
                        description="Open a web browser with optional URL",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "browser": {
                                    "type": "string",
                                    "enum": ["chrome", "firefox", "safari", "edge", "default"],
                                    "description": "Browser to open"
                                },
                                "url": {
                                    "type": "string",
                                    "description": "URL to navigate to (optional)"
                                },
                                "new_window": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Open in new window"
                                }
                            },
                            "required": []
                        }
                    ),
                    Tool(
                        name="navigate_url",
                        description="Navigate to a URL in active browser",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "URL to navigate to"
                                },
                                "method": {
                                    "type": "string",
                                    "enum": ["address_bar", "ctrl_l", "cmd_l"],
                                    "default": "address_bar",
                                    "description": "Navigation method"
                                }
                            },
                            "required": ["url"]
                        }
                    ),
                ])
            
            # Application Control Tools
            tools.extend([
                Tool(
                    name="launch_application",
                    description="Launch an application by name or path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Application name or executable"
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command line arguments",
                                "default": []
                            },
                            "wait": {
                                "type": "boolean",
                                "default": False,
                                "description": "Wait for application to start"
                            }
                        },
                        "required": ["app_name"]
                    }
                ),
                Tool(
                    name="find_window",
                    description="Find application window by title or class",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "window_title": {
                                "type": "string",
                                "description": "Window title to search for"
                            },
                            "partial_match": {
                                "type": "boolean", 
                                "default": True,
                                "description": "Allow partial title matches"
                            }
                        },
                        "required": ["window_title"]
                    }
                ),
                Tool(
                    name="list_applications",
                    description="List currently running applications",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter_system": {
                                "type": "boolean",
                                "default": True,
                                "description": "Filter out system processes"
                            }
                        }
                    }
                )
            ])
            
            # UI Interaction Tools
            tools.extend([
                Tool(
                    name="click_element",
                    description="Click on a UI element by description or coordinates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "element_description": {
                                "type": "string",
                                "description": "Description of element to click"
                            },
                            "coordinates": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "number"},
                                    "y": {"type": "number"}
                                },
                                "description": "Exact coordinates to click (optional)"
                            },
                            "click_type": {
                                "type": "string",
                                "enum": ["single", "double", "right"],
                                "default": "single"
                            }
                        }
                    }
                ),
                Tool(
                    name="type_text",
                    description="Type text in currently focused element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            },
                            "speed": {
                                "type": "number",
                                "default": 0.05,
                                "description": "Typing speed (seconds between characters)"
                            },
                            "clear_first": {
                                "type": "boolean",
                                "default": False,
                                "description": "Clear field before typing"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="send_key",
                    description="Send keyboard key or key combination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string", 
                                "description": "Key to send (e.g., 'enter', 'ctrl+c', 'alt+tab')"
                            },
                            "repeat": {
                                "type": "number",
                                "default": 1,
                                "description": "Number of times to repeat"
                            }
                        },
                        "required": ["key"]
                    }
                ),
                Tool(
                    name="scroll",
                    description="Scroll in a direction",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["up", "down", "left", "right"],
                                "description": "Scroll direction"
                            },
                            "amount": {
                                "type": "number",
                                "default": 3,
                                "description": "Scroll amount (clicks)"
                            },
                            "coordinates": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "number"},
                                    "y": {"type": "number"}
                                },
                                "description": "Scroll at specific coordinates (optional)"
                            }
                        },
                        "required": ["direction"]
                    }
                )
            ])
            
            # System Tools
            tools.extend([
                Tool(
                    name="execute_command",
                    description="Execute system command with safety checks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute"
                            },
                            "shell": {
                                "type": "boolean",
                                "default": True,
                                "description": "Execute through shell"
                            },
                            "timeout": {
                                "type": "number",
                                "default": 30,
                                "description": "Timeout in seconds"
                            },
                            "capture_output": {
                                "type": "boolean",
                                "default": True,
                                "description": "Capture command output"
                            }
                        },
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="take_screenshot",
                    description="Capture screenshot of screen or region",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "number"},
                                    "y": {"type": "number"},
                                    "width": {"type": "number"},
                                    "height": {"type": "number"}
                                },
                                "description": "Screen region to capture (optional)"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Save filename (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_system_info",
                    description="Get system information and capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_processes": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include running processes"
                            }
                        }
                    }
                )
            ])
            
            # File System Tools
            tools.extend([
                Tool(
                    name="open_file_manager",
                    description="Open file manager at specified path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "default": ".",
                                "description": "Path to open"
                            }
                        }
                    }
                ),
                Tool(
                    name="list_files",
                    description="List files in directory",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "path": {
                                "type": "string",
                                "default": ".",
                                "description": "Directory path"
                            },
                            "show_hidden": {
                                "type": "boolean",
                                "default": False,
                                "description": "Show hidden files"
                            }
                        }
                    }
                )
            ])
            
            return tools
        
        # Tool Call Handlers
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool execution."""
            
            logger.info(f"Executing tool: {name} with args: {arguments}")
            
            # Safety check
            if not self._is_command_safe(name, arguments):
                return [TextContent(
                    type="text",
                    text=f"Command blocked for safety: {name} with {arguments}"
                )]
            
            # Record command
            self._record_command(name, arguments)
            
            try:
                # Route to appropriate tool handler
                result = None
                
                # Browser tools
                if name == "open_browser":
                    result = await self.browser_tools.open_browser(**arguments)
                elif name == "navigate_url":
                    result = await self.browser_tools.navigate_url(**arguments)
                
                # Application tools
                elif name == "launch_application":
                    result = await self.application_tools.launch_application(**arguments)
                elif name == "find_window":
                    result = await self.application_tools.find_window(**arguments)
                elif name == "list_applications":
                    result = await self.application_tools.list_applications(**arguments)
                
                # UI interaction tools
                elif name == "click_element":
                    result = await self.ui_tools.click_element(**arguments)
                elif name == "type_text":
                    result = await self.ui_tools.type_text(**arguments)
                elif name == "send_key":
                    result = await self.ui_tools.send_key(**arguments)
                elif name == "scroll":
                    result = await self.ui_tools.scroll(**arguments)
                
                # System tools
                elif name == "execute_command":
                    result = await self.system_tools.execute_command(**arguments)
                elif name == "take_screenshot":
                    result = await self.system_tools.take_screenshot(**arguments)
                elif name == "get_system_info":
                    result = await self.system_tools.get_system_info(**arguments)
                
                # File tools
                elif name == "open_file_manager":
                    result = await self.file_tools.open_file_manager(**arguments)
                elif name == "list_files":
                    result = await self.file_tools.list_files(**arguments)
                
                else:
                    result = f"Unknown tool: {name}"
                
                # Increment success counter
                self.executed_commands += 1
                
                return [TextContent(type="text", text=str(result))]
                
            except Exception as e:
                error_msg = f"Tool execution failed: {name} - {str(e)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
    
    def _setup_resources(self) -> None:
        """Setup MCP resources."""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="system://info",
                    name="System Information", 
                    description="Current system information and capabilities",
                    mimeType="application/json"
                ),
                Resource(
                    uri="system://capabilities",
                    name="System Capabilities",
                    description="Available automation capabilities",
                    mimeType="application/json"
                ),
                Resource(
                    uri="command://history", 
                    name="Command History",
                    description="Recent command execution history",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource content."""
            
            if uri == "system://info":
                return json.dumps({
                    "os": self.system_env.os,
                    "architecture": self.system_env.architecture,
                    "display_server": self.system_env.display_server,
                    "desktop_environment": self.system_env.desktop_environment,
                    "screen_resolution": self.system_env.screen_resolution,
                    "cpu_count": self.system_env.cpu_count,
                    "memory_gb": self.system_env.memory_gb,
                    "has_audio": self.system_env.has_audio,
                    "has_microphone": self.system_env.has_microphone
                })
            
            elif uri == "system://capabilities":
                return json.dumps({
                    "capabilities": self.system_env.capabilities,
                    "os_commands": get_os_commands()
                })
            
            elif uri == "command://history":
                return json.dumps({
                    "recent_commands": self.command_history[-20:],
                    "total_executed": self.executed_commands,
                    "total_blocked": self.blocked_commands
                })
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    def _is_command_safe(self, tool_name: str, arguments: dict) -> bool:
        """Check if command is safe to execute."""
        
        # Get security configuration
        security_config = self.settings.get_security_config()
        
        # Check for blocked patterns in system commands
        if tool_name == "execute_command":
            command = arguments.get("command", "")
            
            for pattern in security_config["blocked_patterns"]:
                if pattern.lower() in command.lower():
                    logger.warning(f"Blocked dangerous command pattern: {pattern} in {command}")
                    self.blocked_commands += 1
                    return False
        
        # Check for sensitive operations
        if tool_name in security_config["sensitive_operations"]:
            if security_config["require_confirmation"]:
                logger.warning(f"Sensitive operation {tool_name} requires confirmation")
                return False
        
        # Rate limiting check (simplified)
        recent_commands = len([cmd for cmd in self.command_history[-60:] 
                             if (datetime.now() - cmd["timestamp"]).seconds < 60])
        
        if recent_commands > security_config["rate_limits"]["per_minute"]:
            logger.warning("Rate limit exceeded")
            return False
        
        return True
    
    def _record_command(self, tool_name: str, arguments: dict) -> None:
        """Record command execution for history and analysis."""
        from datetime import datetime
        
        record = {
            "timestamp": datetime.now(),
            "tool_name": tool_name,
            "arguments": arguments,
            "system_info": {
                "os": self.system_env.os,
                "pid": psutil.Process().pid
            }
        }
        
        self.command_history.append(record)
        
        # Limit history size
        if len(self.command_history) > 1000:
            self.command_history = self.command_history[-500:]
    
    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting MCP Server...")
        
        # Initialize with proper options
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="agentic-os-control",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


# Tool implementation files will be created separately
async def main():
    """Main entry point for MCP server."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())