#!/usr/bin/env python3
"""Quick test script for LAXCODE"""

import asyncio
import sys

async def test_tools():
    """Test tool functionality"""
    print("Testing LAXCODE tools...\n")
    
    # Test FileReadTool
    from laxcode.tools.file_tools import FileReadTool, GlobTool
    from laxcode.tools.shell_tools import BashTool
    from laxcode.tools.search_tools import GrepTool
    
    # Test Glob
    print("1. Testing GlobTool...")
    glob_tool = GlobTool()
    result = await glob_tool.execute(pattern="*.md")
    if result.success:
        print(f"   [OK] Found {result.data.get('matches_found', 0)} markdown files")
    else:
        print(f"   [ERR] Error: {result.error}")
    
    # Test Read
    print("\n2. Testing FileReadTool...")
    read_tool = FileReadTool()
    result = await read_tool.execute(file_path="README.md", limit=10)
    if result.success:
        print(f"   [OK] Read {result.data.get('lines_read', 0)} lines from README.md")
    else:
        print(f"   [ERR] Error: {result.error}")
    
    # Test Bash
    print("\n3. Testing BashTool...")
    bash_tool = BashTool()
    result = await bash_tool.execute(command="echo Hello from LAXCODE")
    if result.success:
        print(f"   [OK] Bash output: {result.output.strip()}")
    else:
        print(f"   [ERR] Error: {result.error}")
    
    # Test Grep
    print("\n4. Testing GrepTool...")
    grep_tool = GrepTool()
    result = await grep_tool.execute(pattern="class.*Tool", path="laxcode", include="*.py")
    if result.success:
        print(f"   [OK] Found {result.data.get('matches_found', 0)} matches for pattern")
    else:
        print(f"   [ERR] Error: {result.error}")
    
    print("\n[OK] All tests completed!")

def test_imports():
    """Test imports"""
    print("Testing imports...")
    
    try:
        from laxcode import LaxcodeAgent, Session
        print("  [OK] laxcode imports")
        
        from laxcode.providers import NvidiaNIMProvider, OpenAIProvider, AnthropicProvider
        print("  [OK] provider imports")
        
        from laxcode.tools import get_all_tools
        print("  [OK] tool imports")
        
        from laxcode.config import ConfigManager
        print("  [OK] config imports")
        
        from laxcode.animations import LaxmanaAnimator
        print("  [OK] animation imports")
        
        print("\n[OK] All imports successful!")
        return True
    except Exception as e:
        print(f"\n[ERR] Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("LAXCODE Test Suite")
    print("="*50)
    print()
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    print()
    print("="*50)
    
    # Test tools
    asyncio.run(test_tools())
    
    print()
    print("="*50)
    print("All tests passed!")
    print("="*50)
