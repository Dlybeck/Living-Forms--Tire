"""
Unified Tire Sales Assistant Agent
Combines internal thinking process (like Scribe) with user interaction and form generation
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from .ai_client import AIClient, ModelType

from .form_builder import FormBuilder
from .function_call_parser import FunctionCallParser
from config.prompt import prompt

logger = logging.getLogger(__name__)

class UnifiedTireAgent:
    """
    Unified Tire Sales Assistant Agent
    Combines internal thinking process with user interaction and form generation
    """
    
    def __init__(self, ai_client: AIClient, form_builder: FormBuilder):
        self.ai_client = ai_client
        self.form_builder = form_builder
        self.function_parser = FunctionCallParser()
        self.agent_name = "UnifiedTireAgent"
        
        logger.debug(f"Initialized {self.agent_name}")
    
    def get_agent_prompt(self) -> str:
        return prompt
    
    def _get_agent_display_name(self) -> str:
        return "Tire Sales Assistant"
    
    async def process_message(self, 
                            user_message: str, 
                            roadmap: Dict[str, Any],
                            conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message with internal thinking and external response generation
        """
        try:
            # Build comprehensive context including conversation history
            enhanced_context = await self._build_enhanced_context(user_message, roadmap, conversation_context)
            
            # Generate response with internal thinking and external output
            response = await self._generate_unified_response(user_message, roadmap, enhanced_context)
            
            # Extract internal analysis and external components
            response_text = response.get("text", "")
            logger.debug(f"Raw AI response: {response_text[:200]}...")
            
            internal_analysis, conversation_text, form_html = self._parse_unified_response(response_text)
            
            logger.debug(f"Parsed - Internal: {len(internal_analysis)} chars, Conversation: {len(conversation_text)} chars, Form: {len(form_html)} chars")
            
            # Update roadmap with internal analysis (like Scribe did)
            if internal_analysis:
                roadmap['ai_notepad'] = internal_analysis
            

            
            return {
                "response": conversation_text,
                "conversation_text": conversation_text,
                "form_html": form_html,
                "enhanced_notepad": internal_analysis,

                "current_agent": self.agent_name,
                "agent_display_name": self._get_agent_display_name()
            }
            
        except Exception as e:
            logger.error(f"Error in UnifiedTireAgent: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _build_enhanced_context(self, user_message: str, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build enhanced context including conversation history and current state
        """
        # Get current notepad
        current_notepad = roadmap.get('ai_notepad', '')
        
        # Build form data analysis
        form_data = conversation_context.get('form_data', {})
        form_analysis = ""
        if form_data:
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
        
        # Build conversation history analysis
        conversation_history = conversation_context.get('conversation_history', [])
        conversation_flow = ""
        if conversation_history:
            recent_interactions = conversation_history[-5:]  # Last 5 interactions
            conversation_flow = "Recent Conversation Flow:\n"
            for interaction in recent_interactions:
                if interaction.get('type') == 'form_submission':
                    flow_data = interaction.get('form_data', {})
                    if flow_data.get('_context', {}).get('is_initial_form'):
                        conversation_flow += f"- User initially selected: {flow_data['_context']['selected_label']}\n"
                    else:
                        choices = []
                        for key, value in flow_data.items():
                            if key not in ['_context'] and value and str(value).lower() not in ['false', 'none', '']:
                                choices.append(f"{key}: {value}")
                        if choices:
                            conversation_flow += f"- User form choices: {', '.join(choices)}\n"
                else:
                    conversation_flow += f"- User message: {interaction.get('message', '')}\n"
        
        # Build enhanced context
        enhanced_context = {
            "current_notepad": current_notepad,
            "user_message": user_message,
            "form_data": form_data,
            "form_analysis": form_analysis,
            "conversation_history": conversation_history,
            "conversation_flow": conversation_flow,
            "current_step": conversation_context.get('current_step', 'unknown'),
            "needs_form": True,
            "current_goal": "Find the right tires for the user's vehicle"
        }
        
        return enhanced_context
    
    async def _generate_unified_response(self, user_message: str, roadmap: Dict[str, Any], enhanced_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate unified response with internal thinking and external output
        """
        # Build the unified prompt
        unified_prompt = f"""
Current AI Notepad:
{enhanced_context.get('current_notepad', '')}

User Message: {user_message}

Form Data: {enhanced_context.get('form_data', {})}
{enhanced_context.get('form_analysis', '')}

Conversation Context:
- Current Step: {enhanced_context.get('current_step', 'unknown')}
- Conversation Flow: {enhanced_context.get('conversation_flow', '')}

Please complete your internal thinking process and generate your response following the exact format specified in your prompt.

Remember to:
1. Complete your "Living Form's Mind: Riley's Head" internal analysis
2. Generate conversational response for the user
3. Generate appropriate form fields if needed
4. Use the exact output format: [INTERNAL_ANALYSIS], [CONVERSATION], [FORM]
"""
        
        # Use O4-mini for better reasoning and analysis
        response = await self.ai_client.generate_response(
            user_message=unified_prompt,
            conversation_context=enhanced_context,
            model_type=ModelType.O4_MINI,  # Use O4-mini for better reasoning
            agent_prompt=self.get_agent_prompt(),
            response_format="function_calls_and_chat",
            function_documentation=self.function_parser.get_function_documentation()
        )
        

        
        return response
    
    def _parse_unified_response(self, response_text: str) -> Tuple[str, str, str]:
        """
        Parse the unified response into internal analysis, conversation text, and form HTML
        """
        internal_analysis = ""
        conversation_text = ""
        form_html = ""
        
        # Extract internal analysis
        internal_match = re.search(r'\[INTERNAL_ANALYSIS\](.*?)(?=\[CONVERSATION\]|\[FORM\]|$)', response_text, re.DOTALL)
        if internal_match:
            internal_analysis = internal_match.group(1).strip()
        
        # Extract conversation text
        conversation_match = re.search(r'\[CONVERSATION\](.*?)(?=\[FORM\]|$)', response_text, re.DOTALL)
        if conversation_match:
            conversation_text = conversation_match.group(1).strip()
        
        # Check if we have embedded function calls in the conversation text
        if conversation_text and re.search(r'\{[^}]+\}', conversation_text):
            logger.debug("Found embedded function calls in conversation text, using embedded form method")
            form_html = self.form_builder.create_embedded_form(conversation_text)
        else:
            # Only use function call parser if no embedded calls found
            conversation_text_from_form, form_html = self.function_parser.parse_function_calls(conversation_text)
            # If no conversation text was extracted from the conversation section, use the one from form parsing
            if not conversation_text and conversation_text_from_form:
                conversation_text = conversation_text_from_form
        
        # If no sections were found, treat the entire response as conversation text
        if not internal_analysis and not conversation_text:
            logger.warning("AI response did not contain the required sections [INTERNAL_ANALYSIS] or [CONVERSATION]. Treating entire response as conversation text.")
            conversation_text = response_text.strip()
            # Check if the conversation text contains embedded function calls
            if re.search(r'\{[^}]+\}', conversation_text):
                form_html = self.form_builder.create_embedded_form(conversation_text)
            else:
                # Try to parse function calls from the entire response
                conversation_text_from_form, form_html = self.function_parser.parse_function_calls(conversation_text)
                if conversation_text_from_form:
                    conversation_text = conversation_text_from_form
        
        return internal_analysis, conversation_text, form_html 
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "response": "I'm experiencing some technical difficulties. Please try again.",
            "conversation_text": "I'm experiencing some technical difficulties. Please try again.",
            "form_html": "",
            "enhanced_notepad": "",

            "current_agent": self.agent_name,
            "agent_display_name": "Tire Sales Assistant"
        } 