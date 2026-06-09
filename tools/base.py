"""Base classes for tool definitions."""

from collections.abc import Callable
from typing import Any
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """Base class for defining a tool that can be called by the AI agent.
    
    Each tool consists of:
    - name: Unique identifier for the tool
    - description: What the tool does (shown to the AI)
    - parameters: JSON Schema for parameters (OpenAI tool format)
    - handler: The Python function that executes the tool
    
    Example:
        read_file_tool = ToolDefinition(
            name="read_file",
            description="Read contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"}
                },
                "required": ["path"]
            },
            handler=read_file_handler
        )
    """
    
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str]
    
    class Config:
        arbitrary_types_allowed = True
    
    def to_openai_tool(self) -> dict[str, Any]:
        """Convert tool definition to OpenAI/Azure tool format.

        Returns:
            A tool dict accepted by the azure-ai-inference ``complete`` call
            (and by Azure OpenAI / OpenAI Chat Completions).

        Note:
            ``parameters`` is already an OpenAI-style JSON Schema dict, so this
            is essentially a pass-through wrapped in the function envelope.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
    
    def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given arguments.
        
        Args:
            **kwargs: Arguments passed from the AI model
            
        Returns:
            String result to send back to the AI
            
        Raises:
            Exception: If tool execution fails
        """
        try:
            return self.handler(**kwargs)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"


class ToolRegistry:
    """Registry for managing all available tools.
    
    Provides methods to register tools and retrieve them in various formats.
    """
    
    def __init__(self) -> None:
        self.tools: dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition) -> None:
        """Register a new tool.
        
        Args:
            tool: ToolDefinition to register
        """
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> ToolDefinition:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolDefinition for the requested tool
            
        Raises:
            KeyError: If tool not found
        """
        return self.tools[name]
    
    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Convert all registered tools to OpenAI/Azure tool format.

        Returns:
            List of tool dicts, one per registered tool, ready to pass as the
            ``tools`` argument to azure-ai-inference / Azure OpenAI / OpenAI.
        """
        return [tool.to_openai_tool() for tool in self.tools.values()]
    
    def execute(self, name: str, **kwargs: Any) -> str:
        """Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        tool = self.get(name)
        return tool.execute(**kwargs)
