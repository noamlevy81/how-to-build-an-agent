"""Code manipulation and search tools.

Provides tools for working with code:
- edit_file: Edit files using exact string replacement
- code_search: Search code using patterns
- find: Find files by name pattern (glob)
"""

import subprocess
from functools import cache
from pathlib import Path
import glob as glob_module


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing exact text.
    
    Uses exact string matching for surgical edits. The old_text must match
    exactly (including whitespace) for the replacement to occur.
    
    Args:
        path: Path to the file to edit
        old_text: Exact text to find and replace
        new_text: Text to replace with
        
    Returns:
        Success or error message
        
    Example:
        >>> edit_file("main.py", "print('Hello')", "print('Hello, World!')")
        "✓ Successfully replaced 1 occurrence in main.py"
    """
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            return f"Error: File not found: {path}"
        
        if not file_path.is_file():
            return f"Error: Path is not a file: {path}"
        
        content = file_path.read_text(encoding='utf-8')
        
        if old_text not in content:
            return (
                f"Error: Could not find exact match in {path}\n"
                f"Searched for:\n{old_text[:100]}..."
                if len(old_text) > 100 else
                f"Searched for:\n{old_text}"
            )
        
        count = content.count(old_text)
        
        if count > 1:
            return (
                f"Error: Found {count} occurrences of the text in {path}\n"
                f"Please make old_text more specific to match exactly one occurrence."
            )
        
        new_content = content.replace(old_text, new_text)
        
        file_path.write_text(new_content, encoding='utf-8')
        
        old_lines = len(old_text.splitlines())
        new_lines = len(new_text.splitlines())
        
        return (
            f"✓ Successfully edited {path}\n"
            f"Replaced {old_lines} line(s) with {new_lines} line(s)"
        )
        
    except PermissionError:
        return f"Error: Permission denied editing file: {path}"
    except Exception as e:
        return f"Error editing file {path}: {str(e)}"


def code_search(
    pattern: str,
    path: str = ".",
    file_pattern: str | None = None,
    case_sensitive: bool = True,
    context_lines: int = 2
) -> str:
    """Search for code patterns using ripgrep if available, otherwise Python fallback.
    
    Args:
        pattern: Search pattern (can be regex)
        path: Directory to search in (default: current directory)
        file_pattern: Glob pattern for files to search (e.g., "*.py")
        case_sensitive: Whether search is case-sensitive (default: True)
        context_lines: Number of context lines to show (default: 2)
        
    Returns:
        Search results with file locations and context
        
    Example:
        >>> code_search("def main", ".", "*.py")
        "src/main.py:10:def main():\\n  ..."
    """
    try:
        try:
            rg_available = subprocess.run(
                ["rg", "--version"],
                capture_output=True,
                text=True
            ).returncode == 0
        except FileNotFoundError:
            rg_available = False
        
        if rg_available:
            return _code_search_ripgrep(pattern, path, file_pattern, case_sensitive, context_lines)
        else:
            return _code_search_python(pattern, path, file_pattern, case_sensitive, context_lines)
            
    except Exception as e:
        return f"Error searching: {str(e)}"


def _code_search_ripgrep(
    pattern: str,
    path: str,
    file_pattern: str | None,
    case_sensitive: bool,
    context_lines: int
) -> str:
    """Search using ripgrep (fast)."""
    cmd = ["rg", pattern, path, "--line-number", "--heading"]
    
    if not case_sensitive:
        cmd.append("--ignore-case")
    
    if file_pattern:
        cmd.extend(["--glob", file_pattern])
    
    if context_lines > 0:
        cmd.extend(["-C", str(context_lines)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return f"Search results for '{pattern}':\n\n{result.stdout}"
    elif result.returncode == 1:
        return f"No matches found for '{pattern}' in {path}"
    else:
        return f"Error running ripgrep: {result.stderr}"


def _code_search_python(
    pattern: str,
    path: str,
    file_pattern: str | None,
    case_sensitive: bool,
    context_lines: int
) -> str:
    """Fallback search using pure Python."""
    import re
    
    results = []
    search_path = Path(path)
    
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"
    
    if file_pattern:
        pattern_path = search_path / "**" / file_pattern
        files = list(Path(".").glob(str(pattern_path)))
    else:
        files = []
        for p in search_path.rglob("*"):
            if p.is_file() and not p.name.startswith('.'):
                files.append(p)
    
    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            for i, line in enumerate(lines):
                if regex.search(line):
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    
                    context = []
                    for j in range(start, end):
                        marker = ">" if j == i else " "
                        context.append(f"  {marker} {j+1:4d} | {lines[j]}")
                    
                    results.append(
                        f"{file_path}:{i+1}:\n" +
                        "\n".join(context)
                    )
                    
        except (UnicodeDecodeError, PermissionError):
            continue
    
    if results:
        return f"Search results for '{pattern}':\n\n" + "\n\n".join(results)
    else:
        return f"No matches found for '{pattern}' in {path}"


def find(pattern: str, path: str = ".", max_results: int = 100) -> str:
    """Find files matching a glob pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "**/*.txt", "test_*.py")
        path: Directory to search in (default: current directory)
        max_results: Maximum number of results to return (default: 100)
        
    Returns:
        List of matching file paths
        
    Example:
        >>> find("*.py", "src")
        "Found 5 files:\\nsrc/main.py\\nsrc/utils.py\\n..."
    """
    try:
        search_path = Path(path)
        
        if not search_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not search_path.is_dir():
            return f"Error: Path is not a directory: {path}"
        
        if "**" in pattern:
            matches = list(search_path.glob(pattern))
        else:
            matches = list(search_path.glob(pattern))
        
        matches = sorted(matches, key=lambda p: str(p))
        
        total_count = len(matches)
        matches = matches[:max_results]
        
        if not matches:
            return f"No files found matching pattern '{pattern}' in {path}"
        
        results = [f"Found {total_count} file(s) matching '{pattern}':"]
        results.append("")
        
        for match in matches:
            # Show relative path and indicate if directory
            rel_path = match.relative_to(search_path) if match.is_relative_to(search_path) else match
            if match.is_dir():
                results.append(f"📁 {rel_path}/")
            else:
                size = match.stat().st_size
                size_str = format_size(size)
                results.append(f"📄 {rel_path} ({size_str})")
        
        if total_count > max_results:
            results.append("")
            results.append(f"... and {total_count - max_results} more files")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error finding files: {str(e)}"


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
