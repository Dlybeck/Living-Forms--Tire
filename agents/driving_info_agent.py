"""
DrivingInfoAgent - Specialized agent for collecting driving patterns and preferences
Handles understanding how the user drives and uses their vehicle
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.conversation_roadmap import ConversationRoadmap, ConversationStep, DataCategory
import logging

logger = logging.getLogger(__name__)

class DrivingInfoAgent(BaseAgent):
    """
    Specialized agent for collecting driving patterns and preferences
    Focuses on understanding how the user drives and uses their vehicle
    """
    
    def __init__(self, ai_client, cost_manager, form_builder):
        super().__init__(ai_client, cost_manager, form_builder, "DrivingInfoAgent")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for driving info collection"""
        from prompts import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for driving info collection"""
        from prompts import DRIVING_INFO_AGENT_PROMPT
        return DRIVING_INFO_AGENT_PROMPT
    
    def _needs_web_search(self, user_message: str, roadmap: ConversationRoadmap) -> bool:
        """Determine if web search is needed for driving info collection"""
        
        # Check if user is asking about specific tire types or performance
        performance_keywords = ['performance', 'handling', 'grip', 'traction', 'braking']
        if any(keyword in user_message.lower() for keyword in performance_keywords):
            logger.info("Web search needed: User asking about tire performance")
            return True
        
        # Check if user is asking about specific driving conditions
        condition_keywords = ['snow', 'rain', 'winter', 'summer', 'all-season', 'off-road']
        if any(keyword in user_message.lower() for keyword in condition_keywords):
            logger.info("Web search needed: User asking about specific driving conditions")
            return True
        
        return False
    
    def _get_form_purpose(self, roadmap: ConversationRoadmap) -> str:
        """Get the purpose of form generation for driving info collection"""
        driving_patterns = roadmap.get_shared_data(DataCategory.DRIVING_PATTERNS)
        
        if not driving_patterns:
            return "collect_basic_driving_info"
        elif not self._has_comprehensive_driving_info(driving_patterns):
            return "collect_detailed_driving_info"
        else:
            return "driving_info_complete"
    
    def _has_basic_driving_info(self, driving_patterns: Dict[str, Any]) -> bool:
        """Check if we have basic driving information"""
        required_fields = ['driving_frequency', 'driving_style']
        return all(field in driving_patterns for field in required_fields)
    
    def _has_comprehensive_driving_info(self, driving_patterns: Dict[str, Any]) -> bool:
        """Check if we have comprehensive driving information"""
        required_fields = ['driving_frequency', 'driving_style', 'environmental_conditions', 'performance_priorities']
        return all(field in driving_patterns for field in required_fields)
    
    def _extract_driving_info_from_message(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Extract driving information from user message"""
        driving_info = {}
        user_lower = user_message.lower()
        
        # Extract driving frequency
        if any(word in user_lower for word in ['daily', 'every day', 'commute']):
            driving_info['driving_frequency'] = 'daily'
        elif any(word in user_lower for word in ['weekly', 'occasionally', 'sometimes']):
            driving_info['driving_frequency'] = 'occasional'
        elif any(word in user_lower for word in ['rarely', 'seldom', 'hardly']):
            driving_info['driving_frequency'] = 'rare'
        
        # Extract driving style
        if any(word in user_lower for word in ['aggressive', 'fast', 'sporty', 'performance']):
            driving_info['driving_style'] = 'aggressive'
        elif any(word in user_lower for word in ['conservative', 'careful', 'slow', 'safe']):
            driving_info['driving_style'] = 'conservative'
        elif any(word in user_lower for word in ['moderate', 'normal', 'average']):
            driving_info['driving_style'] = 'moderate'
        
        # Extract environmental conditions
        conditions = []
        if any(word in user_lower for word in ['snow', 'winter', 'cold']):
            conditions.append('snow')
        if any(word in user_lower for word in ['rain', 'wet', 'water']):
            conditions.append('rain')
        if any(word in user_lower for word in ['highway', 'freeway', 'interstate']):
            conditions.append('highway')
        if any(word in user_lower for word in ['city', 'urban', 'stop and go']):
            conditions.append('city')
        
        if conditions:
            driving_info['environmental_conditions'] = conditions
        
        # Extract performance priorities
        priorities = []
        if any(word in user_lower for word in ['handling', 'grip', 'traction']):
            priorities.append('handling')
        if any(word in user_lower for word in ['comfort', 'smooth', 'quiet']):
            priorities.append('comfort')
        if any(word in user_lower for word in ['longevity', 'durability', 'wear']):
            priorities.append('longevity')
        if any(word in user_lower for word in ['fuel efficiency', 'mpg', 'economy']):
            priorities.append('fuel_efficiency')
        
        if priorities:
            driving_info['performance_priorities'] = priorities
        
        return driving_info if driving_info else None
    
    async def process_message(self, user_message: str, roadmap: ConversationRoadmap, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with driving info collection logic"""
        
        # Extract driving info if present in message
        driving_info = self._extract_driving_info_from_message(user_message)
        if driving_info:
            # Merge with existing driving patterns
            existing_patterns = roadmap.get_shared_data(DataCategory.DRIVING_PATTERNS) or {}
            merged_patterns = {**existing_patterns, **driving_info}
            self.update_roadmap_data(roadmap, DataCategory.DRIVING_PATTERNS, merged_patterns)
            logger.info(f"Extracted driving info from message: {driving_info}")
        
        # Process with base agent logic
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        # Check if we can advance to next step
        if roadmap.has_data_for_category(DataCategory.DRIVING_PATTERNS):
            if roadmap.can_advance_to_step(ConversationStep.PREFERENCES_GATHERING):
                roadmap.advance_to_next_step()
                logger.info("Advanced to preferences gathering step")
        
        return response 