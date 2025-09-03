"""
IPC Client - Desktop app communication with backend service
WebSocket client for real-time communication with the backend IPC server.
"""

import asyncio
import json
import uuid
import time
from typing import Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
import logging
import threading

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..themes.professional_theme import professional_theme


logger = logging.getLogger(__name__)


@dataclass
class IPCMessage:
    """IPC message structure."""
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: float
    response_to: Optional[str] = None


class IPCClient:
    """WebSocket client for desktop app backend communication."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        
        # Connection state
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.client_id: Optional[str] = None
        
        # Message handling
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.subscriptions: Set[str] = set()
        
        # Background tasks
        self.connection_task: Optional[asyncio.Task] = None
        self.message_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Auto-reconnect settings
        self.auto_reconnect = True
        self.reconnect_interval = 5  # seconds
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "connection_attempts": 0,
            "disconnections": 0,
            "errors": 0
        }
        
        # Event loop for async operations
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
        
        # Setup default message handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default message handlers."""
        
        self.message_handlers = {
            "connection_established": self._handle_connection_established,
            "response": self._handle_response,
            "error": self._handle_error,
            "disconnect": self._handle_disconnect,
            
            # Execution events
            "execution_state_changed": self._handle_execution_state_changed,
            "execution_plan_loaded": self._handle_plan_loaded,
            "execution_step_updated": self._handle_step_updated,
            "execution_completed": self._handle_execution_completed,
            "execution_error": self._handle_execution_error,
            "execution_paused": self._handle_execution_paused,
            
            # Chat events
            "chat_response": self._handle_chat_response,
            
            # Approval requests
            "approval_request": self._handle_approval_request
        }
    
    def start(self) -> None:
        """Start the IPC client."""
        
        if self.loop_thread and self.loop_thread.is_alive():
            logger.warning("IPC client already running")
            return
        
        logger.info("Starting IPC client...")
        
        # Start event loop in separate thread
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait a moment for loop to start
        time.sleep(0.1)
    
    def stop(self) -> None:
        """Stop the IPC client."""
        
        logger.info("Stopping IPC client...")
        
        if self.loop and not self.loop.is_closed():
            # Schedule disconnect in the event loop
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
            
            # Stop the event loop
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Wait for thread to finish
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=5)
    
    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in background thread."""
        
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Start connection task
            self.connection_task = self.loop.create_task(self._connect_with_retry())
            
            # Run event loop
            self.loop.run_forever()
            
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
    
    async def _connect_with_retry(self) -> None:
        """Connect to server with retry logic."""
        
        while self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                await self._connect()
                self.reconnect_attempts = 0  # Reset on successful connection
                break
                
            except Exception as e:
                self.reconnect_attempts += 1
                self.stats["connection_attempts"] += 1
                self.stats["errors"] += 1
                
                logger.warning(f"Connection attempt {self.reconnect_attempts} failed: {e}")
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    logger.info(f"Retrying connection in {self.reconnect_interval} seconds...")
                    await asyncio.sleep(self.reconnect_interval)
                else:
                    logger.error("Max reconnection attempts reached")
                    break
    
    async def _connect(self) -> None:
        """Connect to the IPC server."""
        
        try:
            logger.info(f"Connecting to IPC server at {self.uri}")
            
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.uri,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=10**6,  # 1MB max message size
                    compression=None
                ),
                timeout=10.0  # 10 second connection timeout
            )
            
            self.connected = True
            self.stats["connection_attempts"] += 1
            
            logger.info("Connected to IPC server")
            
            # Start message handling and heartbeat
            self.message_task = asyncio.create_task(self._handle_messages())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Authenticate with timeout
            await asyncio.wait_for(self._authenticate(), timeout=15.0)
            
        except asyncio.TimeoutError:
            self.connected = False
            self.websocket = None
            logger.error(f"Failed to connect to IPC server: Connection timeout after 10 seconds")
            raise
        except Exception as e:
            self.connected = False
            self.websocket = None
            logger.error(f"Failed to connect to IPC server: {type(e).__name__}: {e}")
            raise
    
    async def _disconnect(self) -> None:
        """Disconnect from the IPC server."""
        
        try:
            self.connected = False
            self.auto_reconnect = False
            
            # Cancel background tasks
            if self.message_task:
                self.message_task.cancel()
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            
            # Close websocket
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            self.stats["disconnections"] += 1
            logger.info("Disconnected from IPC server")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def _authenticate(self) -> None:
        """Authenticate with the IPC server."""
        
        auth_data = {
            "client_type": "desktop_app",
            "version": "1.0.0",
            "capabilities": ["voice_input", "chat", "execution_control"]
        }
        
        response = await self.send_request("auth", auth_data, timeout=10.0)
        
        if response.get("authenticated"):
            self.client_id = response.get("client_id")
            logger.info(f"Authenticated with server, client ID: {self.client_id}")
            
            # Subscribe to default events with timeout
            await asyncio.wait_for(self._subscribe_to_default_events(), timeout=10.0)
        else:
            raise Exception("Authentication failed")
    
    async def _subscribe_to_default_events(self) -> None:
        """Subscribe to default event types."""
        
        default_subscriptions = [
            "execution_updates",
            "chat_updates",
            "approval_requests",
            "system_updates"
        ]
        
        await self.subscribe(default_subscriptions)
    
    async def _handle_messages(self) -> None:
        """Handle incoming messages from server."""
        
        try:
            async for raw_message in self.websocket:
                try:
                    # Process message with timeout to prevent hanging
                    await asyncio.wait_for(
                        self._process_message(raw_message),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Message processing timeout")
                    self.stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    self.stats["errors"] += 1
                    
        except ConnectionClosed:
            logger.info("Connection closed by server")
            self.connected = False
            
            if self.auto_reconnect:
                # Schedule reconnection with exponential backoff
                self.reconnect_attempts += 1
                backoff_delay = min(self.reconnect_interval * (2 ** (self.reconnect_attempts - 1)), 60)
                logger.info(f"Scheduling reconnection in {backoff_delay} seconds (attempt {self.reconnect_attempts})")
                await asyncio.sleep(backoff_delay)
                asyncio.create_task(self._connect_with_retry())
                
        except WebSocketException as e:
            logger.warning(f"WebSocket error: {e}")
            self.connected = False
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            self.connected = False
    
    async def _process_message(self, raw_message: str) -> None:
        """Process incoming message."""
        
        try:
            data = json.loads(raw_message)
            message = IPCMessage(**data)
            
            self.stats["messages_received"] += 1
            
            logger.debug(f"Received message: {message.type}")
            
            # Handle response to pending request
            if message.response_to and message.response_to in self.pending_responses:
                future = self.pending_responses.pop(message.response_to)
                if not future.cancelled():
                    future.set_result(message.data)
                return
            
            # Handle regular message
            handler = self.message_handlers.get(message.type)
            if handler:
                try:
                    await handler(message.data)
                except Exception as e:
                    logger.error(f"Handler error for {message.type}: {e}")
            else:
                logger.debug(f"No handler for message type: {message.type}")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages."""
        
        consecutive_failures = 0
        max_failures = 3
        
        while self.connected:
            try:
                # Check if websocket is still alive
                if self.websocket and self.websocket.closed:
                    logger.warning("WebSocket closed, stopping heartbeat")
                    break
                
                await asyncio.wait_for(
                    self.send_message("ping", {}), 
                    timeout=10.0
                )
                consecutive_failures = 0  # Reset on successful ping
                await asyncio.sleep(30)  # Ping every 30 seconds
                
            except asyncio.TimeoutError:
                consecutive_failures += 1
                logger.warning(f"Heartbeat timeout (failure {consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    logger.error("Multiple heartbeat failures, connection unhealthy")
                    self.connected = False
                    break
                    
                await asyncio.sleep(5)  # Short retry delay
                
            except Exception as e:
                consecutive_failures += 1
                logger.debug(f"Heartbeat error: {e}")
                
                if consecutive_failures >= max_failures:
                    logger.error("Multiple heartbeat failures, stopping heartbeat")
                    break
                    
                await asyncio.sleep(5)
    
    async def send_message(self, message_type: str, data: Dict[str, Any]) -> None:
        """Send message to server without expecting response."""
        
        if not self.connected or not self.websocket:
            raise Exception("Not connected to server")
        
        message = IPCMessage(
            id=str(uuid.uuid4()),
            type=message_type,
            data=data,
            timestamp=time.time()
        )
        
        message_json = json.dumps(asdict(message))
        await self.websocket.send(message_json)
        
        self.stats["messages_sent"] += 1
        logger.debug(f"Sent message: {message_type}")
    
    async def send_request(self, message_type: str, data: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """Send message and wait for response."""
        
        if not self.connected or not self.websocket:
            raise Exception("Not connected to server")
        
        message_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.pending_responses[message_id] = future
        
        try:
            message = IPCMessage(
                id=message_id,
                type=message_type,
                data=data,
                timestamp=time.time()
            )
            
            message_json = json.dumps(asdict(message))
            await self.websocket.send(message_json)
            
            self.stats["messages_sent"] += 1
            logger.debug(f"Sent request: {message_type}")
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            self.pending_responses.pop(message_id, None)
            raise Exception(f"Request timeout for {message_type}")
        except Exception:
            self.pending_responses.pop(message_id, None)
            raise
    
    async def subscribe(self, event_types: list) -> Dict[str, Any]:
        """Subscribe to event types."""
        
        self.subscriptions.update(event_types)
        return await self.send_request("subscribe", {"events": event_types})
    
    async def unsubscribe(self, event_types: list) -> Dict[str, Any]:
        """Unsubscribe from event types."""
        
        self.subscriptions -= set(event_types)
        return await self.send_request("unsubscribe", {"events": event_types})
    
    # Default message handlers
    
    async def _handle_connection_established(self, data: Dict[str, Any]) -> None:
        """Handle connection established message."""
        
        logger.info("Connection established with server")
        self.client_id = data.get("client_id")
    
    async def _handle_response(self, data: Dict[str, Any]) -> None:
        """Handle generic response message."""
        
        # This is handled in _process_message
        pass
    
    async def _handle_error(self, data: Dict[str, Any]) -> None:
        """Handle error message from server."""
        
        error_message = data.get("error", "Unknown server error")
        logger.error(f"Server error: {error_message}")
        
        # Notify UI if handler is registered
        if "on_server_error" in self.message_handlers:
            await self.message_handlers["on_server_error"](data)
    
    async def _handle_disconnect(self, data: Dict[str, Any]) -> None:
        """Handle disconnect message."""
        
        reason = data.get("reason", "Unknown reason")
        logger.info(f"Server requested disconnect: {reason}")
        
        await self._disconnect()
    
    async def _handle_execution_state_changed(self, data: Dict[str, Any]) -> None:
        """Handle execution state change."""
        
        state = data.get("state", "unknown")
        logger.debug(f"Execution state changed to: {state}")
        
        # Notify UI handler if registered
        if "on_execution_state_changed" in self.message_handlers:
            await self.message_handlers["on_execution_state_changed"](data)
    
    async def _handle_plan_loaded(self, data: Dict[str, Any]) -> None:
        """Handle execution plan loaded."""
        
        plan = data.get("plan")
        logger.info(f"Execution plan loaded: {plan.get('title') if plan else 'Unknown'}")
        
        if "on_plan_loaded" in self.message_handlers:
            await self.message_handlers["on_plan_loaded"](data)
    
    async def _handle_step_updated(self, data: Dict[str, Any]) -> None:
        """Handle execution step update."""
        
        step_id = data.get("step_id")
        status = data.get("status")
        
        logger.debug(f"Step {step_id} status: {status}")
        
        if "on_step_updated" in self.message_handlers:
            await self.message_handlers["on_step_updated"](data)
    
    async def _handle_execution_completed(self, data: Dict[str, Any]) -> None:
        """Handle execution completion."""
        
        success = data.get("success", False)
        logger.info(f"Execution completed, success: {success}")
        
        if "on_execution_completed" in self.message_handlers:
            await self.message_handlers["on_execution_completed"](data)
    
    async def _handle_execution_error(self, data: Dict[str, Any]) -> None:
        """Handle execution error."""
        
        error = data.get("error", "Unknown execution error")
        logger.error(f"Execution error: {error}")
        
        if "on_execution_error" in self.message_handlers:
            await self.message_handlers["on_execution_error"](data)
    
    async def _handle_execution_paused(self, data: Dict[str, Any]) -> None:
        """Handle execution paused."""
        
        logger.info("Execution paused")
        
        if "on_execution_paused" in self.message_handlers:
            await self.message_handlers["on_execution_paused"](data)
    
    async def _handle_chat_response(self, data: Dict[str, Any]) -> None:
        """Handle chat response."""
        
        message = data.get("message", "")
        logger.debug(f"Chat response received: {message[:50]}...")
        
        if "on_chat_response" in self.message_handlers:
            await self.message_handlers["on_chat_response"](data)
    
    async def _handle_approval_request(self, data: Dict[str, Any]) -> None:
        """Handle user approval request."""
        
        step_title = data.get("step_title", "Unknown step")
        logger.info(f"Approval requested for: {step_title}")
        
        if "on_approval_request" in self.message_handlers:
            await self.message_handlers["on_approval_request"](data)
    
    # Public API methods (thread-safe)
    
    def execute_request(self, user_request: str, execution_mode: str = "supervised") -> None:
        """Execute user request (thread-safe)."""
        
        if not self.loop or self.loop.is_closed():
            logger.warning("Event loop not available for execute_request")
            return
        
        asyncio.run_coroutine_threadsafe(
            self.send_message("execute_request", {
                "request": user_request,
                "mode": execution_mode
            }),
            self.loop
        )
    
    def send_chat_message(self, message: str) -> None:
        """Send chat message (thread-safe)."""
        
        if not self.loop or self.loop.is_closed():
            logger.warning("Event loop not available for send_chat_message")
            return
        
        asyncio.run_coroutine_threadsafe(
            self.send_message("chat_message", {"message": message}),
            self.loop
        )
    
    def pause_execution(self) -> None:
        """Pause execution (thread-safe)."""
        
        if not self.loop or self.loop.is_closed():
            logger.warning("Event loop not available for pause_execution")
            return
        
        asyncio.run_coroutine_threadsafe(
            self.send_message("pause_execution", {}),
            self.loop
        )
    
    def resume_execution(self) -> None:
        """Resume execution (thread-safe)."""
        
        if not self.loop or self.loop.is_closed():
            logger.warning("Event loop not available for resume_execution")
            return
        
        asyncio.run_coroutine_threadsafe(
            self.send_message("resume_execution", {}),
            self.loop
        )
    
    def cancel_execution(self) -> None:
        """Cancel execution (thread-safe)."""
        
        if not self.loop or self.loop.is_closed():
            logger.warning("Event loop not available for cancel_execution")
            return
        
        asyncio.run_coroutine_threadsafe(
            self.send_message("cancel_execution", {}),
            self.loop
        )
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register message handler."""
        
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for: {message_type}")
    
    def unregister_handler(self, message_type: str) -> None:
        """Unregister message handler."""
        
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            logger.debug(f"Unregistered handler for: {message_type}")
    
    def is_connected(self) -> bool:
        """Check if connected to server."""
        
        return self.connected
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        
        return {
            "connected": self.connected,
            "client_id": self.client_id,
            "subscriptions": list(self.subscriptions),
            "stats": self.stats.copy(),
            "reconnect_attempts": self.reconnect_attempts
        }
    
    def check_connection_health(self) -> Dict[str, Any]:
        """Check connection health and return diagnostic information."""
        
        health_info = {
            "connected": self.connected,
            "websocket_closed": self.websocket.closed if self.websocket else True,
            "client_id": self.client_id,
            "reconnect_attempts": self.reconnect_attempts,
            "auto_reconnect": self.auto_reconnect,
            "event_loop_running": self.loop and not self.loop.is_closed() if self.loop else False,
            "background_tasks": {
                "connection_task": self.connection_task and not self.connection_task.done() if self.connection_task else False,
                "message_task": self.message_task and not self.message_task.done() if self.message_task else False,
                "heartbeat_task": self.heartbeat_task and not self.heartbeat_task.done() if self.heartbeat_task else False
            },
            "stats": self.stats.copy()
        }
        
        # Add health recommendations
        recommendations = []
        if not self.connected:
            recommendations.append("Client is disconnected")
        if self.websocket and self.websocket.closed:
            recommendations.append("WebSocket connection is closed")
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            recommendations.append("Max reconnection attempts reached")
        if not self.loop or self.loop.is_closed():
            recommendations.append("Event loop is not running")
            
        health_info["recommendations"] = recommendations
        health_info["status"] = "healthy" if not recommendations else "unhealthy"
        
        return health_info