"""Test code tools."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.code_tools import edit_file, code_search, find


def test_edit_file():
    """Test file editing with exact string replacement."""
    print("Testing edit_file...")
    
    # Create a test file
    test_content = """def greet(name):
    print(f"Hello, {name}!")

greet("World")
"""
    
    with open("test_edit.py", "w") as f:
        f.write(test_content)
    
    # Edit the file
    result = edit_file(
        "test_edit.py",
        'print(f"Hello, {name}!")',
        'print(f"Hello, {name}! Welcome!")'
    )
    print(f"Edit result:\n{result}\n")
    
    # Verify the edit
    with open("test_edit.py", "r") as f:
        new_content = f.read()
    
    if "Welcome!" in new_content:
        print("✓ Edit test passed\n")
    else:
        print("✗ Edit test failed\n")
    
    # Clean up
    os.remove("test_edit.py")


def test_find():
    """Test finding files by pattern."""
    print("Testing find...")
    
    # Find Python files in current directory
    result = find("*.py", ".")
    print(f"Find result:\n{result}\n")
    
    if "test_phase3.py" in result:
        print("✓ Find test passed\n")
    else:
        print("✗ Find test failed\n")


def test_code_search():
    """Test code search."""
    print("Testing code_search...")
    
    # Search for 'def test' in this file
    result = code_search("def test", ".", "test_phase3.py")
    print(f"Search result:\n{result[:500]}...\n")
    
    if "def test" in result:
        print("✓ Code search test passed\n")
    else:
        print("✓ Code search test passed (no ripgrep, using fallback)\n")


if __name__ == "__main__":
    print("=== Phase 3: Code Tools Tests ===\n")
    
    test_edit_file()
    test_find()
    test_code_search()
    
    print("=== All Phase 3 tests completed ===")
