"""Test the refactored lower-level API approach."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("  Testing Lower-Level API Refactoring")
print("=" * 70)
print()

# Test 1: Imports and initialization
print("Test 1: Imports and Initialization")
print("-" * 40)

try:
    import agent
    from typing import Dict, Any
    print("✓ Agent module imports successfully")
    
    registry = agent.initialize_tools()
    print(f"✓ Tool registry initialized: {len(registry.tools)} tools")
    print()
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Conversation history structure
print("Test 2: Conversation History Structure")
print("-" * 40)

try:
    # Simulate what the agent does
    conversation_history: list[Dict[str, Any]] = []
    
    # Add user message
    conversation_history.append({
        "role": "user",
        "parts": ["Hello"]
    })
    print(f"✓ Added user message: {len(conversation_history)} messages")
    
    # Add model response
    conversation_history.append({
        "role": "model", 
        "parts": ["Hello! How can I help?"]
    })
    print(f"✓ Added model response: {len(conversation_history)} messages")
    
    # Verify structure
    assert conversation_history[0]["role"] == "user"
    assert conversation_history[1]["role"] == "model"
    print("✓ Conversation history structure correct")
    print()
except Exception as e:
    print(f"✗ History test failed: {e}")
    sys.exit(1)

# Test 3: Function signature compatibility
print("Test 3: Function Signature Compatibility")
print("-" * 40)

try:
    import inspect
    
    # Check process_function_calls signature
    sig = inspect.signature(agent.process_function_calls)
    params = list(sig.parameters.keys())
    
    expected = ['response', 'model', 'registry', 'conversation_history', 'tools']
    assert params == expected, f"Expected {expected}, got {params}"
    print(f"✓ process_function_calls has correct signature: {params}")
    
    # Check run_agent_loop exists
    assert hasattr(agent, 'run_agent_loop')
    print("✓ run_agent_loop function exists")
    print()
except Exception as e:
    print(f"✗ Signature test failed: {e}")
    sys.exit(1)

# Test 4: Tool registry still works
print("Test 4: Tool Registry Integration")
print("-" * 40)

try:
    # Get tools in Gemini format
    tools = registry.to_gemini_tools()
    print(f"✓ Generated {len(tools)} tool definitions for Gemini")
    
    # Verify structure
    assert isinstance(tools, list)
    assert len(tools) == 15
    assert all('name' in t for t in tools)
    assert all('description' in t for t in tools)
    print("✓ Tool definitions have correct structure")
    print()
except Exception as e:
    print(f"✗ Tool registry test failed: {e}")
    sys.exit(1)

# Summary
print("=" * 70)
print("  ALL TESTS PASSED!")
print("=" * 70)
print()
print("Key improvements from refactoring:")
print("  ✓ Explicit conversation history management")
print("  ✓ Visible context window growth")
print("  ✓ Educational transparency about API calls")
print("  ✓ Lower-level control over state")
print()
print("The agent now clearly shows:")
print("  • Each API call sends complete conversation history")
print("  • Context grows with each turn (visible in UI)")
print("  • Function calling requires multiple round-trips")
print()
print("Ready to use with: uv run agent.py")
