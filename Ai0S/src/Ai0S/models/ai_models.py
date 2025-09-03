"""
AI Models Integration - Dual Model Configuration
Implements Gemini 2.0 Flash for voice transcription and Groq for intelligence/planning.
"""

import base64
import asyncio
import json
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
from groq import Groq
import google.generativeai as genai
from pydantic import BaseModel, Field

from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class ModelType(Enum):
    """AI Model types for different tasks."""
    VOICE_TRANSCRIPTION = "gemini_2_flash"
    INTELLIGENCE_PLANNING = "groq_llama"
    VISION_ANALYSIS = "groq_llama"
    TASK_EXECUTION = "groq_llama"


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    groq_api_key: str
    gemini_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash-exp"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30


class ExecutionPlan(BaseModel):
    """Structured execution plan from AI."""
    task_id: str
    user_intent: str
    total_steps: int
    estimated_time: float
    steps: List['ExecutionStep']
    contingency_plans: Dict[str, List['ExecutionStep']]
    success_criteria: str
    confidence_score: float


class ExecutionStep(BaseModel):
    """Individual execution step."""
    step_id: str
    order: int
    description: str
    action_type: str  # "click", "type", "command", "wait", "verify"
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    pre_conditions: List[str] = Field(default_factory=list)
    post_conditions: List[str] = Field(default_factory=list)
    timeout: float = 30.0
    retry_strategy: Optional[str] = None
    fallback_step_id: Optional[str] = None
    expected_screen_change: Optional[str] = None


class ScreenAnalysis(BaseModel):
    """Screen analysis results from vision model."""
    applications: List[str]
    ui_elements: List[Dict[str, Any]]
    text_content: List[str]
    clickable_elements: List[Dict[str, Any]]
    unexpected_elements: List[Dict[str, Any]]
    confidence_score: float
    recommendations: List[str]


class AIModels:
    """Dual AI model system for agentic OS control."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._setup_models()
        
    def _setup_models(self) -> None:
        """Initialize both AI models."""
        try:
            # Setup Gemini 2.0 Flash for voice transcription
            genai.configure(api_key=self.config.gemini_api_key)
            self.gemini = genai.GenerativeModel(self.config.gemini_model)
            logger.info("Gemini 2.0 Flash initialized successfully")
            
            # Setup Groq for intelligence and planning
            self.groq = Groq(api_key=self.config.groq_api_key)
            logger.info("Groq initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes, audio_format: str = "webm") -> str:
        """
        Transcribe audio using Gemini 2.0 Flash.
        This is the ONLY use case for Gemini - audio transcription.
        """
        try:
            logger.info("Starting audio transcription with Gemini 2.0 Flash")
            
            # Prepare audio for Gemini
            response = await asyncio.to_thread(
                self.gemini.generate_content,
                [
                    "Transcribe this audio to text accurately. Return only the transcribed text without any additional commentary:",
                    {
                        "mime_type": f"audio/{audio_format}",
                        "data": audio_data
                    }
                ]
            )
            
            transcript = response.text.strip()
            logger.info(f"Audio transcribed successfully: {len(transcript)} characters")
            return transcript
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            raise
    
    async def analyze_screen(self, screenshot_data: bytes) -> ScreenAnalysis:
        """
        Analyze screenshot using Gemini for visual understanding.
        Direct image to LLM analysis without OCR.
        """
        try:
            logger.info("Analyzing screenshot with Gemini vision model")
            
            # Encode screenshot to base64
            screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
            
            # Create detailed prompt for screen analysis
            analysis_prompt = """
            Analyze this screenshot and provide a detailed JSON analysis with the following structure:
            {
                "applications": ["list of visible applications"],
                "ui_elements": [
                    {
                        "type": "button|input|menu|window|dialog",
                        "text": "visible text",
                        "position": {"x": 0, "y": 0},
                        "size": {"width": 0, "height": 0},
                        "clickable": true/false,
                        "description": "element description"
                    }
                ],
                "text_content": ["all visible text content"],
                "clickable_elements": [
                    {
                        "element_id": "unique_id",
                        "text": "element text",
                        "type": "element type",
                        "coordinates": {"x": 0, "y": 0}
                    }
                ],
                "unexpected_elements": [
                    {
                        "type": "popup|dialog|notification|error",
                        "description": "what appeared unexpectedly"
                    }
                ],
                "confidence_score": 0.95,
                "recommendations": ["suggested next actions"]
            }
            
            Focus on identifying:
            1. All interactive UI elements with precise coordinates
            2. Any popups, dialogs, or unexpected windows
            3. Current application state and context
            4. Available actions and clickable elements
            5. Any error messages or alerts
            
            Return valid JSON only.
            """
            
            # Use Gemini 2.5 Pro for vision analysis
            import google.generativeai as genai
            from PIL import Image
            import io
            
            # Configure Gemini with API key
            genai.configure(api_key=self.config.gemini_api_key)
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_data))
            
            # Use Gemini 2.5 Pro specifically for vision
            model = genai.GenerativeModel('gemini-2.5-pro')
            
            response = await asyncio.to_thread(
                model.generate_content,
                [analysis_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens
                )
            )
            
            # Parse Gemini response
            response_text = response.text
            analysis_json = json.loads(response_text)
            screen_analysis = ScreenAnalysis(**analysis_json)
            
            logger.info(f"Screen analysis completed with confidence: {screen_analysis.confidence_score}")
            return screen_analysis
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            # Return basic fallback analysis
            return ScreenAnalysis(
                applications=[],
                ui_elements=[],
                text_content=[],
                clickable_elements=[],
                unexpected_elements=[],
                confidence_score=0.0,
                recommendations=["Screenshot analysis failed - manual intervention required"]
            )
    
    async def create_execution_plan(
        self, 
        user_intent: str, 
        screen_analysis: ScreenAnalysis,
        system_context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Generate dynamic execution plan using Groq intelligence.
        No hardcoded workflows - everything AI generated.
        """
        try:
            logger.info(f"Creating execution plan for: {user_intent}")
            
            # Build comprehensive context for planning
            planning_prompt = f"""
            You are an intelligent OS control agent. Generate a detailed execution plan for the user's request.
            
            USER REQUEST: {user_intent}
            
            CURRENT SCREEN STATE:
            - Applications: {screen_analysis.applications}
            - UI Elements: {len(screen_analysis.ui_elements)} detected
            - Clickable Elements: {len(screen_analysis.clickable_elements)} available
            - Unexpected Elements: {screen_analysis.unexpected_elements}
            
            SYSTEM CONTEXT:
            - OS: {system_context.get('os', 'Unknown')}
            - Display Server: {system_context.get('display_server', 'Unknown')}
            - Capabilities: {system_context.get('capabilities', [])}
            
            Generate a JSON execution plan with this structure:
            {{
                "task_id": "unique_task_id",
                "user_intent": "{user_intent}",
                "total_steps": 5,
                "estimated_time": 30.0,
                "steps": [
                    {{
                        "step_id": "step_1",
                        "order": 1,
                        "description": "Clear description of what this step does",
                        "action_type": "click|type|command|wait|verify",
                        "target": "element description or command",
                        "parameters": {{"key": "value"}},
                        "pre_conditions": ["what must be true before this step"],
                        "post_conditions": ["what should be true after this step"],
                        "timeout": 10.0,
                        "retry_strategy": "retry_on_failure|wait_and_retry|fallback",
                        "fallback_step_id": "alternative_step_id",
                        "expected_screen_change": "description of expected change"
                    }}
                ],
                "contingency_plans": {{
                    "error_recovery": [
                        {{"step_id": "error_step_1", "description": "Handle error case"}}
                    ],
                    "unexpected_popup": [
                        {{"step_id": "popup_step_1", "description": "Handle popup"}}
                    ]
                }},
                "success_criteria": "How to determine if the task succeeded",
                "confidence_score": 0.9
            }}
            
            PLANNING GUIDELINES:
            1. Break complex tasks into atomic, executable steps
            2. Include error handling and fallback strategies
            3. Consider the current screen state when planning
            4. Generate OS-appropriate commands dynamically
            5. Include verification steps to ensure success
            6. Plan for unexpected UI elements (popups, dialogs)
            7. Estimate realistic timeouts for each step
            8. Provide clear success criteria
            
            Return valid JSON only.
            """
            
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=self.config.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert OS automation agent that generates dynamic execution plans."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            plan_json = json.loads(response.choices[0].message.content)
            execution_plan = ExecutionPlan(**plan_json)
            
            logger.info(f"Execution plan created with {execution_plan.total_steps} steps")
            return execution_plan
            
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            # Return basic fallback plan
            return ExecutionPlan(
                task_id="fallback_plan",
                user_intent=user_intent,
                total_steps=1,
                estimated_time=5.0,
                steps=[
                    ExecutionStep(
                        step_id="fallback_step",
                        order=1,
                        description=f"Manual execution required for: {user_intent}",
                        action_type="command",
                        parameters={"error": "AI planning failed"}
                    )
                ],
                contingency_plans={},
                success_criteria="Manual verification required",
                confidence_score=0.0
            )
    
    async def adapt_plan(
        self, 
        original_plan: ExecutionPlan, 
        current_screen: ScreenAnalysis,
        error_context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Adapt execution plan based on unexpected screen state or errors.
        Dynamic plan modification using AI intelligence.
        """
        try:
            logger.info("Adapting execution plan due to unexpected state")
            
            adaptation_prompt = f"""
            The original execution plan encountered an unexpected situation. Generate an adapted plan.
            
            ORIGINAL PLAN:
            - Task: {original_plan.user_intent}
            - Current Step: {error_context.get('current_step', 'Unknown')}
            - Steps Completed: {error_context.get('completed_steps', 0)}
            
            CURRENT SCREEN STATE:
            - Applications: {current_screen.applications}
            - Unexpected Elements: {current_screen.unexpected_elements}
            - Available Elements: {len(current_screen.clickable_elements)}
            
            ERROR CONTEXT:
            - Error Type: {error_context.get('error_type', 'Unknown')}
            - Error Details: {error_context.get('error_details', 'No details')}
            - Failed Action: {error_context.get('failed_action', 'Unknown')}
            
            Generate an adapted execution plan that:
            1. Handles the current unexpected state
            2. Recovers from the error gracefully
            3. Continues toward the original goal
            4. Includes new steps to handle obstacles
            5. Updates success criteria if needed
            
            Use the same JSON structure as the original plan.
            Return valid JSON only.
            """
            
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=self.config.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert at adapting execution plans when unexpected situations occur."},
                    {"role": "user", "content": adaptation_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            adapted_json = json.loads(response.choices[0].message.content)
            adapted_plan = ExecutionPlan(**adapted_json)
            
            logger.info(f"Plan adapted successfully with {adapted_plan.total_steps} steps")
            return adapted_plan
            
        except Exception as e:
            logger.error(f"Plan adaptation failed: {e}")
            return original_plan  # Return original plan if adaptation fails
    
    async def analyze_command_intent(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user command intent and extract structured information.
        Used for command parsing and understanding.
        """
        try:
            intent_prompt = f"""
            Analyze this user command and extract structured information:
            
            USER COMMAND: {user_input}
            
            CONTEXT:
            - Current Applications: {context.get('active_apps', [])}
            - Recent Actions: {context.get('recent_actions', [])}
            - Available Capabilities: {context.get('capabilities', [])}
            
            Return JSON analysis:
            {{
                "intent_type": "web_navigation|file_operation|application_control|system_command|complex_task",
                "primary_action": "main action to perform",
                "target_application": "target app or null",
                "parameters": {{"key": "extracted parameters"}},
                "complexity": "simple|medium|complex",
                "requires_confirmation": true/false,
                "estimated_steps": 3,
                "confidence": 0.95,
                "interpretation": "human readable interpretation"
            }}
            
            Return valid JSON only.
            """
            
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=self.config.groq_model,
                messages=[
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            intent_analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Command intent analyzed: {intent_analysis.get('intent_type')}")
            return intent_analysis
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                "intent_type": "unknown",
                "primary_action": user_input,
                "target_application": None,
                "parameters": {},
                "complexity": "unknown",
                "requires_confirmation": True,
                "estimated_steps": 1,
                "confidence": 0.0,
                "interpretation": f"Could not analyze: {user_input}"
            }


async def create_ai_models() -> AIModels:
    """Factory function to create AI models with configuration."""
    settings = get_settings()
    
    config = ModelConfig(
        groq_api_key=settings.GROQ_API_KEY,
        gemini_api_key=settings.GEMINI_API_KEY,
        groq_model=getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile'),
        gemini_model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp'),
    )
    
    return AIModels(config)


# Global AI models instance
_ai_models: Optional[AIModels] = None


async def get_ai_models() -> AIModels:
    """Get global AI models instance."""
    global _ai_models
    if _ai_models is None:
        _ai_models = await create_ai_models()
    return _ai_models