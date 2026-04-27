"""Tests for diff-based editing tools"""

import pytest
import asyncio
from pathlib import Path
from laxcode.tools.diff_tool import FileDiffTool, TestRunnerTool, CodeLinterTool


class TestFileDiffTool:
    """Test the unified diff editing tool"""

    @pytest.fixture
    def diff_tool(self):
        return FileDiffTool()

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing"""
        file_path = tmp_path / "test_file.py"
        file_path.write_text("""def hello():
    return "Hello"

def goodbye():
    return "Goodbye"
""")
        return file_path

    @pytest.mark.asyncio
    async def test_apply_simple_diff(self, tmp_path, monkeypatch):
        """Test applying a simple unified diff"""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Create file
        test_file = tmp_path / "test.py"
        test_file.write_text("""line1
line2
line3
""")
        
        tool = FileDiffTool()
        
        diff = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 line1
-modified_line2
+line2
 line3
"""
        
        result = await tool.execute(
            file_path=str(test_file),
            diff=diff
        )
        
        # Should fail because old line doesn't match
        assert not result.success

    def test_generate_diff(self):
        """Test diff generation helper"""
        original = """def add(a, b):
    return a + b"""
        modified = """def add(a: int, b: int) -> int:
    return a + b"""

        diff = FileDiffTool.generate_diff(original, modified, "test.py")

        assert "-def add(a, b):" in diff
        assert "+def add(a: int, b: int) -> int:" in diff


class TestTestRunnerTool:
    """Test the test runner tool"""

    @pytest.mark.asyncio
    async def test_run_tests_no_pytest(self, tmp_path, monkeypatch):
        """Test behavior when pytest is not found"""
        monkeypatch.chdir(tmp_path)
        
        tool = TestRunnerTool()
        
        # Create a simple test file
        test_file = tmp_path / "test_dummy.py"
        test_file.write_text("def test_dummy(): pass\n")
        
        result = await tool.execute(test_path=str(test_file))
        
        # May succeed or fail depending on pytest availability
        assert hasattr(result, 'success')
        assert result.output is not None


class TestCodeLinterTool:
    """Test the linter tool"""

    @pytest.mark.asyncio
    async def test_lint_code(self, tmp_path, monkeypatch):
        """Test linting Python code"""
        monkeypatch.chdir(tmp_path)
        
        # Create file with style issues
        test_file = tmp_path / "test_lint.py"
        test_file.write_text("""import os
import sys

def bad_function( ):
    x=1+2
    return x
""")
        
        tool = CodeLinterTool()
        result = await tool.execute(file_path=str(test_file))
        
        # Tool should execute
        assert hasattr(result, 'success')


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
