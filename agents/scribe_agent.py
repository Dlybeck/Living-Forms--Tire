"""
Scribe AI Agent
Automatically extracts and records important information from conversations
"""

import re
import logging
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from agents.ai_client import AIClient
from agents.cost_manager import CostManager, ModelType
from agents.form_builder import FormBuilder
from utils.conversation_enums import ConversationStep, DataCategory
from prompts.scribe_agent_prompt import SCRIBE_AGENT_PROMPT

logger = logging.getLogger(__name__)

class ScribeAgent(BaseAgent):
    """
    Scribe AI Agent - Automatically extracts and records important information
    """
    
    def __init__(self, ai_client: AIClient, cost_manager: CostManager, form_builder: FormBuilder):
        super().__init__(ai_client, cost_manager, form_builder, "ScribeAgent")
    
    def get_system_prompt(self) -> str:
        return SCRIBE_AGENT_PROMPT
    
    def get_agent_prompt(self) -> str:
        return "Extract and record any important information from this conversation."
    
    async def extract_and_record(self, user_message: str, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract important information from the conversation and record it in the notepad using GPT-4o
        """
        logger.info(f"ScribeAgent starting extraction for message: {user_message[:100]}...")
        try:
            # Use GPT-4o for intelligent information extraction
            current_notepad = roadmap.get('ai_notepad', '')
            
            # Build the extraction prompt
            form_data = conversation_context.get('form_data', {})
            
            # Enhanced context extraction for initial form
            context_info = ""
            if form_data.get('_context', {}).get('is_initial_form'):
                context_info = f"""
Initial Form Context:
- User selected: {form_data['_context']['selected_label']}
- Description: {form_data['_context']['selected_description']}
- User context: {form_data['_context']['user_context']}
"""
            
            # Analyze form data for user choices and progression
            form_analysis = ""
            if form_data:
                # Check for specific user choices in the form
                user_choices = []
                for key, value in form_data.items():
                    if key not in ['_context'] and value and str(value).lower() not in ['false', 'none', '']:
                        if isinstance(value, list):
                            user_choices.extend([f"{key}: {v}" for v in value if v])
                        else:
                            user_choices.append(f"{key}: {value}")
                
                if user_choices:
                    form_analysis = f"""
User Form Choices:
{chr(10).join([f"- {choice}" for choice in user_choices])}
"""
            
            # Build comprehensive context for the ScribeAgent
            conversation_history = conversation_context.get('conversation_history', [])
            current_step = conversation_context.get('current_step', 'unknown')
            
            # Analyze the conversation flow
            conversation_flow = ""
            if conversation_history:
                # Get the last few interactions to understand progression
                recent_interactions = conversation_history[-3:]  # Last 3 interactions
                conversation_flow = "Recent Conversation Flow:\n"
                for interaction in recent_interactions:
                    if interaction.get('type') == 'form_submission':
                        flow_data = interaction.get('form_data', {})
                        if flow_data.get('_context', {}).get('is_initial_form'):
                            conversation_flow += f"- User initially selected: {flow_data['_context']['selected_label']}\n"
                        else:
                            # Extract what the user chose from the form
                            choices = []
                            for key, value in flow_data.items():
                                if key not in ['_context'] and value and str(value).lower() not in ['false', 'none', '']:
                                    choices.append(f"{key}: {value}")
                            if choices:
                                conversation_flow += f"- User form choices: {', '.join(choices)}\n"
                    else:
                        conversation_flow += f"- User message: {interaction.get('message', '')}\n"
            
            extraction_prompt = f"""
Current AI Notepad:
{current_notepad}

User Message: {user_message}

Form Data: {form_data}
{context_info}
{form_analysis}

Conversation Context:
- Current Step: {current_step}
- Conversation Flow: {conversation_flow}

Please analyze this information and update the AI Notepad with any important details. 

CRITICAL: Pay special attention to the "User Intent & Current Task" section and update it based on the conversation progression:

1. **User's Primary Goal**: What is the user ultimately trying to achieve?
2. **Current User Focus/Action**: What is the user actively working on or has just decided to do? (e.g., "checking tire sidewall for size," "being guided through information finding process")
3. **Next Expected Input/System Action**: What information are we waiting for from the user, or what is the logical next step for the system?

IMPORTANT GUIDANCE FOR CONVERSATION PROGRESSION:
- If the user initially said "I'm not sure" and the system offered options, update "Current User Focus/Action" to reflect that the user is now being guided through the information finding process
- If the user made specific choices from offered options, update "Current User Focus/Action" to reflect their chosen method
- If the user submitted a form with choices, update "Next Expected Input/System Action" to reflect what the system should do next based on those choices
- Always update the situation based on the user's actual choices, not assumptions

Focus on:
- Vehicle information (make, model, year, tire size, VIN)
- User situation (proximity to car, document access)
- User preferences (budget, driving patterns, tire type preferences)
- Conversation context (user's goals, challenges, questions)

Update the notepad with new information, replacing outdated details. Keep it concise and actionable.

IMPORTANT: Only record factual information. Do NOT add conversational text, suggestions, or next steps. The notepad should contain only the raw data and facts.
"""
            
            # Generate response using GPT-4o
            response = await self.ai_client.generate_response(
                user_message=extraction_prompt,
                conversation_context={"current_step": "information_extraction"},
                model_type=ModelType.GPT_4O_MINI,  # Use GPT-4o as requested
                response_format="text"
            )
            
            # Extract the updated notepad content
            updated_notepad = response.get("text", "").strip()
            
            # Track cost
            self.cost_manager.track_cost("scribe_extraction", response["cost"], roadmap)
            
            # Update the roadmap with new notepad content
            roadmap['ai_notepad'] = updated_notepad
            
            logger.info(f"ScribeAgent updated notepad: {updated_notepad[:100]}...")
            
            return {
                "extracted_info": {"notepad_updated": True},
                "notepad_updated": True,
                "notepad_content": updated_notepad
            }
            
        except Exception as e:
            logger.error(f"Error in ScribeAgent extraction: {str(e)}")
            return {"extracted_info": {}, "notepad_updated": False, "notepad_content": roadmap.get('ai_notepad', '')} 