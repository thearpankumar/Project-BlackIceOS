"""
Decision Agent - Workflow Routing and Task Completion Assessment
Analyzes verification results and decides whether to continue, complete, or handle errors.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

from ...backend.models.ai_models import AIModels
from ..orchestrator.multi_agent_state import StateManager, TaskStatus, MultiAgentState

logger = logging.getLogger(__name__)


class WorkflowDecision(Enum):
    """Possible workflow decisions."""
    CONTINUE = "continue"           # Continue with next command
    TASK_COMPLETE = "complete"      # Task successfully completed
    TASK_FAILED = "failed"          # Task failed and should stop
    RECOVERY_NEEDED = "recovery"    # Error recovery required
    USER_INPUT_REQUIRED = "user_input"  # Need user intervention


class DecisionResult:
    """Result of decision analysis."""
    
    def __init__(
        self,
        decision: WorkflowDecision,
        reasoning: str,
        confidence: float,
        completion_assessment: Optional[str] = None,
        error_analysis: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        user_guidance: Optional[str] = None
    ):
        self.decision = decision
        self.reasoning = reasoning
        self.confidence = confidence
        self.completion_assessment = completion_assessment
        self.error_analysis = error_analysis
        self.recovery_suggestions = recovery_suggestions or []
        self.user_guidance = user_guidance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "completion_assessment": self.completion_assessment,
            "error_analysis": self.error_analysis,
            "recovery_suggestions": self.recovery_suggestions,
            "user_guidance": self.user_guidance
        }


class DecisionAgent:
    """
    Decision Agent - Makes workflow routing decisions based on verification results.
    
    Core responsibilities:
    - Analyze verification results and current state
    - Determine if user's original intent has been fulfilled
    - Decide whether to continue, complete, or handle errors
    - Provide clear reasoning for decisions
    - Route workflow to appropriate next step
    """
    
    def __init__(self, ai_models: AIModels, state_manager: StateManager):
        self.ai_models = ai_models
        self.state_manager = state_manager
        self.agent_name = "Decision"
    
    async def make_workflow_decision(self, task_id: str) -> DecisionResult:
        """
        Analyze current state and make workflow routing decision.
        """
        try:
            logger.info(f"Making workflow decision for task {task_id}")
            
            # Get current state and context
            state = await self.state_manager.get_state(task_id)
            if not state:
                logger.error(f"No state found for task {task_id}")
                return self._create_failed_decision("No task state available")
            
            context = self.state_manager.get_task_context_for_agent(task_id)
            
            # Check for maximum attempts reached
            if state["attempt_count"] >= state["max_attempts"]:
                return self._create_failed_decision(
                    f"Maximum attempts ({state['max_attempts']}) reached without completion"
                )
            
            # Analyze current situation with AI
            decision_result = await self._analyze_and_decide(state, context)
            
            # Update state with decision
            await self.state_manager.update_state(task_id, {
                "decision_reasoning": decision_result.reasoning,
                "status": self._map_decision_to_status(decision_result.decision)
            })
            
            # Handle specific decision types
            await self._handle_decision_actions(task_id, decision_result)
            
            logger.info(f"Decision made for {task_id}: {decision_result.decision.value}")
            return decision_result
            
        except Exception as e:
            logger.error(f"Decision making failed for task {task_id}: {e}")
            return self._create_failed_decision(f"Decision making error: {e}")
    
    async def _analyze_and_decide(
        self, 
        state: MultiAgentState, 
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Use AI to analyze situation and make workflow decision."""
        
        # Build comprehensive decision prompt
        decision_prompt = self._build_decision_prompt(state, context)
        
        try:
            # Use AI to make decision with timeout
            import google.generativeai as genai
            logger.info(f"🤖 Calling Gemini API for decision making (timeout: {self.ai_models.config.timeout}s)")
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_models.gemini.generate_content,
                    decision_prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=1024
                    )
                ),
                timeout=self.ai_models.config.timeout
            )
            
            logger.info("✅ Gemini API call completed successfully")
            
            # Check if response was blocked by safety filters
            if not response.candidates or response.candidates[0].finish_reason == 2:
                logger.warning("Gemini response blocked by safety filters - using fallback logic")
                return self._create_fallback_decision(state, context)
            
            # Parse AI response
            response_text = response.text.strip() if response.text else ""
            if not response_text:
                logger.error("Empty response from AI")
                return self._create_failed_decision("Empty AI response")
            
            # Handle markdown-wrapped JSON
            if response_text.startswith('```json'):
                # Extract JSON from markdown code block
                start = response_text.find('```json') + 7
                end = response_text.rfind('```')
                if end > start:
                    response_text = response_text[start:end].strip()
                    
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response text: {response_text[:200]}...")
                return self._create_failed_decision(f"JSON parsing error: {e}")
            
            # Validate response
            if not self._validate_decision_response(response_json):
                logger.error("Invalid decision response format")
                return self._create_failed_decision("Invalid AI decision response")
            
            # Create decision result
            decision_result = DecisionResult(
                decision=WorkflowDecision(response_json["decision"]),
                reasoning=response_json["reasoning"],
                confidence=response_json["confidence"],
                completion_assessment=response_json.get("completion_assessment"),
                error_analysis=response_json.get("error_analysis"),
                recovery_suggestions=response_json.get("recovery_suggestions", []),
                user_guidance=response_json.get("user_guidance")
            )
            
            return decision_result
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Gemini API call timed out after {self.ai_models.config.timeout}s")
            return self._create_failed_decision(f"AI decision timeout after {self.ai_models.config.timeout}s")
        except Exception as e:
            logger.error(f"❌ AI decision analysis failed: {e}")
            return self._create_failed_decision(f"AI decision analysis error: {e}")
    
    def _build_decision_prompt(self, state: MultiAgentState, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for AI decision making."""
        
        # Format recent actions with results
        action_summary = "No actions taken yet"
        if state["action_history"]:
            recent_actions = state["action_history"][-3:]  # Last 3 actions
            action_lines = []
            for i, action in enumerate(recent_actions, 1):
                status = "Completed" if action["success"] else "Incomplete"
                action_lines.append(f"  {i}. {status}: {action['command']}")
                action_lines.append(f"     Expected: {action['expected_result']}")
                if action.get("actual_result"):
                    action_lines.append(f"     Actual: {action['actual_result']}")
                if action.get("error_message"):
                    action_lines.append(f"     Issue: {action['error_message']}")
            action_summary = "\n".join(action_lines)
        
        # Format verification result
        verification_info = "No verification available"
        if state.get("verification_result"):
            verify = state["verification_result"]
            status = "Completed" if verify['success'] else "Incomplete"
            verification_info = f"""
Last Check:
  - Status: {status}
  - Result: {verify['actual_result']}
  - Confidence: {verify['confidence']:.2f}
  - Notes: {verify['verification_reasoning']}"""
        
        # Format screen state
        screen_info = "No screen analysis available"
        if context.get("current_screen"):
            screen = context["current_screen"]
            screen_info = f"""
Current Screen:
  - Applications: {screen.get('applications', [])}
  - UI Elements: {len(screen.get('ui_elements', []))}
  - Unexpected Elements: {screen.get('unexpected_elements', [])}
  - Analysis: {screen.get('analysis_summary', 'No summary')}"""
        
        # Format error context
        error_context = ""
        if state["error_messages"]:
            recent_errors = state["error_messages"][-2:]
            error_context = f"\n\nRecent Issues:\n" + "\n".join(f"  - {error}" for error in recent_errors)
        
        prompt = f"""
You are a workflow decision assistant helping with task completion analysis.

USER REQUEST: {state['user_intent']}

CURRENT STATUS:
- Step: {state['current_step']} (Attempt: {state['attempt_count']}/{state['max_attempts']})
- Status: {state['status']}
- Confidence: {state['confidence_score']:.2f}

RECENT ACTIONS:
{action_summary}

{verification_info}

{screen_info}

{error_context}

TASK:
Analyze the situation and determine the next workflow step:

1. COMPLETION CHECK: Has the user request been fulfilled?
   - Compare what was requested vs what has been accomplished
   - Check if the current state shows the desired outcome
   - Consider if partial completion is acceptable

2. ISSUE ANALYSIS: Are there any problems preventing progress?
   - Commands that didn't work as expected
   - Unexpected interface elements
   - Application states that block progress

3. PROGRESS EVALUATION: Is the task moving forward effectively?
   - Are recent actions bringing us closer to the goal?
   - Is the workflow repeating unsuccessful attempts?

NEXT STEP OPTIONS:
- "continue": Keep going - task is progressing well
- "complete": Task successfully finished - user request fulfilled
- "failed": Task cannot proceed - unrecoverable issues
- "recovery": Issue recovery needed - specific problem to address
- "user_input": Need human guidance or clarification

RESPONSE FORMAT (JSON):
{{
    "decision": "continue|complete|failed|recovery|user_input",
    "reasoning": "detailed explanation of decision",
    "confidence": 0.85,
    "completion_assessment": "if complete, explain how well user request was fulfilled",
    "error_analysis": "if recovery needed, describe the specific problem",
    "recovery_suggestions": ["specific", "recovery", "actions"],
    "user_guidance": "if user_input needed, what should user do"
}}

DECISION GUIDELINES:
- COMPLETE: User request clearly fulfilled based on current state
- CONTINUE: Making progress, no blocking issues, within attempt limits
- RECOVERY: Specific recoverable issue preventing progress
- FAILED: Unrecoverable error or too many failed attempts
- USER_INPUT: Ambiguous situation requiring human decision

Make your decision based on the complete analysis:
"""
        
        return prompt
    
    def _validate_decision_response(self, response: Dict[str, Any]) -> bool:
        """Validate decision response format."""
        required_fields = ["decision", "reasoning", "confidence"]
        
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field in decision response: {field}")
                return False
        
        # Validate decision value
        try:
            WorkflowDecision(response["decision"])
        except ValueError:
            logger.error(f"Invalid decision value: {response['decision']}")
            return False
        
        # Validate confidence
        confidence = response["confidence"]
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            logger.error(f"Invalid confidence value: {confidence}")
            return False
        
        return True
    
    def _create_failed_decision(self, reason: str) -> DecisionResult:
        """Create a failed decision result."""
        return DecisionResult(
            decision=WorkflowDecision.TASK_FAILED,
            reasoning=reason,
            confidence=1.0,
            error_analysis=reason
        )
    
    def _create_fallback_decision(self, state: MultiAgentState, context: Dict[str, Any]) -> DecisionResult:
        """Create fallback decision when AI is blocked by safety filters."""
        
        # Simple rule-based logic when AI is unavailable
        recent_actions = state.get("action_history", [])
        last_verification = state.get("verification_result", {})
        
        # If no actions taken yet, continue
        if not recent_actions:
            return DecisionResult(
                decision=WorkflowDecision.CONTINUE,
                reasoning="Starting task execution - no actions taken yet",
                confidence=0.8
            )
        
        # Get last action
        last_action = recent_actions[-1] if recent_actions else {}
        
        # If last action succeeded and it was a browser launch, continue to navigate
        if (last_action.get("success", False) and 
            "chrome" in last_action.get("command", "").lower()):
            return DecisionResult(
                decision=WorkflowDecision.CONTINUE,
                reasoning="Browser launched successfully - ready for next action",
                confidence=0.7
            )
        
        # If last action failed and we haven't tried too many times
        attempt_count = state.get("attempt_count", 0)
        max_attempts = state.get("max_attempts", 5)
        
        if not last_action.get("success", False) and attempt_count < max_attempts:
            return DecisionResult(
                decision=WorkflowDecision.RECOVERY_NEEDED,
                reasoning="Previous action incomplete - attempting recovery",
                confidence=0.6,
                error_analysis="Action did not complete successfully",
                recovery_suggestions=["Try alternative approach", "Verify system state"]
            )
        
        # If we've tried many times, complete with whatever we have
        if attempt_count >= max_attempts:
            return DecisionResult(
                decision=WorkflowDecision.TASK_COMPLETE,
                reasoning="Maximum attempts reached - completing current state",
                confidence=0.5,
                completion_assessment="Task attempted multiple times - best effort completion"
            )
        
        # Default to continue
        return DecisionResult(
            decision=WorkflowDecision.CONTINUE,
            reasoning="Continuing with next action",
            confidence=0.6
        )
    
    def _map_decision_to_status(self, decision: WorkflowDecision) -> str:
        """Map workflow decision to task status."""
        mapping = {
            WorkflowDecision.CONTINUE: TaskStatus.IN_PROGRESS.value,
            WorkflowDecision.TASK_COMPLETE: TaskStatus.COMPLETED.value,
            WorkflowDecision.TASK_FAILED: TaskStatus.FAILED.value,
            WorkflowDecision.RECOVERY_NEEDED: TaskStatus.IN_PROGRESS.value,
            WorkflowDecision.USER_INPUT_REQUIRED: TaskStatus.REQUIRES_USER_INPUT.value
        }
        return mapping.get(decision, TaskStatus.IN_PROGRESS.value)
    
    async def _handle_decision_actions(self, task_id: str, decision: DecisionResult) -> None:
        """Handle specific actions based on decision type."""
        
        if decision.decision == WorkflowDecision.TASK_COMPLETE:
            # Calculate completion metrics
            state = await self.state_manager.get_state(task_id)
            if state:
                start_time = datetime.fromisoformat(state["start_time"])
                total_time = (datetime.now() - start_time).total_seconds()
                
                await self.state_manager.update_state(task_id, {
                    "total_execution_time": total_time,
                    "completion_reason": decision.completion_assessment or "Task completed",
                    "should_continue": False
                })
                
                logger.info(f"Task {task_id} completed successfully in {total_time:.2f} seconds")
        
        elif decision.decision == WorkflowDecision.TASK_FAILED:
            await self.state_manager.update_state(task_id, {
                "completion_reason": decision.error_analysis or "Task failed",
                "should_continue": False
            })
            
            logger.warning(f"Task {task_id} marked as failed: {decision.reasoning}")
        
        elif decision.decision == WorkflowDecision.RECOVERY_NEEDED:
            # Increment error recovery attempts
            state = await self.state_manager.get_state(task_id)
            if state:
                await self.state_manager.update_state(task_id, {
                    "error_recovery_attempts": state["error_recovery_attempts"] + 1
                })
            
            logger.info(f"Recovery needed for task {task_id}: {decision.error_analysis}")
        
        elif decision.decision == WorkflowDecision.USER_INPUT_REQUIRED:
            logger.info(f"User input required for task {task_id}: {decision.user_guidance}")
    
    async def assess_task_completion_quality(self, task_id: str) -> Dict[str, Any]:
        """
        Assess how well the completed task fulfilled the user's original intent.
        """
        try:
            state = await self.state_manager.get_state(task_id)
            if not state:
                return {"quality_score": 0.0, "assessment": "No task state available"}
            
            # Build assessment prompt
            assessment_prompt = f"""
Assess how well this completed task fulfilled the user's original intent.

ORIGINAL REQUEST: {state['user_intent']}
TOTAL STEPS TAKEN: {state['current_step']}
FINAL STATUS: {state['status']}

EXECUTION SUMMARY:
{self.state_manager.get_action_history_summary(task_id)}

Rate the completion quality and provide assessment:
{{
    "quality_score": 0.85,  // 0.0-1.0 how well intent was fulfilled
    "assessment": "detailed assessment of completion quality",
    "strengths": ["what", "went", "well"],
    "areas_for_improvement": ["what", "could", "be", "better"],
    "user_satisfaction_prediction": "likely user reaction"
}}
"""
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_models.gemini.generate_content,
                    assessment_prompt
                ),
                timeout=self.ai_models.config.timeout
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Task completion assessment failed: {e}")
            return {
                "quality_score": 0.0,
                "assessment": f"Assessment failed: {e}",
                "strengths": [],
                "areas_for_improvement": ["Assessment system error"],
                "user_satisfaction_prediction": "Unknown due to assessment error"
            }