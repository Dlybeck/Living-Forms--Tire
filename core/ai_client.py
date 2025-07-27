import os
import logging

from typing import Dict, Optional, Any
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Simple model type enum"""
    O4_MINI = "o4-mini"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet"

class AIClient:
    """
    AI client for the Living Form Tire Sales Assistant
    Handles communication with AI models
    """
    
    def __init__(self):
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
        
        self.base_urls = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'anthropic': 'https://api.anthropic.com/v1/messages'
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
        
        logger.debug("AI Client initialized with core model set")
    
    async def generate_response(self, user_message: str, conversation_context: Dict[str, Any], 
                              model_type: ModelType, agent_prompt: str, 
                              function_documentation: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AI response using specified model
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(user_message, conversation_context, agent_prompt, function_documentation)
            
            # Get model configuration
            model_config = self.model_mappings[model_type]
            
            # Make API call using unified method
            response = await self._call_api(prompt, model_config, model_config['provider'])
            
            return {
                'text': response['text'],
                'usage': response['usage'],
                'model': model_type.value,
                'provider': model_config['provider']
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
        prompt = f"{system_prompt}\n\n{context_info}\n\nUser: {user_message}\n\nAssistant:"
        
        logger.debug(f"Built prompt length: {len(prompt)} characters")
        logger.debug(f"Prompt ends with: {prompt[-200:]}...")
        
        return prompt
    
    def _format_conversation_context(self, conversation_context: Dict[str, Any]) -> str:
        """Format conversation context for the AI"""
        # The context is already formatted in the tire agent's prompt
        # This method is kept for compatibility but simplified
        return ""
    
    async def _call_api(self, prompt: str, model_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Call API for the specified provider"""
        
        if provider == 'openai':
            headers = {
                'Authorization': f'Bearer {self.api_keys["openai"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model_config['model_name'],
                'messages': [
                    {'role': 'system', 'content': prompt}
                ]
            }
            
            # Handle different token parameter names for different models
            if 'max_completion_tokens' in model_config:
                data['max_completion_tokens'] = model_config['max_completion_tokens']
            else:
                data['max_tokens'] = model_config['max_tokens']
            
            # Only add temperature for models that support it (not O4-mini)
            if not model_config['model_name'].startswith('o4-'):
                data['temperature'] = 0.7
                
        elif provider == 'anthropic':
            headers = {
                'x-api-key': self.api_keys['anthropic'],
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': model_config['model_name'],
                'max_tokens': model_config['max_tokens'],
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Make the API call
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_urls[provider], headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract response based on provider
                    if provider == 'openai':
                        return {
                            'text': result['choices'][0]['message']['content'],
                            'usage': result['usage']
                        }
                    else:  # anthropic
                        return {
                            'text': result['content'][0]['text'],
                            'usage': result.get('usage', {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0})
                        }
                else:
                    error_text = await response.text()
                    raise Exception(f"{provider.title()} API error: {response.status} - {error_text}")
    
 