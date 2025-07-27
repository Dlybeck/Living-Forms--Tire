"""
Unified Tire Sales Assistant Agent
Combines internal thinking process with user interaction and form generation
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from .ai_client import AIClient, ModelType
from .form_builder import FormBuilder
from .utils import create_error_response
from config.prompt import prompt

logger = logging.getLogger(__name__)

class TireAgent:
    """
    Tire Sales Assistant Agent
    Combines internal thinking process with user interaction and form generation
    """
    
    def __init__(self, ai_client: AIClient, form_builder: FormBuilder):
        self.ai_client = ai_client
        self.form_builder = form_builder

        self.agent_name = "TireAgent"
        
        logger.debug(f"Initialized {self.agent_name}")
    
    def get_agent_prompt(self) -> str:
        return prompt
    

    
    async def process_message(self, 
                            user_message: str, 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message with internal thinking and external response generation
        """
        try:
            # Generate response with internal thinking and external output
            response = await self._generate_unified_response(user_message, context)
            
            # Extract internal analysis and external components
            response_text = response.get("text", "")
            logger.debug(f"Raw AI response: {response_text[:200]}...")
            
            internal_analysis, conversation_text, form_html = self._parse_unified_response(response_text)
            
            logger.debug(f"Parsed - Internal: {len(internal_analysis)} chars, Conversation: {len(conversation_text)} chars, Form: {len(form_html)} chars")
            
            # Update context with internal analysis
            if internal_analysis:
                context['ai_notepad'] = internal_analysis
            

            
            return {
                "response": conversation_text,
                "form_html": form_html,
                "ai_notepad": context.get('ai_notepad', internal_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in TireAgent: {str(e)}")
            return create_error_response(str(e))
    

    
    async def _generate_unified_response(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate unified response with internal thinking and external output
        """
        # Build the unified prompt
        unified_prompt = f"""
            Current AI Notepad:
            {context.get('ai_notepad', '')}

            User Message: {user_message}

            Form Data: {context.get('form_data', {})}

            Conversation Context:
            - Current Step: {context.get('current_step', 'unknown')}
            - Conversation History: {len(context.get('conversation_history', []))} interactions

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
            conversation_context=context,
            model_type=ModelType.O4_MINI,  # Use O4-mini for better reasoning
            agent_prompt=self.get_agent_prompt(),
            function_documentation=self.form_builder.get_function_documentation()
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

        
        # If no sections were found, treat the entire response as conversation text
        if not internal_analysis and not conversation_text:
            logger.warning("AI response did not contain the required sections [INTERNAL_ANALYSIS] or [CONVERSATION]. Treating entire response as conversation text.")
            conversation_text = response_text.strip()
            # Check if the conversation text contains embedded function calls
            if re.search(r'\{[^}]+\}', conversation_text):
                form_html = self.form_builder.create_embedded_form(conversation_text)

        
        return internal_analysis, conversation_text, form_html 