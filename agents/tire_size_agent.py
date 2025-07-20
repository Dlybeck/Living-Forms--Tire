"""
TireSizeAgent - Specialized agent for tire size discovery
Handles the complex task of finding the user's tire size through various methods
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.conversation_enums import ConversationStep, DataCategory
import re
import logging

logger = logging.getLogger(__name__)

class TireSizeAgent(BaseAgent):
    """
    Specialized agent for tire size discovery
    Uses web search and creative problem-solving to find tire sizes
    """
    
    def __init__(self, ai_client, cost_manager, form_builder):
        super().__init__(ai_client, cost_manager, form_builder, "TireSizeAgent")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for tire size discovery"""
        from prompts import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for tire size discovery"""
        from prompts import TIRE_SIZE_AGENT_PROMPT
        return TIRE_SIZE_AGENT_PROMPT
    
    def _needs_web_search(self, user_message: str, roadmap: Dict[str, Any]) -> bool:
        """Determine if web search is needed for tire size discovery"""
        
        # Check if we have complete vehicle info
        # For now, assume we don't need web search
        return False
        
        # Check if user mentioned VIN
        if 'vin' in user_message.lower() or 'vehicle identification' in user_message.lower():
            logger.info("Web search needed: User mentioned VIN for decoding")
            return True
        
        # Check if user is asking for tire size help
        tire_size_keywords = ['tire size', 'what size', 'size tire', 'factory tire', 'oem tire']
        if any(keyword in user_message.lower() for keyword in tire_size_keywords):
            logger.info("Web search needed: User asking for tire size help")
            return True
        
        return False
    
    def _get_form_purpose(self, roadmap: Dict[str, Any]) -> str:
        """Get the purpose of form generation for tire size discovery"""
        # For now, return a default purpose
        return "collect_vehicle_info"
    
    def _extract_tire_size_from_message(self, user_message: str) -> Optional[str]:
        """Extract tire size from user message"""
        # Look for tire size pattern (e.g., 225/60R16)
        tire_size_pattern = r'\b\d{3}/\d{2}R\d{2}\b'
        match = re.search(tire_size_pattern, user_message.upper())
        if match:
            return match.group()
        return None
    
    async def process_message(self, user_message: str, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with tire size discovery logic"""
        
        # Check for form data first
        form_data = conversation_context.get('form_data', {})
        if form_data:
            logger.info(f"Processing form data: {form_data}")
            
            # Let ScribeAgent handle the information extraction and recording
            # We just log what was provided for debugging
            for field, value in form_data.items():
                if value and str(value).lower() not in ['false', 'none', '']:
                    logger.info(f"User provided {field}: {value}")
        
        # Extract tire size if present in message
        tire_size = self._extract_tire_size_from_message(user_message)
        if tire_size:
            logger.info(f"Extracted tire size from message: {tire_size}")
            conversation_context['extracted_tire_size'] = tire_size
        
        # Extract vehicle info if present
        vehicle_info = self._extract_vehicle_info(user_message)
        if vehicle_info:
            logger.info(f"Extracted vehicle info: {vehicle_info}")
            conversation_context['extracted_vehicle_info'] = vehicle_info
        
        # Process with base agent logic
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        return response
    
    def _extract_vehicle_info(self, user_message: str) -> Optional[Dict[str, str]]:
        """Extract vehicle information from user message"""
        vehicle_info = {}
        user_lower = user_message.lower()
        
        # Extract make
        makes = ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai', 'volkswagen', 'bmw', 'mercedes', 'audi']
        for make in makes:
            if make in user_lower:
                vehicle_info['make'] = make.title()
                break
        
        # Extract model (common models)
        models = {
            'kia': ['forte', 'soul', 'sportage', 'sorento', 'telluride', 'k5', 'rio'],
            'honda': ['civic', 'accord', 'cr-v', 'pilot', 'odyssey', 'fit'],
            'toyota': ['camry', 'corolla', 'rav4', 'highlander', 'sienna', 'prius'],
            'ford': ['f-150', 'escape', 'explorer', 'mustang', 'focus', 'fusion'],
            'chevrolet': ['silverado', 'equinox', 'tahoe', 'camaro', 'cruze', 'malibu']
        }
        
        current_make = vehicle_info.get('make', '').lower()
        if current_make in models:
            for model in models[current_make]:
                if model in user_lower:
                    vehicle_info['model'] = model.title()
                    break
        
        # Extract year (4-digit year)
        year_match = re.search(r'\b(19|20)\d{2}\b', user_message)
        if year_match:
            vehicle_info['year'] = year_match.group()
        
        return vehicle_info if vehicle_info else None 