"""
Simplified Agent Coordinator
Uses only the Unified Tire Agent for all processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from agents.unified_tire_agent import UnifiedTireAgent
from agents.ai_client import AIClient
from agents.cost_manager import CostManager
from agents.form_builder import FormBuilder
from utils.state_manager import StateManager, ConversationState

logger = logging.getLogger(__name__)

class SimplifiedCoordinator:
    """
    Simplified coordinator using only the Unified Tire Agent
    """
    
    def __init__(self, ai_client: AIClient, cost_manager: CostManager, form_builder: FormBuilder):
        self.ai_client = ai_client
        self.cost_manager = cost_manager
        self.form_builder = form_builder
        
        # Initialize only the unified agent
        self.unified_agent = UnifiedTireAgent(ai_client, cost_manager, form_builder)
        
        # Initialize management components
        self.state_manager = StateManager()
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
        
        logger.info("SimplifiedCoordinator initialized with Unified Tire Agent")
    
    async def process_message(self, user_message: str, session_id: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process message with unified agent system
        """
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id)
            
            # Get current state
            state = await self.state_manager.get_state()
            if not state:
                state = await self.state_manager.initialize_session(session_id)
            
            # Build conversation context
            conversation_context = await self._build_conversation_context(session_id, state, form_data)
            
            # Process with Unified Tire Agent (handles everything)
            response = await self.unified_agent.process_message(
                user_message=user_message,
                roadmap=session,
                conversation_context=conversation_context
            )
            
            # Update session history
            await self._update_session_history(session, user_message, response, form_data)
            
            # Add coordinator metadata
            response["current_agent"] = "UnifiedTireAgent"
            response["agent_display_name"] = "Tire Sales Assistant"
            response["coordinator_info"] = {
                "current_step": "unified_assistance",
                "agent_type": "unified_system",
                "unified_agent_active": True
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SimplifiedCoordinator: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get existing session or create new one
        """
        async with self._session_lock:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'session_id': session_id,
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat(),
                    'conversation_history': [],
                    'ai_notepad': '',
                    'current_step': 'initial'
                }
                logger.info(f"Created new session: {session_id}")
            else:
                self.active_sessions[session_id]['last_activity'] = datetime.now().isoformat()
            
            return self.active_sessions[session_id]
    
    async def _build_conversation_context(self, session_id: str, state: ConversationState, form_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build conversation context for the unified agent
        """
        session = self.active_sessions.get(session_id, {})
        conversation_history = session.get('conversation_history', [])
        
        # Build context
        context = {
            'session_id': session_id,
            'conversation_history': conversation_history,
            'current_step': session.get('current_step', 'unknown'),
            'form_data': form_data or {},
            'state': state,
            'needs_form': True
        }
        
        return context
    
    async def _update_session_history(self, session: Dict[str, Any], user_message: str, response: Dict[str, Any], form_data: Optional[Dict[str, Any]]):
        """
        Update session history with the interaction
        """
        # Add user message to history
        session['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'type': 'user_message',
            'message': user_message,
            'form_data': form_data
        })
        
        # Add system response to history
        session['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'type': 'system_response',
            'response': response.get('response', ''),
            'form_html': response.get('form_html', ''),
            'agent': response.get('current_agent', 'Unknown')
        })
        
        # Update session
        await self._update_session(session['session_id'], session)
    
    async def _update_session(self, session_id: str, session: Dict[str, Any]):
        """
        Update session in storage
        """
        self.active_sessions[session_id] = session
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create error response
        """
        return {
            "response": f"I apologize, but I encountered an error: {error_message}. Please try again.",
            "conversation_text": f"I apologize, but I encountered an error: {error_message}. Please try again.",
            "form_html": "",
            "enhanced_notepad": "",
            "cost_info": {
                "total_cost": 0.0,
                "model_used": "error"
            },
            "current_agent": "UnifiedTireAgent",
            "agent_display_name": "Tire Sales Assistant",
            "coordinator_info": {
                "current_step": "error",
                "agent_type": "unified_system",
                "error": error_message
            }
        }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        """
        session = self.active_sessions.get(session_id, {})
        return {
            'session_id': session_id,
            'created_at': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'conversation_count': len(session.get('conversation_history', [])),
            'current_step': session.get('current_step', 'unknown'),
            'ai_notepad': session.get('ai_notepad', ''),
            'agent_type': 'unified_system'
        }
    
    async def cleanup_expired_sessions(self):
        """
        Clean up expired sessions
        """
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            last_activity = datetime.fromisoformat(session.get('last_activity', current_time.isoformat()))
            if (current_time - last_activity).total_seconds() > 3600:  # 1 hour timeout
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status
        """
        return {
            'active_sessions': len(self.active_sessions),
            'agent_type': 'unified_system',
            'unified_agent_active': True,
            'system_status': 'operational'
        } 