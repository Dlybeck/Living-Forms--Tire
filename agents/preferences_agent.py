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
        return """
You are a preferences specialist. Your job is to understand the user's budget constraints and performance priorities for tire selection.

**YOUR MISSION:**
Collect detailed information about the user's preferences, including:
- Budget range and constraints
- Performance priorities and trade-offs
- Special considerations and requirements
- Brand preferences and loyalty
- Installation and service preferences

**KEY AREAS TO EXPLORE:**
1. **Budget Range**: Total budget, per-tire budget, installation costs
2. **Performance Priorities**: Handling vs comfort vs longevity vs fuel efficiency
3. **Special Considerations**: All-season needs, winter performance, noise sensitivity
4. **Brand Preferences**: Brand loyalty, previous experiences, recommendations
5. **Service Preferences**: Installation location, warranty importance, maintenance

**CONVERSATION APPROACH:**
- Help users understand the trade-offs between different tire characteristics
- Explain how budget affects performance options
- Suggest ways to maximize value within their constraints
- Be educational about tire performance characteristics

**FORM GENERATION:**
Create forms to collect:
- Budget range and constraints
- Performance priority rankings
- Special considerations and requirements
- Brand preferences and experiences
- Service and installation preferences

**CRITICAL - AVOID PERSONAL QUESTIONS:**
- NEVER ask for personal information like names of family members, friends, or specific people
- NEVER ask "who can you ask" or "who do you know" - this is intrusive
- Instead, suggest general approaches: "You could ask family or friends" or "Check with someone who might know"
- Focus on WHAT information they need to find, not WHO they should ask
- If suggesting they ask others, keep it general: "Ask someone who might know your vehicle details"
- Your goal is to help them understand what information they need, not to gather personal details about their relationships
"""
    
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for preferences gathering"""
        return """
You are the PreferencesAgent, specialized in understanding budget and performance preferences.

**CURRENT GOAL**: Collect comprehensive information about the user's budget and performance preferences.

**KEY INFORMATION TO GATHER**:
1. Budget range and constraints (total and per-tire)
2. Performance priority rankings (handling, comfort, longevity, efficiency)
3. Special considerations (all-season, winter, noise, etc.)
4. Brand preferences and experiences
5. Service and installation preferences

**CONVERSATION STRATEGY**:
- Help users understand performance trade-offs
- Explain how budget affects options
- Suggest ways to maximize value
- Be educational about tire characteristics

**FORM GENERATION PRIORITY**:
- Collect budget range and constraints
- Assess performance priorities
- Gather special considerations
- Identify brand preferences
- Determine service preferences

Focus on being helpful and educational about tire selection trade-offs.
"""
    
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
    
    def _needs_form_generation(self, user_message: str, roadmap: ConversationRoadmap, reasoning_response: Dict[str, Any]) -> bool:
        """Determine if form generation is needed for preferences gathering"""
        
        # Check if we already have comprehensive preferences
        budget_preferences = roadmap.get_shared_data(DataCategory.BUDGET_PREFERENCES)
        if budget_preferences and self._has_comprehensive_preferences(budget_preferences):
            logger.info("No form needed: Already have comprehensive preferences")
            return False
        
        # Check if user provided preferences in message
        if self._extract_preferences_from_message(user_message):
            logger.info("No form needed: Preferences found in message")
            return False
        
        # Check if we need to collect more information
        if not budget_preferences or not self._has_basic_preferences(budget_preferences):
            logger.info("Form needed: Missing basic preferences")
            return True
        
        # Check if user needs help with specific aspects
        help_keywords = ['not sure', 'don\'t know', 'help', 'what do you mean', 'explain']
        if any(keyword in user_message.lower() for keyword in help_keywords):
            logger.info("Form needed: User needs help with preferences")
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