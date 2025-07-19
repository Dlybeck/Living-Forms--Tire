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
            
            # Handle location/region data
            if 'user_location' in form_data:
                location = form_data['user_location']
                logger.info(f"User provided location: {location}")
                conversation_context['user_location'] = location
                conversation_context['location_provided'] = True
            
            # Handle mileage data
            if 'total_mileage' in form_data:
                total_mileage = form_data['total_mileage']
                logger.info(f"User provided total mileage: {total_mileage}")
                conversation_context['total_mileage'] = total_mileage
                conversation_context['mileage_provided'] = True
                
                # Calculate annual mileage if we have model year
                if 'vehicle_year' in conversation_context.get('important_data', {}):
                    vehicle_year = conversation_context['important_data']['vehicle_year']
                    current_year = 2024  # Could be made dynamic
                    years_owned = current_year - int(vehicle_year) + 1
                    if years_owned > 0:
                        annual_mileage = int(total_mileage) / years_owned
                        conversation_context['calculated_annual_mileage'] = round(annual_mileage)
                        logger.info(f"Calculated annual mileage: {annual_mileage}")
            
            # Handle driving environment
            if 'driving_environment' in form_data:
                environment = form_data['driving_environment']
                logger.info(f"User driving environment: {environment}")
                conversation_context['driving_environment'] = environment
                conversation_context['environment_provided'] = True
            
            # Handle weather conditions
            if 'weather_conditions' in form_data:
                weather = form_data['weather_conditions']
                logger.info(f"User weather conditions: {weather}")
                conversation_context['weather_conditions'] = weather
                conversation_context['weather_provided'] = True
            
            # Handle driving style
            if 'driving_style' in form_data:
                style = form_data['driving_style']
                logger.info(f"User driving style: {style}")
                conversation_context['driving_style'] = style
                conversation_context['style_provided'] = True
            
            # Handle vehicle usage
            if 'vehicle_usage' in form_data:
                usage = form_data['vehicle_usage']
                logger.info(f"User vehicle usage: {usage}")
                conversation_context['vehicle_usage'] = usage
                conversation_context['usage_provided'] = True
            
            # Handle ownership plans
            if 'ownership_plans' in form_data:
                plans = form_data['ownership_plans']
                logger.info(f"User ownership plans: {plans}")
                conversation_context['ownership_plans'] = plans
                conversation_context['plans_provided'] = True
        
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