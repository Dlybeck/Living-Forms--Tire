"""
PreferencesAgent - Specialized agent for gathering budget and performance preferences
Handles understanding user's budget constraints and performance priorities
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.conversation_enums import ConversationStep, DataCategory
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
    
    def _needs_web_search(self, user_message: str, roadmap: Dict[str, Any]) -> bool:
        """Determine if web search is needed"""
        return False
    
    def _get_form_purpose(self, roadmap: Dict[str, Any]) -> str:
        """Get the purpose of form generation for preferences gathering"""
        # For now, return a default purpose since we're using simplified session structure
        return "collect_preferences"
    
    async def process_message(self, user_message: str, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with preferences gathering logic"""
        
        # Check for form data first
        form_data = conversation_context.get('form_data', {})
        if form_data:
            logger.info(f"Processing preferences form data: {form_data}")
            
            # Handle budget range
            if 'budget_range' in form_data:
                budget_range = form_data['budget_range']
                logger.info(f"User provided budget range: {budget_range}")
                conversation_context['budget_range'] = budget_range
                conversation_context['budget_provided'] = True
            
            # Handle budget category
            if 'budget_category' in form_data:
                category = form_data['budget_category']
                logger.info(f"User budget category: {category}")
                conversation_context['budget_category'] = category
                conversation_context['category_provided'] = True
            
            # Handle performance priorities
            if 'performance_priorities' in form_data:
                priorities = form_data['performance_priorities']
                logger.info(f"User performance priorities: {priorities}")
                conversation_context['performance_priorities'] = priorities
                conversation_context['priorities_provided'] = True
            
            # Handle tire type preferences
            if 'tire_type' in form_data:
                tire_type = form_data['tire_type']
                logger.info(f"User tire type preference: {tire_type}")
                conversation_context['tire_type_preference'] = tire_type
                conversation_context['tire_type_provided'] = True
            
            # Handle brand preferences
            if 'brand_preferences' in form_data:
                brands = form_data['brand_preferences']
                logger.info(f"User brand preferences: {brands}")
                conversation_context['brand_preferences'] = brands
                conversation_context['brands_provided'] = True
            
            # Handle run-flat preferences
            if 'run_flat_preference' in form_data:
                run_flat = form_data['run_flat_preference']
                logger.info(f"User run-flat preference: {run_flat}")
                conversation_context['run_flat_preference'] = run_flat
                conversation_context['run_flat_provided'] = True
            
            # Handle special considerations
            if 'special_considerations' in form_data:
                considerations = form_data['special_considerations']
                logger.info(f"User special considerations: {considerations}")
                conversation_context['special_considerations'] = considerations
                conversation_context['considerations_provided'] = True
            
            # Handle installation preferences
            if 'installation_preferences' in form_data:
                installation = form_data['installation_preferences']
                logger.info(f"User installation preferences: {installation}")
                conversation_context['installation_preferences'] = installation
                conversation_context['installation_provided'] = True
        
        # Extract preferences if present in message
        preferences = self._extract_preferences_from_message(user_message)
        if preferences:
            logger.info(f"Extracted preferences from message: {preferences}")
            conversation_context['extracted_preferences'] = preferences
        
        # Process with base agent logic
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        return response
    
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