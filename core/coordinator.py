"""
Agent Coordinator
Uses the Unified Tire Agent for all processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from .tire_agent import TireAgent
from .ai_client import AIClient
from .form_builder import FormBuilder
from .utils import create_error_response

logger = logging.getLogger(__name__)

class Coordinator:
    """
    Coordinator using the Unified Tire Agent
    """
    
    def __init__(self, ai_client: AIClient, form_builder: FormBuilder):
        self.ai_client = ai_client
        self.form_builder = form_builder
        
        # Initialize the tire agent
        self.tire_agent = TireAgent(ai_client, form_builder)
        

        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
        
        logger.debug("Coordinator initialized with Tire Agent")
    
    async def process_message(self, user_message: str, session_id: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process message with unified agent system
        """
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id)
            
            # Build unified context combining session data and current request
            context = {
                **session,  # session_id, conversation_history, ai_notepad, current_step
                'form_data': form_data or {},
                'needs_form': True
            }
            
            # Process with Tire Agent
            response = await self.tire_agent.process_message(
                user_message=user_message,
                context=context
            )
            
            # Update session with any changes from the agent (like ai_notepad)
            session['ai_notepad'] = context.get('ai_notepad', session.get('ai_notepad', ''))
            
            # Update session history
            await self._update_session_history(session, user_message, response, form_data)
            
            # Add coordinator metadata
            response["coordinator_info"] = {
                "current_step": "unified_assistance"
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SimplifiedCoordinator: {str(e)}")
            return create_error_response(str(e), include_coordinator_info=True)
    
    async def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get existing session or create new one
        """
        async with self._session_lock:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'session_id': session_id,
                    'conversation_history': [],
                    'ai_notepad': '',
                    'current_step': 'initial'
                }
                logger.debug(f"Created new session: {session_id}")

            
            return self.active_sessions[session_id]
    

    
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
            'agent': 'TireAgent'
        })
        
        # Update session
        await self._update_session(session['session_id'], session)
    
    async def _update_session(self, session_id: str, session: Dict[str, Any]):
        """
        Update session in storage
        """
        self.active_sessions[session_id] = session
    

    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        """
        session = self.active_sessions.get(session_id, {})
        return {
            'ai_notepad': session.get('ai_notepad', '')
        }
    

    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status
        """
        return {
            'active_sessions': len(self.active_sessions),
            'system_health': 'operational'
        } 