"""
Memory Manager using LangChain components
Replaces current session management with LangChain's memory systems
"""

from typing import Dict, Any, List
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain_core.messages import HumanMessage, AIMessage
import logging

logger = logging.getLogger(__name__)

class LangChainMemoryManager:
    """
    Memory manager using LangChain's memory components
    """
    
    def __init__(self, max_tokens: int = 2000):
        self.memories: Dict[str, Any] = {}
        self.max_tokens = max_tokens
    
    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """
        Get or create memory for a session
        """
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 exchanges
                return_messages=True,
                memory_key="chat_history"
            )
        return self.memories[session_id]
    
    def add_user_message(self, session_id: str, message: str, form_data: Dict[str, Any] = None):
        """
        Add user message to memory
        """
        memory = self.get_memory(session_id)
        
        # Create context from form data
        context = ""
        if form_data:
            context = f"Form data: {form_data}"
        
        full_message = f"{message}\n{context}".strip()
        memory.chat_memory.add_user_message(full_message)
    
    def add_ai_message(self, session_id: str, message: str, form_html: str = None):
        """
        Add AI response to memory
        """
        memory = self.get_memory(session_id)
        
        # Create context from form HTML
        context = ""
        if form_html:
            context = f"\nForm provided: {form_html[:100]}..."
        
        full_message = f"{message}{context}".strip()
        memory.chat_memory.add_ai_message(full_message)
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get formatted chat history for the agent
        """
        memory = self.get_memory(session_id)
        messages = memory.chat_memory.messages
        
        history = []
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                history.append({
                    'user': messages[i].content,
                    'assistant': messages[i + 1].content
                })
        
        return history
    
    def get_memory_variables(self, session_id: str) -> Dict[str, Any]:
        """
        Get memory variables for LangChain chains
        """
        memory = self.get_memory(session_id)
        return memory.load_memory_variables({})
    
    def clear_memory(self, session_id: str):
        """
        Clear memory for a session
        """
        if session_id in self.memories:
            del self.memories[session_id]
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        """
        memory = self.get_memory(session_id)
        return {
            'message_count': len(memory.chat_memory.messages),
            'has_memory': session_id in self.memories
        } 