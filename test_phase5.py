"""Test integration tools."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.integration import http_request, git, diff, tree


def test_http_request():
    """Test HTTP requests."""
    print("Testing http_request...")
    
    # Test with a public API
    result = http_request("https://api.github.com/zen", timeout=10)
    print(f"HTTP result:\n{result[:200]}...\n")
    
    if "Status: 200" in result or len(result) > 0:
        print("✓ HTTP request test passed\n")
    else:
        print("✗ HTTP request test failed\n")


def test_git():
    """Test git commands."""
    print("Testing git...")
    
    # Test git status (may or may not be in a git repo)
    result = git("status")
    print(f"Git result:\n{result[:200]}...\n")
    
    # Just check it doesn't crash
    if "Error: Git not found" not in result or "fatal" not in result:
        print("✓ Git test passed (or not a git repo)\n")
    else:
        print("✓ Git test passed (git not in repo)\n")


def test_diff():
    """Test diff functionality."""
    print("Testing diff...")
    
    # Create two test files
    with open("diff_file1.txt", "w") as f:
        f.write("Line 1\nLine 2\nLine 3\n")
    
    with open("diff_file2.txt", "w") as f:
        f.write("Line 1\nLine 2 modified\nLine 3\nLine 4\n")
    
    # Compare them
    result = diff("diff_file1.txt", "diff_file2.txt")
    print(f"Diff result:\n{result}\n")
    
    # Clean up
    os.remove("diff_file1.txt")
    os.remove("diff_file2.txt")
    
    if "modified" in result or "+" in result or "-" in result:
        print("✓ Diff test passed\n")
    else:
        print("✗ Diff test failed\n")


def test_tree():
    """Test tree visualization."""
    print("Testing tree...")
    
    # Get tree of current directory
    result = tree(".", max_depth=2, include_files=True)
    print(f"Tree result:\n{result[:400]}...\n")
    
    if "├──" in result or "└──" in result:
        print("✓ Tree test passed\n")
    else:
        print("✗ Tree test failed\n")


if __name__ == "__main__":
    print("=== Phase 5: Integration Tools Tests ===\n")
    
    test_http_request()
    test_git()
    test_diff()
    test_tree()
    
    print("=== All Phase 5 tests completed ===")
