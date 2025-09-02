"""
Execution Controller - Orchestrates plan execution with MCP integration
Advanced execution engine with real-time monitoring, error recovery, and safety controls.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum
import logging

from .task_planner import TaskPlanner, PlanningResult, TaskContext
from .visual_monitor import VisualStateMonitor
from ..models.ai_models import ExecutionPlan, ExecutionStep
from .mcp_executor import get_mcp_executor, MCPExecutor
from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    AUTOMATIC = "automatic"    # Full automation
    SUPERVISED = "supervised"  # User approval for risky steps
    MANUAL = "manual"         # User confirmation for each step


class ExecutionState(Enum):
    IDLE = "idle"
    PLANNING = "planning" 
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionController:
    """Advanced execution controller with MCP integration and safety controls."""
    
    def __init__(self, 
                 ai_models,
                 task_planner: TaskPlanner,
                 visual_monitor: VisualStateMonitor,
                 ui_callbacks: Optional[Dict[str, Callable]] = None):
        
        self.ai_models = ai_models
        self.task_planner = task_planner
        self.visual_monitor = visual_monitor
        self.mcp_executor = None  # Will be initialized later
        self.ui_callbacks = ui_callbacks or {}
        
        self.settings = get_settings()
        self.system_env = get_system_environment()
        
        # Execution state
        self.state = ExecutionState.IDLE
        self.current_plan: Optional[ExecutionPlan] = None
        self.current_step_index = 0
        self.execution_mode = ExecutionMode.SUPERVISED
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.step_results: Dict[str, Any] = {}
        self.execution_context = {}
        
        # Safety and monitoring
        self.safety_checks_enabled = True
        self.max_retry_attempts = 3
        self.step_timeout = 300  # 5 minutes per step
        
        # Real-time monitoring
        self.monitoring_active = False
        self.screen_state_history = []
        
        # Statistics
        self.execution_stats = {
            "plans_executed": 0,
            "steps_completed": 0,
            "steps_failed": 0,
            "total_execution_time": 0,
            "success_rate": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the execution controller."""
        
        try:
            # Initialize MCP executor
            self.mcp_executor = await get_mcp_executor()
            logger.info("Execution controller initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize execution controller: {e}")
            raise
    
    async def execute_user_request(self, user_request: str, 
                                 execution_mode: ExecutionMode = ExecutionMode.SUPERVISED) -> Dict[str, Any]:
        """Execute a user request from planning to completion."""
        
        try:
            logger.info(f"Starting execution of user request: {user_request}")
            
            self.execution_mode = execution_mode
            self.state = ExecutionState.PLANNING
            
            # Notify UI of state change
            await self._notify_ui("state_changed", {"state": self.state.value})
            
            # Step 1: Create execution context
            context = await self._create_task_context(user_request)
            
            # Step 2: Generate execution plan
            planning_result = await self.task_planner.create_execution_plan(context)
            
            if planning_result.confidence < 0.3:
                logger.warning(f"Low confidence plan ({planning_result.confidence:.2f}), execution may fail")
            
            # Step 3: Load plan into visualizer
            self.current_plan = planning_result.plan
            await self._notify_ui("plan_loaded", {"plan": self.current_plan})
            
            # Step 4: Execute plan
            self.state = ExecutionState.EXECUTING
            await self._notify_ui("state_changed", {"state": self.state.value})
            
            execution_result = await self._execute_plan(self.current_plan)
            
            # Step 5: Finalize execution
            if execution_result["success"]:
                self.state = ExecutionState.COMPLETED
                logger.info("Execution completed successfully")
            else:
                self.state = ExecutionState.FAILED
                logger.error(f"Execution failed: {execution_result.get('error', 'Unknown error')}")
            
            await self._notify_ui("state_changed", {"state": self.state.value})
            
            # Update statistics
            self._update_execution_stats(execution_result)
            
            return {
                "success": execution_result["success"],
                "plan_id": self.current_plan.id,
                "steps_completed": execution_result.get("steps_completed", 0),
                "total_steps": len(self.current_plan.steps),
                "execution_time": execution_result.get("execution_time", 0),
                "error": execution_result.get("error"),
                "final_state": self.state.value
            }
            
        except Exception as e:
            logger.error(f"Execution controller error: {e}")
            self.state = ExecutionState.FAILED
            await self._notify_ui("state_changed", {"state": self.state.value})
            
            return {
                "success": False,
                "error": str(e),
                "final_state": self.state.value
            }
    
    async def _create_task_context(self, user_request: str) -> TaskContext:
        """Create comprehensive context for task planning."""
        
        # Capture current screen state
        screen_state = await self.visual_monitor.get_current_state()
        
        # Get conversation history from UI if available
        conversation_history = []
        if "get_conversation_history" in self.ui_callbacks:
            conversation_history = self.ui_callbacks["get_conversation_history"]()
        
        context = TaskContext(
            user_request=user_request,
            current_screen_state=screen_state,
            conversation_history=conversation_history,
            system_capabilities=self.system_env.capabilities,
            user_preferences=self.settings.user_preferences,
            previous_failed_attempts=self._get_recent_failures(user_request)
        )
        
        return context
    
    def _get_recent_failures(self, user_request: str) -> List[Dict[str, Any]]:
        """Get recent failed attempts for similar requests."""
        
        # Look for similar requests in execution history
        recent_failures = []
        
        for record in self.execution_history[-10:]:  # Last 10 executions
            if (not record.get("success", False) and 
                self._is_similar_request(record.get("user_request", ""), user_request)):
                
                recent_failures.append({
                    "request": record.get("user_request"),
                    "error": record.get("error"),
                    "failed_steps": record.get("failed_steps", []),
                    "timestamp": record.get("timestamp")
                })
        
        return recent_failures
    
    def _is_similar_request(self, request1: str, request2: str) -> bool:
        """Check if two requests are similar (simple similarity check)."""
        
        # This is a simplified similarity check
        # In a more advanced system, you'd use semantic similarity
        
        words1 = set(request1.lower().split())
        words2 = set(request2.lower().split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        overlap = len(words1.intersection(words2))
        similarity = overlap / max(len(words1), len(words2))
        
        return similarity > 0.5
    
    async def _execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute the execution plan step by step."""
        
        start_time = time.time()
        steps_completed = 0
        failed_steps = []
        
        plan.started_at = datetime.now()
        
        try:
            # Start monitoring if enabled
            if self.settings.execution_settings.get("enable_monitoring", True):
                await self._start_execution_monitoring()
            
            for step_index, step in enumerate(plan.steps):
                self.current_step_index = step_index
                
                logger.info(f"Executing step {step_index + 1}/{len(plan.steps)}: {step.title}")
                
                # Update step status
                step.status = StepStatus.RUNNING
                step.start_time = datetime.now()
                await self._notify_ui("step_updated", {
                    "step_id": step.id,
                    "status": step.status.value,
                    "progress": 0.0
                })
                
                # Execute step with safety checks and retries
                step_result = await self._execute_step_with_retry(step)
                
                if step_result["success"]:
                    step.status = StepStatus.COMPLETED
                    step.progress = 1.0
                    step.end_time = datetime.now()
                    steps_completed += 1
                    
                    logger.info(f"Step completed: {step.title}")
                else:
                    step.status = StepStatus.FAILED
                    step.error_message = step_result.get("error", "Unknown error")
                    step.end_time = datetime.now()
                    failed_steps.append(step.id)
                    
                    logger.error(f"Step failed: {step.title} - {step.error_message}")
                    
                    # Attempt recovery or adaptation
                    recovery_result = await self._handle_step_failure(step, step_result)
                    
                    if not recovery_result["continue_execution"]:
                        logger.error("Execution halted due to unrecoverable failure")
                        break
                
                await self._notify_ui("step_updated", {
                    "step_id": step.id,
                    "status": step.status.value,
                    "progress": step.progress,
                    "error_message": getattr(step, 'error_message', None)
                })
                
                # Check for pause/stop requests
                if self.state == ExecutionState.PAUSED:
                    await self._handle_pause_state()
                elif self.state == ExecutionState.CANCELLED:
                    logger.info("Execution cancelled by user")
                    break
            
            # Stop monitoring
            await self._stop_execution_monitoring()
            
            plan.completed_at = datetime.now()
            execution_time = time.time() - start_time
            
            success = len(failed_steps) == 0
            
            # Record execution
            execution_record = {
                "user_request": getattr(self.execution_context, "user_request", ""),
                "plan_id": plan.id,
                "success": success,
                "steps_completed": steps_completed,
                "total_steps": len(plan.steps),
                "failed_steps": failed_steps,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if not success and failed_steps:
                execution_record["error"] = f"Failed steps: {', '.join(failed_steps)}"
            
            self.execution_history.append(execution_record)
            
            return {
                "success": success,
                "steps_completed": steps_completed,
                "failed_steps": failed_steps,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Plan execution error: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "steps_completed": steps_completed,
                "execution_time": time.time() - start_time
            }
    
    async def _execute_step_with_retry(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute a step with retry logic and safety checks."""
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retry_attempts:
            try:
                # Safety check before execution
                if self.safety_checks_enabled:
                    safety_check = await self._perform_safety_check(step)
                    if not safety_check["safe"]:
                        return {
                            "success": False,
                            "error": f"Safety check failed: {safety_check['reason']}"
                        }
                
                # Get user approval for supervised mode
                if self.execution_mode == ExecutionMode.SUPERVISED and self._step_requires_approval(step):
                    approval = await self._request_user_approval(step)
                    if not approval:
                        return {
                            "success": False,
                            "error": "User did not approve step execution"
                        }
                
                # Execute the step
                step_result = await self._execute_single_step(step)
                
                if step_result["success"]:
                    return step_result
                
                last_error = step_result.get("error", "Unknown error")
                logger.warning(f"Step execution failed (attempt {retry_count + 1}): {last_error}")
                
                retry_count += 1
                
                if retry_count <= self.max_retry_attempts:
                    # Wait before retry
                    await asyncio.sleep(min(retry_count * 2, 10))
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Step execution exception (attempt {retry_count + 1}): {e}")
                retry_count += 1
        
        return {
            "success": False,
            "error": f"Max retries exceeded. Last error: {last_error}",
            "retry_count": retry_count
        }
    
    async def _execute_single_step(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute a single step using MCP tools."""
        
        try:
            # Get step metadata
            metadata = step.metadata or {}
            tool_name = metadata.get("tool_name")
            tool_category = metadata.get("tool_category")
            parameters = metadata.get("parameters", {})
            
            if not tool_name:
                return {
                    "success": False,
                    "error": "No tool specified for step"
                }
            
            logger.debug(f"Executing MCP tool: {tool_name} with parameters: {parameters}")
            
            # Create timeout for step execution
            try:
                result = await asyncio.wait_for(
                    self.mcp_server.call_tool(tool_name, parameters),
                    timeout=self.step_timeout
                )
                
                # Parse result
                if isinstance(result, dict) and result.get("success", True):
                    return {
                        "success": True,
                        "result": result,
                        "tool_name": tool_name
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Tool execution failed"),
                        "tool_name": tool_name
                    }
                    
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "error": f"Step timed out after {self.step_timeout} seconds",
                    "tool_name": tool_name
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Step execution error: {str(e)}"
            }
    
    async def _perform_safety_check(self, step: ExecutionStep) -> Dict[str, Any]:
        """Perform safety checks before step execution."""
        
        metadata = step.metadata or {}
        tool_name = metadata.get("tool_name", "")
        parameters = metadata.get("parameters", {})
        
        # Check for dangerous operations
        dangerous_patterns = [
            "rm -rf", "del /f", "format", "shutdown", "reboot",
            "mkfs", "dd if=", "chmod 777", "> /dev/"
        ]
        
        # Check step description and parameters for dangerous patterns
        text_to_check = f"{step.description} {json.dumps(parameters)}".lower()
        
        for pattern in dangerous_patterns:
            if pattern in text_to_check:
                return {
                    "safe": False,
                    "reason": f"Detected dangerous operation: {pattern}"
                }
        
        # Check for system file access
        if tool_name in ["file_tools", "system_tools"]:
            file_path = parameters.get("path", parameters.get("file_path", ""))
            if file_path and self._is_system_path(file_path):
                return {
                    "safe": False,
                    "reason": f"Access to system path not allowed: {file_path}"
                }
        
        return {"safe": True}
    
    def _is_system_path(self, path: str) -> bool:
        """Check if path is a system path that should be protected."""
        
        system_paths = [
            "/bin", "/sbin", "/usr/bin", "/usr/sbin",
            "/etc", "/boot", "/sys", "/proc",
            "C:\\Windows\\System32", "C:\\Windows\\SysWOW64",
            "C:\\Program Files", "C:\\Program Files (x86)"
        ]
        
        path_lower = path.lower()
        return any(path_lower.startswith(sp.lower()) for sp in system_paths)
    
    def _step_requires_approval(self, step: ExecutionStep) -> bool:
        """Check if step requires user approval in supervised mode."""
        
        # Steps that always require approval
        approval_required_tools = [
            "system_tools",  # System commands
            "file_tools"     # File operations
        ]
        
        tool_category = step.metadata.get("tool_category", "") if step.metadata else ""
        
        return tool_category in approval_required_tools
    
    async def _request_user_approval(self, step: ExecutionStep) -> bool:
        """Request user approval for step execution."""
        
        if "request_approval" in self.ui_callbacks:
            approval = await self.ui_callbacks["request_approval"](step)
            logger.info(f"User approval for step '{step.title}': {approval}")
            return approval
        
        # Default to approval if no UI callback
        logger.warning("No approval callback available, defaulting to approved")
        return True
    
    async def _handle_step_failure(self, step: ExecutionStep, step_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle step failure with recovery strategies."""
        
        error_context = {
            "step_id": step.id,
            "step_title": step.title,
            "error": step_result.get("error"),
            "retry_count": step_result.get("retry_count", 0),
            "tool_name": step_result.get("tool_name")
        }
        
        # Try to adapt the plan
        if self.current_plan:
            adapted_plan = await self.task_planner.adapt_plan_during_execution(
                self.current_plan, step.id, error_context
            )
            
            if adapted_plan:
                logger.info("Plan adapted after step failure")
                
                # Update current plan with adapted version
                # This is a simplified adaptation - in practice, you'd need
                # more sophisticated plan merging logic
                remaining_steps = self.current_plan.steps[self.current_step_index + 1:]
                adapted_steps = adapted_plan.steps
                
                # Replace remaining steps with adapted steps
                self.current_plan.steps = (
                    self.current_plan.steps[:self.current_step_index + 1] + adapted_steps
                )
                
                await self._notify_ui("plan_adapted", {"plan": self.current_plan})
                
                return {"continue_execution": True, "adapted": True}
        
        # If we can't adapt, check if this is a critical failure
        critical_failure = step_result.get("retry_count", 0) >= self.max_retry_attempts
        
        return {
            "continue_execution": not critical_failure,
            "adapted": False
        }
    
    async def _start_execution_monitoring(self) -> None:
        """Start real-time execution monitoring."""
        
        self.monitoring_active = True
        
        # Start monitoring task
        asyncio.create_task(self._monitor_execution_loop())
        
        logger.info("Execution monitoring started")
    
    async def _monitor_execution_loop(self) -> None:
        """Main monitoring loop."""
        
        while self.monitoring_active and self.state == ExecutionState.EXECUTING:
            try:
                # Capture current state
                current_state = await self.visual_monitor.get_current_state()
                
                # Store state history
                self.screen_state_history.append({
                    "timestamp": time.time(),
                    "state": current_state
                })
                
                # Keep only recent history
                if len(self.screen_state_history) > 10:
                    self.screen_state_history = self.screen_state_history[-10:]
                
                # Check for unexpected changes or errors
                await self._analyze_execution_state(current_state)
                
                # Wait before next monitoring cycle
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _analyze_execution_state(self, current_state: Dict[str, Any]) -> None:
        """Analyze current execution state for issues."""
        
        # This is where you'd implement advanced monitoring logic
        # For now, it's a placeholder
        
        pass
    
    async def _stop_execution_monitoring(self) -> None:
        """Stop execution monitoring."""
        
        self.monitoring_active = False
        logger.info("Execution monitoring stopped")
    
    async def _handle_pause_state(self) -> None:
        """Handle paused execution state."""
        
        logger.info("Execution paused, waiting for resume")
        
        await self._notify_ui("execution_paused", {})
        
        # Wait until state changes from paused
        while self.state == ExecutionState.PAUSED:
            await asyncio.sleep(0.5)
        
        logger.info("Execution resumed")
    
    async def _notify_ui(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """Notify UI of execution events."""
        
        if "ui_notification" in self.ui_callbacks:
            try:
                await self.ui_callbacks["ui_notification"](event_type, data or {})
            except Exception as e:
                logger.error(f"UI notification error: {e}")
    
    def _update_execution_stats(self, execution_result: Dict[str, Any]) -> None:
        """Update execution statistics."""
        
        self.execution_stats["plans_executed"] += 1
        
        if execution_result.get("success", False):
            self.execution_stats["steps_completed"] += execution_result.get("steps_completed", 0)
        
        failed_steps = len(execution_result.get("failed_steps", []))
        self.execution_stats["steps_failed"] += failed_steps
        
        execution_time = execution_result.get("execution_time", 0)
        self.execution_stats["total_execution_time"] += execution_time
        
        # Calculate success rate
        total_plans = self.execution_stats["plans_executed"]
        successful_plans = total_plans - len([r for r in self.execution_history if not r.get("success", False)])
        self.execution_stats["success_rate"] = successful_plans / total_plans if total_plans > 0 else 0.0
    
    def pause_execution(self) -> bool:
        """Pause current execution."""
        
        if self.state == ExecutionState.EXECUTING:
            self.state = ExecutionState.PAUSED
            logger.info("Execution paused by user")
            return True
        
        return False
    
    def resume_execution(self) -> bool:
        """Resume paused execution."""
        
        if self.state == ExecutionState.PAUSED:
            self.state = ExecutionState.EXECUTING
            logger.info("Execution resumed by user")
            return True
        
        return False
    
    def cancel_execution(self) -> bool:
        """Cancel current execution."""
        
        if self.state in [ExecutionState.EXECUTING, ExecutionState.PAUSED]:
            self.state = ExecutionState.CANCELLED
            logger.info("Execution cancelled by user")
            return True
        
        return False
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        
        return {
            "state": self.state.value,
            "execution_mode": self.execution_mode.value,
            "current_plan_id": self.current_plan.id if self.current_plan else None,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.current_plan.steps) if self.current_plan else 0,
            "statistics": self.execution_stats.copy()
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history."""
        
        return self.execution_history.copy()