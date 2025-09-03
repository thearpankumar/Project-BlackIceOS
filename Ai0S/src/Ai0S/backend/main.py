"""
Main Backend Service - Agentic AI OS Control System
Integrates all backend components and provides IPC service for the desktop app.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from .models.ai_models import AIModels, get_ai_models
from .core.visual_monitor import VisualStateMonitor, initialize_visual_monitor
from .core.mcp_executor import MCPExecutor, initialize_mcp_executor
from .core.task_planner import TaskPlanner
from .core.execution_controller import ExecutionController
from .core.error_recovery import ErrorRecoverySystem
from .security.security_framework import SecurityFramework
from .ipc.ipc_server import IPCServer
from ..agents.orchestrator.langgraph_orchestrator import LangGraphOrchestrator
from ..mcp_server.server import MCPServer
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class BackendService:
    """Main backend service that integrates all components."""
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        
        # Core components
        self.ai_models = None
        self.orchestrator = None
        self.visual_monitor = None
        self.task_planner = None
        self.execution_controller = None
        self.error_recovery = None
        self.security_framework = None
        self.mcp_executor = None
        
        # Communication services
        self.ipc_server = None
        self.mcp_server = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        
        log_level = getattr(logging, self.settings.LOG_LEVEL.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    self.settings.get_data_paths()["logs"] / "backend.log"
                )
            ]
        )
    
    async def start(self) -> None:
        """Start the backend service."""
        
        try:
            logger.info("Starting Agentic AI OS Control Backend Service...")
            
            # Initialize core AI components
            await self._initialize_core_components()
            
            # Start communication services
            await self._start_communication_services()
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            self.running = True
            logger.info("Backend service started successfully")
            
            # Keep service running
            try:
                await self._run_service_loop()
            except KeyboardInterrupt:
                logger.info("Service interrupted by user")
                await self.shutdown()
            
        except Exception as e:
            logger.error(f"Failed to start backend service: {e}")
            raise
    
    async def _initialize_core_components(self) -> None:
        """Initialize all core backend components."""
        
        logger.info("Initializing AI models...")
        self.ai_models = await get_ai_models()
        
        logger.info("Initializing security framework...")
        self.security_framework = SecurityFramework()
        
        logger.info("Initializing error recovery system...")
        self.error_recovery = ErrorRecoverySystem(self.ai_models)
        
        logger.info("Initializing visual monitor...")
        self.visual_monitor = initialize_visual_monitor(self.ai_models)
        await self.visual_monitor.start_monitoring()
        
        logger.info("Initializing MCP server...")
        self.mcp_server = MCPServer()
        
        logger.info("Initializing MCP executor...")
        self.mcp_executor = initialize_mcp_executor(
            self.mcp_server,
            self.security_framework,
            self.error_recovery
        )
        
        logger.info("Initializing task planner...")
        self.task_planner = TaskPlanner(self.ai_models)
        
        logger.info("Initializing execution controller...")
        self.execution_controller = ExecutionController(
            ai_models=self.ai_models,
            task_planner=self.task_planner,
            visual_monitor=self.visual_monitor
        )
        
        logger.info("Initializing LangGraph orchestrator...")
        self.orchestrator = LangGraphOrchestrator()
        
        logger.info("Core components initialized successfully")
    
    async def _start_communication_services(self) -> None:
        """Start IPC and MCP communication services."""
        
        try:
            # Start IPC server for desktop app communication
            logger.info("Starting IPC server...")
            self.ipc_server = IPCServer(
                execution_controller=self.execution_controller,
                task_planner=self.task_planner,
                ai_models=self.ai_models,
                host=self.settings.WS_HOST,
                port=self.settings.WS_PORT
            )
            
            await self.ipc_server.start_server()
            
            # Start MCP server for tool execution
            logger.info("Starting MCP server...")
            self.mcp_server = MCPServer()
            
            # Run MCP server in background task
            asyncio.create_task(self._run_mcp_server())
            
            logger.info("Communication services started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start communication services: {e}")
            raise
    
    async def _run_mcp_server(self) -> None:
        """Run MCP server in background."""
        try:
            await self.mcp_server.run()
        except Exception as e:
            logger.error(f"MCP server error: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.running = False
            # Force immediate shutdown on second signal
            if hasattr(self, '_shutdown_called'):
                logger.warning("Force shutdown initiated")
                import os
                os._exit(1)
            self._shutdown_called = True
            
            # Schedule shutdown in the event loop
            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(self.shutdown())
                # Add callback to force exit if shutdown takes too long
                def timeout_callback():
                    if not task.done():
                        logger.error("Shutdown timeout - forcing exit")
                        import os
                        os._exit(1)
                loop.call_later(3.0, timeout_callback)
            except RuntimeError:
                import os
                os._exit(1)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _run_service_loop(self) -> None:
        """Main service event loop."""
        
        try:
            while self.running:
                # Perform periodic maintenance tasks
                await self._perform_maintenance()
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            logger.info("Service loop cancelled")
        except Exception as e:
            logger.error(f"Service loop error: {e}")
    
    async def _perform_maintenance(self) -> None:
        """Perform periodic maintenance tasks."""
        
        try:
            # Log statistics
            if self.ipc_server:
                status = self.ipc_server.get_server_status()
                logger.debug(f"IPC Server - Clients: {status['connected_clients']}")
            
            # Cleanup old data, check health, etc.
            # This would include cleanup of old screenshots, logs, etc.
            
        except Exception as e:
            logger.debug(f"Maintenance task error: {e}")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the backend service."""
        
        try:
            logger.info("Shutting down backend service...")
            self.running = False
            
            # Stop communication services
            if self.ipc_server:
                await self.ipc_server.stop_server()
            
            # Stop visual monitoring
            if self.visual_monitor:
                await self.visual_monitor.stop_monitoring()
            
            # Cancel any running tasks
            tasks = [task for task in asyncio.all_tasks() if not task.done() and task != asyncio.current_task()]
            if tasks:
                logger.info(f"Cancelling {len(tasks)} remaining tasks...")
                for task in tasks:
                    task.cancel()
                
                # Wait for tasks to complete cancellation with timeout
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Task cancellation timeout")
                except Exception:
                    pass
            
            logger.info("Backend service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Signal completion to main thread
            pass
    
    def get_status(self) -> dict:
        """Get current service status."""
        
        return {
            "running": self.running,
            "components": {
                "ai_models": self.ai_models is not None,
                "orchestrator": self.orchestrator is not None,
                "visual_monitor": self.visual_monitor is not None,
                "task_planner": self.task_planner is not None,
                "execution_controller": self.execution_controller is not None,
                "ipc_server": self.ipc_server is not None and self.ipc_server.running,
                "mcp_server": self.mcp_server is not None
            },
            "ipc_server_status": self.ipc_server.get_server_status() if self.ipc_server else None
        }


async def main():
    """Main entry point for the backend service."""
    
    service = None
    try:
        service = BackendService()
        await service.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        if service:
            await service.shutdown()
    except Exception as e:
        logger.error(f"Backend service failed: {e}")
        if service:
            await service.shutdown()
        return 1
    finally:
        if service and service.running:
            await service.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))