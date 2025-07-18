"""
RecommendationAgent - Specialized agent for generating personalized tire recommendations
Handles the complex task of analyzing user data and generating tailored recommendations
"""

from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from utils.conversation_roadmap import ConversationRoadmap, ConversationStep, DataCategory
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
    
    def _needs_web_search(self, user_message: str, roadmap: ConversationRoadmap) -> bool:
        """Determine if web search is needed for recommendation generation"""
        
        # Always use web search for recommendations to get current pricing and availability
        logger.info("Web search needed: Generating tire recommendations")
        return True
    
    def _get_form_purpose(self, roadmap: ConversationRoadmap) -> str:
        """Get the purpose of form generation for recommendation generation"""
        
        # Check if recommendations have been generated
        recommendations = roadmap.get_shared_data(DataCategory.SPECIAL_CONSIDERATIONS)
        if recommendations and recommendations.get('recommendations'):
            return "collect_recommendation_feedback"
        else:
            return "generate_recommendations"
    
    async def process_message(self, user_message: str, roadmap: ConversationRoadmap, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with recommendation generation logic"""
        
        # Check if we have all required data for recommendations
        if self._has_all_required_data(roadmap):
            # Generate recommendations if not already done
            if not self._has_recommendations(roadmap):
                recommendations = await self._generate_recommendations(roadmap)
                if recommendations:
                    self.update_roadmap_data(roadmap, DataCategory.SPECIAL_CONSIDERATIONS, {
                        'recommendations': recommendations,
                        'generated_at': 'now'
                    })
                    logger.info(f"Generated {len(recommendations)} recommendations")
        
        # Process with base agent logic
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        # Check if we can advance to next step
        if self._has_recommendations(roadmap):
            if roadmap.can_advance_to_step(ConversationStep.COMPARISON_ANALYSIS):
                roadmap.advance_to_next_step()
                logger.info("Advanced to comparison analysis step")
        
        return response
    
    def _has_all_required_data(self, roadmap: ConversationRoadmap) -> bool:
        """Check if we have all required data for recommendations"""
        required_categories = [
            DataCategory.TIRE_SPECS,
            DataCategory.DRIVING_PATTERNS,
            DataCategory.BUDGET_PREFERENCES
        ]
        
        for category in required_categories:
            if not roadmap.has_data_for_category(category):
                return False
        
        return True
    
    def _has_recommendations(self, roadmap: ConversationRoadmap) -> bool:
        """Check if recommendations have been generated"""
        special_considerations = roadmap.get_shared_data(DataCategory.SPECIAL_CONSIDERATIONS)
        return special_considerations and special_considerations.get('recommendations')
    
    async def _generate_recommendations(self, roadmap: ConversationRoadmap) -> List[Dict[str, Any]]:
        """Generate personalized tire recommendations"""
        try:
            # Get user data
            tire_specs = roadmap.get_shared_data(DataCategory.TIRE_SPECS)
            driving_patterns = roadmap.get_shared_data(DataCategory.DRIVING_PATTERNS)
            budget_preferences = roadmap.get_shared_data(DataCategory.BUDGET_PREFERENCES)
            
            # Build recommendation criteria
            criteria = {
                'tire_size': tire_specs.get('current_tire_size'),
                'driving_style': driving_patterns.get('driving_style'),
                'environmental_conditions': driving_patterns.get('environmental_conditions', []),
                'performance_priorities': driving_patterns.get('performance_priorities', []),
                'budget_range': budget_preferences.get('budget_range'),
                'special_considerations': budget_preferences.get('special_considerations', [])
            }
            
            # Generate recommendations using tire database
            recommendations = await self._query_tire_database(criteria)
            
            return recommendations
            
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