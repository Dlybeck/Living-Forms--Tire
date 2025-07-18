"""
AgentCoordinator - Manages the flow between specialized agents
Coordinates the multi-agent system and handles conversation progression
"""

from typing import Dict, Any, Optional
from agents.tire_size_agent import TireSizeAgent
from agents.driving_info_agent import DrivingInfoAgent
from agents.preferences_agent import PreferencesAgent
from agents.recommendation_agent import RecommendationAgent
from utils.conversation_roadmap import ConversationRoadmap, ConversationStep, DataCategory
import logging

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    Coordinates the multi-agent system
    Manages conversation flow and delegates to appropriate specialized agents
    """
    
    def __init__(self, ai_client, cost_manager, form_builder, tire_database):
        self.ai_client = ai_client
        self.cost_manager = cost_manager
        self.form_builder = form_builder
        self.tire_database = tire_database
        
        # Initialize specialized agents
        self.tire_size_agent = TireSizeAgent(ai_client, cost_manager, form_builder)
        self.driving_info_agent = DrivingInfoAgent(ai_client, cost_manager, form_builder)
        self.preferences_agent = PreferencesAgent(ai_client, cost_manager, form_builder)
        self.recommendation_agent = RecommendationAgent(ai_client, cost_manager, form_builder, tire_database)
        
        # Agent mapping by conversation step
        self.agent_mapping = {
            ConversationStep.GREETING: self.tire_size_agent,
            ConversationStep.TIRE_SIZE_DISCOVERY: self.tire_size_agent,
            ConversationStep.DRIVING_INFO_COLLECTION: self.driving_info_agent,
            ConversationStep.PREFERENCES_GATHERING: self.preferences_agent,
            ConversationStep.RECOMMENDATION_GENERATION: self.recommendation_agent,
            ConversationStep.COMPARISON_ANALYSIS: self.recommendation_agent,
            ConversationStep.FINAL_SELECTION: self.recommendation_agent,
            ConversationStep.COMPLETED: self.recommendation_agent
        }
        
        logger.info("AgentCoordinator initialized with all specialized agents")
    
    async def process_message(self, user_message: str, roadmap: ConversationRoadmap, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process message by delegating to the appropriate specialized agent
        """
        try:
            # Get the current conversation step
            current_step = roadmap.current_step
            logger.info(f"Processing message with {current_step.value} agent")
            
            # Get the appropriate agent for this step
            agent = self.agent_mapping.get(current_step)
            if not agent:
                logger.error(f"No agent found for step: {current_step}")
                return self._create_error_response(f"No agent available for step: {current_step.value}")
            
            # Process with the specialized agent
            response = await agent.process_message(user_message, roadmap, conversation_context)
            
            # Add coordination metadata
            response['coordinator_info'] = {
                'current_step': current_step.value,
                'agent_used': agent.agent_name,
                'roadmap_progress': roadmap.get_conversation_summary()
            }
            
            logger.info(f"Message processed by {agent.agent_name} for step {current_step.value}")
            return response
            
        except Exception as e:
            logger.error(f"Error in AgentCoordinator: {str(e)}")
            return self._create_error_response(str(e))
    
    def get_current_agent(self, roadmap: ConversationRoadmap):
        """Get the current agent based on roadmap step"""
        return self.agent_mapping.get(roadmap.current_step)
    
    def can_advance_step(self, roadmap: ConversationRoadmap) -> bool:
        """Check if we can advance to the next conversation step"""
        current_step = roadmap.current_step
        
        # Check if current step is complete
        if current_step == ConversationStep.GREETING:
            # Can advance from greeting if we have any vehicle or tire info
            return (roadmap.has_data_for_category(DataCategory.VEHICLE_INFO) or 
                   roadmap.has_data_for_category(DataCategory.TIRE_SPECS))
        
        elif current_step == ConversationStep.TIRE_SIZE_DISCOVERY:
            # Can advance if we have tire specs
            return roadmap.has_data_for_category(DataCategory.TIRE_SPECS)
        
        elif current_step == ConversationStep.DRIVING_INFO_COLLECTION:
            # Can advance if we have driving patterns
            return roadmap.has_data_for_category(DataCategory.DRIVING_PATTERNS)
        
        elif current_step == ConversationStep.PREFERENCES_GATHERING:
            # Can advance if we have budget preferences
            return roadmap.has_data_for_category(DataCategory.BUDGET_PREFERENCES)
        
        elif current_step == ConversationStep.RECOMMENDATION_GENERATION:
            # Can advance if we have recommendations
            special_considerations = roadmap.get_shared_data(DataCategory.SPECIAL_CONSIDERATIONS)
            return special_considerations and special_considerations.get('recommendations')
        
        elif current_step == ConversationStep.COMPARISON_ANALYSIS:
            # Can advance if user has provided feedback
            return True  # Simplified for now
        
        elif current_step == ConversationStep.FINAL_SELECTION:
            # Can advance if user has made a selection
            return True  # Simplified for now
        
        return False
    
    def get_next_step(self, roadmap: ConversationRoadmap) -> Optional[ConversationStep]:
        """Get the next conversation step"""
        current_step = roadmap.current_step
        
        step_sequence = [
            ConversationStep.GREETING,
            ConversationStep.TIRE_SIZE_DISCOVERY,
            ConversationStep.DRIVING_INFO_COLLECTION,
            ConversationStep.PREFERENCES_GATHERING,
            ConversationStep.RECOMMENDATION_GENERATION,
            ConversationStep.COMPARISON_ANALYSIS,
            ConversationStep.FINAL_SELECTION,
            ConversationStep.COMPLETED
        ]
        
        try:
            current_index = step_sequence.index(current_step)
            if current_index + 1 < len(step_sequence):
                return step_sequence[current_index + 1]
        except ValueError:
            logger.error(f"Current step {current_step} not found in sequence")
        
        return None
    
    def get_missing_data_summary(self, roadmap: ConversationRoadmap) -> Dict[str, Any]:
        """Get a summary of missing data for the current step"""
        current_goal = roadmap.get_current_goal()
        missing_data = roadmap.get_missing_data()
        
        return {
            'current_step': roadmap.current_step.value,
            'current_goal': current_goal.description,
            'missing_categories': [cat.value for cat in missing_data],
            'required_data': [cat.value for cat in current_goal.required_data],
            'optional_data': [cat.value for cat in current_goal.optional_data]
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            'total_agents': len(self.agent_mapping),
            'available_steps': list(self.agent_mapping.keys()),
            'agent_names': [agent.agent_name for agent in self.agent_mapping.values()]
        }
    
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
            "cost_info": {"total_cost": 0.0, "reasoning_model": "error", "form_model": "none"},
            "source": "coordinator_error",
            "coordinator_info": {
                "error": error_message,
                "current_step": "error",
                "agent_used": "none"
            }
        } 