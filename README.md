# grok-code

**Terminal-based coding agent powered by Grok/XAI** - A Claude Code-like experience using Grok's powerful reasoning capabilities.

## 🎉 Features

### Core Capabilities
- **File Operations**: Read, write, edit files with safety validation
- **Code Exploration**: Find files (glob), search content (grep), read with line numbers
- **Command Execution**: Run bash commands with sandboxing and permission system
- **Function Calling**: Native xAI function calling with tool execution loop

### 🛡️ Safety Features (CRITICAL)
- **Path Validation**: Blocks writes to system directories (`/etc`, `/usr`, `/bin`, etc.)
- **Command Sandboxing**: Prevents destructive commands (`rm -rf`, `dd`, `mkfs`, etc.)
- **Permission System**: User approval required for risky operations with session caching
- **Sensitive File Warnings**: Alerts when modifying `.env`, credentials, SSH keys, etc.
- **Timeout Protection**: Commands limited to 5 minutes max
- **Output Limits**: Prevents memory issues from large outputs

### ✅ Test Coverage
**70 comprehensive tests** following Test-Driven Development (TDD):
- Core API Client: 8 tests
- Tool Registry: 8 tests
- **Safety Validators: 17 tests** (CRITICAL)
- Read-Only Tools: 13 tests
- Write Tools: 13 tests
- Bash Tool: 11 tests

## 🚀 Quick Start

### Installation

```bash
# Navigate to project
cd /Users/ksy-syd-mbp-200/Documents/coding/cursor/grok-code

# Activate virtual environment
source venv/bin/activate
```

### Configuration

Your `.env` file should be configured with:
```bash
XAI_API_KEY=your-xai-api-key-here
XAI_CHAT_ENDPOINT=https://api.x.ai/v1/chat/completions
XAI_MODEL=grok-code-fast-1
GROK_CODE_WORKING_DIR=/Users/ksy-syd-mbp-200/Documents/coding/cursor/grok-code
GROK_CODE_MAX_TOOL_ITERATIONS=20
```

### Usage

**Single Query Mode:**
```bash
python grok_code.py "Read the README.md file"
```

**Interactive Mode:**
```bash
python grok_code.py --interactive
```

**Interactive Commands:**
- `/exit` or `/quit` - Exit interactive mode
- `/clear` - Clear conversation history
- `/tools` - List available tools

## 🔧 Available Tools

### Read-Only Tools (Safe - No Permission)
1. **read_file** - Read file contents with line numbers
2. **glob** - Find files by pattern (e.g., `**/*.py`)
3. **grep** - Search file contents with regex

### Write Tools (Requires Permission)
4. **write_file** - Create or overwrite files
5. **edit_file** - Edit with exact string replacement

### Command Execution (Sandboxed)
6. **bash** - Execute bash commands
   - Safe commands (ls, cat, git status) - Auto-approved
   - Risky commands (rm, mv, git push) - Requires permission
   - Destructive commands (rm -rf /, dd) - Always blocked

## 🛡️ Safety System

### Blocked Operations
- System directory writes: `/etc`, `/usr`, `/bin`, `/sbin`, etc.
- Destructive commands: `rm -rf /`, `dd`, `mkfs`, fork bombs

### Permission Required
- Overwriting existing files
- Writing sensitive files (`.env`, credentials, SSH keys)
- Risky commands (rm, mv, git push, npm install, etc.)

## 🧪 Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing

# Specific test file
pytest tests/test_safety.py -v
```

## 🎯 Example Usage

```bash
# Explore codebase
python grok_code.py "Find all Python files and show me the test files"

# Read and analyze
python grok_code.py "Read core/api_client.py and explain the function calling loop"

# Safe commands
python grok_code.py "Run git status"

# File modification (requires permission)
python grok_code.py "Add a docstring to the execute_with_tools function"
```

## 📁 Project Structure

```
grok-code/
├── core/              # Core functionality
├── tools/             # Tool implementations
├── safety/            # Safety systems (CRITICAL)
├── tests/             # Comprehensive test suite (70 tests)
├── grok_code.py       # Main CLI entry point
├── .env               # Configuration
└── requirements.txt   # Dependencies
```

## 🚧 Status: Version 1.0 COMPLETE

### ✅ Completed (70/70 tests passing)
- Core API client with function calling
- Tool registry system
- **Critical safety systems**
- Read/Write/Edit tools
- Bash tool with sandboxing
- Basic CLI interface

### 🔄 Future Enhancements
- Plan mode workflow (plan → approve → execute)
- Enhanced UI components
- Git integration
- Code analysis tools

---

**Note**: This is a complete rewrite of grokterm with focus on coding agent capabilities and safety. Original grokterm.py archived as grokterm.py.backup.
