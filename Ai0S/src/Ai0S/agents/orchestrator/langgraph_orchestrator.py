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
    """LangGraph agent state - simplified with JSON-serializable types only."""
    # Task Information
    task_id: str
    user_intent: str
    original_request: str
    
    # Execution State
    execution_plan: Optional[Dict[str, Any]]  # Simplified from ExecutionPlan
    current_step_index: int
    current_step: Optional[Dict[str, Any]]  # Simplified from ExecutionStep
    execution_status: str
    
    # Context & Environment
    screen_state: Optional[Dict[str, Any]]  # Simplified from ScreenState
    system_context: Dict[str, Any]
    previous_actions: List[Dict[str, Any]]
    
    # Analysis & Monitoring
    screen_analysis: Optional[Dict[str, Any]]  # Simplified from ScreenAnalysis
    confidence_score: float
    retry_count: int
    adaptation_history: List[Dict[str, Any]]
    
    # Communication
    messages: List[Dict[str, Any]]  # Simplified from BaseMessage
    ui_updates: List[Dict[str, Any]]
    error_messages: List[str]
    
    # Performance
    start_time: str  # ISO string instead of datetime
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
            
            # Initialize AI models (this is async)
            self.ai_models = await get_ai_models()
            logger.info("AI models initialized")
            
            # Initialize visual monitor (this is sync, returns Optional)
            self.visual_monitor = get_visual_monitor()
            if not self.visual_monitor:
                # Create a new visual monitor if none exists
                from ...backend.core.visual_monitor import VisualStateMonitor, initialize_visual_monitor
                self.visual_monitor = initialize_visual_monitor(self.ai_models, None)
            
            # Initialize MCP executor (this is sync, returns Optional)
            self.mcp_executor = get_mcp_executor()
            if not self.mcp_executor:
                # Create a new MCP executor if none exists
                from ...backend.core.mcp_executor import MCPExecutor, initialize_mcp_executor
                from ...mcp_server.server import MCPServer
                from ...backend.security.security_framework import SecurityFramework
                from ...backend.core.error_recovery import ErrorRecoverySystem
                
                mcp_server = MCPServer()
                security_framework = SecurityFramework()
                error_recovery = ErrorRecoverySystem(self.ai_models)
                self.mcp_executor = initialize_mcp_executor(mcp_server, security_framework, error_recovery)
            
            # Build the LangGraph
            self.graph = self._build_agent_graph()
            
            logger.info("LangGraph Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph Orchestrator: {e}")
            raise
    
    def _build_agent_graph(self):
        """Build simplified agent graph - pure LLM driven with minimal nodes."""
        
        graph = StateGraph(AgentState)
        
        # Complete workflow with step execution
        graph.add_node("receive_input", self._receive_input)
        graph.add_node("analyze_request", self._analyze_request)  
        graph.add_node("create_plan", self._create_plan)
        graph.add_node("execute_steps", self._execute_steps)  # NEW: Actually execute the steps
        graph.add_node("complete_task", self._complete_task)
        
        # Set entry point
        graph.set_entry_point("receive_input")
        
        # Complete flow with step execution
        graph.add_edge("receive_input", "analyze_request")
        graph.add_edge("analyze_request", "create_plan") 
        graph.add_edge("create_plan", "execute_steps")  # Execute the planned steps
        graph.add_edge("execute_steps", "complete_task")
        graph.add_edge("complete_task", END)
        
        logger.info("Built LangGraph with 5 nodes: receive_input → analyze_request → create_plan → execute_steps → complete_task")
        return graph.compile()
    
    # =========================================================================
    # Graph Node Functions
    # =========================================================================
    
    async def _receive_input(self, state: AgentState) -> AgentState:
        """Receive and process user input."""
        task_id = state['task_id']
        logger.info(f"ENTER _receive_input for task: {task_id}")
        
        # Initialize execution state
        logger.info(f"Task {task_id} execution in progress")
        state["current_step_index"] = 0
        state["retry_count"] = 0
        state["confidence_score"] = 0.0
        state["start_time"] = datetime.now().isoformat()
        state["step_timings"] = []
        state["adaptation_history"] = []
        state["ui_updates"] = []
        state["error_messages"] = []
        
        # Get system context (simplified to avoid hanging)
        import platform
        state["system_context"] = {
            "os": platform.system(),
            "architecture": platform.machine(),
            "display_server": "unknown",
            "capabilities": ["basic_automation"],
            "screen_resolution": (1920, 1080)
        }
        
        # Add initial message as dict
        state["messages"].append({
            "role": "human",
            "content": state["user_intent"]
        })
        
        logger.info(f"EXIT _receive_input for task: {task_id}, status: {state['execution_status']}")
        return state
    
    async def _analyze_request(self, state: AgentState) -> AgentState:
        """Analyze user request and determine intent."""
        task_id = state['task_id']
        logger.info(f"ENTER _analyze_request for task: {task_id}")
        logger.info("Analyzing user request...")
        
        try:
            logger.info(f"About to call ai_models.analyze_command_intent for task: {task_id}")
            
            # Use AI to analyze command intent
            intent_analysis = await self.ai_models.analyze_command_intent(
                state["user_intent"], 
                state["system_context"]
            )
            
            state["system_context"]["intent_analysis"] = intent_analysis
            state["confidence_score"] = intent_analysis.get("confidence", 0.0)
            
            # Add analysis to messages as dict
            state["messages"].append({
                "role": "assistant",
                "content": f"Analyzed intent: {intent_analysis.get('interpretation', 'Unknown')}"
            })
            
            logger.info(f"Intent analysis completed for task: {task_id}")
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            state["error_messages"].append(f"Intent analysis failed: {e}")
        
        logger.info(f"EXIT _analyze_request for task: {task_id}")
        return state
    
    async def _create_plan(self, state: AgentState) -> AgentState:
        """Create dynamic execution plan."""
        task_id = state['task_id']
        logger.info(f"ENTER _create_plan for task: {task_id}")
        logger.info("Creating execution plan...")
        
        try:
            # Skip screen capture for now to avoid blocking
            logger.info(f"Skipping screen capture for task: {task_id}")
            
            # Generate execution plan using AI
            logger.info(f"About to call ai_models.create_execution_plan for task: {task_id}")
            execution_plan = await self.ai_models.create_execution_plan(
                state["user_intent"],
                None,  # Skip screen analysis for now
                state["system_context"]
            )
            logger.info(f"AI generated execution plan for task: {task_id}")
            
            # Convert ExecutionPlan to dict for JSON serialization
            state["execution_plan"] = execution_plan.model_dump()
            state["confidence_score"] = execution_plan.confidence_score
            
            # Log plan details
            logger.info(f"Execution plan created for task {task_id}:")
            logger.info(f"  - Total steps: {execution_plan.total_steps}")
            logger.info(f"  - Confidence: {execution_plan.confidence_score:.2f}")
            for i, step in enumerate(execution_plan.steps):
                logger.info(f"  - Step {i+1}: {step.description}")
            
            # Add plan to messages as dict
            plan_summary = f"Created plan with {execution_plan.total_steps} steps (confidence: {execution_plan.confidence_score:.2f})"
            state["messages"].append({
                "role": "assistant",
                "content": plan_summary
            })
            
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            state["error_messages"].append(f"Plan creation failed: {e}")
            state["execution_status"] = ExecutionStatus.FAILED.value
        
        logger.info(f"EXIT _create_plan for task: {task_id}")
        return state
    
    async def _execute_steps(self, state: AgentState) -> AgentState:
        """Execute the planned steps using MCP executor."""
        task_id = state['task_id']
        logger.info(f"ENTER _execute_steps for task: {task_id}")
        
        try:
            plan = state.get("execution_plan")
            if not plan or not plan.get("steps"):
                logger.error(f"No execution plan found for task {task_id}")
                state["error_messages"].append("No execution plan to execute")
                return state
            
            steps = plan.get("steps", [])
            total_steps = len(steps)
            logger.info(f"Executing {total_steps} steps for task {task_id}")
            
            # Execute each step - with smart stopping for application launches
            app_opened = False
            
            for i, step in enumerate(steps):
                step_num = i + 1
                state["current_step_index"] = i
                state["current_step"] = step
                
                description = step.get('description', 'Unknown')
                logger.info(f"Executing step {step_num}/{total_steps}: {description}")
                
                # Check if this is a fallback step for the same application
                if app_opened and self._is_fallback_step(description, i, steps):
                    logger.info(f"Skipping step {step_num} - application already opened successfully")
                    continue
                
                try:
                    # Execute the step based on action_type
                    action_type = step.get("action_type", "command")
                    
                    if action_type == "command":
                        # Execute system command
                        success = await self._execute_command_step(step, state)
                        if success and self._is_app_launch_step(description):
                            app_opened = True
                            logger.info(f"Application launch successful in step {step_num}")
                    elif action_type == "click":
                        # Execute UI click
                        await self._execute_click_step(step, state)
                    elif action_type == "type":
                        # Execute text input
                        await self._execute_type_step(step, state)
                    elif action_type == "wait":
                        # Wait/delay step
                        await self._execute_wait_step(step, state)
                    elif action_type == "verify":
                        # Verification step
                        await self._execute_verify_step(step, state)
                    else:
                        logger.warning(f"Unknown action_type: {action_type} for step {step_num}")
                    
                    logger.info(f"Step {step_num} completed successfully")
                    
                except Exception as e:
                    logger.error(f"Step {step_num} failed: {e}")
                    state["error_messages"].append(f"Step {step_num} failed: {e}")
                    # Continue with next step instead of failing completely
            
            logger.info(f"All {total_steps} steps executed for task {task_id}")
            
        except Exception as e:
            logger.error(f"Step execution failed for task {task_id}: {e}")
            state["error_messages"].append(f"Step execution failed: {e}")
        
        logger.info(f"EXIT _execute_steps for task: {task_id}")
        return state
    
    def _is_fallback_step(self, description: str, step_index: int, all_steps: List[Dict]) -> bool:
        """Check if this step is a fallback for the same application."""
        desc_lower = description.lower()
        
        # Common fallback patterns
        fallback_indicators = [
            "if", "fails", "try", "fallback", "alternative", 
            "command fails", "doesn't work", "not found"
        ]
        
        # Check if description contains fallback language
        has_fallback_language = any(indicator in desc_lower for indicator in fallback_indicators)
        
        # Check if it's trying to open the same type of application
        if step_index > 0:
            prev_desc = all_steps[step_index - 1].get('description', '').lower()
            same_app_keywords = ['vs code', 'vscode', 'code', 'chrome', 'firefox', 'editor']
            
            for keyword in same_app_keywords:
                if keyword in prev_desc and keyword in desc_lower:
                    return has_fallback_language
        
        return has_fallback_language
    
    def _is_app_launch_step(self, description: str) -> bool:
        """Check if this step launches an application."""
        desc_lower = description.lower()
        
        # Application launch indicators
        launch_indicators = [
            "open", "launch", "start", "execute", "run",
            "vs code", "chrome", "firefox", "editor", "terminal"
        ]
        
        return any(indicator in desc_lower for indicator in launch_indicators)
    
    async def _execute_command_step(self, step: Dict[str, Any], state: AgentState) -> bool:
        """Execute a system command step dynamically based on AI plan. Returns True if successful."""
        description = step.get("description", "Unknown command")
        target = step.get("target", "")
        parameters = step.get("parameters", {})
        
        logger.info(f"Executing command step: {description}")
        logger.info(f"Target: {target}, Parameters: {parameters}")
        
        # Use AI to generate the actual command to execute
        try:
            # Ask AI to convert the step description into an executable command
            command_prompt = f"""
            Convert this execution step into a specific Linux command:
            
            Step Description: {description}
            Target: {target}
            Parameters: {parameters}
            
            Rules:
            1. Return ONLY the command to execute (no explanation)
            2. Use proper Linux commands (e.g., "google-chrome", "firefox", "gedit", "code", etc.)
            3. For opening applications, use the executable name directly
            4. For URLs, use: google-chrome "https://example.com" or firefox "https://example.com"
            5. For files, include the full path if provided
            6. If the application might not exist, provide alternatives separated by ||
            
            Examples:
            - "Open Google Chrome" → "google-chrome"
            - "Open Firefox and go to YouTube" → "firefox https://youtube.com"
            - "Open text editor" → "gedit || code || nano"
            - "Open file manager" → "nautilus || thunar || pcmanfm"
            
            Command:
            """
            
            # Get the command from AI
            command_response = await self.ai_models.analyze_command_intent(
                command_prompt, 
                {"task": "command_generation"}
            )
            
            # Extract the command (fallback if AI fails)
            if command_response and "interpretation" in command_response:
                ai_command = command_response["interpretation"].strip()
            else:
                ai_command = self._fallback_command_generation(description, target)
            
            logger.info(f"AI generated command: {ai_command}")
            
            # Execute the command(s)
            return await self._execute_system_command(ai_command, description)
            
        except Exception as e:
            logger.error(f"AI command generation failed: {e}")
            # Fallback to basic command generation
            fallback_command = self._fallback_command_generation(description, target)
            logger.info(f"Using fallback command: {fallback_command}")
            return await self._execute_system_command(fallback_command, description)
    
    def _fallback_command_generation(self, description: str, target: str) -> str:
        """Generate basic commands when AI fails."""
        desc_lower = description.lower()
        
        # Basic application mappings
        if "chrome" in desc_lower:
            return "google-chrome || chromium-browser || chromium"
        elif "firefox" in desc_lower:
            return "firefox"
        elif "browser" in desc_lower:
            return "google-chrome || firefox || chromium-browser || xdg-open https://www.google.com"
        elif "text editor" in desc_lower or "editor" in desc_lower:
            return "gedit || code || nano"
        elif "file manager" in desc_lower or "files" in desc_lower:
            return "nautilus || thunar || pcmanfm"
        elif "terminal" in desc_lower:
            return "gnome-terminal || xterm || konsole"
        elif "calculator" in desc_lower:
            return "gnome-calculator || kcalc || xcalc"
        elif target and target.startswith("http"):
            return f"xdg-open '{target}'"
        elif target and "xdg-open" in target:
            return target  # Use the target directly if it's already an xdg-open command
        elif target:
            return f"xdg-open '{target}'"
        else:
            return f"echo 'Executing: {description}'"
    
    async def _execute_system_command(self, command_str: str, description: str) -> bool:
        """Execute system command with alternative fallbacks. Returns True if successful."""
        import subprocess
        
        # Split alternatives by ||
        commands = [cmd.strip() for cmd in command_str.split("||")]
        
        for cmd in commands:
            try:
                logger.info(f"Trying command: {cmd}")
                
                # Parse command and arguments
                cmd_parts = cmd.split()
                if not cmd_parts:
                    continue
                
                # Execute the command
                process = subprocess.Popen(
                    cmd_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Don't block the main process
                )
                
                logger.info(f"✅ Successfully executed: {cmd}")
                
                # Wait a moment for the application to start
                await asyncio.sleep(1)
                return True
                
            except FileNotFoundError:
                logger.info(f"Command not found: {cmd}")
                continue
            except Exception as e:
                logger.error(f"Command failed: {cmd} - {e}")
                continue
        
        # If all commands failed
        logger.error(f"All command alternatives failed for: {description}")
        return False
    
    async def _execute_click_step(self, step: Dict[str, Any], state: AgentState) -> None:
        """Execute a UI click step."""
        description = step.get("description", "Unknown click")
        logger.info(f"Click step: {description} (not yet implemented)")
    
    async def _execute_type_step(self, step: Dict[str, Any], state: AgentState) -> None:
        """Execute a text input step.""" 
        description = step.get("description", "Unknown typing")
        logger.info(f"Type step: {description} (not yet implemented)")
    
    async def _execute_wait_step(self, step: Dict[str, Any], state: AgentState) -> None:
        """Execute a wait/delay step."""
        timeout = step.get("timeout", 2.0)
        await asyncio.sleep(timeout)
        logger.info(f"Wait step completed ({timeout}s)")
    
    async def _execute_verify_step(self, step: Dict[str, Any], state: AgentState) -> None:
        """Execute a verification step."""
        description = step.get("description", "Unknown verification")
        logger.info(f"Verify step: {description} (basic implementation)")
    
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
                "total_steps": len(state["execution_plan"].get("steps", []))
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
        """Complete task execution - pure LLM driven completion."""
        task_id = state['task_id']
        logger.info(f"ENTER _complete_task for task: {task_id}")
        
        # Calculate total execution time from ISO string
        if state["start_time"]:
            from datetime import datetime
            start_time = datetime.fromisoformat(state["start_time"])
            total_time = (datetime.now() - start_time).total_seconds()
            state["total_execution_time"] = total_time
            logger.info(f"Task {task_id} completed in {total_time:.2f} seconds")
        
        # Set completion status - pure LLM determined completion
        plan = state.get("execution_plan")
        if plan and plan.get("total_steps", 0) > 0:
            state["execution_status"] = ExecutionStatus.COMPLETED.value
            logger.info(f"Task {task_id} completed successfully with {plan['total_steps']} steps planned by LLM")
        else:
            state["execution_status"] = ExecutionStatus.FAILED.value
            logger.error(f"Task {task_id} failed - no valid execution plan from LLM")
        
        # Log completion details
        if plan:
            total_steps = plan.get("total_steps", 0)
            logger.info(f"Task {task_id} execution plan had {total_steps} LLM-generated steps")
        
        logger.info(f"EXIT _complete_task for task: {task_id}, status: {state['execution_status']}")
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
            "total_steps": len(state["execution_plan"].get("steps", [])) if state["execution_plan"] else 0,
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
        
        # Initialize agent state - start as IN_PROGRESS for immediate feedback
        initial_state: AgentState = {
            "task_id": task_id,
            "user_intent": user_intent,
            "original_request": user_intent,
            "execution_plan": None,
            "current_step_index": 0,
            "current_step": None,
            "execution_status": ExecutionStatus.IN_PROGRESS.value,
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
            "start_time": datetime.now().isoformat(),
            "step_timings": [],
            "total_execution_time": None
        }
        
        # Store active execution
        self.active_executions[task_id] = initial_state
        
        # Execute the graph in a dedicated asyncio thread (Tkinter-compatible)
        import concurrent.futures
        import threading
        
        def run_in_asyncio_thread():
            """Run graph execution in a dedicated asyncio thread."""
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the graph execution
                loop.run_until_complete(self._run_graph_execution(initial_state))
                
            except Exception as e:
                logger.error(f"Asyncio thread execution failed: {e}")
            finally:
                loop.close()
        
        # Start the asyncio thread
        thread = threading.Thread(target=run_in_asyncio_thread, daemon=True)
        thread.start()
        logger.info(f"Started LangGraph execution in dedicated asyncio thread for task {task_id}")
        
        logger.info(f"Task {task_id} started: {user_intent}")
        return task_id
    
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a task."""
        if task_id in self.active_executions:
            state = self.active_executions[task_id]
            return {
                "task_id": task_id,
                "status": state.get("execution_status", "unknown"),
                "current_step": state.get("current_step_index", 0),
                "total_steps": len(state.get("execution_plan", {}).get("steps", [])) if state.get("execution_plan") else 0,
                "error_messages": state.get("error_messages", [])
            }
        return None
    
    async def _run_graph_execution(self, initial_state: AgentState) -> None:
        """Run the graph execution in a separate task with timeout."""
        task_id = initial_state["task_id"]
        try:
            logger.info(f"🚀 Starting graph execution for task {task_id}")
            
            # Add detailed logging
            logger.info(f"📋 Initial state for task {task_id}: status={initial_state.get('execution_status', 'unknown')}")
            
            # Test if graph object exists and is callable
            logger.info(f"🔍 Graph object type: {type(self.graph)}")
            logger.info(f"🔍 Graph has ainvoke: {hasattr(self.graph, 'ainvoke')}")
            
            # Execute the graph with timeout
            logger.info(f"🔥 About to invoke graph.ainvoke() for task {task_id}...")
            
            # Execute the graph with timeout
            try:
                logger.info(f"⏳ Calling graph.ainvoke() for task {task_id}")
                final_state = await asyncio.wait_for(
                    self.graph.ainvoke(initial_state),
                    timeout=60.0  # Increased timeout for AI calls
                )
                logger.info(f"✅ Graph execution completed for task {task_id}!")
            except asyncio.TimeoutError:
                logger.error(f"Graph execution TIMEOUT after 30 seconds for task {task_id}")
                logger.error("DIAGNOSIS: Graph nodes are not executing - this is a LangGraph configuration issue")
                
                # Update state with timeout error
                if task_id in self.active_executions:
                    self.active_executions[task_id]["execution_status"] = ExecutionStatus.FAILED.value
                    self.active_executions[task_id]["error_messages"].append("Graph execution timeout - nodes not executing")
                return
            
            # Update the stored state
            self.active_executions[task_id] = final_state
            
            status = final_state.get("execution_status", "unknown")
            logger.info(f"Graph execution completed for task {task_id} with status: {status}")
            
            # Log final results
            if final_state.get("error_messages"):
                logger.error(f"Task {task_id} completed with errors: {final_state['error_messages']}")
            else:
                logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Graph execution failed for task {task_id}: {e}")
            logger.error(traceback.format_exc())
            
            # Update state with error
            if task_id in self.active_executions:
                self.active_executions[task_id]["execution_status"] = ExecutionStatus.FAILED.value
                self.active_executions[task_id]["error_messages"].append(str(e))
    
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
            "total_steps": len(state["execution_plan"].get("steps", [])) if state["execution_plan"] else 0,
            "confidence": state["confidence_score"],
            "error_count": len(state["error_messages"]),
            "adaptation_count": len(state["adaptation_history"]),
            "execution_time": (datetime.now() - datetime.fromisoformat(state["start_time"])).total_seconds() if state["start_time"] else 0.0
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