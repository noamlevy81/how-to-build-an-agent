"""Base classes for tool definitions."""

from collections.abc import Callable
from typing import Any
from pydantic import BaseModel
import google.generativeai as genai


def _convert_to_gemini_schema(schema: dict[str, Any]) -> genai.protos.Schema:
    """Convert OpenAI-style JSON Schema to Gemini protobuf Schema.
    
    Args:
        schema: OpenAI-style JSON Schema dict
        
    Returns:
        Gemini protobuf Schema object
    """
    # Map JSON Schema types to Gemini protobuf types
    type_map = {
        "string": genai.protos.Type.STRING,
        "number": genai.protos.Type.NUMBER,
        "integer": genai.protos.Type.INTEGER,
        "boolean": genai.protos.Type.BOOLEAN,
        "array": genai.protos.Type.ARRAY,
        "object": genai.protos.Type.OBJECT,
    }
    
    schema_type = schema.get("type", "object")
    gemini_type = type_map.get(schema_type, genai.protos.Type.STRING)
    
    kwargs: dict[str, Any] = {"type": gemini_type}
    
    # Add description if present
    if "description" in schema:
        kwargs["description"] = schema["description"]
    
    # Handle properties for object types
    if "properties" in schema:
        kwargs["properties"] = {
            name: _convert_to_gemini_schema(prop_schema)
            for name, prop_schema in schema["properties"].items()
        }
    
    # Handle required fields
    if "required" in schema:
        kwargs["required"] = schema["required"]
    
    # Handle array items
    if "items" in schema:
        kwargs["items"] = _convert_to_gemini_schema(schema["items"])
    
    # Handle enum values
    if "enum" in schema:
        kwargs["enum"] = schema["enum"]
    
    return genai.protos.Schema(**kwargs)


class ToolDefinition(BaseModel):
    """Base class for defining a tool that can be called by the AI agent.
    
    Each tool consists of:
    - name: Unique identifier for the tool
    - description: What the tool does (shown to the AI)
    - parameters: JSON Schema for parameters (Gemini format)
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
    
    def to_gemini_format(self) -> genai.protos.FunctionDeclaration:
        """Convert tool definition to Gemini API format.
        
        Returns:
            Gemini FunctionDeclaration protobuf object
            
        Note:
            Gemini uses protobuf-based Schema objects, not OpenAI-style
            JSON Schema dicts. This method handles the conversion.
        """
        return genai.protos.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=_convert_to_gemini_schema(self.parameters)
        )
    
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
    
    def to_gemini_tools(self) -> list[genai.protos.Tool]:
        """Convert all registered tools to Gemini format.
        
        Returns:
            List containing a single Tool with all function declarations
        """
        function_declarations = [
            tool.to_gemini_format() for tool in self.tools.values()
        ]
        return [genai.protos.Tool(function_declarations=function_declarations)]
    
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
