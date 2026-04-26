# LAXCODE

<p align="center">
  <img src="https://img.shields.io/badge/version-1.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <strong>Agentic AI Coding Assistant powered by Laxmana AI</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/NVIDIA-NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA NIM">
  <img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI">
  <img src="https://img.shields.io/badge/Anthropic-191919?style=for-the-badge&logo=anthropic&logoColor=white" alt="Anthropic">
</p>

---

## 🚀 Features

- **🎨 Laxmana AI Animations** - Beautiful terminal animations that react to your commands
- **🤖 Multi-Provider Support** - NVIDIA NIM (FREE), OpenAI, Anthropic Claude
- **📁 File Operations** - Read, edit, search files with line numbers
- **🔧 Tool System** - Extensible architecture with file, shell, and search tools
- **💬 Interactive Chat** - Natural conversation with AI assistant
- **📊 Session Management** - Persistent conversation history
- **🛡️ Safety First** - Restricted file operations and validated shell commands

## 🎭 Laxmana AI Animation System

The Laxmana AI core provides visual feedback through beautiful terminal animations:

| Mode | Color | When Active |
|------|-------|-------------|
| 🟡 **Idle** | Gold | Waiting for input |
| 🟢 **Listening** | Green | Ready to receive |
| 🟣 **Processing** | Purple | Thinking/working |
| 🔵 **Working** | Cyan | Generating code |
| 🔴 **Error** | Red | Error occurred |
| ✅ **Success** | Green | Completed |

## 📦 Installation

### From PyPI (Coming Soon)

```bash
pip install laxcode
```

### From Source

```bash
git clone https://github.com/venkattejaa/LAXCODE.git
cd LAXCODE
pip install -e .
```

## 🚀 Quick Start

### 1. Configure Your API Key

```bash
laxcode setup
```

This will guide you through:
- Selecting your AI provider (NVIDIA NIM recommended - it's FREE!)
- Entering your API key
- Choosing your preferred model
- Setting preferences

### 2. Start Coding

```bash
# Interactive mode
laxcode

# Single message
laxcode "Create a Python function to calculate fibonacci"
```

## 🔌 Provider Setup

### NVIDIA NIM (Recommended - FREE!)

1. Get your free API key: https://build.nvidia.com/explore
2. Run: `laxcode setup`
3. Select NVIDIA NIM
4. Enter your API key

**Available Free Models:**
- `llama-3.1-8b` (Fast, efficient) ⭐ Recommended
- `llama-3.1-70b` (High quality)
- `llama-3.1-405b` (Best quality)
- `nemotron-4-340b` (NVIDIA's model)
- `phi-3-medium` (Fast)
- `mistral-7b` (Efficient)
- `mixtral-8x7b` (MoE)
- `gemma-2-9b` (Lightweight)

### OpenAI

```bash
export OPENAI_API_KEY=your_key_here
laxcode setup
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY=your_key_here
laxcode setup
```

## 💻 Usage

### Interactive Commands

Once in interactive mode (`laxcode`), you can use:

```
/help       Show help message
/config     Show current configuration
/sessions   List saved sessions
/tools      List available tools
/models     Show available models
/clear      Clear the screen
/exit       Exit LAXCODE
```

### Quick Tools

```
/read <path>        Read a file with line numbers
/glob <pattern>     Find files (e.g., "**/*.py")
/grep <pattern>     Search for text in files
```

### Example Session

```bash
$ laxcode

██╗      █████╗ ██╗  ██╗ ██████╗ ██████╗ ██████╗ ███████╗
██║     ██╔══██╗╚██╗██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║     ███████║ ╚███╔╝ ██║     ██║   ██║██║  ██║█████╗
██║     ██╔══██║ ██╔██╗ ██║     ██║   ██║██║  ██║██╔══╝
███████╗██║  ██║██╔╝ ██╗╚██████╗╚██████╔╝██████╔╝███████╗
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝

           Powered by Laxmana AI
     Agentic Coding Assistant for Developers

🚀 LAXMANA v1.2 COMING SOON!

Ready to code! Type /help for available commands.

❯❯❯ Create a Python function to calculate fibonacci

[Processing... ✓]

Here's a Python function to calculate Fibonacci numbers:

```python
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

❯❯❯ /read fibonacci.py

[File: fibonacci.py]
[Lines: 1-12 of 12]

```python
1: def fibonacci(n: int) -> int:
2:     """Calculate the nth Fibonacci number."""
3:     if n < 0:
4:         raise ValueError("n must be non-negative")
5:     if n <= 1:
6:         return n
7:
8:     a, b = 0, 1
9:     for _ in range(2, n + 1):
10:         a, b = b, a + b
11:     return b
12:
```

❯❯❯ /exit

Goodbye! 👋
```

## 🛠️ Available Tools

### File Operations

- **read** - Read file contents with line numbers
- **edit** - Edit files by replacing text
- **glob** - Find files matching glob patterns
- **view** - View directory structure

### Shell Operations

- **bash** - Execute shell commands safely

### Search Operations

- **grep** - Search for patterns in files

## ⚙️ Configuration

Configuration is stored in `~/.laxcode/config.json`:

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

### Environment Variables

- `NVIDIA_API_KEY` - NVIDIA NIM API key
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

## 🎯 What's Coming in v1.2

- 🎨 **Enhanced Laxmana AI animations** - Voice waveform sync
- 🤝 **Multi-agent collaboration** - Multiple agents working together
- 🔍 **Code review & auto-refactoring** - AI-powered code improvements
- 🔎 **Project-wide intelligent search** - Find anything instantly
- 💻 **GitHub Copilot-style completions** - Inline suggestions
- 🏠 **Local model support** - Run models locally with Llama.cpp

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Powered by [NVIDIA NIM](https://build.nvidia.com/explore)
- Inspired by Claude Code and Kimi Code
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Laxmana AI](https://github.com/venkattejaa/LAXCODE) animation system

## 🔗 Links

- GitHub: https://github.com/venkattejaa/LAXCODE
- Issues: https://github.com/venkattejaa/LAXCODE/issues
- Documentation: https://github.com/venkattejaa/LAXCODE#readme
- Discord: Coming soon!

---

<p align="center">
  <strong>LAXCODE</strong> - Code with the power of Laxmana AI
</p>

<p align="center">
  Made with ❤️ by the LAXCODE Team
</p>
