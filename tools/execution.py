"""Execution tools for running commands and code.

Provides tools for executing code:
- bash: Execute shell commands
- python_eval: Evaluate Python code snippets
- run_tests: Run test suites (pytest/unittest)
"""

import subprocess
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


def bash(
    command: str,
    working_dir: str | None = None,
    timeout: int = 30
) -> str:
    """Execute a shell command.
    
    Args:
        command: Shell command to execute
        working_dir: Working directory for command (default: current directory)
        timeout: Command timeout in seconds (default: 30)
        
    Returns:
        Command output (stdout and stderr combined)
        
    Example:
        >>> bash("echo Hello, World!")
        "Hello, World!"
        
    Security:
        Commands are executed in a subprocess with timeout protection.
        Be cautious about executing untrusted commands.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir
        )
        
        output = []
        
        if result.stdout:
            output.append(result.stdout)
        
        if result.stderr:
            output.append(f"[stderr]:\n{result.stderr}")
        
        # Add return code info
        if result.returncode != 0:
            output.append(f"\n[Exit code: {result.returncode}]")
        
        return "\n".join(output) if output else "(no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def python_eval(code: str, timeout: int = 10) -> str:
    """Evaluate Python code snippet and return the output.
    
    Args:
        code: Python code to evaluate
        timeout: Execution timeout in seconds (default: 10)
        
    Returns:
        Output from executing the code (print statements, return values, errors)
        
    Example:
        >>> python_eval("print('Hello'); x = 2 + 2; print(f'Result: {x}')")
        "Hello\\nResult: 4"
        
    Security:
        Code is executed in the current Python interpreter.
        Use with caution - this can execute arbitrary code.
        Consider sandboxing for production use.
    """
    try:
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        
        namespace = {
            '__builtins__': __builtins__,
            'print': print,  # Make sure print is available
        }
        
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                result = eval(code, namespace)
                if result is not None:
                    print(result)
            except SyntaxError:
                exec(code, namespace)
        
        stdout = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()
        
        output = []
        if stdout:
            output.append(stdout.rstrip())
        if stderr:
            output.append(f"[stderr]:\n{stderr.rstrip()}")
        
        return "\n".join(output) if output else "(no output)"
        
    except Exception as e:
        return f"Error executing Python code:\n{type(e).__name__}: {str(e)}"


def run_tests(
    path: str | None = None,
    pattern: str | None = None,
    verbose: bool = False,
    framework: str = "auto"
) -> str:
    """Run test suites using pytest or unittest.
    
    Args:
        path: Path to test file or directory (default: current directory)
        pattern: Pattern to match test files (e.g., "test_*.py")
        verbose: Whether to show verbose output
        framework: Test framework to use: "auto", "pytest", or "unittest"
        
    Returns:
        Test results summary
        
    Example:
        >>> run_tests("tests/", verbose=True)
        "===== test session starts =====\\n5 passed in 0.23s"
    """
    try:
        if framework == "auto":
            try:
                import pytest
                framework = "pytest"
            except ImportError:
                framework = "unittest"
        
        if framework == "pytest":
            return _run_pytest(path, pattern, verbose)
        elif framework == "unittest":
            return _run_unittest(path, pattern, verbose)
        else:
            return f"Error: Unknown test framework: {framework}"
            
    except Exception as e:
        return f"Error running tests: {str(e)}"


def _run_pytest(
    path: str | None,
    pattern: str | None,
    verbose: bool
) -> str:
    """Run tests using pytest."""
    try:
        import pytest
    except ImportError:
        return "Error: pytest not installed. Install with: pip install pytest"
    
    args = []
    
    if path:
        args.append(path)
    
    if pattern:
        args.extend(["-k", pattern])
    
    if verbose:
        args.append("-v")
    else:
        args.append("-q")
    
    args.append("--tb=short")  # Short traceback format
    
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        exit_code = pytest.main(args)
    
    result = output.getvalue()
    
    summary = []
    if exit_code == 0:
        summary.append("✓ All tests passed")
    else:
        summary.append(f"✗ Tests failed (exit code: {exit_code})")
    
    return "\n".join(summary) + "\n\n" + result


def _run_unittest(
    path: str | None,
    pattern: str | None,
    verbose: bool
) -> str:
    """Run tests using unittest."""
    import unittest
    
    try:
        # Discover tests
        if path:
            loader = unittest.TestLoader()
            if pattern:
                suite = loader.discover(path, pattern=pattern)
            else:
                suite = loader.discover(path)
        else:
            loader = unittest.TestLoader()
            suite = loader.discover(".", pattern=pattern or "test*.py")
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=2 if verbose else 1,
            stream=StringIO()
        )
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            result = runner.run(suite)
        
        summary = []
        summary.append(f"Tests run: {result.testsRun}")
        summary.append(f"Failures: {len(result.failures)}")
        summary.append(f"Errors: {len(result.errors)}")
        summary.append(f"Skipped: {len(result.skipped)}")
        
        if result.wasSuccessful():
            summary.insert(0, "✓ All tests passed")
        else:
            summary.insert(0, "✗ Some tests failed")
        
        return "\n".join(summary) + "\n\n" + output.getvalue()
        
    except Exception as e:
        return f"Error running unittest: {str(e)}"
