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
        return """
You are a tire recommendation specialist. Your job is to analyze user data and generate personalized tire recommendations.

**YOUR MISSION:**
Generate personalized tire recommendations based on:
- Vehicle specifications and tire size
- Driving patterns and usage
- Budget constraints and preferences
- Performance priorities and requirements
- Special considerations and needs

**RECOMMENDATION PROCESS:**
1. **Analyze Requirements**: Review all collected user data
2. **Match Criteria**: Find tires that meet the user's needs
3. **Rank Options**: Prioritize recommendations based on fit
4. **Explain Choices**: Provide clear reasoning for each recommendation
5. **Compare Options**: Highlight differences between recommendations

**RECOMMENDATION TYPES:**
- **Primary Recommendation**: Best overall match for user's needs
- **Budget Alternative**: Cost-effective option that meets requirements
- **Premium Option**: High-performance choice if budget allows
- **Specialized Option**: Specific solution for unique requirements

**EXPLANATION APPROACH:**
- Explain why each tire is recommended
- Highlight key features and benefits
- Address specific user concerns and priorities
- Provide clear comparisons between options
- Include pricing and value considerations

**FORM GENERATION:**
Create forms to collect:
- User feedback on recommendations
- Questions about specific tires
- Requests for more information
- Comparison preferences
- Final selection preferences

**CRITICAL - AVOID PERSONAL QUESTIONS:**
- NEVER ask for personal information like names of family members, friends, or specific people
- NEVER ask "who can you ask" or "who do you know" - this is intrusive
- Instead, suggest general approaches: "You could ask family or friends" or "Check with someone who might know"
- Focus on WHAT information they need to find, not WHO they should ask
- If suggesting they ask others, keep it general: "Ask someone who might know your vehicle details"
- Your goal is to help them understand what information they need, not to gather personal details about their relationships
"""
    
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for recommendation generation"""
        return """
You are the RecommendationAgent, specialized in generating personalized tire recommendations.

**CURRENT GOAL**: Generate personalized tire recommendations based on comprehensive user data.

**RECOMMENDATION STRATEGY**:
1. Analyze all collected user data (vehicle, driving patterns, preferences)
2. Generate 3-5 personalized recommendations
3. Explain why each tire is recommended
4. Provide clear comparisons and trade-offs
5. Address user's specific needs and concerns

**RECOMMENDATION STRUCTURE**:
- Primary recommendation (best overall match)
- Budget alternative (cost-effective option)
- Premium option (if budget allows)
- Specialized options (for unique requirements)

**EXPLANATION FOCUS**:
- Why each tire matches their needs
- Key features and benefits
- Performance characteristics
- Value for money
- Trade-offs and considerations

**FORM GENERATION PRIORITY**:
- Collect feedback on recommendations
- Gather questions about specific tires
- Assess comparison preferences
- Determine final selection criteria

Focus on being helpful and educational about tire selection and providing clear, actionable recommendations.
"""
    
    def _needs_web_search(self, user_message: str, roadmap: ConversationRoadmap) -> bool:
        """Determine if web search is needed for recommendation generation"""
        
        # Always use web search for recommendations to get current pricing and availability
        logger.info("Web search needed: Generating tire recommendations")
        return True
    
    def _needs_form_generation(self, user_message: str, roadmap: ConversationRoadmap, reasoning_response: Dict[str, Any]) -> bool:
        """Determine if form generation is needed for recommendation generation"""
        
        # Check if user is asking for more information or comparisons
        info_keywords = ['more info', 'tell me more', 'compare', 'difference', 'why']
        if any(keyword in user_message.lower() for keyword in info_keywords):
            logger.info("Form needed: User asking for more information")
            return True
        
        # Check if user is providing feedback on recommendations
        feedback_keywords = ['like', 'dislike', 'prefer', 'better', 'worse', 'good', 'bad']
        if any(keyword in user_message.lower() for keyword in feedback_keywords):
            logger.info("Form needed: User providing feedback")
            return True
        
        # Check if user is ready to make a selection
        selection_keywords = ['choose', 'select', 'buy', 'purchase', 'decide']
        if any(keyword in user_message.lower() for keyword in selection_keywords):
            logger.info("Form needed: User ready to make selection")
            return True
        
        return False
    
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