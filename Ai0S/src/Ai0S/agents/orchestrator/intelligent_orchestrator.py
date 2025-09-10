"""
Intelligent Multi-Agent Orchestrator - New Implementation
Replaces the old single-agent system with intelligent recursive workflow.
Uses Commander, Verification, and Decision agents working together.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from ...backend.models.ai_models import get_ai_models, AIModels
from ...backend.core.mcp_executor import get_mcp_executor, MCPExecutor
from .recursive_workflow import RecursiveWorkflowOrchestrator, WorkflowResult
from .multi_agent_state import get_state_manager, StateManager, TaskStatus

logger = logging.getLogger(__name__)


class IntelligentOrchestrator:
    """
    New Intelligent Orchestrator using multi-agent recursive workflow.
    
    This replaces the old LangGraphOrchestrator with a more sophisticated
    system that actually understands what's happening on screen.
    """
    
    def __init__(self):
        self.ai_models: Optional[AIModels] = None
        self.mcp_executor: Optional[MCPExecutor] = None
        self.workflow_orchestrator: Optional[RecursiveWorkflowOrchestrator] = None
        self.state_manager: StateManager = get_state_manager()
        
        # UI callback for real-time updates
        self.ui_callback: Optional[Callable] = None
        
        # Performance tracking
        self.execution_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_steps": 0.0,
            "average_execution_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the intelligent orchestrator."""
        try:
            logger.info("🚀 Initializing Intelligent Multi-Agent Orchestrator")
            
            # Initialize AI models
            self.ai_models = await get_ai_models()
            logger.info("✅ AI models initialized")
            
            # Initialize MCP executor
            self.mcp_executor = get_mcp_executor()
            if not self.mcp_executor:
                from ...backend.core.mcp_executor import MCPExecutor, initialize_mcp_executor
                from ...mcp_server.server import MCPServer
                from ...backend.security.security_framework import SecurityFramework
                from ...backend.core.error_recovery import ErrorRecoverySystem
                
                mcp_server = MCPServer()
                security_framework = SecurityFramework()
                error_recovery = ErrorRecoverySystem(self.ai_models)
                self.mcp_executor = initialize_mcp_executor(mcp_server, security_framework, error_recovery)
            logger.info("✅ MCP executor initialized")
            
            # Initialize recursive workflow orchestrator
            self.workflow_orchestrator = RecursiveWorkflowOrchestrator(
                ai_models=self.ai_models,
                mcp_executor=self.mcp_executor
            )
            logger.info("✅ Recursive workflow orchestrator initialized")
            
            logger.info("🎉 Intelligent Multi-Agent Orchestrator ready!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Intelligent Orchestrator: {e}")
            raise
    
    async def execute_task(self, user_intent: str, task_id: Optional[str] = None) -> str:
        """
        Execute a task using intelligent multi-agent workflow.
        
        Args:
            user_intent: User's natural language request
            task_id: Optional task ID, generated if not provided
            
        Returns:
            Task ID for tracking
        """
        if not self.workflow_orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        logger.info(f"🎯 Starting intelligent task execution: {user_intent}")
        logger.info(f"📋 Task ID: {task_id}")
        
        # Start task execution using recursive workflow
        actual_task_id = await self.workflow_orchestrator.execute_task(user_intent, task_id)
        
        # Update stats
        self.execution_stats["total_tasks"] += 1
        
        # Send UI update (sync callback)
        if self.ui_callback:
            try:
                self.ui_callback({
                    "event_type": "task_started",
                    "task_id": actual_task_id,
                    "user_intent": user_intent,
                    "timestamp": datetime.now().isoformat(),
                    "orchestrator_type": "intelligent_multi_agent"
                })
            except Exception as e:
                logger.warning(f"UI callback failed: {e}")
        
        logger.info(f"✅ Task {actual_task_id} started with intelligent multi-agent system")
        return actual_task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task."""
        if not self.workflow_orchestrator:
            return None
        
        # Get status from workflow orchestrator
        status = await self.workflow_orchestrator.get_task_status(task_id)
        if status:
            # Add orchestrator type for identification
            status["orchestrator_type"] = "intelligent_multi_agent"
            
            # Send UI update (sync callback)
            if self.ui_callback:
                try:
                    self.ui_callback({
                        "event_type": "status_update",
                        "task_id": task_id,
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"UI status callback failed: {e}")
        
        return status
    
    def set_ui_callback(self, callback: Callable) -> None:
        """Set callback for UI updates."""
        self.ui_callback = callback
        logger.info("✅ UI callback registered with intelligent orchestrator")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get overall execution statistics."""
        # Merge with workflow orchestrator stats
        workflow_stats = {}
        if self.workflow_orchestrator:
            workflow_stats = self.workflow_orchestrator.get_workflow_stats()
        
        combined_stats = {
            **self.execution_stats,
            **workflow_stats,
            "orchestrator_type": "intelligent_multi_agent",
            "features": [
                "recursive_workflow",
                "real_time_verification", 
                "intelligent_decision_making",
                "screen_analysis",
                "adaptive_execution"
            ]
        }
        
        return combined_stats
    
    async def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task information including action history."""
        try:
            state = await self.state_manager.get_state(task_id)
            if not state:
                return None
            
            # Get action history summary
            action_summary = self.state_manager.get_action_history_summary(task_id, last_n=10)
            
            return {
                "task_id": task_id,
                "user_intent": state["user_intent"],
                "status": state["status"],
                "current_step": state["current_step"],
                "attempt_count": state["attempt_count"],
                "confidence_score": state["confidence_score"],
                "action_history_summary": action_summary,
                "error_count": len(state["error_messages"]),
                "recovery_attempts": state["error_recovery_attempts"],
                "should_continue": state["should_continue"],
                "completion_reason": state.get("completion_reason"),
                "start_time": state["start_time"],
                "execution_time": state.get("total_execution_time"),
                "orchestrator_type": "intelligent_multi_agent"
            }
            
        except Exception as e:
            logger.error(f"Failed to get task details for {task_id}: {e}")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        try:
            # Update state to stop execution
            success = await self.state_manager.update_state(task_id, {
                "should_continue": False,
                "status": TaskStatus.FAILED.value,
                "completion_reason": "Task cancelled by user"
            })
            
            if success:
                logger.info(f"✅ Task {task_id} cancelled successfully")
                
                # Send UI update (sync callback)
                if self.ui_callback:
                    try:
                        self.ui_callback({
                            "event_type": "task_cancelled",
                            "task_id": task_id,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"UI cancel callback failed: {e}")
                        
                return True
            else:
                logger.warning(f"⚠️ Failed to cancel task {task_id} - task not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cancelling task {task_id}: {e}")
            return False
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of all active tasks."""
        try:
            active_tasks = []
            
            # Get all active tasks from state manager
            for task_id, state in self.state_manager.active_tasks.items():
                if state["status"] in [TaskStatus.IN_PROGRESS.value, TaskStatus.PENDING.value]:
                    active_tasks.append({
                        "task_id": task_id,
                        "user_intent": state["user_intent"], 
                        "status": state["status"],
                        "current_step": state["current_step"],
                        "start_time": state["start_time"],
                        "confidence_score": state["confidence_score"]
                    })
            
            return active_tasks
            
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return []
    
    async def cleanup_completed_tasks(self) -> int:
        """Clean up completed tasks and return count of cleaned tasks."""
        try:
            cleanup_count = 0
            completed_tasks = []
            
            # Find completed tasks
            for task_id, state in self.state_manager.active_tasks.items():
                if state["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                    completed_tasks.append(task_id)
            
            # Clean up completed tasks
            for task_id in completed_tasks:
                success = await self.state_manager.cleanup_completed_task(task_id)
                if success:
                    cleanup_count += 1
            
            if cleanup_count > 0:
                logger.info(f"🧹 Cleaned up {cleanup_count} completed tasks")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Task cleanup failed: {e}")
            return 0


# Global orchestrator instance
_intelligent_orchestrator: Optional[IntelligentOrchestrator] = None


async def get_intelligent_orchestrator() -> IntelligentOrchestrator:
    """Get global intelligent orchestrator instance."""
    global _intelligent_orchestrator
    if _intelligent_orchestrator is None:
        _intelligent_orchestrator = IntelligentOrchestrator()
        await _intelligent_orchestrator.initialize()
    return _intelligent_orchestrator


# Backward compatibility function
async def get_orchestrator() -> IntelligentOrchestrator:
    """Backward compatibility function - returns intelligent orchestrator."""
    return await get_intelligent_orchestrator()


if __name__ == "__main__":
    # Test the intelligent orchestrator
    async def test_intelligent_orchestrator():
        orchestrator = await get_intelligent_orchestrator()
        
        print("🧪 === Testing Intelligent Multi-Agent Orchestrator ===")
        
        # Test task execution
        task_id = await orchestrator.execute_task("open google chrome and go to youtube.com")
        print(f"🎯 Started intelligent task: {task_id}")
        
        # Monitor task progress
        for i in range(30):  # Monitor for up to 30 seconds
            await asyncio.sleep(1)
            status = await orchestrator.get_task_status(task_id)
            if status:
                print(f"📊 Step {status['current_step']}: {status['status']} (confidence: {status['confidence_score']:.2f})")
                
                if status['status'] in ['completed', 'failed']:
                    print(f"🏁 Task finished: {status['status']}")
                    
                    # Get detailed results
                    details = await orchestrator.get_task_details(task_id)
                    if details:
                        print(f"📋 Final details: {details['completion_reason']}")
                        print(f"⏱️ Execution time: {details.get('execution_time', 0):.2f}s")
                    break
        
        # Show statistics
        stats = orchestrator.get_execution_stats()
        print(f"📈 Execution stats: {stats}")
    
    asyncio.run(test_intelligent_orchestrator())