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
    # Meta Llama Models
    "llama-3.1-8b": "meta/llama-3.1-8b-instruct",
    "llama-3.1-70b": "meta/llama-3.1-70b-instruct",
    "llama-3.1-405b": "meta/llama-3.1-405b-instruct",
    "llama-3.2-1b": "meta/llama-3.2-1b-instruct",
    "llama-3.2-3b": "meta/llama-3.2-3b-instruct",
    "llama-3.3-70b": "meta/llama-3.3-70b-instruct",
    "llama-2-7b": "meta/llama-2-7b-chat",
    "llama-2-70b": "meta/llama-2-70b-chat",
    # NVIDIA Models
    "nemotron-4-340b": "nvidia/nemotron-4-340b-instruct",
    "nemotron-reward": "nvidia/nemotron-4-340b-reward",
    "nemotron-3-8b": "nvidia/nemotron-3-8b-chat",
    # Microsoft Phi Models
    "phi-3-medium": "microsoft/phi-3-medium-128k-instruct",
    "phi-3-mini": "microsoft/phi-3-mini-128k-instruct",
    "phi-3-small": "microsoft/phi-3-small-128k-instruct",
    # Mistral Models
    "mistral-7b": "mistralai/mistral-7b-instruct-v0.3",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct-v0.1",
    "mistral-large": "mistralai/mistral-large-2.1",
    # Google Gemma Models
    "gemma-2-9b": "google/gemma-2-9b-it",
    "gemma-2-27b": "google/gemma-2-27b-it",
    "gemma-7b": "google/gemma-7b-it",
    # Moonshot AI Kimi Models (from screenshots)
    "kimi-k2-instruct": "moonshotai/kimi-k2-instruct",
    "kimi-k2-instruct-0905": "moonshotai/kimi-k2-instruct-0905",
    "kimi-k2-thinking": "moonshotai/kimi-k2-thinking",
    "kimi-k2.5": "moonshotai/kimi-k2.5",
    # Qwen Models
    "qwen2-7b": "qwen/qwen2-7b-instruct",
    "qwen2-72b": "qwen/qwen2-72b-instruct",
    "qwen2-5-7b": "qwen/qwen2.5-7b-instruct",
    "qwen2-5-72b": "qwen/qwen2.5-72b-instruct",
    "qwen2-5-coder-7b": "qwen/qwen2.5-coder-7b-instruct",
    "qwen2-5-coder-32b": "qwen/qwen2.5-coder-32b-instruct",
    # DeepSeek Models (from screenshots)
    "deepseek-v3.2": "deepseek-ai/deepseek-v3.2",
    "deepseek-v4-flash": "deepseek-ai/deepseek-v4-flash",
    "deepseek-v4-pro": "deepseek-ai/deepseek-v4-pro",
    "deepseek-v3.1-terminus": "deepseek-ai/deepseek-v3.1-terminus",
    "deepseek-coder-6.7b": "deepseek-ai/deepseek-coder-6.7b-instruct",
    "deepseek-coder-33b": "deepseek-ai/deepseek-coder-33b-instruct",
    "deepseek-llm-67b": "deepseek-ai/deepseek-llm-67b-chat",
    "deepseek-v2": "deepseek-ai/deepseek-v2-chat",
    "deepseek-v3": "deepseek-ai/deepseek-v3",
    # CodeLlama Models
    "codellama-7b": "meta/codellama-7b-instruct",
    "codellama-34b": "meta/codellama-34b-instruct",
    "codellama-70b": "meta/codellama-70b-instruct",
    # Other Popular Models
    "fuyu-8b": "adept/fuyu-8b",
    "starcoder2-15b": "bigcode/starcoder2-15b",
    "starcoder2-7b": "bigcode/starcoder2-7b",
    "persimmon-8b": "adept/persimmon-8b-chat",
    "bloomz-7b1": "bigscience/bloomz-7b1",
    "mamba-codestral-7b": "mistralai/mamba-codestral-7b-v0.1",
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
    
    async def chat(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> Response:
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
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
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
        # Meta Llama Models
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
        "meta/llama-3.2-1b-instruct": {
            "description": "Llama 3.2 1B - Ultra-fast edge model",
            "context_length": 128000,
            "recommended_for": ["quick tasks", "mobile", "edge"],
        },
        "meta/llama-3.2-3b-instruct": {
            "description": "Llama 3.2 3B - Fast edge model",
            "context_length": 128000,
            "recommended_for": ["quick tasks", "mobile"],
        },
        "meta/llama-3.3-70b-instruct": {
            "description": "Llama 3.3 70B - Latest high quality model",
            "context_length": 128000,
            "recommended_for": ["complex coding", "reasoning"],
        },
        "meta/llama-2-7b-chat": {
            "description": "Llama 2 7B - Classic chat model",
            "context_length": 4096,
            "recommended_for": ["chat", "basic tasks"],
        },
        "meta/llama-2-70b-chat": {
            "description": "Llama 2 70B - Classic large model",
            "context_length": 4096,
            "recommended_for": ["complex tasks"],
        },
        # NVIDIA Models
        "nvidia/nemotron-4-340b-instruct": {
            "description": "Nemotron 4 340B - NVIDIA's own model",
            "context_length": 4096,
            "recommended_for": ["coding", "instruction following"],
        },
        "nvidia/nemotron-3-8b-chat": {
            "description": "Nemotron 3 8B - Efficient chat model",
            "context_length": 4096,
            "recommended_for": ["chat", "coding"],
        },
        # Microsoft Phi Models
        "microsoft/phi-3-medium-128k-instruct": {
            "description": "Phi-3 Medium - Fast and capable",
            "context_length": 128000,
            "recommended_for": ["quick tasks", "chat"],
        },
        "microsoft/phi-3-small-128k-instruct": {
            "description": "Phi-3 Small - Compact and fast",
            "context_length": 128000,
            "recommended_for": ["quick tasks"],
        },
        # Mistral Models
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
        "mistralai/mistral-large-2.1": {
            "description": "Mistral Large 2.1 - Best Mistral model",
            "context_length": 128000,
            "recommended_for": ["complex coding", "reasoning"],
        },
        # Moonshot AI Models
        "moonshotai/moonshot-v1-8b-chat": {
            "description": "Moonshot V1 8B - Fast chat model",
            "context_length": 128000,
            "recommended_for": ["chat", "quick tasks"],
        },
        "moonshotai/moonshot-v1-32b-chat": {
            "description": "Moonshot V1 32B - Balanced chat model",
            "context_length": 128000,
            "recommended_for": ["chat", "coding"],
        },
        "moonshotai/moonshot-v1-72b-chat": {
            "description": "Moonshot V1 72B - High quality chat",
            "context_length": 128000,
            "recommended_for": ["complex tasks", "reasoning"],
        },
        "moonshotai/moonshot-v1-128k": {
            "description": "Moonshot 128K - Long context model",
            "context_length": 128000,
            "recommended_for": ["long documents", "analysis"],
        },
        # Qwen Models
        "qwen/qwen2-7b-instruct": {
            "description": "Qwen2 7B - Alibaba's efficient model",
            "context_length": 32768,
            "recommended_for": ["coding", "chat"],
        },
        "qwen/qwen2-72b-instruct": {
            "description": "Qwen2 72B - Alibaba's large model",
            "context_length": 128000,
            "recommended_for": ["complex tasks", "reasoning"],
        },
        "qwen/qwen2.5-7b-instruct": {
            "description": "Qwen2.5 7B - Latest 7B model",
            "context_length": 128000,
            "recommended_for": ["coding", "chat", "analysis"],
        },
        "qwen/qwen2.5-72b-instruct": {
            "description": "Qwen2.5 72B - Latest large model",
            "context_length": 128000,
            "recommended_for": ["complex coding", "reasoning"],
        },
        "qwen/qwen2.5-coder-7b-instruct": {
            "description": "Qwen2.5 Coder 7B - Code specialist",
            "context_length": 128000,
            "recommended_for": ["coding", "code completion"],
        },
        "qwen/qwen2.5-coder-32b-instruct": {
            "description": "Qwen2.5 Coder 32B - Advanced code model",
            "context_length": 128000,
            "recommended_for": ["complex coding", "code review"],
        },
        # DeepSeek Models
        "deepseek-ai/deepseek-coder-6.7b-instruct": {
            "description": "DeepSeek Coder 6.7B - Code specialist",
            "context_length": 16384,
            "recommended_for": ["coding", "code completion"],
        },
        "deepseek-ai/deepseek-coder-33b-instruct": {
            "description": "DeepSeek Coder 33B - Advanced coding",
            "context_length": 16384,
            "recommended_for": ["complex coding", "code review"],
        },
        "deepseek-ai/deepseek-llm-67b-chat": {
            "description": "DeepSeek LLM 67B - General purpose",
            "context_length": 4096,
            "recommended_for": ["chat", "reasoning"],
        },
        "deepseek-ai/deepseek-v2-chat": {
            "description": "DeepSeek V2 - Advanced reasoning",
            "context_length": 128000,
            "recommended_for": ["complex reasoning", "analysis"],
        },
        "deepseek-ai/deepseek-v3": {
            "description": "DeepSeek V3 - Latest flagship",
            "context_length": 128000,
            "recommended_for": ["coding", "reasoning", "analysis"],
        },
        # CodeLlama Models
        "meta/codellama-7b-instruct": {
            "description": "CodeLlama 7B - Code specialist",
            "context_length": 16384,
            "recommended_for": ["coding", "code completion"],
        },
        "meta/codellama-34b-instruct": {
            "description": "CodeLlama 34B - Advanced coding",
            "context_length": 16384,
            "recommended_for": ["complex coding"],
        },
        "meta/codellama-70b-instruct": {
            "description": "CodeLlama 70B - Best code model",
            "context_length": 16384,
            "recommended_for": ["complex coding", "code review"],
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
