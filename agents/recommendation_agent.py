"""
RecommendationAgent - Specialized agent for generating personalized tire recommendations
Handles the complex task of analyzing user data and generating tailored recommendations
"""

from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from utils.conversation_enums import ConversationStep, DataCategory
import logging

logger = logging.getLogger(__name__)

class RecommendationAgent(BaseAgent):
    """
    Specialized agent for generating personalized tire recommendations
    Uses comprehensive user data to create tailored tire suggestions
    """
    
    def __init__(self, ai_client, cost_manager, form_builder, tire_database):
        super().__init__(ai_client, cost_manager, form_builder, "RecommendationAgent")
        self.tire_database = tire_database
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for recommendation generation"""
        from prompts import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for recommendation generation"""
        from prompts import RECOMMENDATION_AGENT_PROMPT
        return RECOMMENDATION_AGENT_PROMPT
    
    def _needs_web_search(self, user_message: str, roadmap: Dict[str, Any]) -> bool:
        """Determine if web search is needed"""
        return False
        
        return True
    
    def _has_recommendations(self, roadmap: Dict[str, Any]) -> bool:
        """Check if recommendations have been generated"""
        # For now, return False since we're using simplified session structure
        return False
    
    async def _generate_recommendations(self, roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized tire recommendations"""
        try:
            # For now, return mock recommendations since we're using simplified session structure
            return await self._query_tire_database({})
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    async def _query_tire_database(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query tire database for recommendations"""
        try:
            # This would integrate with the actual tire database
            # For now, return mock recommendations
            return [
                {
                    'id': 'rec_1',
                    'name': 'Michelin Defender T+H',
                    'category': 'primary',
                    'price_range': '$120-150',
                    'features': ['All-season', 'Long tread life', 'Good fuel efficiency'],
                    'reasoning': 'Best overall match for your driving needs and budget'
                },
                {
                    'id': 'rec_2', 
                    'name': 'Bridgestone Turanza QuietTrack',
                    'category': 'premium',
                    'price_range': '$150-180',
                    'features': ['Premium comfort', 'Low noise', 'Excellent handling'],
                    'reasoning': 'Premium option with superior comfort and quietness'
                },
                {
                    'id': 'rec_3',
                    'name': 'Goodyear Assurance WeatherReady',
                    'category': 'budget',
                    'price_range': '$90-120',
                    'features': ['All-weather', 'Good value', 'Reliable performance'],
                    'reasoning': 'Cost-effective option that meets your requirements'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error querying tire database: {str(e)}")
            return [] 