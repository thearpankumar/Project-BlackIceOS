#!/usr/bin/env python3
"""
Agent State Test - Test our exact AgentState TypedDict
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import TypedDict, Dict, Any, Optional, List

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langgraph.graph import StateGraph, END, START


class AgentState(TypedDict):
    """Exact copy of our AgentState for testing."""
    # Task Information
    task_id: str
    user_intent: str
    original_request: str
    
    # Execution State
    execution_plan: Optional[Dict[str, Any]]
    current_step_index: int
    current_step: Optional[Dict[str, Any]]
    execution_status: str
    
    # Context & Environment
    screen_state: Optional[Dict[str, Any]]
    system_context: Dict[str, Any]
    previous_actions: List[Dict[str, Any]]
    
    # Analysis & Monitoring
    screen_analysis: Optional[Dict[str, Any]]
    confidence_score: float
    retry_count: int
    adaptation_history: List[Dict[str, Any]]
    
    # Communication
    messages: List[Dict[str, Any]]
    ui_updates: List[Dict[str, Any]]
    error_messages: List[str]
    
    # Performance
    start_time: str
    step_timings: List[float]
    total_execution_time: Optional[float]


async def test_receive_input(state: AgentState) -> AgentState:
    """Test first node with our AgentState."""
    print(f"🔥 ENTER test_receive_input - task_id: {state['task_id']}")
    state["execution_status"] = "in_progress"
    state["messages"].append({"role": "human", "content": state["user_intent"]})
    print(f"🔥 EXIT test_receive_input - status: {state['execution_status']}")
    return state


async def test_complete_task(state: AgentState) -> AgentState:
    """Test completion node."""
    print(f"🔥 ENTER test_complete_task - task_id: {state['task_id']}")
    state["execution_status"] = "completed"
    print(f"🔥 EXIT test_complete_task - status: {state['execution_status']}")
    return state


async def test_agent_state():
    """Test our AgentState with minimal logic."""
    
    print("🚀 Testing Our AgentState with LangGraph")
    print("=" * 50)
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("receive_input", test_receive_input)
    graph.add_node("complete_task", test_complete_task)
    
    graph.set_entry_point("receive_input")
    graph.add_edge("receive_input", "complete_task")
    graph.add_edge("complete_task", END)
    
    print("✅ Graph built and compiled")
    compiled_graph = graph.compile()
    
    # Create initial state exactly like our system
    initial_state: AgentState = {
        "task_id": "test_agent_state",
        "user_intent": "test command",
        "original_request": "test command",
        "execution_plan": None,
        "current_step_index": 0,
        "current_step": None,
        "execution_status": "pending",
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
    
    print(f"📋 Initial state created with task_id: {initial_state['task_id']}")
    
    # Execute
    print("🚀 Starting graph execution...")
    try:
        final_state = await asyncio.wait_for(
            compiled_graph.ainvoke(initial_state),
            timeout=10.0
        )
        
        print("✅ Graph execution completed!")
        print(f"📋 Final status: {final_state['execution_status']}")
        print(f"📋 Messages count: {len(final_state['messages'])}")
        
        if final_state["execution_status"] == "completed":
            print("🎉 SUCCESS: AgentState works with LangGraph!")
        else:
            print(f"⚠️  Issue: Status is {final_state['execution_status']}")
            
    except asyncio.TimeoutError:
        print("⏰ TIMEOUT: AgentState causing hanging!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent_state())