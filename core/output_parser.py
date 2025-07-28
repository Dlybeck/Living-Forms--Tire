"""
Output Parser using LangChain components
Replaces manual response parsing with structured output parsing
"""

from typing import Dict, Any, Optional
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
import re
import logging

logger = logging.getLogger(__name__)

class TireAgentResponse(BaseModel):
    """Structured response format for the tire agent"""
    internal_analysis: str = Field(description="The internal thinking process (Riley's Head)")
    conversation: str = Field(description="The conversational response to the user with embedded form fields")
    form_fields: Optional[str] = Field(default=None, description="Any additional form field specifications")

class LangChainOutputParser:
    """
    Output parser using LangChain's structured output capabilities
    """
    
    def __init__(self):
        self.parser = PydanticOutputParser(pydantic_object=TireAgentResponse)
        self.fallback_parser = StrOutputParser()
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response using LangChain output parser with fallback
        """
        try:
            # Try structured parsing first
            parsed = self.parser.parse(response_text)
            logger.debug("Successfully parsed response using structured parser")
            
            return {
                'internal_analysis': parsed.internal_analysis,
                'conversation_text': parsed.conversation,
                'form_fields': parsed.form_fields
            }
            
        except Exception as e:
            logger.warning(f"Structured parsing failed, falling back to regex: {e}")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> Dict[str, Any]:
        """
        Fallback parsing using regex (current method)
        """
        internal_analysis = ""
        conversation_text = ""
        form_fields = None
        
        # Extract internal analysis
        internal_match = re.search(r'\[INTERNAL_ANALYSIS\](.*?)(?=\[CONVERSATION\]|\[FORM\]|$)', response_text, re.DOTALL)
        if internal_match:
            internal_analysis = internal_match.group(1).strip()
        
        # Extract conversation text
        conversation_match = re.search(r'\[CONVERSATION\](.*?)(?=\[FORM\]|$)', response_text, re.DOTALL)
        if conversation_match:
            conversation_text = conversation_match.group(1).strip()
        
        # If no sections found, treat entire response as conversation
        if not internal_analysis and not conversation_text:
            conversation_text = response_text.strip()
        
        return {
            'internal_analysis': internal_analysis,
            'conversation_text': conversation_text,
            'form_fields': form_fields
        }
    
    def get_parser_instructions(self) -> str:
        """
        Get instructions for the AI to use structured output
        """
        return f"""
        Please format your response as a JSON object with the following structure:
        {{
            "internal_analysis": "Your complete internal thinking process here...",
            "conversation": "Your conversational response with embedded form fields like {{create_text_field(name='example', label='Example Field', required=False)}}",
            "form_fields": null
        }}
        
        If you cannot use JSON format, use the section headers:
        [INTERNAL_ANALYSIS]
        Your internal thinking process...
        
        [CONVERSATION]
        Your conversational response...
        """ 