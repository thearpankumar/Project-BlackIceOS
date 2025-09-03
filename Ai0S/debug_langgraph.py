#!/usr/bin/env python3
"""
Minimal LangGraph Test - Isolate Node Execution Issue
Tests if nodes are being called at all with the simplest possible setup.
"""

import asyncio
import sys
import os
from typing import TypedDict, Dict, Any

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langgraph.graph import StateGraph, END, START


class SimpleState(TypedDict):
    """Minimal state for testing."""
    task_id: str
    message: str
    step_count: int


async def simple_node_1(state: SimpleState) -> SimpleState:
    """First test node - should log and increment."""
    print(f"🔥 ENTER simple_node_1 - task_id: {state['task_id']}")
    state["message"] = "Node 1 executed"
    state["step_count"] = 1
    print(f"🔥 EXIT simple_node_1 - message: {state['message']}")
    return state


async def simple_node_2(state: SimpleState) -> SimpleState:
    """Second test node - should log and increment."""
    print(f"🔥 ENTER simple_node_2 - task_id: {state['task_id']}")
    state["message"] = "Node 2 executed"
    state["step_count"] = 2
    print(f"🔥 EXIT simple_node_2 - message: {state['message']}")
    return state


async def test_minimal_langgraph():
    """Test minimal LangGraph setup."""
    
    print("🚀 Testing Minimal LangGraph Setup")
    print("=" * 50)
    
    # Build graph
    print("📝 Building graph...")
    graph = StateGraph(SimpleState)
    
    # Add nodes
    print("➕ Adding nodes...")
    graph.add_node("node1", simple_node_1)
    graph.add_node("node2", simple_node_2)
    
    # Add edges
    print("🔗 Adding edges...")
    graph.set_entry_point("node1")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", END)
    
    # Compile
    print("⚙️  Compiling graph...")
    try:
        compiled_graph = graph.compile()
        print("✅ Graph compiled successfully")
    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        return
    
    # Test state
    initial_state: SimpleState = {
        "task_id": "test_123",
        "message": "initial",
        "step_count": 0
    }
    
    print(f"📋 Initial state: {initial_state}")
    
    # Execute with timeout
    print("🚀 Starting graph execution...")
    try:
        final_state = await asyncio.wait_for(
            compiled_graph.ainvoke(initial_state),
            timeout=10.0
        )
        
        print("✅ Graph execution completed!")
        print(f"📋 Final state: {final_state}")
        
        if final_state["step_count"] == 2:
            print("🎉 SUCCESS: Both nodes executed!")
        else:
            print(f"⚠️  PARTIAL: Only {final_state['step_count']} nodes executed")
            
    except asyncio.TimeoutError:
        print("⏰ TIMEOUT: Graph execution hanging - nodes not being called!")
        return
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        return


async def main():
    """Main entry point."""
    try:
        await test_minimal_langgraph()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Minimal LangGraph Node Execution Test")
    print("Testing if nodes are called at all...")
    print()
    
    asyncio.run(main())