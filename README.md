# LAXCODE

**An agentic AI coding assistant for your terminal.** Reads your files, writes code, runs shell commands, and remembers context — powered by NVIDIA NIM (free), OpenAI, or Anthropic.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Version](https://img.shields.io/badge/version-1.1.0-green.svg)
![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM-76B900?logo=nvidia&logoColor=white)

---

## What it does

LAXCODE runs in your terminal and acts as a coding agent. You talk to it in plain English — it reads your codebase, writes or edits files, runs bash commands, and searches through your project. It keeps the full conversation in a session so it understands context across messages.

Unlike most AI coding tools, **NVIDIA NIM support means you can run it completely free** — no OpenAI subscription required.

---

## Features

- **Multi-provider** — NVIDIA NIM (free), OpenAI, Anthropic Claude
- **File operations** — read, edit, glob patterns, directory view
- **Shell execution** — runs bash commands with safety checks
- **Code search** — grep across your entire project
- **Session persistence** — conversation history saved to `~/.laxcode/sessions/`
- **Laxmana AI animations** — terminal state indicators (idle, processing, working, error)
- **Single message mode** — use it non-interactively in scripts

---

## Installation

```bash
git clone https://github.com/venkattejaa/LAXCODE.git
cd LAXCODE
pip install -e .
```

PyPI package coming in v1.2.

---

## Quick start

### 1. Get a free NVIDIA NIM API key

Go to [build.nvidia.com/explore](https://build.nvidia.com/explore) → sign up → copy your key. It's free.

### 2. Configure

```bash
laxcode setup
```

Or set directly:

```bash
laxcode --set-nvidia-key YOUR_API_KEY
```

### 3. Run

```bash
# Interactive mode
laxcode

# Single message
laxcode "Write a FastAPI endpoint that returns a list of users"
```

---

## Usage

### Interactive commands

| Command | What it does |
|---|---|
| `/read <path>` | Read a file with line numbers |
| `/glob <pattern>` | Find files matching a pattern |
| `/grep <pattern>` | Search for text across files |
| `/config` | Show current config |
| `/sessions` | List saved sessions |
| `/tools` | List available tools |
| `/clear` | Clear screen |
| `/exit` | Exit |

### Example session

```
❯❯❯ /read src/api.py

❯❯❯ This endpoint has no input validation. Add Pydantic models.

[LAXCODE reads the file, writes the fix, and applies it]

❯❯❯ Now add unit tests for it

[LAXCODE creates test_api.py with pytest tests]
```

---

## Providers

| Provider | Cost | Setup |
|---|---|---|
| NVIDIA NIM | **Free** | `laxcode setup` → select NIM |
| OpenAI | Paid | `export OPENAI_API_KEY=...` |
| Anthropic | Paid | `export ANTHROPIC_API_KEY=...` |

**Recommended free models via NVIDIA NIM:**

- `llama-3.1-8b` — fast, good for most tasks
- `llama-3.1-70b` — higher quality, slower
- `mistral-7b` — efficient

---

## Configuration

Stored at `~/.laxcode/config.json`:

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

---

## Animation states

The terminal shows live state via the Laxmana AI animation system:

| State | Color | Meaning |
|---|---|---|
| Idle | 🟡 Gold | Waiting for input |
| Listening | 🟢 Green | Ready |
| Processing | 🟣 Purple | Thinking |
| Working | 🔵 Cyan | Generating/editing |
| Error | 🔴 Red | Something failed |

---

## Safety

- File operations are restricted to the working directory
- Destructive shell commands are blocked
- API keys are stored in `~/.laxcode/` and never committed

---

## Troubleshooting

**"No API key configured"**

```bash
laxcode setup
```

**Windows Unicode issue**

```bash
chcp 65001
```

**`laxcode` command not found**

```bash
pip install -e .
```

---

## Built by

**Sugali Venkata Teja Naik** — AI engineer and full-stack developer from Guntakal, Andhra Pradesh.

Part of the [LAXMANA](https://github.com/venkattejaa) ecosystem — a 768M parameter multilingual LLM built from scratch.

- GitHub: [@venkattejaa](https://github.com/venkattejaa)
- Portfolio: [venkattejaa.github.io/portfolio](https://venkattejaa.github.io/portfolio)

---

## License

MIT — see [LICENSE](LICENSE)
