"""
AI Models Integration - Gemini 2.5 Flash Single Model Configuration
Implements Gemini 2.5 Flash for all AI tasks: voice transcription, intelligence, and planning.
Optimized for speed while maintaining quality.
"""

import base64
import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import google.generativeai as genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class ModelType(Enum):
    """AI Model types for different tasks - all using Gemini 2.5 Flash."""
    VOICE_TRANSCRIPTION = "gemini_2_5_flash"
    INTELLIGENCE_PLANNING = "gemini_2_5_flash"
    VISION_ANALYSIS = "gemini_2_5_flash"
    TASK_EXECUTION = "gemini_2_5_flash"


@dataclass
class ModelConfig:
    """Configuration for AI models - Using Gemini 2.5 Flash for all tasks."""
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 15  # Reduced timeout to prevent hanging


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
    order: Optional[int] = 0  # Made optional with default
    description: str
    action_type: Optional[str] = "command"  # Made optional with default
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
        """Initialize Gemini 2.5 Flash for all AI tasks."""
        try:
            # Setup Gemini 2.5 Flash for all tasks - transcription, analysis, and planning
            genai.configure(api_key=self.config.gemini_api_key)
            self.gemini = genai.GenerativeModel(self.config.gemini_model)
            logger.info(f"Gemini {self.config.gemini_model} initialized successfully for all AI tasks")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes, audio_format: str = "webm") -> str:
        """
        Transcribe audio using Gemini 2.5 Flash.
        Audio transcription with multimodal capabilities.
        """
        try:
            logger.info("Starting audio transcription with Gemini 2.5 Flash")
            
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
            
            # Simplified prompt for faster, more reliable analysis
            analysis_prompt = """
            Analyze this screenshot and return a JSON response with this structure:
            {
                "applications": ["chrome", "terminal"],
                "ui_elements": [{"type": "window", "text": "Chrome Browser", "clickable": true}],
                "text_content": ["visible text"],
                "clickable_elements": [{"text": "element", "type": "button"}],
                "unexpected_elements": [],
                "confidence_score": 0.9,
                "recommendations": ["next action to take"]
            }
            
            Keep it simple and fast. Return only valid JSON, no markdown.
            """
            
            # Use Gemini 2.5 Pro for vision analysis
            import google.generativeai as genai
            from PIL import Image
            import io
            
            # Configure Gemini with API key
            genai.configure(api_key=self.config.gemini_api_key)
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_data))
            
            # Use Gemini 2.5 Flash for faster vision analysis (Pro is too slow)
            # Configure with relaxed safety settings for UI screenshots
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Use shorter timeout and reduced token limit for faster response
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    model.generate_content,
                    [analysis_prompt, image],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  # Lower temperature for consistency
                        max_output_tokens=1024  # Reduced tokens for speed
                    ),
                    safety_settings=safety_settings
                ),
                timeout=10  # Reduced timeout to 10 seconds
            )
            
            # Parse Gemini response with safety and error handling
            if not response.candidates or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "unknown"
                logger.error(f"Empty response from Gemini vision model. Finish reason: {finish_reason}")
                
                if finish_reason == 2:  # SAFETY filter
                    logger.warning("Gemini blocked screenshot analysis due to safety filters")
                    # Return minimal safe analysis
                    return ScreenAnalysis(
                        applications=["browser"],
                        ui_elements=[{"type": "window", "text": "Application Window", "clickable": True}],
                        text_content=["Content filtered by safety system"],
                        clickable_elements=[{"text": "window", "type": "application"}],
                        unexpected_elements=[],
                        confidence_score=0.3,
                        recommendations=["Continue with basic navigation"]
                    )
                
                raise ValueError(f"Empty response from AI model (finish_reason: {finish_reason})")
            
            response_text = response.text.strip()
            
            if not response_text:
                logger.error("Empty response text from Gemini vision model")
                raise ValueError("Empty response from AI model")
            
            # Handle markdown-wrapped JSON
            if response_text.startswith('```json'):
                start = response_text.find('```json') + 7
                end = response_text.rfind('```')
                if end > start:
                    response_text = response_text[start:end].strip()
                    logger.info("Extracted JSON from markdown wrapper")
            
            try:
                analysis_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response text: {response_text[:500]}...")
                raise ValueError(f"JSON parsing error: {e}")
            
            screen_analysis = ScreenAnalysis(**analysis_json)
            
            logger.info(f"Screen analysis completed with confidence: {screen_analysis.confidence_score}")
            return screen_analysis
            
        except asyncio.TimeoutError:
            logger.error(f"Screen analysis timed out after 10 seconds")
            return ScreenAnalysis(
                applications=["unknown"],
                ui_elements=[{"type": "window", "text": "Timeout", "clickable": False}],
                text_content=["Analysis timed out"],
                clickable_elements=[],
                unexpected_elements=[],
                confidence_score=0.1,
                recommendations=["Retry analysis or proceed manually"]
            )
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            # Return basic fallback analysis
            return ScreenAnalysis(
                applications=["unknown"],
                ui_elements=[{"type": "window", "text": "Error", "clickable": False}],
                text_content=["Analysis failed"],
                clickable_elements=[],
                unexpected_elements=[],
                confidence_score=0.0,
                recommendations=["Analysis failed - manual intervention required"]
            )
    
    async def create_execution_plan(
        self, 
        user_intent: str, 
        screen_analysis: ScreenAnalysis,
        system_context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Generate dynamic execution plan using Gemini 2.5 Flash intelligence.
        No hardcoded workflows - everything AI generated. Optimized for speed.
        """
        try:
            logger.info(f"Creating execution plan for: {user_intent}")
            
            # Build comprehensive context for planning
            screen_info = "Not available" if screen_analysis is None else f"""
            - Applications: {screen_analysis.applications}
            - UI Elements: {len(screen_analysis.ui_elements)} detected
            - Clickable Elements: {len(screen_analysis.clickable_elements)} available
            - Unexpected Elements: {screen_analysis.unexpected_elements}"""
            
            planning_prompt = f"""
            You are an intelligent OS control agent. Generate a detailed execution plan for the user's request.
            
            USER REQUEST: {user_intent}
            
            CURRENT SCREEN STATE:
            {screen_info}
            
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
                        {{
                            "step_id": "error_step_1", 
                            "order": 1,
                            "description": "Handle error case",
                            "action_type": "command"
                        }}
                    ],
                    "unexpected_popup": [
                        {{
                            "step_id": "popup_step_1", 
                            "order": 1,
                            "description": "Handle popup",
                            "action_type": "click"
                        }}
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
                self.gemini.generate_content,
                f"You are an expert OS automation agent that generates dynamic execution plans.\n\n{planning_prompt}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens
                )
            )
            
            plan_json = json.loads(response.text)
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
                self.gemini.generate_content,
                f"You are an expert at adapting execution plans when unexpected situations occur.\n\n{adaptation_prompt}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens
                )
            )
            
            adapted_json = json.loads(response.text)
            adapted_plan = ExecutionPlan(**adapted_json)
            
            logger.info(f"Plan adapted successfully with {adapted_plan.total_steps} steps")
            return adapted_plan
            
        except Exception as e:
            logger.error(f"Plan adaptation failed: {e}")
            return original_plan  # Return original plan if adaptation fails
    
    async def analyze_command_intent(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user command intent and extract structured information using Gemini 2.5 Flash.
        Used for command parsing and understanding. Optimized for speed.
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
                self.gemini.generate_content,
                intent_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=1024
                )
            )
            
            intent_analysis = json.loads(response.text)
            logger.info(f"Command intent analyzed with Gemini: {intent_analysis.get('intent_type')}")
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
    
    async def generate_system_command(self, step_description: str, target: str = "", parameters: Dict[str, Any] = None) -> str:
        """
        Generate a system command from a step description using Gemini 2.5 Flash.
        Pure AI-driven command generation without hardcoding.
        """
        if parameters is None:
            parameters = {}
            
        try:
            command_prompt = f"""
            Convert this execution step into a Linux command. Return ONLY the command, nothing else.
            
            Step: {step_description}
            Target: {target}
            Parameters: {parameters}
            
            Rules:
            1. Return ONLY the executable command
            2. For applications: use executable names (google-chrome, firefox, gedit, code, etc.)
            3. For URLs: use "google-chrome url" or "firefox url" format
            4. For multiple options: separate with || (e.g. "google-chrome || firefox")
            5. For browsers: prefer google-chrome || firefox || chromium-browser
            
            Examples:
            "Open Google Chrome" → "google-chrome"
            "Open browser" → "google-chrome || firefox"
            "Open VS Code" → "code"
            "Open text editor" → "gedit || code || nano"
            
            Command:
            """
            
            response = await asyncio.to_thread(
                self.gemini.generate_content,
                command_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=128  # Short response
                )
            )
            
            command = response.text.strip()
            logger.info(f"AI generated command: {command}")
            return command
            
        except Exception as e:
            logger.error(f"Command generation failed: {e}")
            # Minimal fallback that's not hardcoded - let the system handle the error
            return f"echo 'Could not generate command for: {step_description}'"


async def create_ai_models() -> AIModels:
    """Factory function to create AI models with configuration from .env file."""
    # Load environment variables from .env
    load_dotenv()
    
    # Use GEMINI_API_KEY from .env with fallback to GOOGLE_AI_API_KEY
    gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_AI_API_KEY must be set in .env file")
    
    config = ModelConfig(
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
        timeout=int(os.getenv('GEMINI_TIMEOUT', '15'))  # Configurable timeout
    )
    
    logger.info(f"AI models configured with timeout: {config.timeout}s")
    return AIModels(config)


# Global AI models instance
_ai_models: Optional[AIModels] = None


async def get_ai_models() -> AIModels:
    """Get global AI models instance."""
    global _ai_models
    if _ai_models is None:
        _ai_models = await create_ai_models()
    return _ai_models