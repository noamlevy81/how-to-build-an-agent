# Python Coding Agent 🤖

An educational AI coding assistant built with the Azure AI Inference SDK. This project demonstrates how to build a practical AI agent with function calling capabilities.

## Features

- **16 Tools** for file operations, code search, execution, and more
- **Azure AI Inference Integration** - one SDK that works with both Azure OpenAI and Azure AI Foundry models
- **Modular Architecture** - Each tool is a separate, well-documented module
- **UV Package Management** - Modern Python packaging and dependency management
- **Educational Focus** - Extensive documentation and examples

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- An Azure OpenAI or Azure AI Foundry deployment (endpoint + key, or Entra ID access)

### Installation

```bash
# Clone the repository
git clone https://github.com/noamlevy81/how-to-build-an-agent.git
cd python-agent

# Install dependencies using uv
uv sync

# Configure the backend (Linux/Mac)
export AZURE_INFERENCE_ENDPOINT='https://<resource>.openai.azure.com/openai/deployments/<deployment>'
export AZURE_INFERENCE_MODEL='<deployment-or-model-name>'
export AZURE_INFERENCE_KEY='your-api-key-here'   # omit to use Entra ID (DefaultAzureCredential)

# OR (Windows PowerShell)
$env:AZURE_INFERENCE_ENDPOINT='https://<resource>.openai.azure.com/openai/deployments/<deployment>'
$env:AZURE_INFERENCE_MODEL='<deployment-or-model-name>'
$env:AZURE_INFERENCE_KEY='your-api-key-here'
```

> The same SDK targets **Azure AI Foundry** too — just point `AZURE_INFERENCE_ENDPOINT`
> at the Foundry models endpoint (e.g. `https://<resource>.services.ai.azure.com/models`)
> and set `AZURE_INFERENCE_MODEL` to the model name.

### Run the Agent

```bash
uv run agent.py
```

## Available Tools

### File Operations ✅
- `read_file` - Read file contents with metadata
- `list_files` - List directory contents with filters
- `write_file` - Write to files with directory creation

### Code Tools ✅
- `edit_file` - Edit files with exact string replacement
- `code_search` - Search code using ripgrep or Python fallback
- `find` - Find files by glob pattern

### Execution ✅
- `bash` - Execute shell commands with timeout
- `python_eval` - Evaluate Python code snippets
- `run_tests` - Run pytest/unittest test suites

### Integration ✅
- `http_request` - Make HTTP requests to APIs
- `git` - Read-only git operations (status, log, diff)
- `diff` - Compare files or text strings
- `tree` - Display directory structure as a tree

### Interactive ✅
- `ask_user` - Get human input during execution
- `remember` - Persistent memory across sessions


## Project Structure

```
python-agent/
├── agent.py              # Main agent event loop
├── pyproject.toml        # UV configuration and dependencies
├── tools/
│   ├── __init__.py
│   ├── base.py          # Tool definition base classes
│   ├── file_ops.py      # File operation tools
│   ├── code_tools.py    # Code search and editing
│   ├── execution.py     # Bash, Python eval, tests
│   ├── integration.py   # HTTP, git, diff, tree
│   └── interactive.py   # User interaction, memory
├── docs/
│   ├── ARCHITECTURE.md  # System design details
│   ├── TOOLS.md         # Tool documentation
│   └── EXAMPLES.md      # Usage examples
└── thoughts/            # Planning and research docs
```

## How It Works

The agent follows an **explicit context management** pattern that makes API behavior transparent:

1. **User Input** → Accepts natural language requests
2. **Build Context** → Maintains conversation history as a list of messages
3. **Send to the model** → Sends **complete** conversation history with available tools (context grows!)
4. **Function Calling** → The model decides which tools to call and with what parameters
5. **Tool Execution** → Agent executes the requested tools
6. **Update & Resend** → Adds results to history, sends **full history again** for synthesis
7. **Response** → The model synthesizes results into natural language
8. **Repeat** → Loop continues for multi-step tasks

## Example Usage

```
You: Read the README.md file
Agent: 🔧 Executing: read_file
Agent: Here's the content of README.md:
[content shown...]

You: Find all Python files in the src directory
Agent: 🔧 Executing: find
Agent: Found 5 Python files:
- src/main.py
- src/utils.py
...
```

## Development

### Running Tests

```bash
uv run pytest
```


Built with ❤️ as an educational project to demystify AI agents
