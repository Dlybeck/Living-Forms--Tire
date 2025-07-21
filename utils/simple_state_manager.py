"""
Simple State Manager for Dual Agent System
Minimal state tracking for the simplified system
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, replace

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SimpleConversationState:
    """
    Simple conversation state for dual agent system
    """
    session_id: str
    current_agent: str = "ComprehensiveTireAgent"
    conversation_data: Dict[str, Any] = None
    session_start_time: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.conversation_data is None:
            object.__setattr__(self, 'conversation_data', {})
        if self.session_start_time is None:
            object.__setattr__(self, 'session_start_time', datetime.now())
        if self.last_updated is None:
            object.__setattr__(self, 'last_updated', datetime.now())
    
    def update(self, **kwargs) -> 'SimpleConversationState':
        """Create new state with updates"""
        return replace(self, **kwargs, last_updated=datetime.now())

class SimpleStateManager:
    """
    Simple state manager for dual agent system
    """
    
    def __init__(self):
        self._state: Optional[SimpleConversationState] = None
        self._lock = asyncio.Lock()
        logger.info("SimpleStateManager initialized")
    
    async def initialize_session(self, session_id: str) -> SimpleConversationState:
        """Initialize a new session state"""
        async with self._lock:
            self._state = SimpleConversationState(
                session_id=session_id,
                current_agent="ComprehensiveTireAgent"
            )
            logger.info(f"Initialized new session state: {session_id}")
            return self._state
    
    async def get_state(self) -> Optional[SimpleConversationState]:
        """Get current state"""
        async with self._lock:
            return self._state
    
    async def update_state(self, **kwargs) -> SimpleConversationState:
        """Update state"""
        async with self._lock:
            if self._state is None:
                raise ValueError("No state initialized")
            
            self._state = self._state.update(**kwargs)
            logger.info(f"State updated: {list(kwargs.keys())}")
            return self._state
    
    async def update_conversation_data(self, key: str, value: Any) -> SimpleConversationState:
        """Update conversation data"""
        async with self._lock:
            if self._state is None:
                raise ValueError("No state initialized")
            
            new_data = self._state.conversation_data.copy()
            new_data[key] = value
            
            self._state = self._state.update(conversation_data=new_data)
            logger.info(f"Updated conversation data: {key} = {value}")
            return self._state
    
    async def get_conversation_data(self, key: str, default: Any = None) -> Any:
        """Get conversation data"""
        if self._state is None:
            return default
        return self._state.conversation_data.get(key, default)
    
    async def has_conversation_data(self, key: str) -> bool:
        """Check if conversation data exists"""
        if self._state is None:
            return False
        return key in self._state.conversation_data 