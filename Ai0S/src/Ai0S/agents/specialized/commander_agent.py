"""
Commander Agent - Intelligent Single-Step Command Generation
Generates the next logical command based on user intent, execution history, and current state.
"""

import json
import logging
from typing import Dict, List, Optional, Any
import asyncio

from ...backend.models.ai_models import AIModels
from ..orchestrator.multi_agent_state import StateManager, MultiAgentState, ActionRecord, ActionType

logger = logging.getLogger(__name__)


class CommandDecision:
    """Represents a command decision from the Commander Agent."""
    
    def __init__(
        self,
        command: str,
        action_type: ActionType,
        reasoning: str,
        expected_result: str,
        confidence: float,
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.command = command
        self.action_type = action_type
        self.reasoning = reasoning
        self.expected_result = expected_result
        self.confidence = confidence
        self.parameters = parameters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "command": self.command,
            "action_type": self.action_type.value,
            "reasoning": self.reasoning,
            "expected_result": self.expected_result,
            "confidence": self.confidence,
            "parameters": self.parameters
        }


class CommanderAgent:
    """
    Commander Agent - Generates intelligent single-step commands.
    
    Core responsibility:
    - Analyze current situation (user intent + history + screen state)
    - Generate the ONE next logical command to execute
    - Provide clear expected results for verification
    - Adapt strategy based on previous action results
    """
    
    def __init__(self, ai_models: AIModels, state_manager: StateManager):
        self.ai_models = ai_models
        self.state_manager = state_manager
        self.agent_name = "Commander"
    
    async def generate_next_command(self, task_id: str) -> Optional[CommandDecision]:
        """
        Generate the next single command to execute based on complete context.
        
        Returns None if task should be completed or failed.
        """
        try:
            # Get current state and context
            state = await self.state_manager.get_state(task_id)
            if not state:
                logger.error(f"No state found for task {task_id}")
                return None
            
            context = self.state_manager.get_task_context_for_agent(task_id)
            
            # Check if we should continue
            if not self.state_manager.should_continue_execution(task_id):
                logger.info(f"Task {task_id} should not continue execution")
                return None
            
            # Increment attempt count
            await self.state_manager.update_state(task_id, {
                "attempt_count": state["attempt_count"] + 1
            })
            
            # Generate command using AI
            command_decision = await self._analyze_and_generate_command(state, context)
            
            # Update state with commander decision
            await self.state_manager.update_state(task_id, {
                "commander_last_decision": command_decision.to_dict() if command_decision else None
            })
            
            if command_decision:
                logger.info(f"Commander generated command for {task_id}: {command_decision.command}")
            else:
                logger.info(f"Commander decided no more commands needed for {task_id}")
            
            return command_decision
            
        except Exception as e:
            logger.error(f"Commander agent failed for task {task_id}: {e}")
            return None
    
    async def _analyze_and_generate_command(
        self, 
        state: MultiAgentState, 
        context: Dict[str, Any]
    ) -> Optional[CommandDecision]:
        """Use AI to analyze situation and generate the next command."""
        
        # Build comprehensive prompt for command generation
        analysis_prompt = self._build_command_prompt(state, context)
        
        try:
            # Use AI to generate the next command with timeout
            import google.generativeai as genai
            logger.info(f"🤖 Calling Gemini API for command generation (timeout: {self.ai_models.config.timeout}s)")
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_models.gemini.generate_content,
                    analysis_prompt,
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
                return self._create_fallback_command(state, context)
            
            # Parse AI response
            response_text = response.text.strip() if response.text else ""
            if not response_text:
                logger.error("Empty response from AI")
                return None
            
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
                return None
            
            # Validate response
            if not self._validate_ai_response(response_json):
                logger.error("Invalid AI response format")
                return None
            
            # Check if AI thinks task is complete
            if response_json.get("task_complete", False):
                return None
            
            # Create command decision
            command_decision = CommandDecision(
                command=response_json["command"],
                action_type=ActionType(response_json["action_type"]),
                reasoning=response_json["reasoning"],
                expected_result=response_json["expected_result"],
                confidence=response_json["confidence"],
                parameters=response_json.get("parameters", {})
            )
            
            return command_decision
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Gemini API call timed out after {self.ai_models.config.timeout}s")
            return None  # Let Decision Agent handle the timeout failure
        except Exception as e:
            logger.error(f"❌ AI command generation failed: {e}")
            return None  # Let Decision Agent handle the API failure
    
    def _build_command_prompt(self, state: MultiAgentState, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for AI command generation."""
        
        # Format action history
        action_summary = "No actions taken yet"
        if state["action_history"]:
            recent_actions = state["action_history"][-5:]  # Last 5 actions
            action_lines = []
            for action in recent_actions:
                status = "✅ SUCCESS" if action["success"] else "❌ FAILED"
                action_lines.append(f"  {status}: {action['command']}")
                if action.get("error_message"):
                    action_lines.append(f"    Error: {action['error_message']}")
            action_summary = "\n".join(action_lines)
        
        # Format screen state
        screen_info = "No screen analysis available"
        if context.get("current_screen"):
            screen = context["current_screen"]
            screen_info = f"""
Current Screen Analysis:
  - Applications: {screen.get('applications', [])}
  - UI Elements: {len(screen.get('ui_elements', []))} detected
  - Clickable Elements: {len(screen.get('clickable_elements', []))} available
  - Unexpected Elements: {screen.get('unexpected_elements', [])}
  - Analysis: {screen.get('analysis_summary', 'No analysis')}"""
        
        # Format error context
        error_context = ""
        if state["error_messages"]:
            recent_errors = state["error_messages"][-2:]  # Last 2 errors
            error_context = f"\nRecent Errors:\n" + "\n".join(f"  - {error}" for error in recent_errors)
        
        prompt = f"""
You are the Commander Agent in a multi-agent OS automation system.

TASK OBJECTIVE: {state['user_intent']}

CURRENT SITUATION:
- Step: {state['current_step']} (Attempt: {state['attempt_count']}/{state['max_attempts']})
- Status: {state['status']}
- Confidence: {state['confidence_score']:.2f}

EXECUTION HISTORY:
{action_summary}

CURRENT SCREEN STATE:
{screen_info}

{error_context}

YOUR ROLE:
Generate the ONE next command to execute. Consider:
1. What has been accomplished so far
2. What the current screen shows
3. What logically should happen next
4. Any errors that need to be addressed

RESPONSE FORMAT (JSON):
{{
    "task_complete": false,
    "command": "exact command to execute",
    "action_type": "command|click|type|wait",
    "reasoning": "why this command is the logical next step",
    "expected_result": "what should happen after this command",
    "confidence": 0.85,
    "parameters": {{"any": "additional parameters"}}
}}

If the task is complete, set task_complete: true and omit other fields.

ACTION GENERATION RULES:
1. SYSTEM COMMANDS: For launching applications
   - action_type: "command", command: "google-chrome"
   
2. TERMINAL COMMANDS: For system operations, file management, development
   - action_type: "terminal", command: "ls -la"
   - action_type: "terminal", command: "git clone https://github.com/user/repo"
   - action_type: "terminal", command: "npm install && npm start"
   
3. WEB NAVIGATION: For browser control
   - action_type: "web_navigate", command: "https://youtube.com"
   - action_type: "web_analyze", command: "find_videos" (analyze page elements)
   
4. WEB INTERACTION: For clicking and typing on websites
   - action_type: "click", command: "random_video" (will find and click video)
   - action_type: "type", command: "search query" (type in active field)
   
5. UTILITY ACTIONS:
   - action_type: "wait", command: "3" (wait 3 seconds)

DECISION LOGIC:
- File operations, git, package management, builds → TERMINAL
- Opening applications → COMMAND  
- Navigating to websites → WEB_NAVIGATE
- Clicking on webpage elements → First WEB_ANALYZE, then CLICK
- System info, process management → TERMINAL
- Web research, social media → WEB_NAVIGATE + WEB_ANALYZE

EXAMPLES:
- "open terminal and list files" → action_type: "terminal", command: "ls -la"
- "go to youtube" → action_type: "web_navigate", command: "https://youtube.com"
- "click on any video" → action_type: "web_analyze", command: "find_videos"

Generate the next command:
"""
        
        return prompt
    
    def _validate_ai_response(self, response: Dict[str, Any]) -> bool:
        """Validate AI response format."""
        if response.get("task_complete", False):
            return True
        
        required_fields = ["command", "action_type", "reasoning", "expected_result", "confidence"]
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field in AI response: {field}")
                return False
        
        # Validate action type
        try:
            ActionType(response["action_type"])
        except ValueError:
            logger.error(f"Invalid action_type: {response['action_type']}")
            return False
        
        # Validate confidence
        confidence = response["confidence"]
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            logger.error(f"Invalid confidence value: {confidence}")
            return False
        
        return True
    
    def _create_fallback_command(self, state: MultiAgentState, context: Dict[str, Any]) -> Optional[CommandDecision]:
        """Create fallback command when AI is blocked by safety filters."""
        
        # Simple rule-based command generation
        user_intent = state.get('user_intent', '').lower()
        recent_actions = state.get("action_history", [])
        
        # If no actions yet and user wants to open something
        if not recent_actions:
            if 'chrome' in user_intent or 'browser' in user_intent:
                return CommandDecision(
                    command="google-chrome",
                    action_type=ActionType.COMMAND,
                    reasoning="Fallback: Opening Chrome browser as requested",
                    expected_result="Chrome browser should open",
                    confidence=0.8
                )
            elif 'firefox' in user_intent:
                return CommandDecision(
                    command="firefox",
                    action_type=ActionType.COMMAND,
                    reasoning="Fallback: Opening Firefox browser as requested", 
                    expected_result="Firefox browser should open",
                    confidence=0.8
                )
        
        # If browser opened successfully, next step is to navigate
        last_action = recent_actions[-1] if recent_actions else {}
        if (last_action.get("success", False) and 
            "chrome" in last_action.get("command", "").lower()):
            
            # Look for URL in user intent
            if 'youtube' in user_intent:
                return CommandDecision(
                    command="https://youtube.com",
                    action_type=ActionType.WEB_NAVIGATE,
                    reasoning="Fallback: Navigating to YouTube as requested",
                    expected_result="Should navigate to YouTube website",
                    confidence=0.7
                )
            elif 'google' in user_intent and 'youtube' not in user_intent:
                return CommandDecision(
                    command="https://google.com",
                    action_type=ActionType.WEB_NAVIGATE,
                    reasoning="Fallback: Navigating to Google as requested",
                    expected_result="Should navigate to Google website",
                    confidence=0.7
                )
        
        # If previous command failed, try a wait
        if (last_action and not last_action.get("success", False)):
            return CommandDecision(
                command="2",
                action_type=ActionType.WAIT,
                reasoning="Fallback: Waiting for system to stabilize after failed action",
                expected_result="System should have time to stabilize",
                confidence=0.6
            )
        
        # Default fallback - task might be complete
        return None
    
    async def handle_execution_failure(
        self, 
        task_id: str, 
        failed_command: str, 
        error_message: str
    ) -> Optional[CommandDecision]:
        """
        Handle command execution failure and generate recovery command.
        """
        try:
            state = await self.state_manager.get_state(task_id)
            if not state:
                return None
            
            # Build recovery prompt
            recovery_prompt = f"""
The previous command failed and needs recovery.

FAILED COMMAND: {failed_command}
ERROR: {error_message}

TASK OBJECTIVE: {state['user_intent']}

Generate a recovery command to handle this failure and continue toward the goal.
Consider alternative approaches, error handling, or diagnostic commands.

Use the same JSON format as before.
"""
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_models.gemini.generate_content,
                    recovery_prompt
                ),
                timeout=self.ai_models.config.timeout
            )
            
            response_json = json.loads(response.text)
            
            if not self._validate_ai_response(response_json):
                return None
            
            if response_json.get("task_complete", False):
                return None
            
            recovery_decision = CommandDecision(
                command=response_json["command"],
                action_type=ActionType(response_json["action_type"]),
                reasoning=f"RECOVERY: {response_json['reasoning']}",
                expected_result=response_json["expected_result"],
                confidence=response_json["confidence"],
                parameters=response_json.get("parameters", {})
            )
            
            logger.info(f"Generated recovery command for {task_id}: {recovery_decision.command}")
            return recovery_decision
            
        except Exception as e:
            logger.error(f"Recovery command generation failed: {e}")
            return None
    
