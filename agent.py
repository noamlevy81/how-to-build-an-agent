#!/usr/bin/env python3
"""Python Coding Agent - An AI assistant for software development tasks.

This agent uses the Azure AI Inference SDK (azure-ai-inference), which talks to
both Azure OpenAI deployments and Azure AI Foundry models through the same
Chat Completions messages-array API. It provides 16 tools for file operations,
code search, execution, git integration, and interactive features.

Usage:
    uv run agent.py

Configuration (environment variables):
    AZURE_INFERENCE_ENDPOINT  Endpoint URL. Examples:
        Azure OpenAI:  https://<resource>.openai.azure.com/openai/deployments/<deployment>
        Azure Foundry: https://<resource>.services.ai.azure.com/models
    AZURE_INFERENCE_MODEL     Model / deployment name (required for Foundry,
                              optional for Azure OpenAI per-deployment endpoints).
    AZURE_INFERENCE_KEY       API key. If unset, Entra ID (DefaultAzureCredential)
                              is used instead.
    AZURE_INFERENCE_API_VERSION  Optional API version (defaults to a recent one).
"""

import json
import os
import sys
from typing import Any

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
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

DEFAULT_API_VERSION = "2024-10-21"

# Entra ID token scope for data-plane access to Azure OpenAI / Foundry
# (Cognitive Services) endpoints. Only used when falling back to Entra ID.
COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


def setup_client() -> tuple[ChatCompletionsClient, str | None]:
    """Initialize the Azure AI Inference chat completions client.

    Works for both Azure OpenAI and Azure AI Foundry endpoints; only the
    configuration (endpoint, model, credential) differs between them.

    Returns:
        A tuple of (client, model_name). model_name may be None when the
        endpoint already targets a specific deployment.

    Raises:
        ValueError: If AZURE_INFERENCE_ENDPOINT is not set.
    """
    endpoint = os.environ.get("AZURE_INFERENCE_ENDPOINT")
    if not endpoint:
        raise ValueError(
            "AZURE_INFERENCE_ENDPOINT environment variable not set.\n"
            "Set it to your Azure OpenAI or Azure AI Foundry endpoint, e.g.\n"
            "  https://<resource>.openai.azure.com/openai/deployments/<deployment>\n"
            "  https://<resource>.services.ai.azure.com/models"
        )

    model = os.environ.get("AZURE_INFERENCE_MODEL")
    api_version = os.environ.get("AZURE_INFERENCE_API_VERSION", DEFAULT_API_VERSION)

    api_key = os.environ.get("AZURE_INFERENCE_KEY")
    credential: Any
    # Extra client kwargs that only apply to the Entra ID (token) path.
    credential_kwargs: dict[str, Any] = {}
    if api_key:
        credential = AzureKeyCredential(api_key)
    else:
        # Fall back to Entra ID (managed identity / az login / env credentials).
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        # Token auth needs an explicit data-plane scope; the SDK default scope
        # does not match Azure OpenAI / Foundry endpoints and yields a 401.
        credential_kwargs["credential_scopes"] = [COGNITIVE_SERVICES_SCOPE]

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=credential,
        api_version=api_version,
        **credential_kwargs,
    )
    return client, model


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
    client: ChatCompletionsClient,
    registry: ToolRegistry,
    conversation_history: list[dict[str, Any]],
    tools: list[Any],
    model: str | None,
) -> Any | None:
    """Process tool calls from a chat completion response.

    Args:
        response: Response from the chat completions client
        client: ChatCompletionsClient instance
        registry: Tool registry
        conversation_history: Complete conversation so far (modified in place)
        tools: Tool definitions in OpenAI/Azure format
        model: Model / deployment name (or None)

    Returns:
        Next response after executing tools, or None if no tool calls
    """
    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        return None

    # Append the assistant turn that requested the tool calls.
    conversation_history.append({
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ],
    })

    # Execute each tool and append its result as a 'tool' message.
    for tc in tool_calls:
        console.print(f"[cyan]🔧 Executing: {tc.function.name}[/cyan]")

        try:
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
        except json.JSONDecodeError:
            args = {}

        result = registry.execute(tc.function.name, **args)

        conversation_history.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })

    console.print(f"[dim]📤 Sending context: {len(conversation_history)} messages[/dim]")
    return client.complete(
        messages=conversation_history,
        tools=tools,
        model=model,
    )


def run_agent_loop() -> None:
    """Main agent event loop.

    Flow:
    1. User provides input
    2. Send ENTIRE conversation history + new message to the model with tools
    3. Process any tool calls (sending full history again with results)
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
        client, model = setup_client()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    
    registry = initialize_tools()
    
    # Prepare tools for API
    tools: list[Any]
    if registry.tools:
        tools = registry.to_openai_tools()
        console.print(f"[green]✓ Loaded {len(tools)} tools[/green]\n")
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
                "content": user_input
            })
            
            console.print(f"[cyan]🤔 Thinking...[/cyan] [dim](context: {len(conversation_history)} messages)[/dim]")
            
            response: Any = client.complete(
                messages=conversation_history,
                tools=tools,
                model=model,
            )
            
            while response.choices[0].message.tool_calls:
                response = process_function_calls(
                    response,
                    client,
                    registry,
                    conversation_history,
                    tools,
                    model,
                )
                if response is None:
                    break
            
            if response:
                final_message = response.choices[0].message
                conversation_history.append({
                    "role": "assistant",
                    "content": final_message.content or "",
                })

                if final_message.content:
                    console.print("\n[bold blue]Agent:[/bold blue]")
                    console.print(Markdown(final_message.content))
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
