"""
Improved Agent Coordinator for Living Form Tire Sales Assistant
Integrates memory management, state management, and handoff protocol
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from agents.tire_size_agent import TireSizeAgent
from agents.driving_info_agent import DrivingInfoAgent
from agents.preferences_agent import PreferencesAgent
from agents.recommendation_agent import RecommendationAgent
from agents.scribe_agent import ScribeAgent
from agents.ai_client import AIClient
from agents.cost_manager import CostManager
from agents.form_builder import FormBuilder
from database.tire_database import TireDatabase
from utils.memory_manager import MemoryManager, MemoryConfig
from utils.state_manager import StateManager, ConversationState, StateValidationError
from utils.agent_handoff import AgentHandoff, HandoffValidationError
from utils.conversation_enums import ConversationStep, DataCategory

logger = logging.getLogger(__name__)

class ImprovedAgentCoordinator:
    """
    Improved agent coordinator with conventional agentic framework patterns
    """
    
    def __init__(self, ai_client: AIClient, cost_manager: CostManager, form_builder: FormBuilder, tire_database: TireDatabase):
        self.ai_client = ai_client
        self.cost_manager = cost_manager
        self.form_builder = form_builder
        self.tire_database = tire_database
        
        # Initialize specialized agents
        self.tire_size_agent = TireSizeAgent(ai_client, cost_manager, form_builder)
        self.driving_info_agent = DrivingInfoAgent(ai_client, cost_manager, form_builder)
        self.preferences_agent = PreferencesAgent(ai_client, cost_manager, form_builder)
        self.recommendation_agent = RecommendationAgent(ai_client, cost_manager, form_builder, tire_database)
        self.scribe_agent = ScribeAgent(ai_client, cost_manager, form_builder)
        
        # Initialize management components
        self.memory_manager = MemoryManager(ai_client, MemoryConfig())
        self.state_manager = StateManager()
        self.handoff_manager = AgentHandoff()
        
        # Agent mapping
        self.agent_mapping = {
            "TireSizeAgent": self.tire_size_agent,
            "DrivingInfoAgent": self.driving_info_agent,
            "PreferencesAgent": self.preferences_agent,
            "RecommendationAgent": self.recommendation_agent,
            "ScribeAgent": self.scribe_agent
        }
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
        
        logger.info("ImprovedAgentCoordinator initialized with all components")
    
    async def process_message(self, user_message: str, session_id: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process message with improved agentic framework
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
            
            # Check if handoff is needed
            current_agent_name = state.current_agent
            should_handoff = await self.handoff_manager.should_handoff(current_agent_name, state, conversation_context)
            
            if should_handoff:
                # Determine target agent
                target_agent_name = await self.handoff_manager.get_agent_for_step(state.current_step)
                
                # Prepare and execute handoff
                handoff_msg = await self.handoff_manager.prepare_handoff(
                    from_agent=current_agent_name,
                    to_agent=target_agent_name,
                    state=state,
                    context=conversation_context
                )
                
                if handoff_msg.status.value == "validated":
                    handoff_result = await self.handoff_manager.execute_handoff(handoff_msg)
                    
                    # Update state with new agent
                    state = await self.state_manager.update_state(
                        current_agent=target_agent_name
                    )
                    
                    logger.info(f"Handoff completed: {handoff_result}")
                else:
                    logger.warning(f"Handoff validation failed: {handoff_msg.validation_result['errors']}")
            
            # Get current agent
            current_agent = self.agent_mapping.get(state.current_agent)
            if not current_agent:
                raise ValueError(f"Unknown agent: {state.current_agent}")
            
            # Process with current agent
            response = await current_agent.process_message(
                user_message=user_message,
                roadmap=session,  # Pass session instead of roadmap
                conversation_context=conversation_context
            )
            
            # Update session history with response
            await self._update_session_history(session, user_message, response, form_data)
            
            # Check if memory compression is needed
            compression_occurred = await self.memory_manager.compress_conversation_if_needed(session)
            if compression_occurred:
                logger.info("Memory compression completed")
            
            # Update session
            await self._update_session(session_id, session)
            
            # Add coordination metadata
            response['coordinator_info'] = {
                'current_step': state.current_step.value,
                'current_agent': state.current_agent,
                'handoff_occurred': should_handoff,
                'compression_occurred': compression_occurred,
                'memory_stats': self.memory_manager.get_memory_stats(session),
                'state_summary': await self.state_manager.get_state_summary()
            }
            
            # Debug logging
            logger.info(f"Coordinator info: current_agent={state.current_agent}, handoff_occurred={should_handoff}")
            logger.info(f"Response keys: {list(response.keys())}")
            
            # Add handoff information for debugging
            if should_handoff:
                response['handoff_info'] = {
                    'from_agent': current_agent_name,
                    'to_agent': target_agent_name,
                    'reason': handoff_msg.validation_result.get('reason', 'Agent handoff'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add notepad content to response (use enhanced Control Headquarters scene if available)
            if 'enhanced_notepad' in response:
                response['notepad_content'] = response['enhanced_notepad']
            else:
                response['notepad_content'] = session.get('ai_notepad', '')
            
            return response
            
        except Exception as e:
            logger.error(f"Error in ImprovedAgentCoordinator: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create session with proper locking"""
        async with self._session_lock:
            if session_id not in self.active_sessions:
                # Create new session with simplified structure
                session = {
                    'session_id': session_id,
                    'conversation_history': [],
                    'ai_notepad': "",
                    'created_at': datetime.now(),
                    'last_activity': datetime.now()
                }
                self.active_sessions[session_id] = session
                logger.info(f"Created new session: {session_id}")
            else:
                # Update last activity
                self.active_sessions[session_id]['last_activity'] = datetime.now()
            
            return self.active_sessions[session_id]
    
    async def _build_conversation_context(self, session_id: str, state: ConversationState, form_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build comprehensive conversation context"""
        context = {
            'session_id': session_id,
            'current_step': state.current_step.value,
            'current_agent': state.current_agent,
            'shared_data': state.shared_data,
            'important_data': state.important_data,
            'conversation_summary': state.conversation_summary,
            'session_start_time': state.session_start_time.isoformat(),
            'last_updated': state.last_updated.isoformat()
        }
        
        # Add form data if provided
        if form_data:
            context['form_data'] = form_data
            context['form_submission'] = True
        
        # Add handoff info if available
        if state.handoff_info:
            context['handoff_info'] = state.handoff_info
        
        # Add memory stats and conversation history
        session = self.active_sessions.get(session_id, {})
        if session:
            context['memory_stats'] = self.memory_manager.get_memory_stats(session)
            
            # Add conversation history for context
            if session.get('conversation_history'):
                context['conversation_history'] = session['conversation_history']
            
            # Add AI notepad if available
            if session.get('ai_notepad'):
                context['notepad_summary'] = session['ai_notepad']
        
        return context
    
    async def _update_state_with_extracted_info(self, state: ConversationState, extracted_info: Dict[str, Any]):
        """Update state with information extracted by ScribeAgent"""
        
        # Update vehicle information
        if 'vehicle_info' in extracted_info:
            vehicle_data = extracted_info['vehicle_info']
            for key, value in vehicle_data.items():
                if value and value not in ['I don\'t know', 'I\'m not sure', '']:
                    await self.state_manager.update_important_data(key, value, "ScribeAgent")
        
        # Update tire information
        if 'tire_info' in extracted_info:
            tire_data = extracted_info['tire_info']
            for key, value in tire_data.items():
                if value and value not in ['I don\'t know', 'I\'m not sure', '']:
                    await self.state_manager.update_important_data(key, value, "ScribeAgent")
        
        # Update preferences
        if 'preferences' in extracted_info:
            pref_data = extracted_info['preferences']
            for key, value in pref_data.items():
                if value and value not in ['I don\'t know', 'I\'m not sure', '']:
                    await self.state_manager.update_important_data(key, value, "ScribeAgent")
        
        # Update situation
        if 'situation' in extracted_info:
            sit_data = extracted_info['situation']
            for key, value in sit_data.items():
                if value and value not in ['I don\'t know', 'I\'m not sure', '']:
                    await self.state_manager.update_important_data(key, value, "ScribeAgent")
    
    async def _update_session_history(self, session: Dict[str, Any], user_message: str, response: Dict[str, Any], form_data: Optional[Dict[str, Any]]):
        """Update session history with new information"""
        
        # Add user message event
        session['conversation_history'].append({
            "timestamp": datetime.now().isoformat(),
            "type": "user_message",
            "message": user_message,
            "has_form_data": bool(form_data)
        })
        
        # Add form submission event if form data provided
        if form_data:
            session['conversation_history'].append({
                "timestamp": datetime.now().isoformat(),
                "type": "form_submission",
                "form_data": form_data,
                "message": user_message,
                "step": "form_submission"
            })
            
            # Add specific method selection if present
            if 'info_method' in form_data:
                session['conversation_history'].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "method_selected",
                    "data": {"method": form_data['info_method']},
                    "step": "method_selection"
                })
        
        # Add AI response event
        session['conversation_history'].append({
            "timestamp": datetime.now().isoformat(),
            "type": "ai_response",
            "response_length": len(response.get("response", "")),
            "has_form": bool(response.get("form_html")),
            "agent": response.get("coordinator_info", {}).get("current_agent", "unknown"),
            "step": response.get("coordinator_info", {}).get("current_step", "unknown")
        })
    
    async def _update_session(self, session_id: str, session: Dict[str, Any]):
        """Update session in storage"""
        async with self._session_lock:
            self.active_sessions[session_id] = session
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "response": f"""
            <div style="background:#fff3cd;padding:15px;border-radius:8px;border:1px solid #ffeaa7;margin-bottom:15px;">
                <p style="margin:0;color:#856404;">I'm experiencing some technical difficulties. Please try again or let me know if you need help with something specific.</p>
            </div>
            """,
            "conversation_text": "I'm experiencing some technical difficulties. Please try again.",
            "form_html": "",
            "cost_info": {"total_cost": 0.0, "model_used": "error"},
            "source": "coordinator_error",
            "coordinator_info": {
                "error": error_message,
                "current_step": "error",
                "current_agent": "none"
            }
        }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session information"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        state = await self.state_manager.get_state()
        
        return {
            'session_id': session_id,
            'created_at': session['created_at'].isoformat(),
            'last_activity': session['last_activity'].isoformat(),
            'state_summary': await self.state_manager.get_state_summary(),
            'memory_stats': self.memory_manager.get_memory_stats(session),
            'handoff_history': await self.handoff_manager.get_handoff_history(5),
            'conversation_length': len(session['conversation_history']),
            'notepad_content': session.get('ai_notepad', '')
        }
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        async with self._session_lock:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if self.memory_manager.is_session_expired(session['created_at']):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
            
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'active_sessions': len(self.active_sessions),
            'memory_manager_config': {
                'max_events': self.memory_manager.config.max_events,
                'max_session_duration_hours': self.memory_manager.config.max_session_duration_hours,
                'compression_threshold': self.memory_manager.config.compression_threshold
            },
            'available_agents': list(self.agent_mapping.keys()),
            'handoff_history_length': len(self.handoff_manager.handoff_history),
            'system_health': 'healthy'
        } 