"""Anthropic Claude API Provider for LAXCODE"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .base import Provider, Message, Response, ToolCall, ProviderConfig, MessageRole


class AnthropicProvider(Provider):
    """Anthropic Claude API Provider"""
    
    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    
    AVAILABLE_MODELS = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20240620",
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = self.DEFAULT_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        return "Anthropic Claude"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
    
    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[Dict]]:
        """Convert to Anthropic format (system + messages)"""
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message += msg.content + "\n"
            elif msg.role == MessageRole.USER:
                anthropic_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == MessageRole.ASSISTANT:
                anthropic_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        return system_message.strip(), anthropic_messages
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self.session
    
    async def chat(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> Response:
        """Send chat request and get complete response"""
        session = await self._ensure_session()
        
        model = self.config.model or "claude-3-sonnet"
        system, anthropic_messages = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "system": system,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        
        # Anthropic has different tool format - skip for now
        
        try:
            async with session.post(
                f"{self.config.base_url}/messages",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                return Response(
                    content=data["content"][0]["text"],
                    tool_calls=[],
                    input_tokens=data.get("usage", {}).get("input_tokens", 0),
                    output_tokens=data.get("usage", {}).get("output_tokens", 0),
                    model=model,
                    finish_reason=data.get("stop_reason"),
                    raw_response=data
                )
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Anthropic API error: {e}") from e
    
    async def chat_stream(self, messages: List[Message]) -> AsyncIterator[str]:
        """Stream chat response"""
        session = await self._ensure_session()
        
        model = self.config.model or "claude-3-sonnet"
        system, anthropic_messages = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "system": system,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "stream": True,
        }
        
        try:
            async with session.post(
                f"{self.config.base_url}/messages",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line or not line.startswith('data: '):
                        continue
                    
                    data = line[6:]
                    
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data)
                        if chunk.get("type") == "content_block_delta":
                            if "delta" in chunk and "text" in chunk["delta"]:
                                yield chunk["delta"]["text"]
                    except json.JSONDecodeError:
                        continue
                        
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Anthropic streaming error: {e}") from e
    
    def get_available_models(self) -> List[str]:
        return list(self.AVAILABLE_MODELS.keys())
    
    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
