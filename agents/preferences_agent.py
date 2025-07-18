"""
PreferencesAgent - Specialized agent for gathering budget and performance preferences
Handles understanding user's budget constraints and performance priorities
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.conversation_roadmap import ConversationRoadmap, ConversationStep, DataCategory
import re
import logging

logger = logging.getLogger(__name__)

class PreferencesAgent(BaseAgent):
    """
    Specialized agent for gathering budget and performance preferences
    Focuses on understanding user's budget constraints and performance priorities
    """
    
    def __init__(self, ai_client, cost_manager, form_builder):
        super().__init__(ai_client, cost_manager, form_builder, "PreferencesAgent")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for preferences gathering"""
        from prompts import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for preferences gathering"""
        from prompts import PREFERENCES_AGENT_PROMPT
        return PREFERENCES_AGENT_PROMPT
    
    def _needs_web_search(self, user_message: str, roadmap: ConversationRoadmap) -> bool:
        """Determine if web search is needed for preferences gathering"""
        
        # Check if user is asking about specific tire brands or models
        brand_keywords = ['michelin', 'bridgestone', 'goodyear', 'continental', 'pirelli']
        if any(keyword in user_message.lower() for keyword in brand_keywords):
            logger.info("Web search needed: User asking about specific tire brands")
            return True
        
        # Check if user is asking about pricing or costs
        price_keywords = ['cost', 'price', 'expensive', 'cheap', 'budget', 'affordable']
        if any(keyword in user_message.lower() for keyword in price_keywords):
            logger.info("Web search needed: User asking about pricing information")
            return True
        
        return False
    
    def _get_form_purpose(self, roadmap: ConversationRoadmap) -> str:
        """Get the purpose of form generation for preferences gathering"""
        budget_preferences = roadmap.get_shared_data(DataCategory.BUDGET_PREFERENCES)
        
        if not budget_preferences:
            return "collect_basic_preferences"
        elif not self._has_comprehensive_preferences(budget_preferences):
            return "collect_detailed_preferences"
        else:
            return "preferences_complete"
    
    def _has_basic_preferences(self, budget_preferences: Dict[str, Any]) -> bool:
        """Check if we have basic preferences"""
        required_fields = ['budget_range', 'performance_priorities']
        return all(field in budget_preferences for field in required_fields)
    
    def _has_comprehensive_preferences(self, budget_preferences: Dict[str, Any]) -> bool:
        """Check if we have comprehensive preferences"""
        required_fields = ['budget_range', 'performance_priorities', 'special_considerations', 'brand_preferences']
        return all(field in budget_preferences for field in required_fields)
    
    def _extract_preferences_from_message(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Extract preferences from user message"""
        preferences = {}
        user_lower = user_message.lower()
        
        # Extract budget information
        budget_match = re.search(r'\$?(\d+)[\s-]*\$?(\d+)?', user_message)
        if budget_match:
            min_budget = int(budget_match.group(1))
            max_budget = int(budget_match.group(2)) if budget_match.group(2) else min_budget + 50
            preferences['budget_range'] = {'min': min_budget, 'max': max_budget}
        
        # Extract budget category
        if any(word in user_lower for word in ['budget', 'cheap', 'affordable', 'economy']):
            preferences['budget_category'] = 'budget'
        elif any(word in user_lower for word in ['premium', 'expensive', 'high-end', 'best']):
            preferences['budget_category'] = 'premium'
        elif any(word in user_lower for word in ['mid-range', 'moderate', 'average']):
            preferences['budget_category'] = 'mid-range'
        
        # Extract performance priorities
        priorities = []
        if any(word in user_lower for word in ['handling', 'grip', 'traction', 'performance']):
            priorities.append('handling')
        if any(word in user_lower for word in ['comfort', 'smooth', 'quiet', 'ride']):
            priorities.append('comfort')
        if any(word in user_lower for word in ['longevity', 'durability', 'wear', 'life']):
            priorities.append('longevity')
        if any(word in user_lower for word in ['fuel efficiency', 'mpg', 'economy', 'efficiency']):
            priorities.append('fuel_efficiency')
        
        if priorities:
            preferences['performance_priorities'] = priorities
        
        # Extract special considerations
        considerations = []
        if any(word in user_lower for word in ['all-season', 'all season', 'year-round']):
            considerations.append('all_season')
        if any(word in user_lower for word in ['winter', 'snow', 'cold']):
            considerations.append('winter_performance')
        if any(word in user_lower for word in ['quiet', 'noise', 'sound']):
            considerations.append('noise_reduction')
        if any(word in user_lower for word in ['warranty', 'guarantee']):
            considerations.append('warranty_important')
        
        if considerations:
            preferences['special_considerations'] = considerations
        
        return preferences if preferences else None
    
    async def process_message(self, user_message: str, roadmap: ConversationRoadmap, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with preferences gathering logic"""
        
        # Extract preferences if present in message
        preferences = self._extract_preferences_from_message(user_message)
        if preferences:
            # Merge with existing preferences
            existing_preferences = roadmap.get_shared_data(DataCategory.BUDGET_PREFERENCES) or {}
            merged_preferences = {**existing_preferences, **preferences}
            self.update_roadmap_data(roadmap, DataCategory.BUDGET_PREFERENCES, merged_preferences)
            logger.info(f"Extracted preferences from message: {preferences}")
        
        # Process with base agent logic
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        # Check if we can advance to next step
        if roadmap.has_data_for_category(DataCategory.BUDGET_PREFERENCES):
            if roadmap.can_advance_to_step(ConversationStep.RECOMMENDATION_GENERATION):
                roadmap.advance_to_next_step()
                logger.info("Advanced to recommendation generation step")
        
        return response 