## LAXCODE v1.2.0

### New Features
- **Diff-based editing** with `apply_diff` tool - safer, reviewable changes using unified diff format
- **Test runner** (`run_tests`) - automatically run pytest and iterate on failures
- **Code linter** (`lint`) - integrated ruff support for style checking
- **Moonshot Kimi provider** - support for kimi-k2.5, k1.6, and k2 models

### Bug Fixes
- Fixed `edit` tool creating new files when `old_string=""` (was failing silently)
- Fixed SYSTEM_PROMPT template escaping causing KeyError on `{name}` variables
- Fixed agent loop indentation error causing syntax issues with while-else
- Removed Unicode characters from SimpleAnimator spinner for Windows compatibility
- Fixed splash screen Unicode box drawing characters causing encoding errors

### Improvements
- Test-driven development guidance in agent prompts
- Enhanced agent loop with verification steps
- Better code quality enforcement
- All 22 unit tests now passing
- ASCII-safe terminal animations for cross-platform support

### Installation
```bash
pip install laxcode
```

Or upgrade:
```bash
pip install --upgrade laxcode
```
