"""
Comprehensive Tire Agent - Single agent handling all tire sales interactions
Replaces the multi-agent system with a unified approach
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
# Removed conversation enums - simplified system
import re
import logging

logger = logging.getLogger(__name__)

class ComprehensiveTireAgent(BaseAgent):
    """
    Comprehensive tire agent that handles all aspects of tire sales
    Uses the new combined prompt to manage the entire conversation flow
    """
    
    def __init__(self, ai_client, cost_manager, form_builder):
        super().__init__(ai_client, cost_manager, form_builder, "ComprehensiveTireAgent")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for comprehensive tire sales"""
        from prompts.system_prompt import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    def get_agent_prompt(self) -> str:
        """Get the comprehensive tire agent prompt"""
        from prompts.new_combined_prompt import COMPREHENSIVE_TIRE_ASSISTANT_PROMPT
        return COMPREHENSIVE_TIRE_ASSISTANT_PROMPT
    
    def _needs_web_search(self, user_message: str, roadmap: Dict[str, Any]) -> bool:
        """Determine if web search is needed"""
        # For now, assume we don't need web search
        return False
    
    def _get_form_purpose(self, roadmap: Dict[str, Any]) -> str:
        """Get the purpose of form generation"""
        return "comprehensive_tire_assistance"
    
    def _extract_tire_size_from_message(self, user_message: str) -> Optional[str]:
        """Extract tire size from user message"""
        # Look for tire size pattern (e.g., 225/60R16)
        tire_size_pattern = r'\b\d{3}/\d{2}R\d{2}\b'
        match = re.search(tire_size_pattern, user_message.upper())
        if match:
            return match.group()
        return None
    
    def _extract_vehicle_info(self, user_message: str) -> Optional[Dict[str, str]]:
        """Extract vehicle information from user message"""
        vehicle_info = {}
        
        # Extract year (4-digit year)
        year_pattern = r'\b(19|20)\d{2}\b'
        year_match = re.search(year_pattern, user_message)
        if year_match:
            vehicle_info['vehicle_year'] = year_match.group()
        
        # Extract make and model (basic patterns)
        # This is simplified - the AI will handle more complex extraction
        return vehicle_info if vehicle_info else None
    
    async def process_message(self, user_message: str, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with comprehensive tire sales logic"""
        
        # Check for form data first
        form_data = conversation_context.get('form_data', {})
        if form_data:
            logger.info(f"Processing form data: {form_data}")
            
            # Log what was provided for debugging
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
        
        # Process with base agent logic (this will use the comprehensive prompt)
        response = await super().process_message(user_message, roadmap, conversation_context)
        
        return response
    
    async def _assess_task_completion(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess if the comprehensive tire assistance task is complete
        This agent handles the entire conversation, so completion is user-driven
        """
        # The comprehensive agent doesn't "complete" - it continues until user is satisfied
        return {
            "is_complete": False,  # Never auto-complete
            "completion_reason": "User-driven completion",
            "next_step": "Continue comprehensive assistance"
        } 