"""Integration tools for external services and utilities.

Provides tools for integration:
- http_request: Make HTTP requests
- git: Read-only git operations
- diff: Compare files or text
- tree: Display directory structure
"""

import subprocess
import urllib.request
import urllib.error
import json
from functools import cache
from pathlib import Path
import difflib


def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    timeout: int = 30
) -> str:
    """Make an HTTP request.
    
    Args:
        url: URL to request
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Optional headers dictionary
        body: Optional request body (for POST, PUT, etc.)
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        Response body as string
        
    Example:
        >>> http_request("https://api.github.com/zen")
        "Design for failure."
    """
    try:
        req = urllib.request.Request(url, method=method)
        
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # Add body if provided
        data = None
        if body:
            data = body.encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        
        # Make request
        with urllib.request.urlopen(req, data=data, timeout=timeout) as response:
            status_code = response.status
            response_body = response.read().decode('utf-8')
            
            # Try to format JSON if possible
            try:
                json_data = json.loads(response_body)
                formatted = json.dumps(json_data, indent=2)
                return f"Status: {status_code}\n\n{formatted}"
            except json.JSONDecodeError:
                return f"Status: {status_code}\n\n{response_body}"
                
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason}\n{e.read().decode('utf-8', errors='ignore')}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason}"
    except TimeoutError:
        return f"Error: Request timed out after {timeout} seconds"
    except Exception as e:
        return f"Error making HTTP request: {str(e)}"


def git(
    command: str,
    working_dir: str | None = None
) -> str:
    """Execute read-only git commands.
    
    Args:
        command: Git command (without 'git' prefix)
        working_dir: Repository directory (default: current directory)
        
    Returns:
        Git command output
        
    Example:
        >>> git("status")
        "On branch main\\nYour branch is up to date..."
        
    Security:
        Only allows read-only operations. Commands like commit, push, pull
        are blocked for safety.
    """
    # List of allowed read-only git commands
    readonly_commands = [
        'status', 'log', 'show', 'diff', 'branch', 'tag',
        'ls-files', 'ls-tree', 'rev-parse', 'describe',
        'blame', 'reflog', 'remote', 'config --list'
    ]
    
    # Check if command is read-only
    command_parts = command.split()
    if not command_parts:
        return "Error: Empty git command"
    
    base_command = command_parts[0]
    is_readonly = any(base_command == cmd.split()[0] for cmd in readonly_commands)
    
    if not is_readonly:
        return (
            f"Error: Command 'git {base_command}' is not allowed.\n"
            f"Only read-only operations are permitted:\n" +
            "\n".join(f"  - git {cmd}" for cmd in readonly_commands)
        )
    
    try:
        result = subprocess.run(
            f"git {command}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=30
        )
        
        output = []
        if result.stdout:
            output.append(result.stdout.rstrip())
        if result.stderr:
            output.append(f"[stderr]:\n{result.stderr.rstrip()}")
        if result.returncode != 0:
            output.append(f"\n[Exit code: {result.returncode}]")
        
        return "\n".join(output) if output else "(no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except FileNotFoundError:
        return "Error: Git not found. Please install git."
    except Exception as e:
        return f"Error executing git command: {str(e)}"


def diff(
    source: str,
    target: str,
    context_lines: int = 3,
    mode: str = "unified"
) -> str:
    """Compare two files or text strings.
    
    Args:
        source: Source file path or text content
        target: Target file path or text content
        context_lines: Number of context lines (default: 3)
        mode: Diff mode - "unified" or "context" (default: unified)
        
    Returns:
        Diff output showing differences
        
    Example:
        >>> diff("file1.txt", "file2.txt")
        "--- file1.txt\\n+++ file2.txt\\n@@ -1,3 +1,3 @@..."
    """
    try:
        # Check if inputs are files or text
        source_path = Path(source)
        target_path = Path(target)
        
        if source_path.is_file() and target_path.is_file():
            # Compare files
            source_lines = source_path.read_text(encoding='utf-8').splitlines(keepends=True)
            target_lines = target_path.read_text(encoding='utf-8').splitlines(keepends=True)
            source_label = str(source_path)
            target_label = str(target_path)
        else:
            # Compare text strings
            source_lines = source.splitlines(keepends=True)
            target_lines = target.splitlines(keepends=True)
            source_label = "source"
            target_label = "target"
        
        # Generate diff
        if mode == "unified":
            diff_lines = difflib.unified_diff(
                source_lines,
                target_lines,
                fromfile=source_label,
                tofile=target_label,
                n=context_lines
            )
        else:  # context mode
            diff_lines = difflib.context_diff(
                source_lines,
                target_lines,
                fromfile=source_label,
                tofile=target_label,
                n=context_lines
            )
        
        result = ''.join(diff_lines)
        
        if not result:
            return "No differences found"
        
        return result
        
    except Exception as e:
        return f"Error generating diff: {str(e)}"


def tree(
    path: str = ".",
    max_depth: int | None = 3,
    include_hidden: bool = False,
    include_files: bool = True
) -> str:
    """Display directory structure as a tree.
    
    Args:
        path: Directory path to visualize (default: current directory)
        max_depth: Maximum depth to traverse (default: 3)
        include_hidden: Include hidden files/dirs (default: False)
        include_files: Include files, not just directories (default: True)
        
    Returns:
        Tree visualization of directory structure
        
    Example:
        >>> tree("src", max_depth=2)
        "src/\\n├── main.py\\n├── utils/\\n│   ├── helpers.py..."
    """
    try:
        dir_path = Path(path)
        
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not dir_path.is_dir():
            return f"Error: Path is not a directory: {path}"
        
        lines = [f"{dir_path.absolute()}/"]
        
        def should_include(item: Path) -> bool:
            """Check if item should be included."""
            if not include_hidden and item.name.startswith('.'):
                return False
            if not include_files and item.is_file():
                return False
            return True
        
        def add_tree_lines(current_path: Path, prefix: str = "", depth: int = 0) -> None:
            """Recursively build tree lines."""
            if max_depth is not None and depth >= max_depth:
                return
            
            try:
                items = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                items = [item for item in items if should_include(item)]
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    
                    # Determine line prefix
                    if is_last:
                        connector = "└── "
                        extension = "    "
                    else:
                        connector = "├── "
                        extension = "│   "
                    
                    # Format item
                    if item.is_dir():
                        lines.append(f"{prefix}{connector}{item.name}/")
                        # Recurse into directory
                        add_tree_lines(item, prefix + extension, depth + 1)
                    else:
                        size = item.stat().st_size
                        size_str = format_size(size)
                        lines.append(f"{prefix}{connector}{item.name} ({size_str})")
                        
            except PermissionError:
                lines.append(f"{prefix}    [Permission Denied]")
        
        add_tree_lines(dir_path)
        
        file_count = sum(1 for line in lines if not line.rstrip().endswith('/') and line != lines[0])
        dir_count = sum(1 for line in lines if line.rstrip().endswith('/')) - 1
        
        lines.append("")
        lines.append(f"{dir_count} directories, {file_count} files")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Error generating tree: {str(e)}"


@cache
def format_size(size: int) -> str:
    """Format file size in human-readable format.
    
    Cached for performance when formatting many file sizes.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"
