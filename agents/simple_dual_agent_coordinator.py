"""
Simple Dual Agent Coordinator
Uses only Scribe Agent (memory/coordination) and Comprehensive Tire Agent (user interaction)
Eliminates complex handoffs and multi-agent coordination
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from agents.comprehensive_tire_agent import ComprehensiveTireAgent
from agents.scribe_agent import ScribeAgent
from agents.ai_client import AIClient
from agents.cost_manager import CostManager
from agents.form_builder import FormBuilder
from database.tire_database import TireDatabase
from utils.memory_manager import MemoryManager, MemoryConfig
from utils.simple_state_manager import SimpleStateManager, SimpleConversationState

logger = logging.getLogger(__name__)

class SimpleDualAgentCoordinator:
    """
    Simple dual-agent coordinator with Scribe + Comprehensive Tire Agent
    """
    
    def __init__(self, ai_client: AIClient, cost_manager: CostManager, form_builder: FormBuilder, tire_database: TireDatabase):
        self.ai_client = ai_client
        self.cost_manager = cost_manager
        self.form_builder = form_builder
        self.tire_database = tire_database
        
        # Initialize only two agents
        self.scribe_agent = ScribeAgent(ai_client, cost_manager, form_builder)
        self.tire_agent = ComprehensiveTireAgent(ai_client, cost_manager, form_builder)
        
        # Initialize management components
        self.memory_manager = MemoryManager(ai_client, MemoryConfig())
        self.state_manager = SimpleStateManager()
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
        
        logger.info("SimpleDualAgentCoordinator initialized with Scribe + Comprehensive Tire Agent")
    
    async def process_message(self, user_message: str, session_id: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process message with simple dual-agent system
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
            
            # Process with ScribeAgent first to extract information
            scribe_result = await self.scribe_agent.extract_and_record(
                user_message=user_message,
                roadmap=session,
                conversation_context=conversation_context
            )
            
            # Update state with extracted information
            if scribe_result.get("extracted_info"):
                await self._update_state_with_extracted_info(state, scribe_result["extracted_info"])
            
            # Process with Comprehensive Tire Agent (handles everything else)
            response = await self.tire_agent.process_message(
                user_message=user_message,
                roadmap=session,
                conversation_context=conversation_context
            )
            
            # Update session history
            await self._update_session_history(session, user_message, response, form_data)
            
            # Add coordinator metadata
            response["current_agent"] = "ComprehensiveTireAgent"
            response["agent_display_name"] = "Tire Sales Assistant"
            response["coordinator_info"] = {
                "current_step": "comprehensive_assistance",
                "agent_type": "dual_system",
                "scribe_active": True,
                "tire_agent_active": True
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SimpleDualAgentCoordinator: {str(e)}")
            return self._create_error_response(f"Processing error: {str(e)}")
    
    async def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create a session"""
        async with self._session_lock:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'session_id': session_id,
                    'created_at': datetime.now().isoformat(),
                    'conversation_history': [],
                    'ai_notepad': '',
                    'current_step': 'comprehensive_assistance',
                    'data_collected': {}
                }
                logger.info(f"Created new session: {session_id}")
            
            return self.active_sessions[session_id]
    
    async def _build_conversation_context(self, session_id: str, state: SimpleConversationState, form_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build conversation context for agents"""
        session = self.active_sessions.get(session_id, {})
        
        # Get conversation history
        conversation_history = session.get('conversation_history', [])
        
        # Get current notepad content
        notepad_content = session.get('ai_notepad', '')
        
        # Build context
        context = {
            'session_id': session_id,
            'conversation_history': conversation_history,
            'current_step': 'comprehensive_assistance',  # Simplified step
            'notepad_content': notepad_content,
            'form_data': form_data or {},
            'state': state.__dict__ if state else {},
            'timestamp': datetime.now().isoformat()
        }
        
        return context
    
    async def _update_state_with_extracted_info(self, state: SimpleConversationState, extracted_info: Dict[str, Any]):
        """Update state with information extracted by Scribe"""
        try:
            # Update state with extracted information
            if extracted_info:
                for key, value in extracted_info.items():
                    await self.state_manager.update_conversation_data(key, value)
            
            logger.info(f"Updated state with extracted info: {extracted_info}")
            
        except Exception as e:
            logger.error(f"Error updating state: {str(e)}")
    
    async def _update_session_history(self, session: Dict[str, Any], user_message: str, response: Dict[str, Any], form_data: Optional[Dict[str, Any]]):
        """Update session history"""
        try:
            # Add user message
            session['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'message': user_message,
                'form_data': form_data
            })
            
            # Add agent response
            session['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'agent_response',
                'response': response.get('response', ''),
                'form_html': response.get('form_html'),
                'agent': response.get('current_agent', 'Unknown')
            })
            
            # Update notepad if provided (check both possible field names)
            if response.get('enhanced_notepad'):
                session['ai_notepad'] = response['enhanced_notepad']
            elif response.get('notepad_content'):
                session['ai_notepad'] = response['notepad_content']
            
            logger.info(f"Updated session history for session: {session['session_id']}")
            
        except Exception as e:
            logger.error(f"Error updating session history: {str(e)}")
    
    async def _update_session(self, session_id: str, session: Dict[str, Any]):
        """Update session in memory"""
        self.active_sessions[session_id] = session
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "response": f"I apologize, but I encountered an error: {error_message}. Please try again.",
            "form_html": None,
            "inline_guidance": None,
            "conversation_state": "error",
            "cost_info": {"total_cost": 0.0},
            "current_agent": "ComprehensiveTireAgent",
            "agent_display_name": "Tire Sales Assistant",
            "coordinator_info": {
                "current_step": "error",
                "agent_type": "dual_system",
                "error": error_message
            }
        }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        session = self.active_sessions.get(session_id, {})
        return {
            'session_id': session_id,
            'created_at': session.get('created_at'),
            'conversation_count': len(session.get('conversation_history', [])),
            'current_step': session.get('current_step'),
            'has_notepad': bool(session.get('ai_notepad'))
        }
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        # Simple cleanup - remove sessions older than 24 hours
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)
        
        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            created_at = datetime.fromisoformat(session['created_at']).timestamp()
            if created_at < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'coordinator_type': 'SimpleDualAgent',
            'active_sessions': len(self.active_sessions),
            'agents': ['ScribeAgent', 'ComprehensiveTireAgent'],
            'status': 'operational'
        } 