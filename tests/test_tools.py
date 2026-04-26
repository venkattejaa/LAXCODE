"""Unit tests for LAXCODE tools"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from laxcode.tools.base import ToolRegistry, get_registry
from laxcode.tools.file_tools import FileReadTool, FileEditTool, GlobTool
from laxcode.tools.shell_tools import BashTool, ViewTool
from laxcode.tools.search_tools import GrepTool


class TestFileReadTool:
    """Tests for FileReadTool"""
    
    @pytest.mark.asyncio
    async def test_read_existing_file(self):
        """Test reading an existing file"""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name
        
        try:
            tool = FileReadTool()
            result = await tool.execute(file_path=temp_path, offset=1, limit=10)
            
            assert result.success
            assert result.data['total_lines'] == 3
            assert 'line1' in result.output
            assert 'line2' in result.output
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading a non-existent file"""
        tool = FileReadTool()
        result = await tool.execute(file_path="/nonexistent/file.txt")
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_read_with_offset(self):
        """Test reading with offset"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for i in range(20):
                f.write(f"line{i}\n")
            temp_path = f.name
        
        try:
            tool = FileReadTool()
            result = await tool.execute(file_path=temp_path, offset=10, limit=5)
            
            assert result.success
            assert result.data['start_line'] == 10
            assert result.data['lines_read'] == 5
        finally:
            os.unlink(temp_path)


class TestFileEditTool:
    """Tests for FileEditTool"""
    
    @pytest.mark.asyncio
    async def test_edit_file(self):
        """Test editing a file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def old_func():\n    pass\n")
            temp_path = f.name
        
        try:
            tool = FileEditTool()
            result = await tool.execute(
                file_path=temp_path,
                old_string="def old_func():\n    pass",
                new_string="def new_func():\n    return True"
            )
            
            assert result.success
            
            # Verify content changed
            content = Path(temp_path).read_text()
            assert "new_func" in content
            assert "old_func" not in content
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_edit_multiple_occurrences(self):
        """Test that editing fails with multiple occurrences"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("hello hello hello")
            temp_path = f.name
        
        try:
            tool = FileEditTool()
            result = await tool.execute(
                file_path=temp_path,
                old_string="hello",
                new_string="goodbye"
            )
            
            assert not result.success
            assert "Multiple occurrences" in result.error
        finally:
            os.unlink(temp_path)


class TestGlobTool:
    """Tests for GlobTool"""
    
    @pytest.mark.asyncio
    async def test_glob_pattern(self):
        """Test globbing with pattern"""
        tool = GlobTool()
        result = await tool.execute(pattern="*.md")
        
        assert result.success
        assert result.data['matches_found'] > 0
    
    @pytest.mark.asyncio
    async def test_glob_specific_path(self):
        """Test globbing in specific path"""
        tool = GlobTool()
        result = await tool.execute(pattern="*.py", path="laxcode")
        
        assert result.success
        assert result.data['matches_found'] > 0


class TestBashTool:
    """Tests for BashTool"""
    
    @pytest.mark.asyncio
    async def test_simple_command(self):
        """Test simple command execution"""
        tool = BashTool()
        result = await tool.execute(command="echo hello")
        
        assert result.success
        assert "hello" in result.output
    
    @pytest.mark.asyncio
    async def test_dangerous_command_blocked(self):
        """Test that dangerous commands are blocked"""
        tool = BashTool()
        result = await tool.execute(command="rm -rf /")
        
        assert not result.success
        assert "Security" in result.error
    
    @pytest.mark.asyncio
    async def test_command_with_description(self):
        """Test command with description"""
        tool = BashTool()
        result = await tool.execute(
            command="echo test",
            description="Testing echo"
        )
        
        assert result.success
        assert result.data['description'] == "Testing echo"


class TestGrepTool:
    """Tests for GrepTool"""
    
    @pytest.mark.asyncio
    async def test_grep_pattern(self):
        """Test basic grep"""
        tool = GrepTool()
        result = await tool.execute(
            pattern="class.*Tool",
            path="laxcode/tools"
        )
        
        assert result.success
        assert result.data['matches_found'] > 0
    
    @pytest.mark.asyncio
    async def test_grep_with_include(self):
        """Test grep with file filter"""
        tool = GrepTool()
        result = await tool.execute(
            pattern="def ",
            path="laxcode/tools",
            include="*.py"
        )
        
        assert result.success
        assert result.data['matches_found'] > 0


class TestViewTool:
    """Tests for ViewTool"""
    
    @pytest.mark.asyncio
    async def test_view_directory(self):
        """Test viewing directory structure"""
        tool = ViewTool()
        result = await tool.execute(path="laxcode", depth=1)
        
        assert result.success
        assert result.data['entries_found'] > 0
    
    @pytest.mark.asyncio
    async def test_view_current_directory(self):
        """Test viewing current directory"""
        tool = ViewTool()
        result = await tool.execute()
        
        assert result.success


class TestToolRegistry:
    """Tests for ToolRegistry"""
    
    def test_get_registry(self):
        """Test getting global registry"""
        registry = get_registry()
        assert isinstance(registry, ToolRegistry)
    
    def test_list_tools(self):
        """Test listing registered tools"""
        registry = get_registry()
        tools = registry.list_tools()
        
        # Check core tools are registered
        assert "read" in tools
        assert "edit" in tools
        assert "glob" in tools
        assert "bash" in tools
        assert "grep" in tools
    
    def test_get_tool(self):
        """Test getting a specific tool"""
        registry = get_registry()
        tool = registry.get("read")
        
        assert tool is not None
        assert tool.name == "read"
    
    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist"""
        registry = get_registry()
        tool = registry.get("nonexistent")
        
        assert tool is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
