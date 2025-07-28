import os
import logging
from typing import Dict, Optional, Any
from enum import Enum

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Simple model type enum"""
    O4_MINI = "o4-mini"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet"

class AIClient:
    """
    AI client for the Living Form Tire Sales Assistant
    Handles communication with AI models using LangChain
    """
    
    def __init__(self):
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
        
        # Model mappings for core functionality
        self.model_mappings = {
            ModelType.O4_MINI: {
                'provider': 'openai',
                'model_name': 'o4-mini-2025-04-16',
                'max_completion_tokens': 4096
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'provider': 'anthropic', 
                'model_name': 'claude-3-5-sonnet-latest',
                'max_tokens': 4096
            }
        }
        
        # Initialize LangChain models
        self._init_langchain_models()
        
        logger.debug("AI Client initialized with LangChain models")
    
    def _init_langchain_models(self):
        """Initialize LangChain model instances"""
        self.langchain_models = {}
        
        # Initialize OpenAI models - O4-mini has very limited parameters
        if self.api_keys['openai']:
            try:
                print("[DEBUG] Instantiating O4-mini with:", {
                    "api_key": self.api_keys['openai'],
                    "model": "o4-mini-2025-04-16",
                    "temperature": 1,
                    "model_kwargs": {"max_completion_tokens": 4096}
                })
                self.langchain_models['openai'] = ChatOpenAI(
                    api_key=self.api_keys['openai'],
                    model="o4-mini-2025-04-16",
                    temperature=1,
                    model_kwargs={
                        "max_completion_tokens": 4096
                    }
                )
                logger.debug("OpenAI O4-mini model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI model: {e}")
        
        # Initialize Anthropic models
        if self.api_keys['anthropic']:
            try:
                print("[DEBUG] Instantiating Claude with:", {
                    "api_key": self.api_keys['anthropic'],
                    "model": "claude-3-5-sonnet-latest",
                    "max_tokens": 4096,
                    "temperature": 0.7
                })
                self.langchain_models['anthropic'] = ChatAnthropic(
                    api_key=self.api_keys['anthropic'],
                    model="claude-3-5-sonnet-latest",
                    max_tokens=4096,
                    temperature=0.7
                )
                logger.debug("Anthropic Claude model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic model: {e}")
    
    async def generate_response(self, user_message: str, conversation_context: Dict[str, Any], 
                              model_type: ModelType, agent_prompt: str, 
                              function_documentation: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AI response using specified model via LangChain
        """
        try:
            # Get model configuration
            model_config = self.model_mappings[model_type]
            provider = model_config['provider']
            print(f"[DEBUG] Using model_type: {model_type}, provider: {provider}")
            
            # Get the appropriate LangChain model
            llm = self.langchain_models.get(provider)
            if not llm:
                raise ValueError(f"No LangChain model available for provider: {provider}")
            print(f"[DEBUG] LangChain model instance: {llm}")
            
            # Build the prompt
            prompt = self._build_prompt(user_message, conversation_context, agent_prompt, function_documentation)
            
            # Create messages for LangChain
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=user_message)
            ]
            print(f"[DEBUG] Messages sent to model: {messages}")
            
            # Make API call using LangChain
            response = await llm.ainvoke(messages)
            
            # Extract response content
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract usage information if available
            usage = self._extract_usage(response, model_config)
            
            return {
                'text': response_text,
                'usage': usage,
                'model': model_type.value,
                'provider': provider
            }
            
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            # Simple fallback response
            return {
                'text': "I'm experiencing some technical difficulties right now. Let me help you with basic tire information. What's your vehicle's make, model, and year?",
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
                'model': 'fallback',
                'provider': 'fallback'
            }
    
    def _extract_usage(self, response, model_config: Dict[str, Any]) -> Dict[str, int]:
        """Extract usage information from LangChain response"""
        try:
            # Try to extract usage from response metadata
            if hasattr(response, 'response_metadata') and response.response_metadata:
                usage = response.response_metadata.get('usage', {})
                return {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
        except Exception as e:
            logger.debug(f"Could not extract usage info: {e}")
        
        # Fallback usage info
        return {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }
    
    def _build_prompt(self, user_message: str, conversation_context: Dict[str, Any], 
                     agent_prompt: str, function_documentation: Optional[str] = None) -> str:
        """Build prompt based on context and format requirements"""
        
        # Use the agent prompt (no fallback to old system prompt)
        system_prompt = agent_prompt
        
        # Add function documentation if provided
        if function_documentation:
            system_prompt += f"\n\n**FUNCTION DOCUMENTATION:**\n{function_documentation}"
            logger.debug(f"Added function documentation to prompt")
        
        # Add conversation context
        context_info = self._format_conversation_context(conversation_context)
        
        # Build the full prompt
        prompt = f"{system_prompt}\n\n{context_info}"
        
        logger.debug(f"Built prompt length: {len(prompt)} characters")
        logger.debug(f"Prompt ends with: {prompt[-200:]}...")
        
        return prompt
    
    def _format_conversation_context(self, conversation_context: Dict[str, Any]) -> str:
        """Format conversation context for the AI"""
        # The context is already formatted in the tire agent's prompt
        # This method is kept for compatibility but simplified
        return ""
    
 