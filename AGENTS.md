# LAXCODE Agent Configuration

## Project Overview

**LAXCODE** is an agentic AI coding assistant powered by Laxmana AI. It provides an interactive CLI experience with beautiful animations and powerful code editing capabilities.

### Key Features

- **Laxmana AI Animations**: Beautiful terminal animations inspired by the HTML version
- **NVIDIA NIM API**: Free access to powerful models (Llama 3.1, Nemotron, etc.)
- **Multi-Provider Support**: NVIDIA NIM, OpenAI, Anthropic Claude
- **File Operations**: Read, edit, search files with line numbers
- **Shell Integration**: Execute commands safely
- **Session Management**: Persistent conversation history
- **Tool System**: Extensible tool architecture

## Architecture

```
laxcode/
├── animations/        # Laxmana AI animation system
│   ├── core.py       # Main animator with Rich
│   └── effects.py    # Particle systems, waveforms
├── providers/         # LLM provider integrations
│   ├── base.py       # Provider interface
│   ├── nvidia_nim.py # NVIDIA NIM API
│   ├── openai.py     # OpenAI API
│   └── anthropic.py  # Claude API
├── tools/            # Available tools
│   ├── base.py       # Tool interface
│   ├── file_tools.py # File operations
│   ├── shell_tools.py# Shell commands
│   └── search_tools.py# Code search
├── core/             # Core components
│   ├── agent.py      # Main agent
│   └── session.py    # Session management
├── config/           # Configuration
│   └── manager.py    # Config manager
└── main.py           # Entry point
```

## Animation System

The Laxmana AI animation system provides visual feedback through terminal-based animations:

### Modes

| Mode | Color | Use Case |
|------|-------|----------|
| IDLE | Gold | Waiting for input |
| LISTENING | Green | Ready to receive |
| PROCESSING | Purple | Thinking/working |
| WORKING | Cyan | Generating code |
| ERROR | Red | Error occurred |
| SUCCESS | Green | Completed successfully |

### Components

- **Particle System**: Floating particles with physics
- **Energy Sparks**: Burst effects for processing
- **Waveform**: Audio-like visualization for working mode
- **Breathing Effect**: Pulsing core animation
- **Connection Lines**: Neural network visualization
- **Glow Effect**: Ambient background glow

## Provider Setup

### NVIDIA NIM (Recommended, Free)

1. Get free API key: https://build.nvidia.com/explore
2. Run: `laxcode setup`
3. Select NVIDIA NIM provider
4. Enter your API key

### OpenAI

1. Get API key: https://platform.openai.com
2. Set environment: `OPENAI_API_KEY=your_key`
3. Run: `laxcode setup`
4. Select OpenAI provider

### Anthropic Claude

1. Get API key: https://console.anthropic.com
2. Set environment: `ANTHROPIC_API_KEY=your_key`
3. Run: `laxcode setup`
4. Select Anthropic provider

## Available Tools

### File Operations

- **read**: Read file contents with line numbers
  ```python
  read(file_path="/path/to/file.py", offset=1, limit=2000)
  ```

- **edit**: Edit file by replacing text
  ```python
  edit(file_path="/path/to/file.py", 
       old_string="def old():",
       new_string="def new():")
  ```

- **glob**: Find files matching pattern
  ```python
  glob(pattern="**/*.py", path=".")
  ```

### Shell Operations

- **bash**: Execute shell commands
  ```python
  bash(command="ls -la", description="List files")
  ```

- **view**: View directory structure
  ```python
  view(path=".", depth=2)
  ```

### Search Operations

- **grep**: Search for patterns in files
  ```python
  grep(pattern="class.*Tool", path=".", include="*.py")
  ```

## Commands

### Interactive Commands

- `/help` - Show help
- `/config` - Show configuration
- `/sessions` - List saved sessions
- `/tools` - List available tools
- `/models` - Show available models
- `/clear` - Clear screen
- `/exit` - Exit LAXCODE

### Quick Tools

- `/read <path>` - Read file
- `/glob <pattern>` - Find files
- `/grep <pattern>` - Search pattern

## Development

### Running from Source

```bash
# Clone repository
git clone https://github.com/venkattejaa/LAXCODE.git
cd LAXCODE

# Install dependencies
pip install -e .

# Run LAXCODE
python -m laxcode
```

### Adding New Tools

1. Create tool class in `laxcode/tools/`
2. Inherit from `Tool` base class
3. Define `name`, `description`, `parameters`
4. Implement `execute()` method
5. Register with `@register_tool` decorator

Example:

```python
from .base import Tool, ToolResult, ToolParameter, register_tool

@register_tool
class MyTool(Tool):
    name = "my_tool"
    description = "My custom tool"
    parameters = [
        ToolParameter(name="arg", type="string", description="Argument")
    ]
    
    async def execute(self, arg: str) -> ToolResult:
        return ToolResult.ok(output=f"Result: {arg}")
```

### Adding New Provider

1. Create provider class in `laxcode/providers/`
2. Inherit from `Provider` base class
3. Implement `chat()`, `chat_stream()`, `get_available_models()`
4. Register in agent initialization

## Version History

- **v1.1.0** (Current): Initial release with NVIDIA NIM, animations, file tools
- **v1.2.0** (Coming Soon):
  - Enhanced Laxmana AI animations
  - Multi-agent collaboration
  - Code review & auto-refactoring
  - Project-wide intelligent search
  - Local model support

## Configuration File

Location: `~/.laxcode/config.json`

```json
{
  "provider": "nvidia",
  "model": "llama-3.1-8b",
  "temperature": 0.7,
  "max_tokens": 4096,
  "animations_enabled": true,
  "show_tokens": true
}
```

## Environment Variables

- `NVIDIA_API_KEY` - NVIDIA NIM API key
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

## Session Storage

Sessions are saved to: `~/.laxcode/sessions/`

Each session includes:
- Message history
- Token counts
- Timestamps
- Metadata

## Safety

- All file operations restricted to workspace
- Dangerous commands require confirmation
- Shell commands validated for safety
- API keys never stored in plain text

## License

MIT License - See LICENSE file for details

## Links

- GitHub: https://github.com/venkattejaa/LAXCODE
- Issues: https://github.com/venkattejaa/LAXCODE/issues
- Discord: Coming soon!

---

**LAXCODE** - Code with the power of Laxmana AI
