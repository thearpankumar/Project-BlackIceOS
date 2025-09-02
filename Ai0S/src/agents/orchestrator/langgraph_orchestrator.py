"""
LangGraph Orchestrator - State Machine with Conditional Routing
Advanced agentic AI orchestration for dynamic OS control with real-time adaptation.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TypedDict
from enum import Enum
import traceback

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

from ...backend.models.ai_models import ExecutionPlan, ExecutionStep, ScreenAnalysis, get_ai_models
from ...backend.core.visual_monitor import VisualStateMonitor, ScreenState, get_visual_monitor
from ...backend.core.mcp_executor import get_mcp_executor, MCPExecutor, ExecutionResult
from ...utils.platform_detector import get_system_environment, get_os_commands
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status types."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ADAPTED = "adapted"
    CANCELLED = "cancelled"


class AgentState(TypedDict):
    """LangGraph agent state."""
    # Task Information
    task_id: str
    user_intent: str
    original_request: str
    
    # Execution State
    execution_plan: Optional[ExecutionPlan]
    current_step_index: int
    current_step: Optional[ExecutionStep]
    execution_status: str
    
    # Context & Environment
    screen_state: Optional[ScreenState]
    system_context: Dict[str, Any]
    previous_actions: List[Dict[str, Any]]
    
    # Analysis & Monitoring
    screen_analysis: Optional[ScreenAnalysis]
    confidence_score: float
    retry_count: int
    adaptation_history: List[Dict[str, Any]]
    
    # Communication
    messages: List[BaseMessage]
    ui_updates: List[Dict[str, Any]]
    error_messages: List[str]
    
    # Performance
    start_time: datetime
    step_timings: List[float]
    total_execution_time: Optional[float]


class ExecutionResult(BaseModel):
    """Result of step execution."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    screen_change: Optional[Dict[str, Any]] = None
    next_action: Optional[str] = None
    requires_adaptation: bool = False
    adaptation_reason: Optional[str] = None


class LangGraphOrchestrator:
    """Advanced LangGraph orchestrator for agentic OS control."""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_models = None
        self.visual_monitor = None
        self.mcp_executor = None
        self.graph = None  # Will be a compiled LangGraph
        
        # Active executions
        self.active_executions: Dict[str, AgentState] = {}
        
        # Performance tracking
        self.execution_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "adaptations_made": 0,
            "avg_execution_time": 0.0
        }
        
        # UI callback for real-time updates
        self.ui_callback: Optional[Callable] = None
    
    async def initialize(self) -> None:
        """Initialize the orchestrator with required components."""
        try:
            logger.info("Initializing LangGraph Orchestrator...")
            
            # Initialize AI models and visual monitor
            self.ai_models = await get_ai_models()
            self.visual_monitor = await get_visual_monitor()
            
            # Initialize MCP executor
            self.mcp_executor = await get_mcp_executor()
            
            # Build the LangGraph
            self.graph = self._build_agent_graph()
            
            logger.info("LangGraph Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph Orchestrator: {e}")
            raise
    
    def _build_agent_graph(self):
        """Build the main agent graph with conditional routing."""
        
        graph = StateGraph(AgentState)
        
        # Add nodes for each stage of execution
        graph.add_node("receive_input", self._receive_input)
        graph.add_node("analyze_request", self._analyze_request)
        graph.add_node("create_plan", self._create_plan)
        graph.add_node("capture_screen", self._capture_screen)
        graph.add_node("execute_step", self._execute_step)
        graph.add_node("verify_progress", self._verify_progress)
        graph.add_node("adapt_plan", self._adapt_plan)
        graph.add_node("complete_task", self._complete_task)
        graph.add_node("handle_error", self._handle_error)
        graph.add_node("update_ui", self._update_ui)
        
        # Set entry point
        graph.set_entry_point("receive_input")
        
        # Add edges with conditional routing
        graph.add_edge("receive_input", "analyze_request")
        graph.add_edge("analyze_request", "create_plan")
        graph.add_edge("create_plan", "update_ui")
        graph.add_edge("update_ui", "capture_screen")
        
        # Conditional routing from screen capture
        graph.add_conditional_edges(
            "capture_screen",
            self._route_from_screen_analysis,
            {
                "execute": "execute_step",
                "adapt": "adapt_plan", 
                "error": "handle_error",
                "complete": "complete_task"
            }
        )
        
        # Conditional routing from step execution
        graph.add_conditional_edges(
            "execute_step",
            self._route_from_execution,
            {
                "verify": "verify_progress",
                "retry": "execute_step",
                "adapt": "adapt_plan",
                "error": "handle_error",
                "complete": "complete_task"
            }
        )
        
        # Conditional routing from progress verification
        graph.add_conditional_edges(
            "verify_progress", 
            self._route_from_verification,
            {
                "next_step": "capture_screen",
                "complete": "complete_task",
                "adapt": "adapt_plan",
                "error": "handle_error"
            }
        )
        
        # Routes from adaptation
        graph.add_edge("adapt_plan", "update_ui")
        
        # Routes from error handling
        graph.add_conditional_edges(
            "handle_error",
            self._route_from_error,
            {
                "retry": "capture_screen",
                "adapt": "adapt_plan", 
                "fail": "complete_task"
            }
        )
        
        # Terminal states
        graph.add_edge("complete_task", END)
        
        return graph.compile()
    
    # =========================================================================
    # Graph Node Functions
    # =========================================================================
    
    async def _receive_input(self, state: AgentState) -> AgentState:
        """Receive and process user input."""
        logger.info(f"Receiving input for task: {state['task_id']}")
        
        # Initialize execution state
        state["execution_status"] = ExecutionStatus.IN_PROGRESS.value
        state["current_step_index"] = 0
        state["retry_count"] = 0
        state["confidence_score"] = 0.0
        state["start_time"] = datetime.now()
        state["step_timings"] = []
        state["adaptation_history"] = []
        state["ui_updates"] = []
        state["error_messages"] = []
        
        # Get system context
        system_env = get_system_environment()
        state["system_context"] = {
            "os": system_env.os,
            "architecture": system_env.architecture,
            "display_server": system_env.display_server,
            "capabilities": system_env.capabilities,
            "screen_resolution": system_env.screen_resolution
        }
        
        # Add initial message
        state["messages"].append(
            HumanMessage(content=state["user_intent"])
        )
        
        await self._send_ui_update(state, "task_started", {
            "task_id": state["task_id"],
            "user_intent": state["user_intent"],
            "status": "analyzing"
        })
        
        return state
    
    async def _analyze_request(self, state: AgentState) -> AgentState:
        """Analyze user request and determine intent."""
        logger.info("Analyzing user request...")
        
        try:
            # Use AI to analyze command intent
            intent_analysis = await self.ai_models.analyze_command_intent(
                state["user_intent"], 
                state["system_context"]
            )
            
            state["system_context"]["intent_analysis"] = intent_analysis
            state["confidence_score"] = intent_analysis.get("confidence", 0.0)
            
            # Add analysis to messages
            state["messages"].append(
                AIMessage(content=f"Analyzed intent: {intent_analysis.get('interpretation', 'Unknown')}")
            )
            
            await self._send_ui_update(state, "intent_analyzed", {
                "intent_type": intent_analysis.get("intent_type"),
                "confidence": intent_analysis.get("confidence"),
                "estimated_steps": intent_analysis.get("estimated_steps"),
                "requires_confirmation": intent_analysis.get("requires_confirmation")
            })
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            state["error_messages"].append(f"Intent analysis failed: {e}")
        
        return state
    
    async def _create_plan(self, state: AgentState) -> AgentState:
        """Create dynamic execution plan."""
        logger.info("Creating execution plan...")
        
        try:
            # Capture current screen for context
            screen_state = await self.visual_monitor.capture_and_analyze(force_analysis=True)
            state["screen_state"] = screen_state
            state["screen_analysis"] = screen_state.analysis
            
            # Generate execution plan using AI
            execution_plan = await self.ai_models.create_execution_plan(
                state["user_intent"],
                screen_state.analysis,
                state["system_context"]
            )
            
            state["execution_plan"] = execution_plan
            state["confidence_score"] = execution_plan.confidence_score
            
            # Add plan to messages
            plan_summary = f"Created plan with {execution_plan.total_steps} steps (confidence: {execution_plan.confidence_score:.2f})"
            state["messages"].append(AIMessage(content=plan_summary))
            
            logger.info(f"Execution plan created: {execution_plan.total_steps} steps")
            
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            state["error_messages"].append(f"Plan creation failed: {e}")
            state["execution_status"] = ExecutionStatus.FAILED.value
        
        return state
    
    async def _capture_screen(self, state: AgentState) -> AgentState:
        """Capture and analyze current screen state."""
        logger.debug("Capturing screen state...")
        
        try:
            # Capture current screen
            screen_state = await self.visual_monitor.capture_and_analyze()
            state["screen_state"] = screen_state
            state["screen_analysis"] = screen_state.analysis
            
            # Check for plan disruptions
            if state["execution_plan"]:
                disruptions = await self.visual_monitor.detect_plan_disruption({})
                if disruptions:
                    state["system_context"]["disruptions"] = disruptions
                    logger.warning(f"Detected {len(disruptions)} plan disruptions")
            
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            state["error_messages"].append(f"Screen capture failed: {e}")
        
        return state
    
    async def _execute_step(self, state: AgentState) -> AgentState:
        """Execute the current step."""
        if not state["execution_plan"] or not state["execution_plan"].steps:
            return state
        
        step_index = state["current_step_index"]
        if step_index >= len(state["execution_plan"].steps):
            state["execution_status"] = ExecutionStatus.COMPLETED.value
            return state
        
        current_step = state["execution_plan"].steps[step_index]
        state["current_step"] = current_step
        
        logger.info(f"Executing step {step_index + 1}: {current_step.description}")
        
        start_time = datetime.now()
        
        try:
            # Send UI update about step execution
            await self._send_ui_update(state, "step_executing", {
                "step_index": step_index,
                "step": current_step.__dict__,
                "total_steps": len(state["execution_plan"].steps)
            })
            
            # Execute the step (placeholder - will be implemented with MCP)
            execution_result = await self._execute_single_step(current_step, state)
            
            # Record timing
            execution_time = (datetime.now() - start_time).total_seconds()
            state["step_timings"].append(execution_time)
            
            # Process execution result
            if execution_result.success:
                logger.info(f"Step {step_index + 1} completed successfully")
                state["current_step_index"] += 1
                state["retry_count"] = 0
                
                # Record action in history
                action_record = {
                    "step_index": step_index,
                    "step": current_step.__dict__,
                    "result": "success",
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
                state["previous_actions"].append(action_record)
                
            else:
                logger.warning(f"Step {step_index + 1} failed: {execution_result.error}")
                state["retry_count"] += 1
                state["error_messages"].append(execution_result.error or "Step execution failed")
                
                if execution_result.requires_adaptation:
                    state["system_context"]["adaptation_needed"] = True
                    state["system_context"]["adaptation_reason"] = execution_result.adaptation_reason
            
            # Send step completion update
            await self._send_ui_update(state, "step_completed", {
                "step_index": step_index,
                "success": execution_result.success,
                "error": execution_result.error,
                "execution_time": execution_time
            })
            
        except Exception as e:
            logger.error(f"Step execution error: {e}")
            state["error_messages"].append(f"Step execution error: {e}")
            state["retry_count"] += 1
        
        return state
    
    async def _execute_single_step(self, step: ExecutionStep, state: AgentState) -> ExecutionResult:
        """Execute a single step using MCP integration."""
        
        try:
            # Use MCP executor to run the step
            if self.mcp_executor:
                result = await self.mcp_executor.execute_step(step)
                
                # Log execution details
                if result.success:
                    logger.debug(f"Step executed successfully: {result.output}")
                else:
                    logger.warning(f"Step failed: {result.error}")
                
                return result
            else:
                # Fallback if MCP executor not available
                logger.warning("MCP executor not available, using fallback execution")
                return ExecutionResult(
                    success=True,
                    output=f"Fallback execution: {step.description}",
                    requires_adaptation=False
                )
                
        except Exception as e:
            logger.error(f"Single step execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}",
                requires_adaptation=True,
                adaptation_reason=f"Unexpected execution error: {e}"
            )
    
    async def _verify_progress(self, state: AgentState) -> AgentState:
        """Verify execution progress and determine next action."""
        logger.debug("Verifying execution progress...")
        
        try:
            # Check if all steps are completed
            if (state["execution_plan"] and 
                state["current_step_index"] >= len(state["execution_plan"].steps)):
                
                state["execution_status"] = ExecutionStatus.COMPLETED.value
                logger.info("All steps completed successfully")
            
            # Check confidence and error rates
            error_rate = len(state["error_messages"]) / max(state["current_step_index"], 1)
            if error_rate > 0.3:  # More than 30% error rate
                state["system_context"]["high_error_rate"] = True
                logger.warning(f"High error rate detected: {error_rate:.2f}")
            
        except Exception as e:
            logger.error(f"Progress verification failed: {e}")
            state["error_messages"].append(f"Progress verification failed: {e}")
        
        return state
    
    async def _adapt_plan(self, state: AgentState) -> AgentState:
        """Adapt execution plan based on current state."""
        logger.info("Adapting execution plan...")
        
        try:
            if not state["execution_plan"] or not state["screen_analysis"]:
                logger.warning("Cannot adapt plan - missing plan or screen analysis")
                return state
            
            # Build error context for adaptation
            error_context = {
                "current_step": state["current_step_index"],
                "completed_steps": state["current_step_index"],
                "error_messages": state["error_messages"][-3:],  # Last 3 errors
                "retry_count": state["retry_count"],
                "disruptions": state["system_context"].get("disruptions", [])
            }
            
            # Use AI to adapt the plan
            adapted_plan = await self.ai_models.adapt_plan(
                state["execution_plan"],
                state["screen_analysis"], 
                error_context
            )
            
            # Update state with adapted plan
            original_plan = state["execution_plan"]
            state["execution_plan"] = adapted_plan
            
            # Record adaptation
            adaptation_record = {
                "timestamp": datetime.now().isoformat(),
                "reason": error_context,
                "original_steps": len(original_plan.steps),
                "adapted_steps": len(adapted_plan.steps),
                "adaptation_count": len(state["adaptation_history"]) + 1
            }
            state["adaptation_history"].append(adaptation_record)
            
            # Update statistics
            self.execution_stats["adaptations_made"] += 1
            
            # Reset retry count after adaptation
            state["retry_count"] = 0
            
            # Send UI update
            await self._send_ui_update(state, "plan_adapted", {
                "reason": "Plan adapted due to execution issues",
                "new_steps": len(adapted_plan.steps),
                "adaptation_count": len(state["adaptation_history"])
            })
            
            logger.info(f"Plan adapted: {len(adapted_plan.steps)} steps")
            
        except Exception as e:
            logger.error(f"Plan adaptation failed: {e}")
            state["error_messages"].append(f"Plan adaptation failed: {e}")
        
        return state
    
    async def _complete_task(self, state: AgentState) -> AgentState:
        """Complete task execution and cleanup."""
        logger.info(f"Completing task: {state['task_id']}")
        
        # Calculate total execution time
        if state["start_time"]:
            total_time = (datetime.now() - state["start_time"]).total_seconds()
            state["total_execution_time"] = total_time
        
        # Determine final status
        if state["execution_status"] != ExecutionStatus.FAILED.value:
            if state["current_step_index"] >= len(state["execution_plan"].steps):
                state["execution_status"] = ExecutionStatus.COMPLETED.value
                self.execution_stats["successful_tasks"] += 1
            else:
                state["execution_status"] = ExecutionStatus.FAILED.value
                self.execution_stats["failed_tasks"] += 1
        else:
            self.execution_stats["failed_tasks"] += 1
        
        # Update statistics
        self.execution_stats["total_tasks"] += 1
        if state["total_execution_time"]:
            current_avg = self.execution_stats["avg_execution_time"]
            total_tasks = self.execution_stats["total_tasks"]
            self.execution_stats["avg_execution_time"] = (
                (current_avg * (total_tasks - 1) + state["total_execution_time"]) / total_tasks
            )
        
        # Final UI update
        await self._send_ui_update(state, "task_complete", {
            "task_id": state["task_id"],
            "status": state["execution_status"],
            "total_time": state["total_execution_time"],
            "steps_completed": state["current_step_index"],
            "total_steps": len(state["execution_plan"].steps) if state["execution_plan"] else 0,
            "adaptations": len(state["adaptation_history"]),
            "error_count": len(state["error_messages"])
        })
        
        # Cleanup
        if state["task_id"] in self.active_executions:
            del self.active_executions[state["task_id"]]
        
        logger.info(f"Task {state['task_id']} completed with status: {state['execution_status']}")
        return state
    
    async def _handle_error(self, state: AgentState) -> AgentState:
        """Handle execution errors with recovery strategies."""
        logger.warning("Handling execution error...")
        
        error_count = len(state["error_messages"])
        retry_count = state["retry_count"]
        
        # Determine error handling strategy
        if retry_count < self.settings.MAX_RETRIES:
            # Try again with retry
            logger.info(f"Retrying step (attempt {retry_count + 1})")
            state["system_context"]["retry_strategy"] = "simple_retry"
        
        elif error_count > 5 or retry_count >= self.settings.MAX_RETRIES:
            # Too many errors, fail the task
            logger.error("Too many errors, failing task")
            state["execution_status"] = ExecutionStatus.FAILED.value
            state["system_context"]["error_strategy"] = "fail_task"
        
        else:
            # Try adaptation
            logger.info("Attempting plan adaptation for error recovery")
            state["system_context"]["error_strategy"] = "adapt_plan"
        
        return state
    
    async def _update_ui(self, state: AgentState) -> AgentState:
        """Send updates to UI."""
        await self._send_ui_update(state, "state_update", {
            "task_id": state["task_id"],
            "status": state["execution_status"],
            "current_step": state["current_step_index"],
            "total_steps": len(state["execution_plan"].steps) if state["execution_plan"] else 0,
            "confidence": state["confidence_score"],
            "error_count": len(state["error_messages"])
        })
        
        return state
    
    # =========================================================================
    # Conditional Routing Functions
    # =========================================================================
    
    def _route_from_screen_analysis(self, state: AgentState) -> str:
        """Route based on screen analysis results."""
        
        # Check for critical errors
        if state["error_messages"] and state["retry_count"] >= self.settings.MAX_RETRIES:
            return "error"
        
        # Check if task is already complete
        if (state["execution_plan"] and 
            state["current_step_index"] >= len(state["execution_plan"].steps)):
            return "complete"
        
        # Check for disruptions requiring adaptation
        disruptions = state["system_context"].get("disruptions", [])
        if disruptions and state["retry_count"] > 1:
            return "adapt"
        
        # Normal execution
        return "execute"
    
    def _route_from_execution(self, state: AgentState) -> str:
        """Route based on execution results."""
        
        # Check if adaptation is needed
        if state["system_context"].get("adaptation_needed"):
            return "adapt"
        
        # Check retry conditions
        if (state["error_messages"] and 
            state["retry_count"] < self.settings.MAX_RETRIES and
            not state["system_context"].get("high_error_rate")):
            return "retry"
        
        # Check for unrecoverable errors
        if (state["error_messages"] and 
            (state["retry_count"] >= self.settings.MAX_RETRIES or
             state["system_context"].get("high_error_rate"))):
            return "error"
        
        # Check if task is complete
        if (state["execution_plan"] and 
            state["current_step_index"] >= len(state["execution_plan"].steps)):
            return "complete"
        
        # Continue with verification
        return "verify"
    
    def _route_from_verification(self, state: AgentState) -> str:
        """Route based on verification results."""
        
        # Check if task is complete
        if state["execution_status"] == ExecutionStatus.COMPLETED.value:
            return "complete"
        
        # Check for high error rates requiring adaptation
        if state["system_context"].get("high_error_rate"):
            return "adapt"
        
        # Check for other errors
        if state["error_messages"] and state["retry_count"] >= self.settings.MAX_RETRIES:
            return "error"
        
        # Continue to next step
        return "next_step"
    
    def _route_from_error(self, state: AgentState) -> str:
        """Route based on error handling strategy."""
        
        strategy = state["system_context"].get("error_strategy", "fail")
        
        if strategy == "simple_retry":
            return "retry"
        elif strategy == "adapt_plan":
            return "adapt" 
        else:
            return "fail"
    
    # =========================================================================
    # Public Interface
    # =========================================================================
    
    async def execute_task(self, user_intent: str, task_id: Optional[str] = None) -> str:
        """
        Execute a task using the LangGraph orchestrator.
        
        Args:
            user_intent: User's natural language request
            task_id: Optional task ID, generated if not provided
            
        Returns:
            Task ID for tracking
        """
        if not self.graph:
            raise RuntimeError("Orchestrator not initialized")
        
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Initialize agent state
        initial_state: AgentState = {
            "task_id": task_id,
            "user_intent": user_intent,
            "original_request": user_intent,
            "execution_plan": None,
            "current_step_index": 0,
            "current_step": None,
            "execution_status": ExecutionStatus.PENDING.value,
            "screen_state": None,
            "system_context": {},
            "previous_actions": [],
            "screen_analysis": None,
            "confidence_score": 0.0,
            "retry_count": 0,
            "adaptation_history": [],
            "messages": [],
            "ui_updates": [],
            "error_messages": [],
            "start_time": datetime.now(),
            "step_timings": [],
            "total_execution_time": None
        }
        
        # Store active execution
        self.active_executions[task_id] = initial_state
        
        # Execute the graph asynchronously
        asyncio.create_task(self._run_graph_execution(initial_state))
        
        logger.info(f"Task {task_id} started: {user_intent}")
        return task_id
    
    async def _run_graph_execution(self, initial_state: AgentState) -> None:
        """Run the graph execution in a separate task."""
        try:
            # Execute the graph
            final_state = await self.graph.ainvoke(initial_state)
            logger.info(f"Graph execution completed for task {initial_state['task_id']}")
            
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            logger.error(traceback.format_exc())
            
            # Update state with error
            if initial_state["task_id"] in self.active_executions:
                error_state = self.active_executions[initial_state["task_id"]]
                error_state["execution_status"] = ExecutionStatus.FAILED.value
                error_state["error_messages"].append(f"Graph execution failed: {e}")
                
                # Send error update to UI
                await self._send_ui_update(error_state, "execution_error", {
                    "task_id": initial_state["task_id"],
                    "error": str(e)
                })
    
    def set_ui_callback(self, callback: Callable) -> None:
        """Set callback for UI updates."""
        self.ui_callback = callback
    
    async def _send_ui_update(self, state: AgentState, event_type: str, data: Dict[str, Any]) -> None:
        """Send update to UI."""
        update = {
            "event_type": event_type,
            "task_id": state["task_id"],
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        state["ui_updates"].append(update)
        
        if self.ui_callback:
            try:
                await self.ui_callback(update)
            except Exception as e:
                logger.error(f"UI callback failed: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task."""
        if task_id not in self.active_executions:
            return None
        
        state = self.active_executions[task_id]
        return {
            "task_id": task_id,
            "status": state["execution_status"],
            "current_step": state["current_step_index"],
            "total_steps": len(state["execution_plan"].steps) if state["execution_plan"] else 0,
            "confidence": state["confidence_score"],
            "error_count": len(state["error_messages"]),
            "adaptation_count": len(state["adaptation_history"]),
            "execution_time": (datetime.now() - state["start_time"]).total_seconds()
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get overall execution statistics."""
        return self.execution_stats.copy()


# Global orchestrator instance
_orchestrator: Optional[LangGraphOrchestrator] = None


async def get_orchestrator() -> LangGraphOrchestrator:
    """Get global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LangGraphOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


if __name__ == "__main__":
    # Test the orchestrator
    async def test_orchestrator():
        orchestrator = await get_orchestrator()
        
        print("=== Testing LangGraph Orchestrator ===")
        
        # Test task execution
        task_id = await orchestrator.execute_task("Open a browser and search for Python tutorials")
        print(f"Started task: {task_id}")
        
        # Monitor task progress
        for _ in range(10):
            await asyncio.sleep(1)
            status = orchestrator.get_task_status(task_id)
            if status:
                print(f"Status: {status['status']} - Step {status['current_step']}/{status['total_steps']}")
                
                if status['status'] in ['completed', 'failed']:
                    break
        
        # Show statistics
        stats = orchestrator.get_execution_stats()
        print(f"Execution stats: {stats}")
    
    asyncio.run(test_orchestrator())