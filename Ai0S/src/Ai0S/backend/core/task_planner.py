"""
Task Planner - Dynamic execution plan generation using AI
Intelligent task decomposition and planning with contextual awareness.
"""

import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ..models.ai_models import AIModels
from ...desktop_app.components.execution_visualizer import ExecutionPlan, ExecutionStep, StepStatus
from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    SIMPLE = "simple"      # Single action tasks
    MODERATE = "moderate"  # Multi-step tasks
    COMPLEX = "complex"    # Complex workflows with dependencies


@dataclass
class TaskContext:
    """Context information for task planning."""
    user_request: str
    current_screen_state: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    system_capabilities: Optional[List[str]] = None
    user_preferences: Optional[Dict[str, Any]] = None
    previous_failed_attempts: Optional[List[Dict[str, Any]]] = None


@dataclass
class PlanningResult:
    """Result of the planning process."""
    plan: ExecutionPlan
    confidence: float  # 0.0 to 1.0
    estimated_duration: int  # seconds
    complexity: TaskComplexity
    risks: List[str]
    alternatives: Optional[List[ExecutionPlan]] = None


class TaskPlanner:
    """Intelligent task planner with AI-powered plan generation."""
    
    def __init__(self, ai_models: AIModels):
        self.ai_models = ai_models
        self.settings = get_settings()
        self.system_env = get_system_environment()
        
        # Planning cache
        self.plan_cache = {}
        self.planning_templates = {}
        
        # Planning statistics
        self.planning_stats = {
            "plans_generated": 0,
            "plans_successful": 0,
            "average_confidence": 0.0,
            "common_failure_patterns": []
        }
        
        # Initialize templates
        self._load_planning_templates()
    
    def _load_planning_templates(self) -> None:
        """Load planning templates for common task patterns."""
        
        self.planning_templates = {
            "web_automation": {
                "pattern": ["open_browser", "navigate_to_url", "interact_with_elements", "extract_data"],
                "tools": ["browser_tools", "ui_interaction_tools"],
                "complexity": TaskComplexity.MODERATE
            },
            "file_operations": {
                "pattern": ["locate_files", "perform_file_ops", "verify_results"],
                "tools": ["file_tools", "system_tools"],
                "complexity": TaskComplexity.SIMPLE
            },
            "application_control": {
                "pattern": ["launch_app", "wait_for_app", "interact_with_app", "verify_action"],
                "tools": ["application_tools", "ui_interaction_tools"],
                "complexity": TaskComplexity.MODERATE
            },
            "system_administration": {
                "pattern": ["check_permissions", "backup_state", "execute_commands", "verify_system"],
                "tools": ["system_tools", "file_tools"],
                "complexity": TaskComplexity.COMPLEX
            },
            "data_processing": {
                "pattern": ["load_data", "process_data", "validate_results", "save_output"],
                "tools": ["file_tools", "system_tools"],
                "complexity": TaskComplexity.MODERATE
            }
        }
    
    async def create_execution_plan(self, context: TaskContext) -> PlanningResult:
        """Create a comprehensive execution plan for a user request."""
        
        try:
            logger.info(f"Creating execution plan for: {context.user_request}")
            
            # Step 1: Analyze the request
            analysis = await self._analyze_request(context)
            
            # Step 2: Generate initial plan
            initial_plan = await self._generate_initial_plan(context, analysis)
            
            # Step 3: Optimize and refine plan
            refined_plan = await self._refine_plan(initial_plan, context, analysis)
            
            # Step 4: Assess risks and alternatives
            risk_assessment = await self._assess_risks(refined_plan, context)
            
            # Step 5: Generate alternatives if needed
            alternatives = None
            if risk_assessment["confidence"] < 0.7:
                alternatives = await self._generate_alternative_plans(context, analysis)
            
            # Create final planning result
            result = PlanningResult(
                plan=refined_plan,
                confidence=risk_assessment["confidence"],
                estimated_duration=risk_assessment["estimated_duration"],
                complexity=analysis["complexity"],
                risks=risk_assessment["risks"],
                alternatives=alternatives
            )
            
            # Update statistics
            self.planning_stats["plans_generated"] += 1
            self._update_planning_stats(result)
            
            logger.info(f"Generated plan with {len(refined_plan.steps)} steps, confidence: {result.confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create execution plan: {e}")
            raise
    
    async def _analyze_request(self, context: TaskContext) -> Dict[str, Any]:
        """Analyze the user request to understand intent and requirements."""
        
        analysis_prompt = f"""
        Analyze this user request for task automation:
        
        Request: "{context.user_request}"
        
        System Information:
        - OS: {self.system_env.os}
        - Desktop Environment: {self.system_env.desktop_environment}
        - Available Capabilities: {self.system_env.capabilities}
        
        Please provide a detailed analysis in JSON format:
        {{
            "primary_intent": "brief description of main goal",
            "task_category": "web_automation|file_operations|application_control|system_administration|data_processing|other",
            "complexity": "simple|moderate|complex",
            "required_tools": ["list", "of", "tool", "categories"],
            "key_entities": ["important", "entities", "from", "request"],
            "success_criteria": ["how", "to", "measure", "success"],
            "potential_challenges": ["possible", "difficulties"],
            "estimated_steps": 5,
            "requires_user_input": false,
            "safety_concerns": ["security", "or", "safety", "issues"]
        }}
        """
        
        try:
            response = await self.ai_models.generate_plan(analysis_prompt)
            analysis = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Validate and enhance analysis
            analysis["complexity"] = TaskComplexity(analysis.get("complexity", "moderate"))
            
            return analysis
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse analysis response, using defaults: {e}")
            
            # Fallback analysis
            return {
                "primary_intent": "Execute user request",
                "task_category": "other",
                "complexity": TaskComplexity.MODERATE,
                "required_tools": ["system_tools"],
                "key_entities": [],
                "success_criteria": ["Task completed successfully"],
                "potential_challenges": ["Unknown challenges"],
                "estimated_steps": 3,
                "requires_user_input": False,
                "safety_concerns": []
            }
    
    async def _generate_initial_plan(self, context: TaskContext, analysis: Dict[str, Any]) -> ExecutionPlan:
        """Generate initial execution plan based on analysis."""
        
        # Get template if available
        template = self.planning_templates.get(analysis["task_category"])
        
        planning_prompt = f"""
        Create a detailed execution plan for this task:
        
        User Request: "{context.user_request}"
        Task Category: {analysis["task_category"]}
        Complexity: {analysis["complexity"].value}
        Required Tools: {analysis["required_tools"]}
        
        System Context:
        - Operating System: {self.system_env.os}
        - Available Tools: {list(self.planning_templates.keys())}
        
        {f"Template Pattern: {template['pattern']}" if template else ""}
        
        Generate a step-by-step execution plan in JSON format:
        {{
            "title": "Concise plan title",
            "description": "Brief plan description", 
            "steps": [
                {{
                    "id": "step_1",
                    "title": "Step title",
                    "description": "Detailed step description",
                    "tool_category": "required_tool_category",
                    "tool_name": "specific_tool_name",
                    "parameters": {{}},
                    "expected_duration": 10,
                    "dependencies": [],
                    "success_criteria": "How to verify success",
                    "failure_recovery": "What to do if step fails"
                }}
            ]
        }}
        
        Make sure steps are:
        1. Specific and actionable
        2. Include proper tool selection
        3. Have clear success criteria
        4. Include error recovery strategies
        5. Are ordered with proper dependencies
        """
        
        try:
            response = await self.ai_models.generate_plan(planning_prompt)
            plan_data = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Convert to ExecutionPlan
            steps = []
            for step_data in plan_data["steps"]:
                step = ExecutionStep(
                    id=step_data["id"],
                    title=step_data["title"],
                    description=step_data["description"],
                    metadata={
                        "tool_category": step_data.get("tool_category"),
                        "tool_name": step_data.get("tool_name"),
                        "parameters": step_data.get("parameters", {}),
                        "expected_duration": step_data.get("expected_duration", 30),
                        "dependencies": step_data.get("dependencies", []),
                        "success_criteria": step_data.get("success_criteria"),
                        "failure_recovery": step_data.get("failure_recovery")
                    }
                )
                steps.append(step)
            
            plan = ExecutionPlan(
                id=str(uuid.uuid4()),
                title=plan_data["title"],
                description=plan_data["description"],
                steps=steps,
                created_at=datetime.now()
            )
            
            return plan
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse planning response: {e}")
            
            # Create fallback plan
            return self._create_fallback_plan(context)
    
    def _create_fallback_plan(self, context: TaskContext) -> ExecutionPlan:
        """Create a simple fallback plan when AI planning fails."""
        
        steps = [
            ExecutionStep(
                id="analyze_request",
                title="Analyze Request",
                description=f"Analyze the user request: {context.user_request}",
                metadata={
                    "tool_category": "system_tools",
                    "expected_duration": 5
                }
            ),
            ExecutionStep(
                id="execute_action",
                title="Execute Action", 
                description="Execute the requested action",
                metadata={
                    "tool_category": "system_tools",
                    "expected_duration": 30
                }
            ),
            ExecutionStep(
                id="verify_result",
                title="Verify Result",
                description="Verify that the action was completed successfully",
                metadata={
                    "tool_category": "system_tools",
                    "expected_duration": 10
                }
            )
        ]
        
        return ExecutionPlan(
            id=str(uuid.uuid4()),
            title="Execute User Request",
            description=f"Execute: {context.user_request}",
            steps=steps,
            created_at=datetime.now()
        )
    
    async def _refine_plan(self, plan: ExecutionPlan, context: TaskContext, analysis: Dict[str, Any]) -> ExecutionPlan:
        """Refine and optimize the execution plan."""
        
        refinement_prompt = f"""
        Review and refine this execution plan:
        
        Original Request: "{context.user_request}"
        Current Plan: {json.dumps(asdict(plan), default=str, indent=2)}
        
        Analysis: {json.dumps(analysis, default=str)}
        
        Consider:
        1. Are steps in the optimal order?
        2. Are there missing error handling steps?
        3. Can any steps be combined or simplified?
        4. Are tool selections appropriate?
        5. Do success criteria make sense?
        
        Provide refined plan in the same JSON format, or return "NO_CHANGES" if plan is already optimal.
        """
        
        try:
            response = await self.ai_models.generate_plan(refinement_prompt)
            
            if response.strip() == "NO_CHANGES":
                return plan
            
            refined_data = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Update plan with refinements
            if "steps" in refined_data:
                refined_steps = []
                for step_data in refined_data["steps"]:
                    # Find existing step or create new one
                    existing_step = next((s for s in plan.steps if s.id == step_data["id"]), None)
                    
                    if existing_step:
                        # Update existing step
                        existing_step.title = step_data.get("title", existing_step.title)
                        existing_step.description = step_data.get("description", existing_step.description)
                        if existing_step.metadata:
                            existing_step.metadata.update(step_data.get("metadata", {}))
                        refined_steps.append(existing_step)
                    else:
                        # Create new step
                        new_step = ExecutionStep(
                            id=step_data["id"],
                            title=step_data["title"],
                            description=step_data["description"],
                            metadata=step_data.get("metadata", {})
                        )
                        refined_steps.append(new_step)
                
                plan.steps = refined_steps
            
            if "title" in refined_data:
                plan.title = refined_data["title"]
            if "description" in refined_data:
                plan.description = refined_data["description"]
            
            return plan
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse refinement response, using original plan: {e}")
            return plan
    
    async def _assess_risks(self, plan: ExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Assess risks and estimate confidence for the execution plan."""
        
        risk_prompt = f"""
        Assess the risks and feasibility of this execution plan:
        
        Plan: {json.dumps(asdict(plan), default=str, indent=2)}
        Original Request: "{context.user_request}"
        System: {self.system_env.os}
        
        Provide risk assessment in JSON format:
        {{
            "confidence": 0.85,
            "estimated_duration": 120,
            "risks": [
                "Risk description 1",
                "Risk description 2"
            ],
            "risk_factors": {{
                "complexity": 0.3,
                "tool_availability": 0.1,
                "system_compatibility": 0.2,
                "user_input_required": 0.0
            }},
            "mitigation_strategies": [
                "Strategy 1",
                "Strategy 2"
            ]
        }}
        """
        
        try:
            response = await self.ai_models.generate_plan(risk_prompt)
            assessment = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Validate confidence score
            assessment["confidence"] = max(0.0, min(1.0, assessment.get("confidence", 0.5)))
            
            return assessment
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse risk assessment, using defaults: {e}")
            
            return {
                "confidence": 0.6,
                "estimated_duration": len(plan.steps) * 30,
                "risks": ["Unknown execution risks"],
                "risk_factors": {"unknown": 0.4},
                "mitigation_strategies": ["Monitor execution closely"]
            }
    
    async def _generate_alternative_plans(self, context: TaskContext, analysis: Dict[str, Any]) -> List[ExecutionPlan]:
        """Generate alternative execution plans for low-confidence scenarios."""
        
        alt_prompt = f"""
        Generate 2-3 alternative execution plans for this request:
        
        Request: "{context.user_request}"
        Analysis: {json.dumps(analysis, default=str)}
        
        Create alternative approaches that:
        1. Use different tool combinations
        2. Have different complexity levels
        3. Focus on different success strategies
        
        Return as JSON array of plans with same structure as before.
        """
        
        try:
            response = await self.ai_models.generate_plan(alt_prompt)
            plans_data = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            alternative_plans = []
            for plan_data in plans_data:
                steps = []
                for step_data in plan_data["steps"]:
                    step = ExecutionStep(
                        id=step_data["id"],
                        title=step_data["title"],
                        description=step_data["description"],
                        metadata=step_data.get("metadata", {})
                    )
                    steps.append(step)
                
                plan = ExecutionPlan(
                    id=str(uuid.uuid4()),
                    title=plan_data["title"],
                    description=plan_data["description"],
                    steps=steps,
                    created_at=datetime.now()
                )
                alternative_plans.append(plan)
            
            return alternative_plans
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to generate alternative plans: {e}")
            return []
    
    def _update_planning_stats(self, result: PlanningResult) -> None:
        """Update planning statistics."""
        
        current_avg = self.planning_stats["average_confidence"]
        total_plans = self.planning_stats["plans_generated"]
        
        # Update rolling average confidence
        new_avg = ((current_avg * (total_plans - 1)) + result.confidence) / total_plans
        self.planning_stats["average_confidence"] = new_avg
    
    async def adapt_plan_during_execution(self, plan: ExecutionPlan, 
                                        failed_step_id: str, 
                                        error_context: Dict[str, Any]) -> Optional[ExecutionPlan]:
        """Adapt plan during execution when a step fails."""
        
        adaptation_prompt = f"""
        A step in the execution plan has failed. Adapt the plan to recover:
        
        Original Plan: {json.dumps(asdict(plan), default=str, indent=2)}
        Failed Step ID: {failed_step_id}
        Error Context: {json.dumps(error_context, default=str)}
        
        Provide an adapted plan that:
        1. Handles the failure appropriately
        2. Continues toward the original goal
        3. Adds recovery or alternative steps
        
        Return adapted plan in same JSON format, or "CANNOT_RECOVER" if recovery is not possible.
        """
        
        try:
            response = await self.ai_models.generate_plan(adaptation_prompt)
            
            if response.strip() == "CANNOT_RECOVER":
                return None
            
            adapted_data = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Create adapted plan
            adapted_steps = []
            for step_data in adapted_data["steps"]:
                step = ExecutionStep(
                    id=step_data["id"],
                    title=step_data["title"], 
                    description=step_data["description"],
                    metadata=step_data.get("metadata", {})
                )
                adapted_steps.append(step)
            
            adapted_plan = ExecutionPlan(
                id=str(uuid.uuid4()),
                title=adapted_data.get("title", plan.title + " (Adapted)"),
                description=adapted_data.get("description", "Adapted plan after failure"),
                steps=adapted_steps,
                created_at=datetime.now()
            )
            
            logger.info(f"Generated adapted plan with {len(adapted_steps)} steps")
            return adapted_plan
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to adapt plan: {e}")
            return None
    
    def get_planning_statistics(self) -> Dict[str, Any]:
        """Get current planning statistics."""
        
        return self.planning_stats.copy()
    
    def clear_plan_cache(self) -> None:
        """Clear the planning cache."""
        
        self.plan_cache.clear()
        logger.info("Planning cache cleared")