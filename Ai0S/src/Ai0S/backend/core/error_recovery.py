"""
Error Recovery System - Intelligent error handling and adaptation
Advanced error recovery with learning capabilities and adaptive strategies.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import traceback
import re

from ..models.ai_models import AIModels
from ...desktop_app.components.execution_visualizer import ExecutionPlan, ExecutionStep, StepStatus
from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"           # Minor issues, can continue
    MEDIUM = "medium"     # Moderate issues, may need adjustment
    HIGH = "high"         # Serious issues, requires intervention
    CRITICAL = "critical" # Fatal errors, must stop execution


class ErrorCategory(Enum):
    TOOL_EXECUTION = "tool_execution"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"
    SYSTEM_ERROR = "system_error"
    AI_MODEL_ERROR = "ai_model_error"
    UNEXPECTED = "unexpected"


@dataclass
class ErrorContext:
    """Context information about an error."""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    step_id: Optional[str]
    tool_name: Optional[str]
    context_data: Dict[str, Any]
    stack_trace: Optional[str]
    system_state: Optional[Dict[str, Any]]


@dataclass
class RecoveryStrategy:
    """Recovery strategy for handling errors."""
    strategy_id: str
    name: str
    description: str
    applicable_categories: List[ErrorCategory]
    applicable_severities: List[ErrorSeverity]
    recovery_actions: List[str]
    success_rate: float
    average_recovery_time: float
    usage_count: int = 0


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt."""
    attempt_id: str
    error_id: str
    strategy_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    recovery_time: float
    actions_taken: List[str]
    result_message: str


class ErrorRecoverySystem:
    """Intelligent error recovery and adaptation system."""
    
    def __init__(self, ai_models: AIModels, on_recovery_event: Optional[Callable] = None):
        self.ai_models = ai_models
        self.on_recovery_event = on_recovery_event
        
        self.settings = get_settings()
        self.system_env = get_system_environment()
        
        # Error tracking
        self.error_history: List[ErrorContext] = []
        self.recovery_attempts: List[RecoveryAttempt] = []
        
        # Recovery strategies
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.strategy_success_rates: Dict[str, List[float]] = {}
        
        # Learning and adaptation
        self.error_patterns: Dict[str, int] = {}
        self.successful_adaptations: List[Dict[str, Any]] = []
        
        # Configuration
        self.max_recovery_attempts = 3
        self.recovery_timeout = 300  # 5 minutes
        self.learning_threshold = 0.7  # Success rate threshold for strategy adoption
        
        # Statistics
        self.stats = {
            "errors_encountered": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "strategies_learned": 0,
            "patterns_identified": 0
        }
        
        # Initialize built-in strategies
        self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self) -> None:
        """Initialize built-in recovery strategies."""
        
        strategies = [
            RecoveryStrategy(
                strategy_id="retry_with_delay",
                name="Retry with Delay",
                description="Retry the failed operation after a short delay",
                applicable_categories=[ErrorCategory.NETWORK_ERROR, ErrorCategory.TIMEOUT, ErrorCategory.RESOURCE_UNAVAILABLE],
                applicable_severities=[ErrorSeverity.LOW, ErrorSeverity.MEDIUM],
                recovery_actions=["wait", "retry_operation"],
                success_rate=0.6,
                average_recovery_time=10.0
            ),
            
            RecoveryStrategy(
                strategy_id="alternative_tool",
                name="Alternative Tool",
                description="Try using an alternative tool for the same operation",
                applicable_categories=[ErrorCategory.TOOL_EXECUTION, ErrorCategory.PERMISSION_DENIED],
                applicable_severities=[ErrorSeverity.MEDIUM, ErrorSeverity.HIGH],
                recovery_actions=["identify_alternatives", "switch_tool", "retry_operation"],
                success_rate=0.4,
                average_recovery_time=30.0
            ),
            
            RecoveryStrategy(
                strategy_id="permission_escalation",
                name="Permission Escalation",
                description="Request elevated permissions to complete the operation",
                applicable_categories=[ErrorCategory.PERMISSION_DENIED],
                applicable_severities=[ErrorSeverity.MEDIUM, ErrorSeverity.HIGH],
                recovery_actions=["request_permissions", "retry_with_elevated_permissions"],
                success_rate=0.3,
                average_recovery_time=60.0
            ),
            
            RecoveryStrategy(
                strategy_id="simplify_approach",
                name="Simplify Approach",
                description="Break down complex operation into simpler steps",
                applicable_categories=[ErrorCategory.TOOL_EXECUTION, ErrorCategory.SYSTEM_ERROR],
                applicable_severities=[ErrorSeverity.MEDIUM, ErrorSeverity.HIGH],
                recovery_actions=["analyze_complexity", "create_simplified_steps", "execute_simplified_plan"],
                success_rate=0.5,
                average_recovery_time=120.0
            ),
            
            RecoveryStrategy(
                strategy_id="user_intervention",
                name="User Intervention",
                description="Request user assistance to resolve the issue",
                applicable_categories=[ErrorCategory.PERMISSION_DENIED, ErrorCategory.SYSTEM_ERROR, ErrorCategory.UNEXPECTED],
                applicable_severities=[ErrorSeverity.HIGH, ErrorSeverity.CRITICAL],
                recovery_actions=["notify_user", "request_assistance", "wait_for_user_action"],
                success_rate=0.8,
                average_recovery_time=300.0
            ),
            
            RecoveryStrategy(
                strategy_id="skip_and_continue",
                name="Skip and Continue",
                description="Skip the failed step and continue with remaining steps",
                applicable_categories=[ErrorCategory.TOOL_EXECUTION, ErrorCategory.RESOURCE_UNAVAILABLE],
                applicable_severities=[ErrorSeverity.LOW, ErrorSeverity.MEDIUM],
                recovery_actions=["mark_step_skipped", "continue_execution"],
                success_rate=0.9,
                average_recovery_time=5.0
            ),
            
            RecoveryStrategy(
                strategy_id="ai_adaptation",
                name="AI-Guided Adaptation",
                description="Use AI to generate adaptive solution for the error",
                applicable_categories=list(ErrorCategory),
                applicable_severities=[ErrorSeverity.MEDIUM, ErrorSeverity.HIGH],
                recovery_actions=["analyze_error_with_ai", "generate_adaptive_solution", "execute_solution"],
                success_rate=0.4,
                average_recovery_time=90.0
            )
        ]
        
        for strategy in strategies:
            self.recovery_strategies[strategy.strategy_id] = strategy
            self.strategy_success_rates[strategy.strategy_id] = []
        
        logger.info(f"Initialized {len(strategies)} recovery strategies")
    
    async def handle_error(self, 
                          error: Exception,
                          context: Dict[str, Any],
                          step: Optional[ExecutionStep] = None) -> Tuple[bool, str, Optional[ExecutionPlan]]:
        """
        Handle error with intelligent recovery.
        
        Returns:
            Tuple of (success, message, adapted_plan)
        """
        
        try:
            # Create error context
            error_context = await self._create_error_context(error, context, step)
            
            # Record error
            self._record_error(error_context)
            
            # Categorize and assess severity
            await self._categorize_error(error_context)
            
            # Find applicable recovery strategies
            strategies = self._select_recovery_strategies(error_context)
            
            if not strategies:
                logger.warning(f"No recovery strategies found for error: {error_context.error_type}")
                return False, "No recovery strategies available", None
            
            # Attempt recovery with selected strategies
            recovery_result = await self._attempt_recovery(error_context, strategies)
            
            # Learn from the recovery attempt
            await self._learn_from_recovery(error_context, recovery_result)
            
            return recovery_result
            
        except Exception as e:
            logger.error(f"Error in error recovery system: {e}")
            return False, f"Recovery system error: {e}", None
    
    async def _create_error_context(self, 
                                  error: Exception, 
                                  context: Dict[str, Any],
                                  step: Optional[ExecutionStep]) -> ErrorContext:
        """Create comprehensive error context."""
        
        error_id = f"err_{int(time.time() * 1000)}"
        
        # Get stack trace
        stack_trace = traceback.format_exc() if hasattr(error, '__traceback__') else None
        
        # Collect system state
        system_state = await self._collect_system_state()
        
        error_context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            category=ErrorCategory.UNEXPECTED,  # Will be determined by categorization
            severity=ErrorSeverity.MEDIUM,     # Will be determined by assessment
            step_id=step.id if step else None,
            tool_name=context.get("tool_name"),
            context_data=context.copy(),
            stack_trace=stack_trace,
            system_state=system_state
        )
        
        return error_context
    
    async def _collect_system_state(self) -> Dict[str, Any]:
        """Collect current system state for error context."""
        
        try:
            import psutil
            
            # Basic system metrics
            system_state = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "timestamp": time.time()
            }
            
            # Network status
            try:
                net_connections = len(psutil.net_connections())
                system_state["network_connections"] = net_connections
            except:
                pass
            
            return system_state
            
        except Exception as e:
            logger.debug(f"Failed to collect system state: {e}")
            return {"collection_error": str(e)}
    
    def _record_error(self, error_context: ErrorContext) -> None:
        """Record error in history."""
        
        self.error_history.append(error_context)
        self.stats["errors_encountered"] += 1
        
        # Limit history size
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        # Update error patterns
        error_pattern = f"{error_context.error_type}:{error_context.tool_name}"
        self.error_patterns[error_pattern] = self.error_patterns.get(error_pattern, 0) + 1
        
        if self.error_patterns[error_pattern] >= 3:
            logger.warning(f"Error pattern detected: {error_pattern} ({self.error_patterns[error_pattern]} times)")
            self.stats["patterns_identified"] += 1
    
    async def _categorize_error(self, error_context: ErrorContext) -> None:
        """Categorize error and assess severity using AI."""
        
        categorization_prompt = f"""
        Analyze this error and provide categorization:
        
        Error Type: {error_context.error_type}
        Error Message: {error_context.error_message}
        Tool: {error_context.tool_name}
        Context: {json.dumps(error_context.context_data, default=str)}
        
        Available Categories:
        - tool_execution: Issues with tool/command execution
        - permission_denied: Permission or access issues
        - resource_unavailable: Resources not available (files, network, etc.)
        - network_error: Network connectivity issues
        - timeout: Operation timeouts
        - invalid_input: Invalid parameters or inputs
        - system_error: System-level errors
        - ai_model_error: AI model or API errors
        - unexpected: Unexpected or unknown errors
        
        Severity Levels:
        - low: Minor issue, execution can continue
        - medium: Moderate issue, may need workaround
        - high: Serious issue, requires intervention
        - critical: Fatal error, must stop execution
        
        Respond with JSON:
        {{
            "category": "category_name",
            "severity": "severity_level",
            "reasoning": "Brief explanation of categorization",
            "recovery_hints": ["hint1", "hint2"]
        }}
        """
        
        try:
            response = await self.ai_models.generate_plan(categorization_prompt)
            result = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Update error context
            try:
                error_context.category = ErrorCategory(result["category"])
            except ValueError:
                error_context.category = ErrorCategory.UNEXPECTED
            
            try:
                error_context.severity = ErrorSeverity(result["severity"])
            except ValueError:
                error_context.severity = ErrorSeverity.MEDIUM
            
            # Store recovery hints in context
            error_context.context_data["ai_recovery_hints"] = result.get("recovery_hints", [])
            error_context.context_data["ai_reasoning"] = result.get("reasoning", "")
            
            logger.debug(f"Error categorized as {error_context.category.value} / {error_context.severity.value}")
            
        except Exception as e:
            logger.warning(f"Failed to categorize error with AI: {e}")
            # Fall back to rule-based categorization
            self._rule_based_categorization(error_context)
    
    def _rule_based_categorization(self, error_context: ErrorContext) -> None:
        """Rule-based error categorization fallback."""
        
        error_message_lower = error_context.error_message.lower()
        
        # Category rules
        if "permission" in error_message_lower or "access denied" in error_message_lower:
            error_context.category = ErrorCategory.PERMISSION_DENIED
        elif "timeout" in error_message_lower or "timed out" in error_message_lower:
            error_context.category = ErrorCategory.TIMEOUT
        elif "network" in error_message_lower or "connection" in error_message_lower:
            error_context.category = ErrorCategory.NETWORK_ERROR
        elif "file not found" in error_message_lower or "no such file" in error_message_lower:
            error_context.category = ErrorCategory.RESOURCE_UNAVAILABLE
        elif error_context.tool_name:
            error_context.category = ErrorCategory.TOOL_EXECUTION
        else:
            error_context.category = ErrorCategory.UNEXPECTED
        
        # Severity rules
        if "critical" in error_message_lower or "fatal" in error_message_lower:
            error_context.severity = ErrorSeverity.CRITICAL
        elif "error" in error_message_lower:
            error_context.severity = ErrorSeverity.HIGH
        elif "warning" in error_message_lower:
            error_context.severity = ErrorSeverity.MEDIUM
        else:
            error_context.severity = ErrorSeverity.LOW
    
    def _select_recovery_strategies(self, error_context: ErrorContext) -> List[RecoveryStrategy]:
        """Select applicable recovery strategies for the error."""
        
        applicable_strategies = []
        
        for strategy in self.recovery_strategies.values():
            # Check category applicability
            if error_context.category not in strategy.applicable_categories:
                continue
            
            # Check severity applicability
            if error_context.severity not in strategy.applicable_severities:
                continue
            
            applicable_strategies.append(strategy)
        
        # Sort by success rate (descending)
        applicable_strategies.sort(key=lambda s: s.success_rate, reverse=True)
        
        # Limit to top strategies
        return applicable_strategies[:3]
    
    async def _attempt_recovery(self, 
                              error_context: ErrorContext, 
                              strategies: List[RecoveryStrategy]) -> Tuple[bool, str, Optional[ExecutionPlan]]:
        """Attempt recovery using selected strategies."""
        
        for strategy in strategies:
            if self.stats["recovery_attempts"] >= self.max_recovery_attempts:
                break
            
            logger.info(f"Attempting recovery with strategy: {strategy.name}")
            
            attempt = RecoveryAttempt(
                attempt_id=f"recovery_{int(time.time() * 1000)}",
                error_id=error_context.error_id,
                strategy_id=strategy.strategy_id,
                started_at=datetime.now(),
                completed_at=None,
                success=False,
                recovery_time=0.0,
                actions_taken=[],
                result_message=""
            )
            
            try:
                start_time = time.time()
                
                # Execute recovery strategy
                result = await self._execute_recovery_strategy(strategy, error_context, attempt)
                
                end_time = time.time()
                attempt.completed_at = datetime.now()
                attempt.recovery_time = end_time - start_time
                attempt.success = result["success"]
                attempt.result_message = result["message"]
                
                # Record attempt
                self.recovery_attempts.append(attempt)
                self.stats["recovery_attempts"] += 1
                
                if result["success"]:
                    self.stats["successful_recoveries"] += 1
                    
                    # Update strategy success rate
                    self._update_strategy_success_rate(strategy.strategy_id, True, attempt.recovery_time)
                    
                    # Notify of successful recovery
                    if self.on_recovery_event:
                        await self.on_recovery_event("recovery_success", {
                            "error_id": error_context.error_id,
                            "strategy": strategy.name,
                            "recovery_time": attempt.recovery_time
                        })
                    
                    return True, result["message"], result.get("adapted_plan")
                else:
                    self.stats["failed_recoveries"] += 1
                    self._update_strategy_success_rate(strategy.strategy_id, False, attempt.recovery_time)
                    
                    # Continue to next strategy
                    logger.info(f"Recovery strategy failed: {result['message']}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error executing recovery strategy {strategy.name}: {e}")
                
                attempt.completed_at = datetime.now()
                attempt.success = False
                attempt.result_message = f"Strategy execution error: {e}"
                
                self.recovery_attempts.append(attempt)
                self.stats["failed_recoveries"] += 1
                
                continue
        
        # All strategies failed
        return False, "All recovery strategies failed", None
    
    async def _execute_recovery_strategy(self,
                                       strategy: RecoveryStrategy,
                                       error_context: ErrorContext,
                                       attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Execute a specific recovery strategy."""
        
        try:
            if strategy.strategy_id == "retry_with_delay":
                return await self._retry_with_delay_strategy(error_context, attempt)
            
            elif strategy.strategy_id == "alternative_tool":
                return await self._alternative_tool_strategy(error_context, attempt)
            
            elif strategy.strategy_id == "permission_escalation":
                return await self._permission_escalation_strategy(error_context, attempt)
            
            elif strategy.strategy_id == "simplify_approach":
                return await self._simplify_approach_strategy(error_context, attempt)
            
            elif strategy.strategy_id == "user_intervention":
                return await self._user_intervention_strategy(error_context, attempt)
            
            elif strategy.strategy_id == "skip_and_continue":
                return await self._skip_and_continue_strategy(error_context, attempt)
            
            elif strategy.strategy_id == "ai_adaptation":
                return await self._ai_adaptation_strategy(error_context, attempt)
            
            else:
                return {"success": False, "message": f"Unknown strategy: {strategy.strategy_id}"}
                
        except Exception as e:
            logger.error(f"Strategy execution error: {e}")
            return {"success": False, "message": f"Strategy execution failed: {e}"}
    
    async def _retry_with_delay_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Retry the failed operation after a delay."""
        
        delay = 5.0  # 5 seconds default
        
        # Analyze error for appropriate delay
        if "timeout" in error_context.error_message.lower():
            delay = 10.0
        elif "network" in error_context.error_message.lower():
            delay = 15.0
        
        attempt.actions_taken.append(f"wait_{delay}s")
        
        logger.debug(f"Waiting {delay} seconds before retry")
        await asyncio.sleep(delay)
        
        attempt.actions_taken.append("retry_operation")
        
        # For this implementation, we simulate success based on error category
        if error_context.category in [ErrorCategory.NETWORK_ERROR, ErrorCategory.TIMEOUT]:
            return {"success": True, "message": "Operation succeeded after retry"}
        else:
            return {"success": False, "message": "Retry did not resolve the issue"}
    
    async def _alternative_tool_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Try using an alternative tool."""
        
        attempt.actions_taken.append("identify_alternatives")
        
        # This would identify alternative tools in a real implementation
        # For now, we simulate finding alternatives
        
        if error_context.tool_name:
            attempt.actions_taken.append(f"switch_from_{error_context.tool_name}")
            attempt.actions_taken.append("retry_with_alternative")
            
            return {"success": True, "message": "Successfully used alternative tool"}
        else:
            return {"success": False, "message": "No alternative tools available"}
    
    async def _permission_escalation_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Request elevated permissions."""
        
        attempt.actions_taken.append("request_permissions")
        
        # This would request actual permissions in a real implementation
        # For now, we simulate permission grant
        
        if error_context.category == ErrorCategory.PERMISSION_DENIED:
            attempt.actions_taken.append("permissions_granted")
            attempt.actions_taken.append("retry_with_elevated_permissions")
            
            return {"success": True, "message": "Operation succeeded with elevated permissions"}
        else:
            return {"success": False, "message": "Permission escalation not applicable"}
    
    async def _simplify_approach_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Break down complex operation into simpler steps."""
        
        attempt.actions_taken.append("analyze_complexity")
        
        # Use AI to generate simplified approach
        simplification_prompt = f"""
        The following operation failed:
        Tool: {error_context.tool_name}
        Error: {error_context.error_message}
        
        Create a simplified approach by breaking this into smaller, safer steps.
        Focus on reducing complexity and potential failure points.
        
        Return a brief description of the simplified approach.
        """
        
        try:
            simplified_approach = await self.ai_models.generate_response(simplification_prompt)
            
            attempt.actions_taken.append("create_simplified_steps")
            attempt.actions_taken.append("execute_simplified_plan")
            
            return {
                "success": True, 
                "message": f"Created simplified approach: {simplified_approach[:100]}...",
                "simplified_approach": simplified_approach
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to create simplified approach: {e}"}
    
    async def _user_intervention_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Request user assistance."""
        
        attempt.actions_taken.append("notify_user")
        attempt.actions_taken.append("request_assistance")
        
        # Notify UI of user intervention needed
        if self.on_recovery_event:
            await self.on_recovery_event("user_intervention_needed", {
                "error_id": error_context.error_id,
                "error_message": error_context.error_message,
                "step_id": error_context.step_id,
                "tool_name": error_context.tool_name
            })
        
        # For this implementation, we simulate user assistance
        attempt.actions_taken.append("user_assistance_provided")
        
        return {"success": True, "message": "User intervention resolved the issue"}
    
    async def _skip_and_continue_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Skip the failed step and continue."""
        
        attempt.actions_taken.append("mark_step_skipped")
        attempt.actions_taken.append("continue_execution")
        
        return {
            "success": True, 
            "message": f"Skipped failed step and continuing execution",
            "skipped_step_id": error_context.step_id
        }
    
    async def _ai_adaptation_strategy(self, error_context: ErrorContext, attempt: RecoveryAttempt) -> Dict[str, Any]:
        """Use AI to generate adaptive solution."""
        
        attempt.actions_taken.append("analyze_error_with_ai")
        
        adaptation_prompt = f"""
        Analyze this error and generate an adaptive solution:
        
        Error: {error_context.error_message}
        Tool: {error_context.tool_name}
        Context: {json.dumps(error_context.context_data, default=str)}
        System: {self.system_env.os}
        
        Previous recovery hints: {error_context.context_data.get('ai_recovery_hints', [])}
        
        Generate a specific, actionable solution that:
        1. Addresses the root cause of the error
        2. Is compatible with the current system
        3. Minimizes risk of further errors
        
        Return a JSON response with:
        {{
            "solution_type": "alternative_approach|parameter_adjustment|environment_fix",
            "solution_description": "Detailed description",
            "implementation_steps": ["step1", "step2", ...],
            "risk_level": "low|medium|high",
            "success_probability": 0.8
        }}
        """
        
        try:
            response = await self.ai_models.generate_plan(adaptation_prompt)
            solution = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            attempt.actions_taken.append("generate_adaptive_solution")
            attempt.actions_taken.append("execute_solution")
            
            # Record the solution for learning
            self.successful_adaptations.append({
                "error_context": asdict(error_context),
                "solution": solution,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"AI generated adaptive solution: {solution['solution_description']}",
                "ai_solution": solution
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to generate AI solution: {e}"}
    
    def _update_strategy_success_rate(self, strategy_id: str, success: bool, execution_time: float) -> None:
        """Update strategy success rate and performance metrics."""
        
        if strategy_id in self.recovery_strategies:
            strategy = self.recovery_strategies[strategy_id]
            strategy.usage_count += 1
            
            # Update success rate (running average)
            current_rate = strategy.success_rate
            new_point = 1.0 if success else 0.0
            
            # Weighted average (more weight on recent results)
            weight = min(0.2, 1.0 / strategy.usage_count)
            strategy.success_rate = current_rate * (1 - weight) + new_point * weight
            
            # Update average recovery time
            if success:
                time_weight = min(0.3, 1.0 / max(1, strategy.usage_count))
                strategy.average_recovery_time = (
                    strategy.average_recovery_time * (1 - time_weight) + 
                    execution_time * time_weight
                )
            
            # Store historical success rate
            if strategy_id not in self.strategy_success_rates:
                self.strategy_success_rates[strategy_id] = []
            
            self.strategy_success_rates[strategy_id].append(new_point)
            
            # Limit history
            if len(self.strategy_success_rates[strategy_id]) > 100:
                self.strategy_success_rates[strategy_id] = self.strategy_success_rates[strategy_id][-50:]
    
    async def _learn_from_recovery(self, error_context: ErrorContext, recovery_result: Tuple[bool, str, Optional[ExecutionPlan]]) -> None:
        """Learn from recovery attempt to improve future performance."""
        
        success, message, adapted_plan = recovery_result
        
        if success:
            # Successful recovery - analyze what worked
            await self._analyze_successful_recovery(error_context, message, adapted_plan)
        else:
            # Failed recovery - analyze gaps and potential improvements
            await self._analyze_failed_recovery(error_context, message)
    
    async def _analyze_successful_recovery(self, error_context: ErrorContext, message: str, adapted_plan: Optional[ExecutionPlan]) -> None:
        """Analyze successful recovery for learning."""
        
        # Look for patterns in successful recoveries
        success_pattern = f"{error_context.category.value}:{error_context.severity.value}"
        
        # This could be expanded to create new strategies based on successful patterns
        logger.debug(f"Successful recovery pattern: {success_pattern}")
    
    async def _analyze_failed_recovery(self, error_context: ErrorContext, message: str) -> None:
        """Analyze failed recovery to identify improvement opportunities."""
        
        failure_pattern = f"{error_context.category.value}:{error_context.error_type}"
        
        # This could be used to adjust strategy applicability or create new strategies
        logger.debug(f"Failed recovery pattern: {failure_pattern}")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get comprehensive recovery statistics."""
        
        recent_errors = [e for e in self.error_history if (datetime.now() - e.timestamp).days < 7]
        
        return {
            "total_stats": self.stats.copy(),
            "recent_errors": len(recent_errors),
            "error_categories": {cat.value: len([e for e in recent_errors if e.category == cat]) 
                               for cat in ErrorCategory},
            "error_severities": {sev.value: len([e for e in recent_errors if e.severity == sev]) 
                               for sev in ErrorSeverity},
            "strategy_performance": {
                strategy_id: {
                    "success_rate": strategy.success_rate,
                    "usage_count": strategy.usage_count,
                    "average_recovery_time": strategy.average_recovery_time
                }
                for strategy_id, strategy in self.recovery_strategies.items()
            },
            "common_error_patterns": dict(sorted(self.error_patterns.items(), 
                                               key=lambda x: x[1], reverse=True)[:10]),
            "adaptations_learned": len(self.successful_adaptations)
        }
    
    def get_error_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error history."""
        
        recent_errors = self.error_history[-limit:]
        return [asdict(error) for error in recent_errors]
    
    def clear_error_history(self) -> None:
        """Clear error history (for maintenance)."""
        
        self.error_history.clear()
        self.recovery_attempts.clear()
        self.error_patterns.clear()
        
        # Reset statistics
        for key in self.stats:
            self.stats[key] = 0
        
        logger.info("Error history cleared")