"""
Recursive Multi-Agent Workflow System
Coordinates Commander, Verification, and Decision agents in an intelligent recursive loop.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from ...backend.models.ai_models import AIModels
from ...backend.core.mcp_executor import MCPExecutor
from .multi_agent_state import StateManager, MultiAgentState, ActionRecord, ActionType, TaskStatus
from ..specialized.commander_agent import CommanderAgent, CommandDecision
from ..specialized.verification_agent import VerificationAgent, VerificationResult
from ..specialized.decision_agent import DecisionAgent, DecisionResult, WorkflowDecision

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Final result of workflow execution."""
    task_id: str
    success: bool
    final_status: TaskStatus
    total_steps: int
    execution_time: float
    completion_reason: str
    quality_assessment: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None


class RecursiveWorkflowOrchestrator:
    """
    Recursive Multi-Agent Workflow Orchestrator.
    
    Coordinates the three specialized agents:
    1. Commander: Generates next command based on context
    2. Verification: Analyzes screen state after command execution
    3. Decision: Determines workflow routing (continue/complete/fail/recover)
    
    Workflow Loop:
    User Intent → Commander → Execute → Verify → Decision → [Loop or Complete]
    """
    
    def __init__(self, ai_models: AIModels, mcp_executor: MCPExecutor):
        self.ai_models = ai_models
        self.mcp_executor = mcp_executor
        self.state_manager = StateManager()
        
        # Initialize specialized agents
        self.commander = CommanderAgent(ai_models, self.state_manager)
        self.verifier = VerificationAgent(self.state_manager)  # No AI models needed
        self.decider = DecisionAgent(ai_models, self.state_manager)
        
        # Build LangGraph workflow
        self.graph = self._build_recursive_workflow()
        
        # Performance tracking
        self.workflow_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_steps": 0.0,
            "average_execution_time": 0.0
        }
    
    def _build_recursive_workflow(self):
        """Build the recursive multi-agent workflow using LangGraph."""
        
        # Define the workflow state
        workflow = StateGraph(MultiAgentState)
        
        # Add workflow nodes
        workflow.add_node("initialize_task", self._initialize_task)
        workflow.add_node("generate_command", self._generate_command)
        workflow.add_node("execute_command", self._execute_command) 
        workflow.add_node("verify_execution", self._verify_execution)
        workflow.add_node("make_decision", self._make_decision)
        workflow.add_node("handle_recovery", self._handle_recovery)
        workflow.add_node("complete_task", self._complete_task)
        workflow.add_node("fail_task", self._fail_task)
        
        # Set entry point
        workflow.set_entry_point("initialize_task")
        
        # Define workflow edges with conditional routing
        workflow.add_edge("initialize_task", "generate_command")
        workflow.add_edge("generate_command", "execute_command")
        workflow.add_edge("execute_command", "verify_execution")
        workflow.add_edge("verify_execution", "make_decision")
        
        # Conditional routing from decision node
        workflow.add_conditional_edges(
            "make_decision",
            self._route_decision,
            {
                "continue": "generate_command",      # Loop back for next command
                "complete": "complete_task",         # Task successful
                "failed": "fail_task",               # Task failed
                "recovery": "handle_recovery",       # Error recovery
                "user_input": "fail_task"            # Need user input (treat as pause)
            }
        )
        
        # Recovery can either continue or fail
        workflow.add_conditional_edges(
            "handle_recovery", 
            self._route_recovery,
            {
                "continue": "generate_command",      # Retry after recovery
                "failed": "fail_task"                # Recovery failed
            }
        )
        
        # Terminal nodes
        workflow.add_edge("complete_task", END)
        workflow.add_edge("fail_task", END)
        
        # Add memory for state persistence
        memory = MemorySaver()
        compiled_workflow = workflow.compile(checkpointer=memory)
        
        logger.info("Built recursive multi-agent workflow with LangGraph")
        return compiled_workflow
    
    # =========================================================================
    # Workflow Node Functions
    # =========================================================================
    
    async def _initialize_task(self, state: MultiAgentState) -> MultiAgentState:
        """Initialize task and set up initial state."""
        task_id = state["task_id"]
        logger.info(f"🚀 Initializing recursive workflow for task {task_id}")
        
        # Set initial status
        state["status"] = TaskStatus.IN_PROGRESS.value
        state["current_step"] = 0
        state["attempt_count"] = 0
        state["should_continue"] = True
        
        logger.info(f"✅ Task {task_id} initialized for recursive execution")
        return state
    
    async def _generate_command(self, state: MultiAgentState) -> MultiAgentState:
        """Use Commander Agent to generate next command."""
        task_id = state["task_id"]
        logger.info(f"🧠 Commander generating next command for task {task_id}")
        
        try:
            logger.info(f"🔍 About to call commander.generate_next_command for {task_id}")
            # Get command from Commander Agent
            command_decision = await self.commander.generate_next_command(task_id)
            logger.info(f"✅ Commander.generate_next_command completed for {task_id}")
            
            if command_decision is None:
                # Commander failed to generate command (AI timeout/error) or thinks task is complete
                logger.warning(f"⚠️ Commander returned None for task {task_id}")
                
                # Increment error recovery attempts
                state["error_recovery_attempts"] += 1
                
                # If we've tried too many times, fail the task
                if state["error_recovery_attempts"] >= 3:
                    state["should_continue"] = False
                    state["completion_reason"] = "Commander agent failed repeatedly - AI may be unavailable"
                    state["status"] = TaskStatus.FAILED.value
                    logger.error(f"❌ Task {task_id} failed - Commander unable to generate commands after 3 attempts")
                else:
                    # Try again after brief delay
                    logger.info(f"🔄 Retrying command generation for task {task_id} (attempt {state['error_recovery_attempts']}/3)")
                    state["error_messages"].append(f"Commander retry attempt {state['error_recovery_attempts']}/3")
                    await asyncio.sleep(2)  # Brief delay before retry
            else:
                # Reset error recovery attempts on success
                state["error_recovery_attempts"] = 0
                # Store command decision in state
                state["commander_last_decision"] = command_decision.to_dict()
                logger.info(f"💡 Commander generated: {command_decision.command}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Command generation failed for {task_id}: {e}")
            state["error_messages"].append(f"Command generation exception: {e}")
            state["error_recovery_attempts"] += 1
            
            if state["error_recovery_attempts"] >= 3:
                state["should_continue"] = False
                state["completion_reason"] = f"Command generation failed repeatedly: {e}"
                state["status"] = TaskStatus.FAILED.value
            
            return state
    
    async def _execute_command(self, state: MultiAgentState) -> MultiAgentState:
        """Execute the command generated by Commander."""
        task_id = state["task_id"]
        
        # Check if we have a command to execute
        if not state.get("commander_last_decision"):
            logger.warning(f"⚠️ No command to execute for task {task_id}")
            state["error_messages"].append("No command generated")
            return state
        
        command_info = state["commander_last_decision"]
        command = command_info["command"]
        
        logger.info(f"⚡ Executing command for task {task_id}: {command}")
        
        # Skip screenshot capture - not implemented in verification agent
        pre_execution_screenshot = None
        
        # Create action record
        action_record = ActionRecord(
            action_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            action_type=ActionType(command_info["action_type"]),
            command=command,
            expected_result=command_info["expected_result"],
            screenshot_before=pre_execution_screenshot,
            agent_reasoning=command_info["reasoning"]
        )
        
        # Execute the command based on action type
        execution_success = False
        error_message = None
        
        try:
            # Get action type from command info
            action_type = command_info.get("action_type", "command")
            
            if action_type == "command":
                # Execute system command
                execution_success = await self._execute_system_command(command)
            elif action_type == "terminal":
                # Execute terminal command
                execution_success = await self._execute_terminal_command(command)
            elif action_type == "web_navigate":
                # Execute web navigation
                execution_success = await self._execute_web_navigation(command)
            elif action_type == "web_analyze":
                # Execute web page analysis
                execution_success = await self._execute_web_analysis(command)
            elif action_type == "type":
                # Execute typing action
                execution_success = await self._execute_typing_action(command)
            elif action_type == "click":
                # Execute click action
                execution_success = await self._execute_click_action(command)
            elif action_type == "wait":
                # Execute wait action
                execution_success = await self._execute_wait_action(command)
            else:
                # Default to system command
                execution_success = await self._execute_system_command(command)
            
            action_record.success = execution_success
            
            if execution_success:
                action_record.actual_result = f"{action_type.title()} '{command}' executed successfully"
                logger.info(f"✅ {action_type.title()} executed successfully: {command}")
            else:
                error_message = f"{action_type.title()} execution failed: {command}"
                action_record.error_message = error_message
                logger.warning(f"❌ {action_type.title()} execution failed: {command}")
                
        except Exception as e:
            error_message = f"{action_type.title()} execution error: {e}"
            action_record.error_message = error_message
            action_record.success = False
            logger.error(f"❌ {action_type.title()} execution exception for {task_id}: {e}")
        
        # Add action to history
        await self.state_manager.add_action_record(task_id, action_record)
        
        # Update state
        if error_message:
            state["error_messages"].append(error_message)
        
        return state
    
    async def _verify_execution(self, state: MultiAgentState) -> MultiAgentState:
        """Use Verification Agent to analyze execution results."""
        task_id = state["task_id"]
        
        if not state.get("commander_last_decision"):
            logger.warning(f"⚠️ No command info for verification in task {task_id}")
            return state
            
        command_info = state["commander_last_decision"]
        
        logger.info(f"🔍 Verifying execution for task {task_id}")
        
        try:
            # Get verification from Verification Agent
            verification_result = await self.verifier.verify_command_execution(
                task_id=task_id,
                executed_command=command_info["command"],
                expected_result=command_info["expected_result"]
            )
            
            # Update state with verification
            state["verification_result"] = verification_result.to_dict()
            state["confidence_score"] = verification_result.confidence
            
            if verification_result.success:
                logger.info(f"✅ Verification successful for task {task_id}")
            else:
                logger.warning(f"❌ Verification failed for task {task_id}: {verification_result.actual_result}")
                
            return state
            
        except Exception as e:
            logger.error(f"❌ Verification failed for task {task_id}: {e}")
            state["error_messages"].append(f"Verification failed: {e}")
            return state
    
    async def _make_decision(self, state: MultiAgentState) -> MultiAgentState:
        """Use Decision Agent to determine next workflow step."""
        task_id = state["task_id"]
        logger.info(f"🤔 Making workflow decision for task {task_id}")
        
        try:
            # Get decision from Decision Agent
            decision_result = await self.decider.make_workflow_decision(task_id)
            
            # Update state with decision
            state["decision_reasoning"] = decision_result.reasoning
            
            # Map decision to workflow control
            if decision_result.decision == WorkflowDecision.TASK_COMPLETE:
                state["should_continue"] = False
                state["completion_reason"] = decision_result.completion_assessment or "Task completed successfully"
            elif decision_result.decision == WorkflowDecision.TASK_FAILED:
                state["should_continue"] = False
                state["completion_reason"] = decision_result.error_analysis or "Task failed"
            
            logger.info(f"🎯 Decision made for task {task_id}: {decision_result.decision.value}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Decision making failed for task {task_id}: {e}")
            state["error_messages"].append(f"Decision making failed: {e}")
            state["should_continue"] = False
            state["completion_reason"] = f"Decision system error: {e}"
            return state
    
    async def _handle_recovery(self, state: MultiAgentState) -> MultiAgentState:
        """Handle error recovery scenarios."""
        task_id = state["task_id"]
        logger.info(f"🔧 Handling recovery for task {task_id}")
        
        # Increment recovery attempts
        state["error_recovery_attempts"] += 1
        
        # Check if too many recovery attempts
        if state["error_recovery_attempts"] > 3:
            state["should_continue"] = False
            state["completion_reason"] = "Too many recovery attempts failed"
            logger.warning(f"❌ Too many recovery attempts for task {task_id}")
            return state
        
        # Let Commander generate recovery command
        logger.info(f"🔄 Attempting recovery #{state['error_recovery_attempts']} for task {task_id}")
        return state
    
    async def _complete_task(self, state: MultiAgentState) -> MultiAgentState:
        """Complete successful task execution."""
        task_id = state["task_id"]
        logger.info(f"🎉 Completing successful task {task_id}")
        
        # Calculate final metrics
        if state["start_time"]:
            start_time = datetime.fromisoformat(state["start_time"])
            total_time = (datetime.now() - start_time).total_seconds()
            state["total_execution_time"] = total_time
        
        # Set final status
        state["status"] = TaskStatus.COMPLETED.value
        
        # Get quality assessment
        try:
            quality_assessment = await self.decider.assess_task_completion_quality(task_id)
            logger.info(f"📊 Task quality score: {quality_assessment.get('quality_score', 0.0):.2f}")
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
        
        # Update stats
        self.workflow_stats["successful_tasks"] += 1
        
        logger.info(f"✅ Task {task_id} completed successfully in {state.get('total_execution_time', 0):.2f}s")
        return state
    
    async def _fail_task(self, state: MultiAgentState) -> MultiAgentState:
        """Handle failed task execution."""
        task_id = state["task_id"]
        logger.info(f"❌ Failing task {task_id}")
        
        # Set final status
        state["status"] = TaskStatus.FAILED.value
        
        # Calculate execution time
        if state["start_time"]:
            start_time = datetime.fromisoformat(state["start_time"])
            total_time = (datetime.now() - start_time).total_seconds()
            state["total_execution_time"] = total_time
        
        # Update stats
        self.workflow_stats["failed_tasks"] += 1
        
        failure_reason = state.get("completion_reason", "Unknown failure")
        logger.warning(f"❌ Task {task_id} failed: {failure_reason}")
        return state
    
    # =========================================================================
    # Routing Functions
    # =========================================================================
    
    def _route_decision(self, state: MultiAgentState) -> str:
        """Route workflow based on decision agent result."""
        
        # First check decision reasoning for direct routing
        decision_reasoning = state.get("decision_reasoning", "").lower()
        
        # Use word boundary matching to prevent "continue" matching "complete"
        import re
        if re.search(r'\bcomplete\b', decision_reasoning):
            return "complete"
        elif re.search(r'\bfailed?\b', decision_reasoning):
            return "failed"
        elif re.search(r'\brecovery\b', decision_reasoning):
            return "recovery"
        elif re.search(r'\buser\s+input\b', decision_reasoning):
            return "user_input"
        
        # Check should_continue flag
        if not state.get("should_continue", True):
            if state.get("status") == TaskStatus.COMPLETED.value:
                return "complete"
            else:
                return "failed"
        
        # Default to continue
        return "continue"
    
    def _route_recovery(self, state: MultiAgentState) -> str:
        """Route after recovery attempt."""
        
        # Check if too many recovery attempts
        if state.get("error_recovery_attempts", 0) > 3:
            return "failed"
        
        # Continue trying
        return "continue"
    
    # =========================================================================
    # Execution Interface
    # =========================================================================
    
    async def execute_task(self, user_intent: str, task_id: Optional[str] = None) -> str:
        """
        Execute a task using the recursive multi-agent workflow.
        
        Args:
            user_intent: User's natural language request
            task_id: Optional task ID, generated if not provided
            
        Returns:
            Task ID for tracking
        """
        # Create initial state
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Initialize task state
        task_id = self.state_manager.create_initial_state(user_intent, task_id)
        
        logger.info(f"🚀 Starting recursive workflow execution for task {task_id}")
        
        # Execute workflow in background
        asyncio.create_task(self._run_workflow_execution(task_id))
        
        return task_id
    
    async def _run_workflow_execution(self, task_id: str) -> WorkflowResult:
        """Run the complete workflow execution."""
        try:
            # Get initial state from state manager
            initial_state_data = await self.state_manager.get_state(task_id)
            if not initial_state_data:
                logger.error(f"No initial state found for task {task_id}")
                raise ValueError(f"No initial state found for task {task_id}")
            
            logger.info(f"🔍 Retrieved initial state for task {task_id}: status={initial_state_data.get('status')}")
            
            # Convert to LangGraph state format
            initial_langgraph_state: MultiAgentState = {
                "task_id": task_id,
                "user_intent": initial_state_data["user_intent"],
                "original_request": initial_state_data["original_request"],
                "start_time": initial_state_data["start_time"],
                
                "status": initial_state_data["status"],
                "current_step": initial_state_data["current_step"],
                "max_attempts": initial_state_data["max_attempts"],
                "attempt_count": initial_state_data["attempt_count"],
                
                "action_history": initial_state_data["action_history"],
                "current_screen_state": initial_state_data["current_screen_state"],
                "previous_screen_state": initial_state_data["previous_screen_state"],
                
                "commander_last_decision": initial_state_data["commander_last_decision"],
                "verification_result": initial_state_data["verification_result"],
                "decision_reasoning": initial_state_data["decision_reasoning"],
                
                "execution_context": initial_state_data["execution_context"],
                "learned_patterns": initial_state_data["learned_patterns"],
                "error_recovery_attempts": initial_state_data["error_recovery_attempts"],
                
                "total_execution_time": initial_state_data["total_execution_time"],
                "step_timings": initial_state_data["step_timings"],
                "error_messages": initial_state_data["error_messages"],
                
                "should_continue": initial_state_data["should_continue"],
                "completion_reason": initial_state_data.get("completion_reason"),
                "confidence_score": initial_state_data["confidence_score"]
            }
            
            # Execute the workflow graph
            logger.info(f"🎬 Executing workflow graph for task {task_id}")
            
            final_state = await self.graph.ainvoke(
                initial_langgraph_state,
                config={"configurable": {"thread_id": task_id}}
            )
            
            # Create workflow result
            result = WorkflowResult(
                task_id=task_id,
                success=(final_state["status"] == TaskStatus.COMPLETED.value),
                final_status=TaskStatus(final_state["status"]),
                total_steps=final_state["current_step"],
                execution_time=final_state.get("total_execution_time", 0.0),
                completion_reason=final_state.get("completion_reason", "Unknown"),
                error_details="; ".join(final_state.get("error_messages", []))
            )
            
            # Update workflow stats
            self.workflow_stats["total_tasks"] += 1
            
            logger.info(f"🏁 Workflow execution completed for task {task_id}: {'SUCCESS' if result.success else 'FAILED'}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed for task {task_id}: {e}")
            
            return WorkflowResult(
                task_id=task_id,
                success=False,
                final_status=TaskStatus.FAILED,
                total_steps=0,
                execution_time=0.0,
                completion_reason=f"Workflow execution error: {e}",
                error_details=str(e)
            )
    
    async def _execute_system_command(self, command: str) -> bool:
        """Execute system command using subprocess."""
        import subprocess
        
        try:
            # Split alternatives by ||
            commands = [cmd.strip() for cmd in command.split("||")]
            
            for cmd in commands:
                try:
                    logger.debug(f"Trying command: {cmd}")
                    
                    # Parse command and arguments
                    cmd_parts = cmd.split()
                    if not cmd_parts:
                        continue
                    
                    # Execute the command
                    process = subprocess.Popen(
                        cmd_parts,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True
                    )
                    
                    logger.info(f"✅ Successfully executed: {cmd}")
                    
                    # Wait a moment for the application to start
                    await asyncio.sleep(2)
                    return True
                    
                except FileNotFoundError:
                    logger.debug(f"Command not found: {cmd}")
                    continue
                except Exception as e:
                    logger.debug(f"Command failed: {cmd} - {e}")
                    continue
            
            # All commands failed
            logger.error(f"All command alternatives failed for: {command}")
            return False
            
        except Exception as e:
            logger.error(f"System command execution error: {e}")
            return False
    
    async def _execute_typing_action(self, text: str) -> bool:
        """Execute typing action using UI interaction tools."""
        try:
            from ...mcp_server.tools.ui_interaction_tools import UIInteractionTools
            
            ui_tools = UIInteractionTools()
            
            # Focus address bar with Ctrl+L first
            await ui_tools.send_key('ctrl+l')
            await asyncio.sleep(0.5)
            
            # Type the URL/text
            result = await ui_tools.type_text(text, clear_first=True)
            await asyncio.sleep(0.5)
            
            # Press Enter to navigate
            await ui_tools.send_key('enter')
            await asyncio.sleep(2)  # Wait for page to load
            
            logger.info(f"✅ Typed text successfully: {text}")
            return True
            
        except Exception as e:
            logger.error(f"Typing action failed: {e}")
            return False
    
    async def _execute_click_action(self, target: str) -> bool:
        """Execute click action using web element detection or UI tools."""
        try:
            # Try web element detection first
            if hasattr(self, '_web_detector') and hasattr(self, '_last_web_analysis'):
                return await self._execute_web_click(target)
            
            # Fallback to UI interaction tools
            from ...mcp_server.tools.ui_interaction_tools import UIInteractionTools
            
            ui_tools = UIInteractionTools()
            result = await ui_tools.click_element(element_description=target)
            
            logger.info(f"✅ Click action attempted: {target}")
            return "Successfully" in result
            
        except Exception as e:
            logger.error(f"Click action failed: {e}")
            return False
    
    async def _execute_web_click(self, target: str) -> bool:
        """Execute click using web element detection results."""
        try:
            # Find relevant elements from last analysis
            target_elements = []
            
            # Check all stored analyses
            for analysis_key, analysis in self._last_web_analysis.items():
                if target.lower() in analysis_key.lower() or 'video' in target.lower():
                    # Filter elements by type based on target
                    if 'video' in target.lower():
                        target_elements = [e for e in analysis.elements if e.element_type == 'video' and e.clickable]
                    elif 'button' in target.lower():
                        target_elements = [e for e in analysis.elements if e.element_type == 'button' and e.clickable]
                    else:
                        # Get all clickable elements
                        target_elements = [e for e in analysis.elements if e.clickable]
                    break
            
            if not target_elements:
                logger.warning(f"No clickable elements found for target: {target}")
                return False
            
            # Pick the first/best element (they're already sorted by confidence)
            best_element = target_elements[0]
            
            # Calculate center coordinates
            x = best_element.bounding_box['x'] + best_element.bounding_box['width'] / 2
            y = best_element.bounding_box['y'] + best_element.bounding_box['height'] / 2
            
            # Click using web detector
            success = await self._web_detector.click_element_by_coordinates(x, y)
            
            if success:
                logger.info(f"✅ Web click successful on {best_element.element_type}: {best_element.inner_text[:50]}")
                return True
            else:
                logger.warning(f"❌ Web click failed on element")
                return False
                
        except Exception as e:
            logger.error(f"Web click execution error: {e}")
            return False
    
    async def _execute_wait_action(self, duration_str: str) -> bool:
        """Execute wait/pause action."""
        try:
            # Parse duration (default to 2 seconds if not specified)
            try:
                duration = float(duration_str)
            except (ValueError, TypeError):
                duration = 2.0
            
            logger.info(f"⏱️ Waiting for {duration} seconds...")
            await asyncio.sleep(duration)
            
            return True
            
        except Exception as e:
            logger.error(f"Wait action failed: {e}")
            return False
    
    async def _execute_terminal_command(self, command: str) -> bool:
        """Execute terminal command using InteractiveTerminal."""
        try:
            from ...mcp_server.tools.interactive_terminal import InteractiveTerminal
            
            # Initialize terminal if not exists
            if not hasattr(self, '_terminal'):
                self._terminal = InteractiveTerminal()
            
            # Execute command
            result = await self._terminal.execute_command(command, timeout=60)
            
            if result.success:
                logger.info(f"✅ Terminal command executed: {command}")
                logger.info(f"Output: {result.stdout[:200]}...")
                return True
            else:
                logger.warning(f"❌ Terminal command failed: {command}")
                logger.warning(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Terminal command execution error: {e}")
            return False
    
    async def _execute_web_navigation(self, url: str) -> bool:
        """Execute web navigation using WebElementDetector."""
        try:
            from ...mcp_server.tools.web_element_detector import WebElementDetector
            
            # Initialize web detector if not exists
            if not hasattr(self, '_web_detector'):
                self._web_detector = WebElementDetector()
            
            # Navigate to URL
            success = await self._web_detector.navigate_to_url(url)
            
            if success:
                logger.info(f"✅ Web navigation successful: {url}")
                return True
            else:
                logger.warning(f"❌ Web navigation failed: {url}")
                return False
                
        except Exception as e:
            logger.error(f"Web navigation error: {e}")
            return False
    
    async def _execute_web_analysis(self, target: str) -> bool:
        """Execute web page analysis to find elements."""
        try:
            from ...mcp_server.tools.web_element_detector import WebElementDetector
            
            # Initialize web detector if not exists
            if not hasattr(self, '_web_detector'):
                self._web_detector = WebElementDetector()
            
            # Analyze current page
            analysis = await self._web_detector.analyze_current_page()
            
            if analysis:
                logger.info(f"✅ Web analysis complete: {analysis.clickable_elements} clickable elements found")
                
                # Store analysis results for potential clicking
                if not hasattr(self, '_last_web_analysis'):
                    self._last_web_analysis = {}
                self._last_web_analysis[target] = analysis
                
                return True
            else:
                logger.warning("❌ Web analysis failed")
                return False
                
        except Exception as e:
            logger.error(f"Web analysis error: {e}")
            return False
    
    # =========================================================================
    # Status and Monitoring
    # =========================================================================
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status."""
        state = await self.state_manager.get_state(task_id)
        if not state:
            return None
        
        return {
            "task_id": task_id,
            "status": state["status"],
            "current_step": state["current_step"],
            "attempt_count": state["attempt_count"],
            "confidence_score": state["confidence_score"],
            "error_count": len(state["error_messages"]),
            "should_continue": state["should_continue"],
            "completion_reason": state.get("completion_reason")
        }
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        return self.workflow_stats.copy()