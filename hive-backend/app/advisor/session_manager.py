"""
Session Manager Module
Manages session state for multi-turn conversations.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import asyncio


@dataclass
class MessagePair:
    """A pair of user and assistant messages."""
    user_message: str
    assistant_message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessagePair':
        return cls(**data)


@dataclass
class ConversationWindow:
    """5-level conversation window with auto-summarization."""
    pairs: List[MessagePair] = field(default_factory=list)
    summary: Optional[str] = None
    summarized_pair_count: int = 0
    max_pairs: int = 5
    
    def add_pair(self, user_msg: str, assistant_msg: str):
        """Add a new message pair to the window."""
        pair = MessagePair(
            user_message=user_msg,
            assistant_message=assistant_msg
        )
        self.pairs.append(pair)
    
    def should_summarize(self) -> bool:
        """Check if window should be summarized."""
        return len(self.pairs) >= self.max_pairs
    
    def get_messages_for_summarization(self) -> List[Dict[str, str]]:
        """Get old pairs for summarization."""
        if len(self.pairs) <= self.max_pairs:
            return []
        
        # Get pairs beyond the most recent 5
        old_pairs = self.pairs[:-self.max_pairs]
        return [
            {"user": p.user_message, "assistant": p.assistant_message}
            for p in old_pairs
        ]
    
    def compress_with_summary(self, summary: str):
        """Compress old pairs into summary and keep recent ones."""
        old_count = len(self.pairs) - self.max_pairs
        if old_count > 0:
            self.summarized_pair_count += old_count
            self.pairs = self.pairs[-self.max_pairs:]  # Keep only last 5
            self.summary = summary
    
    def get_context_pairs(self) -> List[MessagePair]:
        """Get current pairs in the window."""
        return self.pairs[-self.max_pairs:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pairs": [p.to_dict() for p in self.pairs],
            "summary": self.summary,
            "summarized_pair_count": self.summarized_pair_count,
            "max_pairs": self.max_pairs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationWindow':
        window = cls(
            summary=data.get("summary"),
            summarized_pair_count=data.get("summarized_pair_count", 0),
            max_pairs=data.get("max_pairs", 5)
        )
        window.pairs = [MessagePair.from_dict(p) for p in data.get("pairs", [])]
        return window


@dataclass
class SessionState:
    """Session state for a conversation."""
    session_id: str
    programme: Optional[str] = None
    current_term: Optional[str] = None
    selected_course_code: Optional[str] = None
    mode: str = "GENERAL"  # STRUCTURE | DETAILS | GENERAL
    conversation_window: ConversationWindow = field(default_factory=ConversationWindow)
    history: List[Dict[str, Any]] = field(default_factory=list)  # Deprecated, use conversation_window
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Manually convert conversation_window
        data['conversation_window'] = self.conversation_window.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create from dictionary."""
        # Extract conversation_window separately
        conv_window_data = data.pop('conversation_window', None)
        session = cls(**data)
        
        if conv_window_data:
            session.conversation_window = ConversationWindow.from_dict(conv_window_data)
        
        return session


class SessionManager:
    """Manages session states for conversations."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            storage_dir: Directory to store session files (optional)
        """
        self.sessions: Dict[str, SessionState] = {}
        self.storage_dir = storage_dir
        
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session(self, session_id: str) -> SessionState:
        """
        Get or create session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            SessionState
        """
        if session_id not in self.sessions:
            # Try to load from storage
            if self.storage_dir:
                session_file = self.storage_dir / f"{session_id}.json"
                if session_file.exists():
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.sessions[session_id] = SessionState.from_dict(data)
                        return self.sessions[session_id]
            
            # Create new session
            self.sessions[session_id] = SessionState(session_id=session_id)
        
        return self.sessions[session_id]
    
    def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> SessionState:
        """
        Update session with new data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of updates
        
        Returns:
            Updated SessionState
        """
        session = self.get_session(session_id)
        
        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        # Update timestamp
        session.updated_at = datetime.utcnow().isoformat()
        
        # Save to storage if enabled
        if self.storage_dir:
            self._save_session(session)
        
        return session
    
    def add_to_history(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add message to session history.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        session = self.get_session(session_id)
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        session.history.append(message)
        session.updated_at = datetime.utcnow().isoformat()
        
        # Keep only last 50 messages to prevent memory bloat
        if len(session.history) > 50:
            session.history = session.history[-50:]
        
        if self.storage_dir:
            self._save_session(session)
    
    def clear_session(self, session_id: str):
        """
        Clear session data.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if self.storage_dir:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
    
    def set_programme(self, session_id: str, programme: str):
        """Set programme for session."""
        self.update_session(session_id, {'programme': programme})
    
    def set_current_term(self, session_id: str, term: str):
        """Set current term for session."""
        self.update_session(session_id, {'current_term': term})
    
    def set_mode(self, session_id: str, mode: str):
        """Set conversation mode."""
        self.update_session(session_id, {'mode': mode})
    
    def set_selected_course(self, session_id: str, course_code: str):
        """Set currently selected course."""
        self.update_session(session_id, {'selected_course_code': course_code})
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context for programme detection and routing.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Context dictionary
        """
        session = self.get_session(session_id)
        
        return {
            'programme': session.programme,
            'current_term': session.current_term,
            'selected_course_code': session.selected_course_code,
            'mode': session.mode,
            'history': session.history[-10:],  # Last 10 messages
            'metadata': session.metadata
        }
    
    async def add_conversation_pair(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str
    ) -> bool:
        """
        Add a conversation pair and auto-summarize if needed.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_message: Assistant's response
        
        Returns:
            True if summarization occurred
        """
        session = self.get_session(session_id)
        
        # Add pair to conversation window
        session.conversation_window.add_pair(user_message, assistant_message)
        session.updated_at = datetime.utcnow().isoformat()
        
        # Check if we should summarize
        if session.conversation_window.should_summarize() and len(session.conversation_window.pairs) > 5:
            await self._compress_conversation(session)
            
            # Save after summarization
            if self.storage_dir:
                self._save_session(session)
            
            return True
        
        # Save session
        if self.storage_dir:
            self._save_session(session)
        
        return False
    
    async def _compress_conversation(self, session: SessionState):
        """
        Compress conversation using LLM summarization.
        
        Args:
            session: Session to compress
        """
        # Get messages to summarize
        messages_to_summarize = session.conversation_window.get_messages_for_summarization()
        
        if not messages_to_summarize:
            return
        
        # Import summarizer
        from app.services.summarizer import summarize_conversation
        
        # Include previous summary if exists
        if session.conversation_window.summary:
            # Prepend previous summary to context
            messages_to_summarize.insert(0, {
                'user': '[Previous conversation summary]',
                'assistant': session.conversation_window.summary
            })
        
        # Generate new summary
        try:
            summary = await summarize_conversation(messages_to_summarize)
            session.conversation_window.compress_with_summary(summary)
        except Exception as e:
            print(f"Summarization error: {e}")
            # On error, just keep the pairs without summary
    
    def get_conversation_context(self, session_id: str) -> str:
        """
        Get formatted conversation context including summary and recent pairs.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Formatted context string for LLM
        """
        session = self.get_session(session_id)
        window = session.conversation_window
        
        context_parts = []
        
        # Add summary if exists
        if window.summary:
            from app.services.summarizer import format_summary_for_context
            summary_text = format_summary_for_context(
                window.summary,
                window.summarized_pair_count
            )
            context_parts.append(summary_text)
        
        # Add recent pairs
        recent_pairs = window.get_context_pairs()
        if recent_pairs:
            context_parts.append("[Recent Conversation]\n")
            for i, pair in enumerate(recent_pairs, 1):
                context_parts.append(f"Student: {pair.user_message}")
                context_parts.append(f"Advisor: {pair.assistant_message}\n")
        
        return "\n".join(context_parts)
    
    def get_memory_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation memory status.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Memory status information
        """
        session = self.get_session(session_id)
        window = session.conversation_window
        
        return {
            'pairs_count': len(window.pairs),
            'summary_available': bool(window.summary),
            'summarized_count': window.summarized_pair_count,
            'will_summarize_at': window.max_pairs + 1,
            'total_pairs': window.summarized_pair_count + len(window.pairs)
        }
    
    def _save_session(self, session: SessionState):
        """Save session to storage."""
        if not self.storage_dir:
            return
        
        session_file = self.storage_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
    
    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self.sessions.keys())
    
    def get_session_count(self) -> int:
        """Get count of active sessions."""
        return len(self.sessions)


# Singleton instance
_manager_instance: Optional[SessionManager] = None


def get_session_manager(storage_dir: Optional[Path] = None) -> SessionManager:
    """
    Get singleton instance of SessionManager.
    
    Args:
        storage_dir: Optional storage directory
    
    Returns:
        SessionManager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SessionManager(storage_dir)
    return _manager_instance


def get_session(session_id: str) -> SessionState:
    """Convenience function to get session."""
    manager = get_session_manager()
    return manager.get_session(session_id)


def update_session(session_id: str, updates: Dict[str, Any]) -> SessionState:
    """Convenience function to update session."""
    manager = get_session_manager()
    return manager.update_session(session_id, updates)
