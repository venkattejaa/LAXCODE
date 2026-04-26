# LAXCODE Quick Start Guide

Welcome to LAXCODE! This guide will help you get started with your new AI coding assistant.

## 🚀 What You've Built

**LAXCODE** is a fully functional agentic AI coding assistant with:
- ✅ NVIDIA NIM API integration (FREE models)
- ✅ Beautiful Laxmana AI terminal animations
- ✅ File operations (read, edit, glob)
- ✅ Shell command execution
- ✅ Code search (grep)
- ✅ Session management
- ✅ Interactive CLI like Claude Code

## 📋 Prerequisites

1. **Python 3.9+** installed
2. **NVIDIA NIM API Key** (free from https://build.nvidia.com/explore)
3. **Git** (optional, for cloning)

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/venkattejaa/LAXCODE.git
cd LAXCODE

# Install LAXCODE
pip install -e .
```

## 🔑 Configuration

### Method 1: Interactive Setup (Recommended)

```bash
laxcode setup
```

Follow the prompts:
1. Select provider (1 for NVIDIA NIM)
2. Enter your API key
3. Select model (1 for llama-3.1-8b)
4. Enable animations (y)
5. Show tokens (y)

### Method 2: Quick Setup (Non-interactive)

```bash
laxcode --set-nvidia-key YOUR_API_KEY
```

### Method 3: Environment Variable

```bash
# Windows
setx NVIDIA_API_KEY "YOUR_API_KEY"

# Linux/macOS
export NVIDIA_API_KEY="YOUR_API_KEY"
```

## 🎮 Basic Usage

### Start Interactive Mode

```bash
laxcode
```

You'll see the Laxmana AI splash screen and can start chatting!

### Send a Single Message

```bash
laxcode "Create a Python function to calculate fibonacci numbers"
```

### Available Commands (in interactive mode)

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/config` | Show current configuration |
| `/sessions` | List saved sessions |
| `/tools` | List available tools |
| `/models` | Show available models |
| `/clear` | Clear the screen |
| `/exit` | Exit LAXCODE |

### Quick Tools (in interactive mode)

| Command | Description | Example |
|---------|-------------|---------|
| `/read <path>` | Read a file | `/read README.md` |
| `/glob <pattern>` | Find files | `/glob **/*.py` |
| `/grep <pattern>` | Search files | `/grep class.*Tool` |

## 💡 Example Workflows

### Example 1: Analyze Code

```
❯❯❯ /read laxcode/main.py

[Shows file contents with line numbers]

❯❯❯ What does this file do?

[AI analyzes the code and explains it]
```

### Example 2: Create a New Feature

```
❯❯❯ Create a calculator module with add, subtract, multiply, divide functions

[AI generates the code]

❯❯❯ Save it to calculator.py

[AI creates the file]
```

### Example 3: Refactor Code

```
❯❯❯ /read old_script.py

❯❯❯ Refactor this to use classes instead of functions

[AI suggests refactored code]

❯❯❯ Apply those changes to old_script.py

[AI edits the file]
```

### Example 4: Debug an Error

```
❯❯❯ /read error_log.txt

❯❯❯ What does this error mean?

[AI explains the error]

❯❯❯ How do I fix it?

[AI provides solution]
```

## 🛠️ Available Tools

LAXCODE can use these tools automatically:

### File Operations
- **read** - Read file contents with line numbers
- **edit** - Edit files by replacing text
- **glob** - Find files matching patterns
- **view** - View directory structure

### Shell Operations
- **bash** - Execute shell commands (with safety checks)

### Search Operations
- **grep** - Search for patterns in files

## 🔒 Safety Features

- File operations are restricted to your workspace
- Dangerous commands (like `rm -rf /`) are blocked
- Shell commands require confirmation
- API keys are stored securely (not in plain text in config)

## 📊 Session Management

Sessions are automatically saved to `~/.laxcode/sessions/`

- Each session has a unique ID
- Conversation history is preserved
- Token usage is tracked
- Resume sessions with `/sessions` command

## 🎨 Animation Modes

The Laxmana AI core shows different animations based on state:

| Mode | Color | When Active |
|------|-------|-------------|
| 🟡 **Idle** | Gold | Waiting for input |
| 🟢 **Listening** | Green | Ready to receive |
| 🟣 **Processing** | Purple | Thinking/working |
| 🔵 **Working** | Cyan | Generating code |
| 🔴 **Error** | Red | Error occurred |

## 🔧 Configuration

Config is stored in `~/.laxcode/config.json`:

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

## 🌟 Tips for Best Results

1. **Be specific** - "Create a Python function that calculates fibonacci numbers up to n"
2. **Provide context** - Reference files you've already read
3. **Iterate** - Ask for clarifications or modifications
4. **Use quick tools** - `/read`, `/glob`, `/grep` for file operations
5. **Save sessions** - They're automatically saved!

## 🐛 Troubleshooting

### "No API key configured"

Run setup again:
```bash
laxcode setup
```

### "API key not working"

Check your key is valid at https://build.nvidia.com/explore

### "UnicodeEncodeError"

This is a Windows terminal encoding issue. Try:
```bash
chcp 65001
```

### Commands not working

Make sure LAXCODE is installed:
```bash
pip install -e .
```

## 📚 Learn More

- **GitHub**: https://github.com/venkattejaa/LAXCODE
- **AGENTS.md**: Detailed architecture documentation
- **README.md**: Full project documentation

## 🚀 What's Next (v1.2)

- Enhanced Laxmana AI animations
- Multi-agent collaboration mode
- Code review & auto-refactoring
- Project-wide intelligent search
- GitHub Copilot-style completions
- Local model support (Llama.cpp)

---

**Happy Coding with LAXCODE!** 🎉

Powered by Laxmana AI
