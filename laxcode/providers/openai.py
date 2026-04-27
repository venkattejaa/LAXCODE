"""OpenAI API Provider for LAXCODE"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .base import Provider, Message, Response, ToolCall, ProviderConfig


class OpenAIProvider(Provider):
    """OpenAI API Provider"""
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    AVAILABLE_MODELS = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4-turbo": "gpt-4-turbo",
        "gpt-4": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = self.DEFAULT_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
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
        
        model = self.config.model or "gpt-4o-mini"
        
        payload = {
            "model": model,
            "messages": self.prepare_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": False,
        }
        
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
            raise RuntimeError(f"OpenAI API error: {e}") from e
    
    async def chat_stream(self, messages: List[Message]) -> AsyncIterator[str]:
        """Stream chat response"""
        session = await self._ensure_session()
        
        model = self.config.model or "gpt-4o-mini"
        
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
            raise RuntimeError(f"OpenAI streaming error: {e}") from e
    
    def get_available_models(self) -> List[str]:
        return list(self.AVAILABLE_MODELS.keys())
    
    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
