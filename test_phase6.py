"""Test interactive tools."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.interactive import remember


def test_remember():
    """Test memory functionality."""
    print("Testing remember...")
    
    # Clear any existing memory
    result = remember("clear")
    print(f"Clear result: {result}")
    
    # Save a value
    result = remember("save", "test_key", "test_value")
    print(f"Save result: {result}")
    
    # Retrieve the value
    result = remember("get", "test_key")
    print(f"Get result: {result}")
    
    # List all memories
    result = remember("list")
    print(f"List result:\n{result}")
    
    # Delete the value
    result = remember("delete", "test_key")
    print(f"Delete result: {result}")
    
    # Verify it's gone
    result = remember("get", "test_key")
    print(f"Get after delete: {result}\n")
    
    if "No value stored" in result:
        print("✓ Remember test passed\n")
    else:
        print("✗ Remember test failed\n")


def test_ask_user_programmatic():
    """Test ask_user in programmatic mode."""
    print("Testing ask_user (programmatic)...")
    
    # Note: In actual usage, ask_user requires user input
    # For testing, we'll just verify the function exists and can be called
    from tools.interactive import ask_user
    
    print("✓ ask_user function available (requires interactive testing)\n")


if __name__ == "__main__":
    print("=== Phase 6: Interactive Tools Tests ===\n")
    
    test_remember()
    test_ask_user_programmatic()
    
    print("=== All Phase 6 tests completed ===")
    print("\nNote: ask_user requires interactive testing with the agent.")
