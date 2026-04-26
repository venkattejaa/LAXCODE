# Contributing to LAXCODE

Thank you for your interest in contributing to LAXCODE! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)

### Suggesting Features

We welcome feature suggestions! Please open an issue with:
- A clear description of the feature
- Why it would be useful
- Any implementation ideas you have

### Pull Requests

1. Fork the repository
2. Create a new branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `python test_laxcode.py`
5. Commit your changes: `git commit -am 'Add my feature'`
6. Push to your branch: `git push origin feature/my-feature`
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/LAXCODE.git
cd LAXCODE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
python test_laxcode.py
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small and focused

## Adding New Tools

1. Create a new class in `laxcode/tools/`
2. Inherit from `Tool` base class
3. Define `name`, `description`, `parameters`
4. Implement `execute()` method
5. Register with `@register_tool` decorator

Example:

```python
from laxcode.tools.base import Tool, ToolResult, ToolParameter, register_tool

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

## Adding New Providers

1. Create a new class in `laxcode/providers/`
2. Inherit from `Provider` base class
3. Implement `chat()`, `chat_stream()`, `get_available_models()`

## License

By contributing to LAXCODE, you agree that your contributions will be licensed under the MIT License.
