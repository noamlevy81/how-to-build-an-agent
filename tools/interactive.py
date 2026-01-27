"""Interactive tools for user engagement and memory.

Provides tools for interaction:
- ask_user: Get input from the user
- remember: Store and retrieve persistent information
"""

import json
from pathlib import Path
from datetime import datetime


# Memory storage location
MEMORY_FILE = Path.home() / ".python_coding_agent_memory.json"


def ask_user(question: str, default: str | None = None) -> str:
    """Ask the user a question and get their input.
    
    Args:
        question: Question to ask the user
        default: Optional default value if user provides no input
        
    Returns:
        User's response
        
    Example:
        >>> ask_user("What is your name?")
        # User types: Alice
        "Alice"
    """
    try:
        # Display the question
        prompt = f"\n[Question] {question}"
        if default:
            prompt += f" (default: {default})"
        prompt += "\n[Your answer]: "
        
        # Get user input
        response = input(prompt).strip()
        
        # Use default if no response
        if not response and default:
            return default
        
        return response if response else "(no response)"
        
    except EOFError:
        return default if default else "(no input available)"
    except KeyboardInterrupt:
        return "(interrupted)"
    except Exception as e:
        return f"Error getting user input: {str(e)}"


def remember(
    action: str,
    key: str | None = None,
    value: str | None = None
) -> str:
    """Store and retrieve persistent information across sessions.
    
    Args:
        action: Action to perform: "save", "get", "list", "delete", "clear"
        key: Memory key (required for save, get, delete)
        value: Value to store (required for save)
        
    Returns:
        Result of the operation
        
    Examples:
        >>> remember("save", "user_name", "Alice")
        "✓ Saved: user_name = Alice"
        
        >>> remember("get", "user_name")
        "Alice"
        
        >>> remember("list")
        "Stored memories:\\n- user_name: Alice\\n- project: python-agent"
    """
    try:
        # Load existing memory
        memory = _load_memory()
        
        if action == "save":
            if not key or value is None:
                return "Error: 'save' requires both key and value"
            
            # Save the value
            memory[key] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            _save_memory(memory)
            
            return f"✓ Saved: {key} = {value}"
        
        elif action == "get":
            if not key:
                return "Error: 'get' requires a key"
            
            if key not in memory:
                return f"No value stored for key: {key}"
            
            return memory[key]["value"]
        
        elif action == "list":
            if not memory:
                return "No memories stored yet"
            
            lines = ["Stored memories:"]
            for k, v in memory.items():
                timestamp = v.get("timestamp", "unknown")
                lines.append(f"  - {k}: {v['value']} (saved: {timestamp})")
            
            return "\n".join(lines)
        
        elif action == "delete":
            if not key:
                return "Error: 'delete' requires a key"
            
            if key not in memory:
                return f"No value stored for key: {key}"
            
            del memory[key]
            _save_memory(memory)
            
            return f"✓ Deleted: {key}"
        
        elif action == "clear":
            _save_memory({})
            return "✓ Cleared all memories"
        
        else:
            return (
                f"Error: Unknown action '{action}'\n"
                "Valid actions: save, get, list, delete, clear"
            )
        
    except Exception as e:
        return f"Error with memory operation: {str(e)}"


from typing import Any


def _load_memory() -> dict[str, Any]:
    """Load memory from disk."""
    if not MEMORY_FILE.exists():
        return {}
    
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_memory(memory: dict[str, Any]) -> None:
    """Save memory to disk."""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        raise Exception(f"Failed to save memory: {e}")
