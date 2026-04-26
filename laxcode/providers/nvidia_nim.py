"""NVIDIA NIM API Provider for LAXCODE

Supports free models from NVIDIA NIM:
- meta/llama-3.1-8b-instruct
- meta/llama-3.1-70b-instruct  
- meta/llama-3.1-405b-instruct
- nvidia/nemotron-4-340b-instruct
- nvidia/nemotron-4-340b-reward
- microsoft/phi-3-medium-128k-instruct
- microsoft/phi-3-mini-128k-instruct
- mistralai/mistral-7b-instruct-v0.3
- mistralai/mixtral-8x7b-instruct-v0.1
- google/gemma-2-9b-it
- google/gemma-2-27b-it
"""

from __future__ import annotations

import json
import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .base import Provider, Message, Response, ToolCall, ProviderConfig


class NvidiaNIMProvider(Provider):
    """
    NVIDIA NIM API Provider
    
    Get your free API key from: https://build.nvidia.com/explore
    """
    
    DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    AVAILABLE_MODELS = {
        "llama-3.1-8b": "meta/llama-3.1-8b-instruct",
        "llama-3.1-70b": "meta/llama-3.1-70b-instruct",
        "llama-3.1-405b": "meta/llama-3.1-405b-instruct",
        "nemotron-4-340b": "nvidia/nemotron-4-340b-instruct",
        "nemotron-reward": "nvidia/nemotron-4-340b-reward",
        "phi-3-medium": "microsoft/phi-3-medium-128k-instruct",
        "phi-3-mini": "microsoft/phi-3-mini-128k-instruct",
        "mistral-7b": "mistralai/mistral-7b-instruct-v0.3",
        "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct-v0.1",
        "gemma-2-9b": "google/gemma-2-9b-it",
        "gemma-2-27b": "google/gemma-2-27b-it",
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = self.DEFAULT_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        return "NVIDIA NIM"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self.session
    
    async def chat(self, messages: List[Message]) -> Response:
        """Send chat request and get complete response"""
        session = await self._ensure_session()
        
        model = self.config.model or self.AVAILABLE_MODELS["llama-3.1-8b"]
        
        payload = {
            "model": model,
            "messages": self.prepare_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": False,
        }
        
        try:
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                choice = data["choices"][0]
                message = choice["message"]
                
                # Parse tool calls if present
                tool_calls = []
                if "tool_calls" in message:
                    for tc in message["tool_calls"]:
                        if tc["type"] == "function":
                            tool_calls.append(ToolCall(
                                id=tc["id"],
                                name=tc["function"]["name"],
                                arguments=json.loads(tc["function"]["arguments"])
                            ))
                
                return Response(
                    content=message.get("content", ""),
                    tool_calls=tool_calls,
                    input_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                    output_tokens=data.get("usage", {}).get("completion_tokens", 0),
                    model=model,
                    finish_reason=choice.get("finish_reason"),
                    raw_response=data
                )
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"NVIDIA NIM API error: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse NVIDIA NIM response: {e}") from e
    
    async def chat_stream(self, messages: List[Message]) -> AsyncIterator[str]:
        """Stream chat response"""
        session = await self._ensure_session()
        
        model = self.config.model or self.AVAILABLE_MODELS["llama-3.1-8b"]
        
        payload = {
            "model": model,
            "messages": self.prepare_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": True,
        }
        
        try:
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line or line.startswith(':'):
                        continue
                    
                    if line.startswith('data: '):
                        data = line[6:]
                        
                        if data == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"NVIDIA NIM streaming error: {e}") from e
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.AVAILABLE_MODELS.keys())
    
    def get_full_model_name(self, alias: str) -> str:
        """Get full model name from alias"""
        return self.AVAILABLE_MODELS.get(alias, alias)
    
    async def close(self) -> None:
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.close())


class NvidiaNIMModelInfo:
    """Model information for NVIDIA NIM"""
    
    MODELS = {
        "meta/llama-3.1-8b-instruct": {
            "description": "Llama 3.1 8B - Fast and efficient for most tasks",
            "context_length": 128000,
            "recommended_for": ["coding", "chat", "analysis"],
        },
        "meta/llama-3.1-70b-instruct": {
            "description": "Llama 3.1 70B - High quality responses",
            "context_length": 128000,
            "recommended_for": ["complex coding", "reasoning", "analysis"],
        },
        "meta/llama-3.1-405b-instruct": {
            "description": "Llama 3.1 405B - Best quality, slower",
            "context_length": 128000,
            "recommended_for": ["most complex tasks", "research"],
        },
        "nvidia/nemotron-4-340b-instruct": {
            "description": "Nemotron 4 340B - NVIDIA's own model",
            "context_length": 4096,
            "recommended_for": ["coding", "instruction following"],
        },
        "microsoft/phi-3-medium-128k-instruct": {
            "description": "Phi-3 Medium - Fast and capable",
            "context_length": 128000,
            "recommended_for": ["quick tasks", "chat"],
        },
        "mistralai/mistral-7b-instruct-v0.3": {
            "description": "Mistral 7B - Efficient and capable",
            "context_length": 32768,
            "recommended_for": ["coding", "chat", "analysis"],
        },
        "mistralai/mixtral-8x7b-instruct-v0.1": {
            "description": "Mixtral 8x7B - MoE architecture",
            "context_length": 32768,
            "recommended_for": ["complex tasks", "reasoning"],
        },
        "google/gemma-2-9b-it": {
            "description": "Gemma 2 9B - Google's model",
            "context_length": 8192,
            "recommended_for": ["lightweight tasks", "chat"],
        },
    }
    
    @classmethod
    def get_info(cls, model: str) -> Dict[str, Any]:
        return cls.MODELS.get(model, {
            "description": "Unknown model",
            "context_length": 4096,
            "recommended_for": ["general"],
        })
    
    @classmethod
    def print_model_table(cls) -> str:
        """Print model information as formatted text"""
        lines = [
            "[bold cyan]Available NVIDIA NIM Models[/bold cyan]",
            "",
        ]
        
        for alias, full_name in NvidiaNIMProvider.AVAILABLE_MODELS.items():
            info = cls.get_info(full_name)
            lines.append(f"[bold green]{alias}[/bold green]")
            lines.append(f"  Full: {full_name}")
            lines.append(f"  {info['description']}")
            lines.append(f"  Context: {info['context_length']:,} tokens")
            lines.append("")
        
        return "\n".join(lines)
