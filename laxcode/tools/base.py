"""Base tool interface for LAXCODE"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, output: str = "", **data) -> "ToolResult":
        return cls(success=True, output=output, data=data)
    
    @classmethod
    def error(cls, message: str, **data) -> "ToolResult":
        return cls(success=False, error=message, data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "data": self.data,
        }


@dataclass
class ToolParameter:
    """Parameter definition for a tool"""
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "description": self.description,
        }
        if self.enum:
            result["enum"] = self.enum
        if self.default is not None:
            result["default"] = self.default
        return result


class Tool(abc.ABC):
    """Base class for tools"""
    
    name: str = ""
    description: str = ""
    parameters: List[ToolParameter] = []
    dangerous: bool = False
    
    def __init__(self):
        pass
    
    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI-compatible tool schema"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_dict()
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """Validate parameters"""
        for param in self.parameters:
            if param.required and param.name not in params:
                return f"Missing required parameter: {param.name}"
            
            if param.name in params and param.enum is not None:
                if params[param.name] not in param.enum:
                    return f"Invalid value for {param.name}: must be one of {param.enum}"
        
        return None


class ToolRegistry:
    """Registry of all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool_class: Type[Tool]) -> None:
        """Register a tool class"""
        instance = tool_class()
        self._tools[instance.name] = instance
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def list_tools(self) -> List[str]:
        """List all tool names"""
        return list(self._tools.keys())


# Global registry
_registry = ToolRegistry()


def register_tool(tool_class: Type[Tool]) -> Type[Tool]:
    """Decorator to register a tool"""
    _registry.register(tool_class)
    return tool_class


def get_registry() -> ToolRegistry:
    """Get the global tool registry"""
    return _registry
