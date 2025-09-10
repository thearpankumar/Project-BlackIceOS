"""
Multi-Agent State Management System for Recursive AI Workflow
Handles shared state, action history, and inter-agent communication.
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict
from enum import Enum
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

import logging
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_USER_INPUT = "requires_user_input"


class ActionType(Enum):
    """Types of actions that can be performed."""
    COMMAND = "command"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    VERIFY = "verify"
    TERMINAL = "terminal"
    WEB_NAVIGATE = "web_navigate"
    WEB_ANALYZE = "web_analyze"


@dataclass
class ActionRecord:
    """Record of a single action taken."""
    action_id: str
    timestamp: str
    action_type: ActionType
    command: str
    expected_result: str
    actual_result: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None
    screenshot_before: Optional[bytes] = None
    screenshot_after: Optional[bytes] = None
    agent_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Handle non-serializable types
        data['action_type'] = self.action_type.value
        if self.screenshot_before:
            data['screenshot_before'] = "<binary_data>"
        if self.screenshot_after:
            data['screenshot_after'] = "<binary_data>"
        return data


@dataclass
class ScreenState:
    """Current screen state analysis."""
    timestamp: str
    screenshot: Optional[bytes]
    applications: List[str]
    ui_elements: List[Dict[str, Any]]
    text_content: List[str]
    clickable_elements: List[Dict[str, Any]]
    unexpected_elements: List[Dict[str, Any]]
    confidence_score: float
    analysis_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.screenshot:
            data['screenshot'] = "<binary_data>"
        return data


class MultiAgentState(TypedDict):
    """Shared state between all agents in the recursive workflow."""
    
    # Task Information
    task_id: str
    user_intent: str
    original_request: str
    start_time: str
    
    # Execution State
    status: str  # TaskStatus
    current_step: int
    max_attempts: int
    attempt_count: int
    
    # Action History
    action_history: List[Dict[str, Any]]  # ActionRecord dicts
    current_screen_state: Optional[Dict[str, Any]]  # ScreenState dict
    previous_screen_state: Optional[Dict[str, Any]]  # ScreenState dict
    
    # Agent Communication
    commander_last_decision: Optional[str]
    verification_result: Optional[Dict[str, Any]]
    decision_reasoning: Optional[str]
    
    # Context and Memory
    execution_context: Dict[str, Any]
    learned_patterns: List[str]
    error_recovery_attempts: int
    
    # Performance Tracking
    total_execution_time: Optional[float]
    step_timings: List[float]
    error_messages: List[str]
    
    # Loop Control
    should_continue: bool
    completion_reason: Optional[str]
    confidence_score: float


class StateManager:
    """Manages multi-agent shared state and provides utilities."""
    
    def __init__(self):
        self.active_tasks: Dict[str, MultiAgentState] = {}
        self._lock = asyncio.Lock()
    
    def create_initial_state(self, user_intent: str, task_id: Optional[str] = None) -> str:
        """Create initial state for a new task."""
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        initial_state: MultiAgentState = {
            "task_id": task_id,
            "user_intent": user_intent,
            "original_request": user_intent,
            "start_time": datetime.now().isoformat(),
            
            "status": TaskStatus.PENDING.value,
            "current_step": 0,
            "max_attempts": 50,  # Maximum recursive attempts
            "attempt_count": 0,
            
            "action_history": [],
            "current_screen_state": None,
            "previous_screen_state": None,
            
            "commander_last_decision": None,
            "verification_result": None,
            "decision_reasoning": None,
            
            "execution_context": {},
            "learned_patterns": [],
            "error_recovery_attempts": 0,
            
            "total_execution_time": None,
            "step_timings": [],
            "error_messages": [],
            
            "should_continue": True,
            "completion_reason": None,
            "confidence_score": 0.0
        }
        
        self.active_tasks[task_id] = initial_state
        logger.info(f"Created initial state for task {task_id}")
        return task_id
    
    async def get_state(self, task_id: str) -> Optional[MultiAgentState]:
        """Get current state for a task."""
        # Simple non-blocking access for now
        return self.active_tasks.get(task_id)
    
    async def update_state(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update state with new data."""
        if task_id not in self.active_tasks:
            return False
        
        state = self.active_tasks[task_id]
        for key, value in updates.items():
            if key in state:
                state[key] = value
            else:
                logger.warning(f"Attempted to update unknown state key: {key}")
        
        logger.debug(f"Updated state for task {task_id}: {list(updates.keys())}")
        return True
    
    async def add_action_record(self, task_id: str, action: ActionRecord) -> bool:
        """Add a new action record to the history."""
        if task_id not in self.active_tasks:
            return False
        
        state = self.active_tasks[task_id]
        state["action_history"].append(action.to_dict())
        state["current_step"] += 1
        
        logger.info(f"Added action record for task {task_id}: {action.command}")
        return True
    
    async def update_screen_state(self, task_id: str, screen_state: ScreenState) -> bool:
        """Update current screen state."""
        if task_id not in self.active_tasks:
            return False
        
        state = self.active_tasks[task_id]
        # Move current to previous
        state["previous_screen_state"] = state["current_screen_state"]
        # Set new current
        state["current_screen_state"] = screen_state.to_dict()
        
        logger.debug(f"Updated screen state for task {task_id}")
        return True
    
    def get_action_history_summary(self, task_id: str, last_n: int = 5) -> str:
        """Get a summary of recent actions for context."""
        if task_id not in self.active_tasks:
            return "No task found"
        
        state = self.active_tasks[task_id]
        recent_actions = state["action_history"][-last_n:]
        
        if not recent_actions:
            return "No actions taken yet"
        
        summary = []
        for action in recent_actions:
            status = "✅" if action["success"] else "❌"
            summary.append(f"{status} Step {action.get('action_id', 'unknown')}: {action['command']}")
        
        return "\n".join(summary)
    
    def should_continue_execution(self, task_id: str) -> bool:
        """Check if execution should continue."""
        if task_id not in self.active_tasks:
            return False
        
        state = self.active_tasks[task_id]
        
        # Check basic continue flag
        if not state["should_continue"]:
            return False
        
        # Check maximum attempts
        if state["attempt_count"] >= state["max_attempts"]:
            logger.warning(f"Task {task_id} reached maximum attempts")
            return False
        
        # Check status
        if state["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
            return False
        
        return True
    
    def get_task_context_for_agent(self, task_id: str) -> Dict[str, Any]:
        """Get relevant context for agents to make decisions."""
        if task_id not in self.active_tasks:
            return {}
        
        state = self.active_tasks[task_id]
        
        return {
            "task_id": task_id,
            "user_intent": state["user_intent"],
            "current_step": state["current_step"],
            "attempt_count": state["attempt_count"],
            "recent_actions": self.get_action_history_summary(task_id),
            "current_screen": state["current_screen_state"],
            "previous_screen": state["previous_screen_state"],
            "error_messages": state["error_messages"][-3:],  # Last 3 errors
            "confidence_score": state["confidence_score"],
            "learned_patterns": state["learned_patterns"]
        }
    
    async def cleanup_completed_task(self, task_id: str) -> bool:
        """Clean up completed task state."""
        async with self._lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                logger.info(f"Cleaned up completed task {task_id}")
                return True
            return False
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get overall execution statistics."""
        total_tasks = len(self.active_tasks)
        completed_tasks = sum(1 for state in self.active_tasks.values() 
                            if state["status"] == TaskStatus.COMPLETED.value)
        failed_tasks = sum(1 for state in self.active_tasks.values() 
                         if state["status"] == TaskStatus.FAILED.value)
        
        return {
            "active_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "average_steps": sum(state["current_step"] for state in self.active_tasks.values()) / max(total_tasks, 1)
        }


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager