"""Session management for LAXCODE"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionMessage:
    """A message in a session"""
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Session:
    """A LAXCODE session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    messages: List[SessionMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    workspace: str = ""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to the session"""
        self.messages.append(SessionMessage(
            role=role,
            content=content,
            metadata=metadata
        ))
        self.updated_at = datetime.now().isoformat()
    
    def add_user_message(self, content: str) -> None:
        """Add a user message"""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str, **metadata) -> None:
        """Add an assistant message"""
        self.add_message("assistant", content, **metadata)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message"""
        self.add_message("system", content)
    
    def update_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Update token counts"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
    
    def get_recent_messages(self, limit: int = 10) -> List[SessionMessage]:
        """Get recent messages"""
        return self.messages[-limit:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "workspace": self.workspace,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())[:8]),
            messages=[SessionMessage.from_dict(m) for m in data.get("messages", [])],
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            workspace=data.get("workspace", ""),
            total_input_tokens=data.get("total_input_tokens", 0),
            total_output_tokens=data.get("total_output_tokens", 0),
            metadata=data.get("metadata", {}),
        )
    
    def to_markdown(self) -> str:
        """Export session as markdown"""
        lines = [
            f"# LAXCODE Session: {self.session_id}",
            "",
            f"**Created:** {self.created_at}",
            f"**Updated:** {self.updated_at}",
            f"**Tokens:** {self.total_input_tokens:,} in / {self.total_output_tokens:,} out",
            "",
            "## Messages",
            "",
        ]
        
        for msg in self.messages:
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.role, "💬")
            lines.append(f"### {role_emoji} {msg.role.upper()}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
        
        return "\n".join(lines)


class SessionStore:
    """Store for managing sessions"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".laxcode" / "sessions"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Session] = {}
    
    def create(self, workspace: str = "") -> Session:
        """Create a new session"""
        session = Session(workspace=workspace or str(Path.cwd()))
        self._sessions[session.session_id] = session
        return session
    
    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        # Check memory first
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Try to load from disk
        session_file = self.base_path / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                self._sessions[session_id] = session
                return session
            except Exception:
                return None
        
        return None
    
    def save(self, session: Session) -> None:
        """Save a session to disk"""
        session_file = self.base_path / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2)
    
    def list_sessions(self) -> List[Session]:
        """List all saved sessions"""
        sessions = []
        for session_file in self.base_path.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append(Session.from_dict(data))
            except Exception:
                continue
        
        # Sort by updated_at (newest first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions
    
    def delete(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        session_file = self.base_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        
        return False


# Global session store
_session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Get the global session store"""
    return _session_store
