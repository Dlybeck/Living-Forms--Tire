import os
import logging
import asyncio
from typing import Dict, Optional, Any
from agents.cost_manager import ModelType
import aiohttp

logger = logging.getLogger(__name__)

class AIClient:
    """
    Simplified AI client for the Living Form Tire Sales Assistant
    Handles communication with AI models with minimal complexity
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
        
        # Simplified model mappings - only the models we actually use
        self.model_mappings = {
            ModelType.GPT_4O_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'max_tokens': 4096,
                'web_search': True
            },
            ModelType.GPT_4_1_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4.1-mini',
                'max_tokens': 4096
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'provider': 'anthropic', 
                'model_name': 'claude-3-5-sonnet-latest',
                'max_tokens': 4096
            }
        }
        
        logger.info("AI Client initialized with simplified model set")
    
    async def generate_response(self, user_message: str, conversation_context: Dict[str, Any], 
                              model_type: ModelType, response_format: str = "text", 
                              function_documentation: Optional[str] = None, 
                              needs_web_search: bool = False) -> Dict[str, Any]:
        """
        Generate AI response using specified model
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(user_message, conversation_context, response_format, function_documentation)
            
            # Get model configuration
            model_config = self.model_mappings[model_type]
            
            # Make API call based on provider
            if model_config['provider'] == 'openai':
                response = await self._call_openai_api(prompt, model_config)
            elif model_config['provider'] == 'anthropic':
                response = await self._call_anthropic_api(prompt, model_config)
            else:
                raise ValueError(f"Unsupported provider: {model_config['provider']}")
            
            # Calculate cost
            cost = self._calculate_cost(response['usage'], model_type)
            
            return {
                'text': response['text'],
                'cost': cost,
                'usage': response['usage'],
                'model': model_type.value,
                'provider': model_config['provider']
            }
            
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            # Simple fallback response
            return {
                'text': "I'm experiencing some technical difficulties right now. Let me help you with basic tire information. What's your vehicle's make, model, and year?",
                'cost': 0.0,
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
                'model': 'fallback',
                'provider': 'fallback'
            }
    
    def _build_prompt(self, user_message: str, conversation_context: Dict[str, Any], 
                     response_format: str, function_documentation: Optional[str] = None) -> str:
        """Build prompt based on context and format requirements"""
        
        # Get the system prompt
        from prompts import get_main_system_prompt
        system_prompt = get_main_system_prompt()
        
        # Add function documentation if provided
        if function_documentation:
            system_prompt += f"\n\n**FUNCTION DOCUMENTATION:**\n{function_documentation}"
        
        # Add conversation context
        context_info = self._format_conversation_context(conversation_context)
        
        # Build the full prompt
        prompt = f"{system_prompt}\n\n{context_info}\n\nUser: {user_message}\n\nAssistant:"
        
        return prompt
    
    def _format_conversation_context(self, conversation_context: Dict[str, Any]) -> str:
        """Format conversation context for the AI"""
        context_parts = []
        
        # Add current goal if available
        if 'current_goal' in conversation_context:
            context_parts.append(f"Current Goal: {conversation_context['current_goal']}")
        
        # Add current step if available
        if 'current_step' in conversation_context:
            context_parts.append(f"Current Step: {conversation_context['current_step']}")
        
        # Add form purpose if available
        if 'form_purpose' in conversation_context:
            context_parts.append(f"Form Purpose: {conversation_context['form_purpose']}")
        
        if context_parts:
            return "Context:\n" + "\n".join(f"- {part}" for part in context_parts)
        
        return ""
    
    async def _call_openai_api(self, prompt: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.api_keys["openai"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model_config['model_name'],
            'messages': [
                {'role': 'system', 'content': prompt}
            ],
            'max_tokens': model_config['max_tokens'],
            'temperature': 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_urls['openai'], headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'text': result['choices'][0]['message']['content'],
                        'usage': result['usage']
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
    
    async def _call_anthropic_api(self, prompt: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Call Anthropic API"""
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_urls['anthropic'], headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'text': result['content'][0]['text'],
                        'usage': result.get('usage', {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")
    
    def _calculate_cost(self, usage: Dict[str, int], model_type: ModelType) -> float:
        """Calculate cost based on token usage and model"""
        # Simplified cost calculation
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        # Rough cost estimates per 1K tokens
        costs = {
            ModelType.GPT_4O_MINI: 0.00015,  # $0.15 per 1K tokens
            ModelType.GPT_4_1_MINI: 0.00015,  # $0.15 per 1K tokens
            ModelType.CLAUDE_3_5_SONNET: 0.0003,  # $0.30 per 1K tokens
        }
        
        cost_per_1k = costs.get(model_type, 0.00015)
        total_tokens = prompt_tokens + completion_tokens
        
        return (total_tokens / 1000) * cost_per_1k
    
 