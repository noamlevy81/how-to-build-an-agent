#!/usr/bin/env python3
"""Python Coding Agent - An AI assistant for software development tasks.

This agent uses Google Gemini API and provides 16 tools for file operations,
code search, execution, git integration, and interactive features.

Usage:
    uv run agent.py

Set GOOGLE_API_KEY environment variable before running.
"""

import os
import sys
from collections.abc import Callable
from typing import Any

import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from tools.base import ToolRegistry, ToolDefinition
from tools.file_ops import read_file, write_file, list_files
from tools.code_tools import edit_file, code_search, find
from tools.execution import bash, python_eval, run_tests
from tools.integration import http_request, git, diff, tree
from tools.interactive import ask_user, remember


console = Console()


def setup_gemini_client() -> genai.GenerativeModel:
    """Initialize Gemini API client.
    
    Returns:
        Configured GenerativeModel instance
        
    Raises:
        ValueError: If GOOGLE_API_KEY not set
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set.\n"
            "Get your API key from: https://aistudio.google.com/apikey"
        )
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def initialize_tools() -> ToolRegistry:
    """Initialize and register all available tools.
    
    Returns:
        ToolRegistry with all tools registered
    """
    registry = ToolRegistry()
    
    # Phase 2: File operations
    registry.register(ToolDefinition(
        name="read_file",
        description="Read the contents of a file from the file system",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        },
        handler=read_file
    ))
    
    registry.register(ToolDefinition(
        name="write_file",
        description="Write content to a file. Creates parent directories if needed.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Whether to create parent directories if they don't exist (default: true)",
                    "default": True
                }
            },
            "required": ["path", "content"]
        },
        handler=write_file
    ))
    
    registry.register(ToolDefinition(
        name="list_files",
        description="List files and directories in a given path",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default: current directory)",
                    "default": "."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively (default: false)",
                    "default": False
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Whether to include hidden files (default: false)",
                    "default": False
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for recursive listing (null = unlimited)",
                }
            },
            "required": []
        },
        handler=list_files
    ))
    
    # Phase 3: Code tools
    registry.register(ToolDefinition(
        name="edit_file",
        description="Edit a file by replacing exact text. The old_text must match exactly.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact text to find and replace (must match exactly including whitespace)"
                },
                "new_text": {
                    "type": "string",
                    "description": "Text to replace with"
                }
            },
            "required": ["path", "old_text", "new_text"]
        },
        handler=edit_file
    ))
    
    registry.register(ToolDefinition(
        name="code_search",
        description="Search for code patterns in files. Supports regex patterns.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (can be regex)"
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                    "default": "."
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern for files to search (e.g., '*.py')"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether search is case-sensitive (default: true)",
                    "default": True
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines to show (default: 2)",
                    "default": 2
                }
            },
            "required": ["pattern"]
        },
        handler=code_search
    ))
    
    registry.register(ToolDefinition(
        name="find",
        description="Find files matching a glob pattern (e.g., '*.py', '**/*.txt')",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files"
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                    "default": "."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)",
                    "default": 100
                }
            },
            "required": ["pattern"]
        },
        handler=find
    ))
    
    registry.register(ToolDefinition(
        name="bash",
        description="Execute a shell command and return the output",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for command (optional)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            "required": ["command"]
        },
        handler=bash
    ))
    
    registry.register(ToolDefinition(
        name="python_eval",
        description="Evaluate Python code and return the output",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to evaluate"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds (default: 10)",
                    "default": 10
                }
            },
            "required": ["code"]
        },
        handler=python_eval
    ))
    
    registry.register(ToolDefinition(
        name="run_tests",
        description="Run test suites using pytest or unittest",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to test file or directory"
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern to match test files (e.g., 'test_*.py')"
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Show verbose output (default: false)",
                    "default": False
                },
                "framework": {
                    "type": "string",
                    "description": "Test framework: 'auto', 'pytest', or 'unittest' (default: 'auto')",
                    "default": "auto"
                }
            },
            "required": []
        },
        handler=run_tests
    ))
    
    # Phase 5: Integration tools
    registry.register(ToolDefinition(
        name="http_request",
        description="Make an HTTP request to a URL",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to request"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method (default: GET)",
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional headers dictionary"
                },
                "body": {
                    "type": "string",
                    "description": "Optional request body"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            "required": ["url"]
        },
        handler=http_request
    ))
    
    registry.register(ToolDefinition(
        name="git",
        description="Execute read-only git commands (status, log, diff, etc.)",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Git command (without 'git' prefix)"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Repository directory (optional)"
                }
            },
            "required": ["command"]
        },
        handler=git
    ))
    
    registry.register(ToolDefinition(
        name="diff",
        description="Compare two files or text strings",
        parameters={
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source file path or text content"
                },
                "target": {
                    "type": "string",
                    "description": "Target file path or text content"
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines (default: 3)",
                    "default": 3
                },
                "mode": {
                    "type": "string",
                    "description": "Diff mode: 'unified' or 'context' (default: unified)",
                    "default": "unified"
                }
            },
            "required": ["source", "target"]
        },
        handler=diff
    ))
    
    registry.register(ToolDefinition(
        name="tree",
        description="Display directory structure as a tree",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (default: current directory)",
                    "default": "."
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to traverse (default: 3)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files/dirs (default: false)",
                    "default": False
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Include files, not just directories (default: true)",
                    "default": True
                }
            },
            "required": []
        },
        handler=tree
    ))
    
    registry.register(ToolDefinition(
        name="ask_user",
        description="Ask the user a question and get their input",
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question to ask the user"
                },
                "default": {
                    "type": "string",
                    "description": "Optional default value if user provides no input"
                }
            },
            "required": ["question"]
        },
        handler=ask_user
    ))
    
    registry.register(ToolDefinition(
        name="remember",
        description="Store and retrieve persistent information across sessions",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'save', 'get', 'list', 'delete', or 'clear'"
                },
                "key": {
                    "type": "string",
                    "description": "Memory key (required for save, get, delete)"
                },
                "value": {
                    "type": "string",
                    "description": "Value to store (required for save)"
                }
            },
            "required": ["action"]
        },
        handler=remember
    ))
    
    return registry


def process_function_calls(
    response: Any,
    model: Any,
    registry: ToolRegistry,
    conversation_history: list[dict[str, Any]],
    tools: list[dict[str, Any]]
) -> Any | None:
    """Process function calls from Gemini response.
    
    Args:
        response: Response from Gemini
        model: GenerativeModel instance
        registry: Tool registry
        conversation_history: Complete conversation so far (modified in place)
        tools: Tool definitions for Gemini
        
    Returns:
        Next response after executing tools, or None if no function calls
    """
    function_calls = []
    
    for part in response.parts:
        if fn_call := part.function_call:
            function_calls.append(fn_call)
    
    if not function_calls:
        return None
    
    function_responses = []
    for fn_call in function_calls:
        console.print(f"[cyan]🔧 Executing: {fn_call.name}[/cyan]")
        
        args = dict(fn_call.args)
        
        result = registry.execute(fn_call.name, **args)
        
        function_responses.append(
            genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=fn_call.name,
                    response={"result": result}
                )
            )
        )
    
    conversation_history.append({
        "role": "model",
        "parts": response.parts
    })
    
    conversation_history.append({
        "role": "user", 
        "parts": function_responses
    })
    
    console.print(f"[dim]📤 Sending context: {len(conversation_history)} messages[/dim]")
    return model.generate_content(
        conversation_history,
        tools=tools
    )


def run_agent_loop() -> None:
    """Main agent event loop.
    
    Flow:
    1. User provides input
    2. Send ENTIRE conversation history + new message to Gemini with available tools
    3. Process any function calls (sending full history again with results)
    4. Display response
    5. Repeat
    
    KEY INSIGHT: Each API call is stateless. We explicitly manage and send
    the complete conversation history with every request. This makes the
    context window growth visible.
    """
    console.print(Panel.fit(
        "[bold blue]Python Coding Agent[/bold blue]\n"
        "Type your requests or 'exit' to quit.\n"
        "[dim]Each request sends the full conversation context.[/dim]",
        border_style="blue"
    ))
    
    # Initialize
    try:
        model = setup_gemini_client()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    
    registry = initialize_tools()
    
    # Prepare tools for API
    if registry.tools:
        tools = registry.to_gemini_tools()
        console.print(f"[green]✓ Loaded {len(tools[0].function_declarations)} tools[/green]\n")
    else:
        tools = []
        console.print("[yellow]⚠ No tools loaded yet (Phase 1 only)[/yellow]\n")

    conversation_history: list[dict[str, Any]] = []
    
    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
            
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if not user_input.strip():
                continue
            
            conversation_history.append({
                "role": "user",
                "parts": [user_input]
            })
            
            console.print(f"[cyan]🤔 Thinking...[/cyan] [dim](context: {len(conversation_history)} messages)[/dim]")
            
            if tools:
                response = model.generate_content(
                    conversation_history,
                    tools=tools
                )
            else:
                response = model.generate_content(conversation_history)
            
            while response.parts and any(part.function_call for part in response.parts):
                response = process_function_calls(
                    response, 
                    model, 
                    registry, 
                    conversation_history,
                    tools
                )
                if response is None:
                    break
            
            if response and response.parts:
                conversation_history.append({
                    "role": "model",
                    "parts": response.parts
                })
            
            if response and response.text:
                console.print("\n[bold blue]Agent:[/bold blue]")
                console.print(Markdown(response.text))
                console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()


def main() -> None:
    """Entry point for the agent."""
    run_agent_loop()


if __name__ == "__main__":
    main()
