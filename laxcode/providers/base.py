"""Base provider interface for LAXCODE"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from enum import Enum


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A message in the conversation"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result
    
    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=MessageRole.SYSTEM, content=content)
    
    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=MessageRole.USER, content=content)
    
    @classmethod
    def assistant(cls, content: str, tool_calls: Optional[List[Dict]] = None) -> "Message":
        return cls(role=MessageRole.ASSISTANT, content=content, tool_calls=tool_calls)


@dataclass
class ToolCall:
    """A tool call from the model"""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": str(self.arguments)
            }
        }


@dataclass
class Response:
    """Response from the LLM"""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


@dataclass
class ProviderConfig:
    """Configuration for a provider"""
    api_key: str
    base_url: Optional[str] = None
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    timeout: float = 120.0
    
    def __post_init__(self):
        if not self.api_key:
            raise ValueError("API key is required")


class Provider(abc.ABC):
    """Base class for LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
    
    @abc.abstractmethod
    async def chat(self, messages: List[Message]) -> Response:
        """Send a chat request and get a complete response"""
        pass
    
    @abc.abstractmethod
    async def chat_stream(self, messages: List[Message]) -> AsyncIterator[str]:
        """Send a chat request and stream the response"""
        pass
    
    @abc.abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    def _count_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def prepare_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert messages to provider format"""
        return [msg.to_dict() for msg in messages]
