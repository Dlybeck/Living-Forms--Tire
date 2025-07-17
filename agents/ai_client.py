import os
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from agents.cost_manager import ModelType
import aiohttp
import json

logger = logging.getLogger(__name__)

class AIClient:
    """
    Handles communication with AI models (Claude, GPT, etc.)
    Manages API calls, token counting, and cost tracking
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
        
        # Model mappings
        self.model_mappings = {
            ModelType.CLAUDE_3_7: {
                'provider': 'anthropic',
                'model_name': 'claude-3-7-sonnet-20240229',  # Updated for July 2025
                'max_tokens': 4096
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'provider': 'anthropic', 
                'model_name': 'claude-3-5-sonnet-20241022',
                'max_tokens': 4096
            },
            ModelType.GPT_4O: {
                'provider': 'openai',
                'model_name': 'gpt-4o',
                'max_tokens': 4096
            },
            ModelType.GPT_3_5_TURBO: {
                'provider': 'openai',
                'model_name': 'gpt-3.5-turbo',
                'max_tokens': 4096
            }
        }
        
        logger.info("AI Client initialized with available models")
    
    async def generate_response(self, user_message: str, conversation_context: Dict[str, Any], 
                              model_type: ModelType, response_format: str = "text") -> Dict[str, Any]:
        """
        Generate AI response using specified model
        """
        try:
            # Build the prompt based on context and format
            prompt = self._build_prompt(user_message, conversation_context, response_format)
            
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
            raise
    
    def _build_prompt(self, user_message: str, conversation_context: Dict[str, Any], response_format: str) -> str:
        """Build prompt based on context and format requirements"""
        
        # Get context information
        current_step = conversation_context.get('current_step', 'greeting')
        user_knowledge_level = conversation_context.get('user_knowledge_level', 'intermediate')
        vehicle_info = conversation_context.get('vehicle_info', {})
        tire_specs = conversation_context.get('tire_specs', {})
        driving_patterns = conversation_context.get('driving_patterns', {})
        budget_preferences = conversation_context.get('budget_preferences', {})
        current_tire_status = conversation_context.get('current_tire_status', {})
        special_considerations = conversation_context.get('special_considerations', {})
        
        # Calculate missing information
        missing_vehicle_info = []
        required_vehicle_fields = ['make', 'model', 'year']
        for field in required_vehicle_fields:
            if not vehicle_info.get(field):
                missing_vehicle_info.append(field)
        
        missing_tire_specs = []
        if not tire_specs.get('quantity_needed'):
            missing_tire_specs.append('quantity_needed')
        
        # Import the system prompt from the prompts module
        from prompts import SYSTEM_PROMPT
        
        # Build the full prompt with context
        system_prompt = SYSTEM_PROMPT + f"""
        
        Current conversation context:
        - Conversation step: {current_step}
        - User knowledge level: {user_knowledge_level}
        - Vehicle info: {vehicle_info}
        - Tire specs: {tire_specs}
        - Driving patterns: {driving_patterns}
        - Budget preferences: {budget_preferences}
        - Current tire status: {current_tire_status}
        - Special considerations: {special_considerations}
        - Missing vehicle info: {missing_vehicle_info}
        - Missing tire specs: {missing_tire_specs}
        - User's actual input: {user_message}
        - Researched information: {conversation_context.get('researched_info', {})}
        """
        
        # Build the full prompt
        full_prompt = f"{system_prompt}\n\nUser message: {user_message}\n\nResponse:"
        
        return full_prompt
    
    async def _call_openai_api(self, prompt: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call to OpenAI"""
        if not self.api_keys['openai']:
            raise ValueError("OpenAI API key not configured")
        
        headers = {
            'Authorization': f'Bearer {self.api_keys["openai"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model_config['model_name'],
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': model_config['max_tokens'],
            'temperature': 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_urls['openai'], headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                return {
                    'text': result['choices'][0]['message']['content'],
                    'usage': {
                        'prompt_tokens': result['usage']['prompt_tokens'],
                        'completion_tokens': result['usage']['completion_tokens'],
                        'total_tokens': result['usage']['total_tokens']
                    }
                }
    
    async def _call_anthropic_api(self, prompt: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call to Anthropic"""
        if not self.api_keys['anthropic']:
            raise ValueError("Anthropic API key not configured")
        
        headers = {
            'x-api-key': self.api_keys['anthropic'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': model_config['model_name'],
            'max_tokens': model_config['max_tokens'],
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_urls['anthropic'], headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                return {
                    'text': result['content'][0]['text'],
                    'usage': {
                        'prompt_tokens': result['usage']['input_tokens'],
                        'completion_tokens': result['usage']['output_tokens'],
                        'total_tokens': result['usage']['input_tokens'] + result['usage']['output_tokens']
                    }
                }
    
    def _calculate_cost(self, usage: Dict[str, int], model_type: ModelType) -> float:
        """Calculate cost based on token usage"""
        # Cost per 1K tokens (July 2025 pricing)
        pricing = {
            ModelType.CLAUDE_3_7: {'input': 0.015, 'output': 0.075},
            ModelType.CLAUDE_3_5_SONNET: {'input': 0.003, 'output': 0.015},
            ModelType.GPT_4O: {'input': 0.005, 'output': 0.015},
            ModelType.GPT_3_5_TURBO: {'input': 0.001, 'output': 0.002}
        }
        
        if model_type not in pricing:
            return 0.0
        
        prices = pricing[model_type]
        input_cost = (usage['prompt_tokens'] / 1000) * prices['input']
        output_cost = (usage['completion_tokens'] / 1000) * prices['output']
        
        return input_cost + output_cost
    
 