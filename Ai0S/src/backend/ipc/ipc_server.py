"""
IPC Server - Inter-Process Communication between desktop app and backend
WebSocket-based communication server for real-time updates and command execution.
"""

import asyncio
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..core.execution_controller import ExecutionController
from ..core.task_planner import TaskPlanner, TaskContext
from ..models.ai_models import AIModels
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class IPCMessage:
    """IPC message structure."""
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: float
    response_to: Optional[str] = None


@dataclass
class ConnectedClient:
    """Represents a connected client."""
    websocket: WebSocketServerProtocol
    client_id: str
    client_type: str  # "desktop_app", "web_client", etc.
    connected_at: datetime
    last_heartbeat: datetime


class IPCServer:
    """WebSocket-based IPC server for backend communication."""
    
    def __init__(self, 
                 execution_controller: ExecutionController,
                 task_planner: TaskPlanner,
                 ai_models: AIModels,
                 host: str = "localhost",
                 port: int = 8765):
        
        self.execution_controller = execution_controller
        self.task_planner = task_planner
        self.ai_models = ai_models
        self.settings = get_settings()
        
        # Server configuration
        self.host = host
        self.port = port
        
        # Client management
        self.clients: Dict[str, ConnectedClient] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of event types
        
        # Message handling
        self.message_handlers = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # Server state
        self.server = None
        self.running = False
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "clients_connected": 0,
            "clients_total": 0,
            "errors": 0
        }
        
        # Setup message handlers
        self._setup_message_handlers()
    
    def _setup_message_handlers(self) -> None:
        """Setup message type handlers."""
        
        self.message_handlers = {
            # Authentication and connection
            "auth": self._handle_auth,
            "ping": self._handle_ping,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            
            # Task execution
            "execute_request": self._handle_execute_request,
            "pause_execution": self._handle_pause_execution,
            "resume_execution": self._handle_resume_execution,
            "cancel_execution": self._handle_cancel_execution,
            
            # Plan management
            "create_plan": self._handle_create_plan,
            "get_plan_status": self._handle_get_plan_status,
            
            # AI interactions
            "chat_message": self._handle_chat_message,
            "voice_transcription": self._handle_voice_transcription,
            
            # System queries
            "get_status": self._handle_get_status,
            "get_history": self._handle_get_history,
            "get_statistics": self._handle_get_statistics,
            
            # Configuration
            "update_settings": self._handle_update_settings,
            "get_settings": self._handle_get_settings
        }
    
    async def start_server(self) -> None:
        """Start the IPC WebSocket server."""
        
        try:
            logger.info(f"Starting IPC server on {self.host}:{self.port}")
            
            # Setup execution controller callbacks
            self._setup_execution_callbacks()
            
            # Start WebSocket server
            self.server = await websockets.serve(
                self._handle_client_connection,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            
            self.running = True
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_monitor())
            asyncio.create_task(self._stats_monitor())
            
            logger.info(f"IPC server started successfully on ws://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")
            raise
    
    async def stop_server(self) -> None:
        """Stop the IPC server."""
        
        try:
            logger.info("Stopping IPC server...")
            
            self.running = False
            
            # Close all client connections
            if self.clients:
                await asyncio.gather(
                    *[self._disconnect_client(client_id, "server_shutdown") 
                      for client_id in list(self.clients.keys())],
                    return_exceptions=True
                )
            
            # Stop server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            logger.info("IPC server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping IPC server: {e}")
    
    def _setup_execution_callbacks(self) -> None:
        """Setup callbacks for execution controller events."""
        
        # Register UI callbacks with execution controller
        ui_callbacks = {
            "ui_notification": self._on_execution_event,
            "request_approval": self._request_user_approval,
            "get_conversation_history": self._get_conversation_history
        }
        
        # Update execution controller with callbacks
        self.execution_controller.ui_callbacks = ui_callbacks
    
    async def _handle_client_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle new client connection."""
        
        client_id = str(uuid.uuid4())
        
        try:
            logger.info(f"New client connection: {client_id}")
            
            # Add to clients (will be properly initialized after auth)
            client = ConnectedClient(
                websocket=websocket,
                client_id=client_id,
                client_type="unknown",
                connected_at=datetime.now(),
                last_heartbeat=datetime.now()
            )
            
            self.clients[client_id] = client
            self.client_subscriptions[client_id] = set()
            
            self.stats["clients_connected"] += 1
            self.stats["clients_total"] += 1
            
            # Send welcome message
            await self._send_message(client_id, "connection_established", {
                "client_id": client_id,
                "server_version": "1.0.0",
                "supported_features": list(self.message_handlers.keys())
            })
            
            # Handle messages
            async for message in websocket:
                try:
                    await self._process_message(client_id, message)
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await self._send_error(client_id, f"Message processing error: {e}")
                    
        except ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
            
        except WebSocketException as e:
            logger.warning(f"WebSocket error for client {client_id}: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error handling client {client_id}: {e}")
            
        finally:
            # Cleanup client
            await self._cleanup_client(client_id)
    
    async def _process_message(self, client_id: str, raw_message: str) -> None:
        """Process incoming message from client."""
        
        try:
            # Parse message
            data = json.loads(raw_message)
            message = IPCMessage(**data)
            
            self.stats["messages_received"] += 1
            
            logger.debug(f"Received message from {client_id}: {message.type}")
            
            # Update client heartbeat
            if client_id in self.clients:
                self.clients[client_id].last_heartbeat = datetime.now()
            
            # Handle message
            handler = self.message_handlers.get(message.type)
            if handler:
                try:
                    response_data = await handler(client_id, message.data)
                    
                    if response_data is not None:
                        await self._send_response(client_id, message.id, response_data)
                        
                except Exception as e:
                    logger.error(f"Handler error for {message.type}: {e}")
                    await self._send_error(client_id, f"Handler error: {e}", message.id)
            else:
                await self._send_error(client_id, f"Unknown message type: {message.type}", message.id)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from client {client_id}: {e}")
            await self._send_error(client_id, "Invalid JSON message")
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            await self._send_error(client_id, f"Processing error: {e}")
    
    async def _send_message(self, client_id: str, message_type: str, data: Dict[str, Any], 
                          response_to: Optional[str] = None) -> bool:
        """Send message to client."""
        
        if client_id not in self.clients:
            logger.warning(f"Attempted to send message to unknown client: {client_id}")
            return False
        
        try:
            message = IPCMessage(
                id=str(uuid.uuid4()),
                type=message_type,
                data=data,
                timestamp=time.time(),
                response_to=response_to
            )
            
            message_json = json.dumps(asdict(message))
            await self.clients[client_id].websocket.send(message_json)
            
            self.stats["messages_sent"] += 1
            logger.debug(f"Sent message to {client_id}: {message_type}")
            
            return True
            
        except ConnectionClosed:
            logger.info(f"Client {client_id} connection closed during send")
            await self._cleanup_client(client_id)
            return False
            
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def _send_response(self, client_id: str, message_id: str, data: Dict[str, Any]) -> bool:
        """Send response to specific message."""
        
        return await self._send_message(client_id, "response", data, message_id)
    
    async def _send_error(self, client_id: str, error_message: str, message_id: Optional[str] = None) -> bool:
        """Send error message to client."""
        
        error_data = {"error": error_message, "timestamp": time.time()}
        return await self._send_message(client_id, "error", error_data, message_id)
    
    async def _broadcast_message(self, message_type: str, data: Dict[str, Any], 
                                subscription_filter: Optional[str] = None) -> int:
        """Broadcast message to subscribed clients."""
        
        sent_count = 0
        
        for client_id, subscriptions in self.client_subscriptions.items():
            if subscription_filter is None or subscription_filter in subscriptions:
                if await self._send_message(client_id, message_type, data):
                    sent_count += 1
        
        return sent_count
    
    async def _cleanup_client(self, client_id: str) -> None:
        """Cleanup client resources."""
        
        if client_id in self.clients:
            del self.clients[client_id]
            self.stats["clients_connected"] -= 1
        
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        
        logger.debug(f"Cleaned up client: {client_id}")
    
    async def _disconnect_client(self, client_id: str, reason: str) -> None:
        """Disconnect specific client."""
        
        if client_id in self.clients:
            try:
                await self._send_message(client_id, "disconnect", {"reason": reason})
                await self.clients[client_id].websocket.close()
            except:
                pass  # Ignore errors during disconnect
        
        await self._cleanup_client(client_id)
    
    # Message handlers
    
    async def _handle_auth(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle client authentication."""
        
        client_type = data.get("client_type", "unknown")
        client_version = data.get("version", "unknown")
        
        # Update client info
        if client_id in self.clients:
            self.clients[client_id].client_type = client_type
        
        logger.info(f"Client {client_id} authenticated as {client_type} v{client_version}")
        
        return {
            "authenticated": True,
            "client_id": client_id,
            "server_capabilities": list(self.message_handlers.keys())
        }
    
    async def _handle_ping(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping message."""
        
        return {"pong": True, "server_time": time.time()}
    
    async def _handle_subscribe(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription request."""
        
        event_types = data.get("events", [])
        
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].update(event_types)
        
        logger.debug(f"Client {client_id} subscribed to: {event_types}")
        
        return {"subscribed": event_types}
    
    async def _handle_unsubscribe(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsubscribe request."""
        
        event_types = data.get("events", [])
        
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id] -= set(event_types)
        
        return {"unsubscribed": event_types}
    
    async def _handle_execute_request(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task execution request."""
        
        user_request = data.get("request", "")
        execution_mode = data.get("mode", "supervised")
        
        if not user_request:
            raise ValueError("Empty user request")
        
        logger.info(f"Executing request from {client_id}: {user_request}")
        
        # Start execution asynchronously
        asyncio.create_task(self._execute_user_request(client_id, user_request, execution_mode))
        
        return {"status": "execution_started", "request": user_request}
    
    async def _execute_user_request(self, client_id: str, user_request: str, execution_mode: str) -> None:
        """Execute user request asynchronously."""
        
        try:
            from ..core.execution_controller import ExecutionMode
            
            mode_map = {
                "automatic": ExecutionMode.AUTOMATIC,
                "supervised": ExecutionMode.SUPERVISED,
                "manual": ExecutionMode.MANUAL
            }
            
            exec_mode = mode_map.get(execution_mode, ExecutionMode.SUPERVISED)
            
            result = await self.execution_controller.execute_user_request(user_request, exec_mode)
            
            # Notify client of completion
            await self._send_message(client_id, "execution_completed", result)
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            await self._send_message(client_id, "execution_error", {"error": str(e)})
    
    async def _handle_pause_execution(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pause execution request."""
        
        success = self.execution_controller.pause_execution()
        return {"paused": success}
    
    async def _handle_resume_execution(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resume execution request."""
        
        success = self.execution_controller.resume_execution()
        return {"resumed": success}
    
    async def _handle_cancel_execution(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cancel execution request."""
        
        success = self.execution_controller.cancel_execution()
        return {"cancelled": success}
    
    async def _handle_create_plan(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle plan creation request."""
        
        user_request = data.get("request", "")
        context_data = data.get("context", {})
        
        # Create task context
        context = TaskContext(
            user_request=user_request,
            current_screen_state=context_data.get("screen_state"),
            conversation_history=context_data.get("conversation_history"),
            system_capabilities=context_data.get("system_capabilities"),
            user_preferences=context_data.get("user_preferences")
        )
        
        # Generate plan
        planning_result = await self.task_planner.create_execution_plan(context)
        
        return {
            "plan_id": planning_result.plan.id,
            "confidence": planning_result.confidence,
            "estimated_duration": planning_result.estimated_duration,
            "complexity": planning_result.complexity.value,
            "risks": planning_result.risks
        }
    
    async def _handle_get_plan_status(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle plan status request."""
        
        return self.execution_controller.get_execution_status()
    
    async def _handle_chat_message(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat message from client."""
        
        message = data.get("message", "")
        
        if not message:
            raise ValueError("Empty chat message")
        
        # Process chat message using AI models
        # For now, use analyze_command_intent as a placeholder for chat
        context = {"active_apps": [], "recent_actions": [], "capabilities": []}
        intent_analysis = await self.ai_models.analyze_command_intent(message, context)
        
        response = intent_analysis.get("interpretation", f"I understand you want to: {message}")
        
        # Broadcast to subscribed clients
        await self._broadcast_message("chat_response", {
            "message": response,
            "client_id": client_id
        }, "chat_updates")
        
        return {"response": response}
    
    async def _handle_voice_transcription(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice transcription request."""
        
        audio_data = data.get("audio_data")
        
        if not audio_data:
            raise ValueError("No audio data provided")
        
        # Transcribe with Gemini 2.0 Flash
        # Note: audio_data should be bytes, but might need format conversion
        try:
            transcription = await self.ai_models.transcribe_audio(audio_data, "webm")
            return {"transcription": transcription}
        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            return {"transcription": "", "error": str(e)}
    
    async def _handle_get_status(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request."""
        
        return {
            "execution_status": self.execution_controller.get_execution_status(),
            "server_stats": self.stats.copy(),
            "connected_clients": len(self.clients),
            "server_uptime": time.time() - getattr(self, '_start_time', time.time())
        }
    
    async def _handle_get_history(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution history request."""
        
        limit = data.get("limit", 20)
        history = self.execution_controller.get_execution_history()
        
        return {"history": history[-limit:] if history else []}
    
    async def _handle_get_statistics(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle statistics request."""
        
        return {
            "server_stats": self.stats.copy(),
            "execution_stats": self.execution_controller.get_execution_status().get("statistics", {}),
            "planning_stats": self.task_planner.get_planning_statistics()
        }
    
    async def _handle_update_settings(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle settings update request."""
        
        # This would update settings in a real implementation
        logger.info(f"Settings update requested by {client_id}: {data}")
        
        return {"updated": True}
    
    async def _handle_get_settings(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle settings request."""
        
        # Return relevant settings
        return {
            "execution_mode": "supervised",
            "auto_approve_safe_actions": False,
            "enable_voice_input": True,
            "enable_screenshot_monitoring": True
        }
    
    # Execution controller callbacks
    
    async def _on_execution_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle execution controller events."""
        
        # Broadcast event to subscribed clients
        await self._broadcast_message(f"execution_{event_type}", data, "execution_updates")
    
    async def _request_user_approval(self, step) -> bool:
        """Request user approval for execution step."""
        
        # Send approval request to clients
        approval_data = {
            "step_id": step.id,
            "step_title": step.title,
            "step_description": step.description,
            "tool_category": step.metadata.get("tool_category") if step.metadata else None
        }
        
        # For now, return True (auto-approve)
        # In a real implementation, this would wait for client response
        logger.info(f"User approval requested for step: {step.title}")
        
        await self._broadcast_message("approval_request", approval_data, "approval_requests")
        
        return True
    
    def _get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history for AI context."""
        
        # This would return actual conversation history
        # For now, return empty list
        return []
    
    # Background tasks
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor client heartbeats and cleanup stale connections."""
        
        while self.running:
            try:
                current_time = datetime.now()
                stale_clients = []
                
                for client_id, client in self.clients.items():
                    # Check if client hasn't sent heartbeat in 60 seconds
                    time_since_heartbeat = (current_time - client.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > 60:
                        stale_clients.append(client_id)
                
                # Cleanup stale clients
                for client_id in stale_clients:
                    logger.warning(f"Removing stale client: {client_id}")
                    await self._disconnect_client(client_id, "heartbeat_timeout")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _stats_monitor(self) -> None:
        """Monitor and log server statistics."""
        
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                logger.info(f"IPC Server Stats - Clients: {len(self.clients)}, "
                          f"Messages Sent: {self.stats['messages_sent']}, "
                          f"Messages Received: {self.stats['messages_received']}, "
                          f"Errors: {self.stats['errors']}")
                
            except Exception as e:
                logger.error(f"Stats monitor error: {e}")
    
    # Public API
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get current server status."""
        
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "connected_clients": len(self.clients),
            "statistics": self.stats.copy()
        }