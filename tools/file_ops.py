"""File operation tools for the coding agent.

Provides basic file system operations:
- read_file: Read file contents
- write_file: Write content to a file
- list_files: List directory contents
"""

import os
from functools import cache
from pathlib import Path


@cache
def _format_size(size: int) -> str:
    """Format file size in human-readable format.
    
    Cached for performance when formatting many file sizes.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"


def read_file(path: str) -> str:
    """Read contents of a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        File contents as a string
        
    Example:
        >>> read_file("README.md")
        "# My Project\\n\\nDescription..."
    """
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            return f"Error: File not found: {path}"
        
        if not file_path.is_file():
            return f"Error: Path is not a file: {path}"
        
        content = file_path.read_text(encoding='utf-8')
        
        line_count = len(content.splitlines())
        size = len(content)
        
        return (
            f"File: {path}\n"
            f"Lines: {line_count}\n"
            f"Size: {size} bytes\n"
            f"\n{content}"
        )
        
    except PermissionError:
        return f"Error: Permission denied reading file: {path}"
    except UnicodeDecodeError:
        return f"Error: File appears to be binary: {path}"
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"


def write_file(path: str, content: str, create_dirs: bool = True) -> str:
    """Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
        create_dirs: Whether to create parent directories if they don't exist
        
    Returns:
        Success or error message
        
    Example:
        >>> write_file("output.txt", "Hello, World!")
        "✓ Successfully wrote 13 bytes to output.txt"
    """
    try:
        file_path = Path(path)
        
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not file_path.parent.exists():
            return f"Error: Parent directory does not exist: {file_path.parent}"
        
        file_path.write_text(content, encoding='utf-8')
        
        size = len(content)
        line_count = len(content.splitlines())
        
        return (
            f"✓ Successfully wrote to {path}\n"
            f"Lines: {line_count}\n"
            f"Size: {size} bytes"
        )
        
    except PermissionError:
        return f"Error: Permission denied writing to file: {path}"
    except Exception as e:
        return f"Error writing file {path}: {str(e)}"


def list_files(
    path: str = ".",
    recursive: bool = False,
    include_hidden: bool = False,
    max_depth: int | None = None
) -> str:
    """List files and directories.
    
    Args:
        path: Directory path to list (default: current directory)
        recursive: Whether to list recursively
        include_hidden: Whether to include hidden files (starting with .)
        max_depth: Maximum depth for recursive listing (None = unlimited)
        
    Returns:
        Formatted list of files and directories
        
    Example:
        >>> list_files("src")
        "src/\\n  main.py\\n  utils.py\\n  tests/"
    """
    try:
        dir_path = Path(path)
        
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not dir_path.is_dir():
            return f"Error: Path is not a directory: {path}"
        
        results = []
        
        def should_include(item_path: Path) -> bool:
            """Check if an item should be included in results."""
            if not include_hidden and item_path.name.startswith('.'):
                return False
            return True
        
        def list_directory(current_path: Path, depth: int = 0, prefix: str = "") -> None:
            """Recursively list directory contents."""
            if max_depth is not None and depth > max_depth:
                return
            
            try:
                items = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                
                for item in items:
                    if not should_include(item):
                        continue
                    
                    indent = "  " * depth
                    marker = "📁 " if item.is_dir() else "📄 "
                    relative = item.relative_to(dir_path)
                    
                    if item.is_file():
                        size = item.stat().st_size
                        size_str = _format_size(size)
                        results.append(f"{indent}{marker}{relative} ({size_str})")
                    else:
                        results.append(f"{indent}{marker}{relative}/")
                    
                    if recursive and item.is_dir():
                        list_directory(item, depth + 1, prefix + "  ")
                        
            except PermissionError:
                results.append(f"{prefix}  [Permission Denied]")
        
        results.append(f"Directory: {dir_path.absolute()}")
        results.append("")
        list_directory(dir_path)
        
        if not results[2:]:  # Check if empty (after header)
            results.append("(empty directory)")
        
        file_count = sum(1 for r in results if "📄" in r)
        dir_count = sum(1 for r in results if "📁" in r)
        results.append("")
        results.append(f"Total: {file_count} files, {dir_count} directories")
        
        return "\n".join(results)
        
    except PermissionError:
        return f"Error: Permission denied accessing directory: {path}"
    except Exception as e:
        return f"Error listing directory {path}: {str(e)}"
