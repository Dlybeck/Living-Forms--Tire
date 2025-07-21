"""
DrivingInfoAgent - Specialized agent for collecting driving patterns and preferences
Handles understanding how the user drives and uses their vehicle
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.conversation_enums import ConversationStep, DataCategory
import logging
import re

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
    
    def _needs_web_search(self, user_message: str, roadmap: Dict[str, Any]) -> bool:
        """Determine if web search is needed"""
        return False
    
    def _get_form_purpose(self, roadmap: Dict[str, Any]) -> str:
        """Get the purpose of form generation for driving info collection"""
        # For now, return a default purpose since we're using simplified session structure
        return "collect_driving_info"
    
    async def process_message(self, user_message: str, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with driving info collection logic"""
        
        # Check for form data first
        form_data = conversation_context.get('form_data', {})
        if form_data:
            logger.info(f"Processing driving info form data: {form_data}")
            
            # Let ScribeAgent handle the information extraction and recording
            # We just log what was provided for debugging
            for field, value in form_data.items():
                if value and str(value).lower() not in ['false', 'none', '']:
                    logger.info(f"User provided {field}: {value}")
        
        # Extract driving info if present in message
        driving_info = self._extract_driving_info_from_message(user_message)
        if driving_info:
            logger.info(f"Extracted driving info from message: {driving_info}")
            conversation_context['extracted_driving_info'] = driving_info
        
        # Process with base agent logic
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        return response
    
    def _extract_driving_info_from_message(self, user_message: str) -> Optional[Dict[str, str]]:
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
    
    async def _assess_task_completion(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if driving information collection is complete"""
        
        # Get form data and conversation context
        form_data = conversation_context.get('form_data', {})
        enhanced_notepad = conversation_context.get('enhanced_notepad', '')
        
        # Required data points for driving information
        required_fields = [
            'user_location', 'total_mileage', 'vehicle_year', 'driving_environment',
            'weather_conditions', 'driving_style', 'vehicle_usage', 'ownership_plans'
        ]
        
        # Check what data we have
        collected_data = {}
        missing_data = []
        quality_score = 0.0
        
        for field in required_fields:
            # Check form data first
            if field in form_data and form_data[field] and str(form_data[field]).lower() not in ['i don\'t know', 'i\'m not sure', '']:
                collected_data[field] = form_data[field]
                quality_score += 0.125  # 1.0 / 8 fields
            else:
                missing_data.append(field)
        
        # Check if we have enough data for recommendations
        is_complete = quality_score >= 0.875  # Need at least 7 out of 8 fields (87.5%)
        recommendation_readiness = quality_score >= 0.75  # Need at least 6 out of 8 fields (75%)
        
        # Determine completion reason
        if is_complete:
            reason = f"Complete driving profile collected ({quality_score:.1%} quality score)"
        elif recommendation_readiness:
            reason = f"Sufficient driving information for recommendations ({quality_score:.1%} quality score)"
        else:
            reason = f"Incomplete driving information - need {len(missing_data)} more data points"
        
        return {
            "is_complete": is_complete,
            "reason": reason,
            "quality_score": quality_score,
            "missing_data": missing_data,
            "recommendation_readiness": recommendation_readiness
        } 