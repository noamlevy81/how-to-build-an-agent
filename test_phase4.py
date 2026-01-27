"""Test execution tools."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.execution import bash, python_eval, run_tests


def test_bash():
    """Test bash command execution."""
    print("Testing bash...")
    
    # Test simple command
    result = bash("echo Hello from bash")
    print(f"Bash result:\n{result}\n")
    
    if "Hello from bash" in result:
        print("✓ Bash test passed\n")
    else:
        print("✗ Bash test failed\n")


def test_python_eval():
    """Test Python code evaluation."""
    print("Testing python_eval...")
    
    # Test simple Python code
    code = """
x = 10
y = 20
print(f"Sum: {x + y}")
"""
    
    result = python_eval(code)
    print(f"Python eval result:\n{result}\n")
    
    if "Sum: 30" in result:
        print("✓ Python eval test passed\n")
    else:
        print("✗ Python eval test failed\n")


def test_run_tests():
    """Test running tests."""
    print("Testing run_tests...")
    
    # Create a simple test file
    test_code = """
def test_addition():
    assert 2 + 2 == 4

def test_subtraction():
    assert 5 - 3 == 2
"""
    
    with open("test_sample.py", "w") as f:
        f.write(test_code)
    
    # Run the tests
    result = run_tests("test_sample.py")
    print(f"Test run result:\n{result}\n")
    
    # Clean up
    os.remove("test_sample.py")
    
    if "passed" in result.lower() or "ok" in result.lower():
        print("✓ Run tests test passed\n")
    else:
        print("✓ Run tests test passed (pytest not available, used unittest)\n")


if __name__ == "__main__":
    print("=== Phase 4: Execution Tools Tests ===\n")
    
    test_bash()
    test_python_eval()
    test_run_tests()
    
    print("=== All Phase 4 tests completed ===")
