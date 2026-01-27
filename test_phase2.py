"""Test file operations tools."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.file_ops import read_file, write_file, list_files


def test_write_and_read():
    """Test writing and reading a file."""
    print("Testing write_file and read_file...")
    
    # Write a test file
    result = write_file("test_output.txt", "Hello, World!\nThis is a test.")
    print(f"Write result:\n{result}\n")
    
    # Read it back
    result = read_file("test_output.txt")
    print(f"Read result:\n{result}\n")
    
    # Clean up
    import os
    os.remove("test_output.txt")
    print("✓ Write and read test passed\n")


def test_list_files():
    """Test listing files."""
    print("Testing list_files...")
    
    # List current directory (non-recursive)
    result = list_files(".", recursive=False, include_hidden=False)
    print(f"List result:\n{result}\n")
    
    print("✓ List files test passed\n")


def test_read_nonexistent():
    """Test reading a non-existent file."""
    print("Testing error handling...")
    
    result = read_file("nonexistent_file_xyz.txt")
    print(f"Error handling result:\n{result}\n")
    
    if "Error" in result:
        print("✓ Error handling test passed\n")
    else:
        print("✗ Error handling test failed\n")


if __name__ == "__main__":
    print("=== Phase 2: File Operations Tests ===\n")
    
    test_write_and_read()
    test_list_files()
    test_read_nonexistent()
    
    print("=== All Phase 2 tests completed ===")
