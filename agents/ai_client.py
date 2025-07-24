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
        
        # Model mappings - prioritize O4-mini for complex reasoning and detailed form generation
        self.model_mappings = {
            ModelType.O4_MINI: {
                'provider': 'openai',
                'model_name': 'o4-mini-2025-04-16',
                'max_completion_tokens': 4096,
                'web_search': True
            },
            ModelType.GPT_4_1: {
                'provider': 'openai',
                'model_name': 'gpt-4.1-2025-04-14',
                'max_tokens': 4096,
                'web_search': True
            },
            ModelType.GPT_4_1_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4.1-mini',
                'max_tokens': 4096,
                'web_search': True
            },
            ModelType.GPT_4O_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'max_tokens': 4096,
                'web_search': True
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'provider': 'anthropic', 
                'model_name': 'claude-3-5-sonnet-latest',
                'max_tokens': 4096
            }
        }
        
        logger.info("AI Client initialized with simplified model set")
    
    async def generate_response(self, user_message: str, conversation_context: Dict[str, Any], 
                              model_type: ModelType, agent_prompt: str, response_format: str = "text", 
                              function_documentation: Optional[str] = None, 
                              needs_web_search: bool = False) -> Dict[str, Any]:
        """
        Generate AI response using specified model
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(user_message, conversation_context, response_format, agent_prompt, function_documentation)
            
            # Get model configuration
            model_config = self.model_mappings[model_type]
            
            # Make API call based on provider
            if model_config['provider'] == 'openai':
                response = await self._call_openai_api(prompt, model_config, needs_web_search)
            elif model_config['provider'] == 'anthropic':
                response = await self._call_anthropic_api(prompt, model_config, needs_web_search)
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
                     response_format: str, agent_prompt: str, function_documentation: Optional[str] = None) -> str:
        """Build prompt based on context and format requirements"""
        
        # Use the agent prompt (no fallback to old system prompt)
        system_prompt = agent_prompt
        
        # Add function documentation if provided
        if function_documentation:
            system_prompt += f"\n\n**FUNCTION DOCUMENTATION:**\n{function_documentation}"
            logger.info(f"Added function documentation to prompt: {function_documentation[:200]}...")
        
        # Add conversation context
        context_info = self._format_conversation_context(conversation_context)
        
        # Build the full prompt
        prompt = f"{system_prompt}\n\n{context_info}\n\nUser: {user_message}\n\nAssistant:"
        
        logger.info(f"Built prompt length: {len(prompt)} characters")
        logger.info(f"Prompt ends with: {prompt[-200:]}...")
        print(f"\n=== PROMPT DEBUG ===")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Last 500 chars of prompt:")
        print(prompt[-500:])
        print(f"=== END PROMPT DEBUG ===\n")
        
        return prompt
    
    def _format_conversation_context(self, conversation_context: Dict[str, Any]) -> str:
        """Format conversation context for the AI - Simplified to rely on ScribeAgent's notepad"""
        context_parts = []
        
        # Debug logging
        logger.info(f"Formatting conversation context: {conversation_context}")
        
        # Add current goal if available
        if 'current_goal' in conversation_context:
            context_parts.append(f"Current Goal: {conversation_context['current_goal']}")
        
        # Add current step if available
        if 'current_step' in conversation_context:
            context_parts.append(f"Current Step: {conversation_context['current_step']}")
        
        # Add form purpose if available
        if 'form_purpose' in conversation_context:
            context_parts.append(f"Form Purpose: {conversation_context['form_purpose']}")
        
        # Add form data if present (for immediate context)
        if 'form_data' in conversation_context:
            form_data = conversation_context['form_data']
            if form_data:
                # Show what the user answered in the form
                answers = []
                for field, value in form_data.items():
                    if field not in ['additional_notes', 'info_method']:  # Skip auto-added fields
                        answers.append(f"{field}: {value}")
                if answers:
                    context_parts.append(f"Form Data: {', '.join(answers)}")
        
        # Add notepad information if available (prefer enhanced Control Headquarters scene)
        if 'enhanced_notepad' in conversation_context:
            context_parts.append(f"AI Notepad (Control Headquarters):\n{conversation_context['enhanced_notepad']}")
        elif 'notepad_summary' in conversation_context:
            context_parts.append(f"AI Notepad:\n{conversation_context['notepad_summary']}")
        
        formatted_context = "Context:\n" + "\n".join(f"- {part}" for part in context_parts) if context_parts else ""
        logger.info(f"Formatted context: {formatted_context}")
        
        return formatted_context
    
    async def _call_openai_api(self, prompt: str, model_config: Dict[str, Any], needs_web_search: bool) -> Dict[str, Any]:
        """Call OpenAI API"""
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
        
        # Add web search tools if needed and supported
        if needs_web_search and model_config.get('web_search', False):
            data['tools'] = [
                {
                    "type": "web_search"
                }
            ]
            data['tool_choice'] = "auto"
            logger.info("Added web search tools to OpenAI API call")
        
        # Handle different token parameter names for different models
        if 'max_completion_tokens' in model_config:
            data['max_completion_tokens'] = model_config['max_completion_tokens']
        else:
            data['max_tokens'] = model_config['max_tokens']
        
        # Only add temperature for models that support it (not O4-mini)
        if not model_config['model_name'].startswith('o4-'):
            data['temperature'] = 0.7
        
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
    
    async def _call_anthropic_api(self, prompt: str, model_config: Dict[str, Any], needs_web_search: bool) -> Dict[str, Any]:
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
            ModelType.O4_MINI: 0.001375,     # $1.375 per 1K tokens (input + output average)
            ModelType.GPT_4_1: 0.0025,       # $2.50 per 1K tokens (input + output average)
            ModelType.GPT_4O_MINI: 0.00015,  # $0.15 per 1K tokens
            ModelType.GPT_4_1_MINI: 0.00015,  # $0.15 per 1K tokens
            ModelType.CLAUDE_3_5_SONNET: 0.0003,  # $0.30 per 1K tokens
        }
        
        cost_per_1k = costs.get(model_type, 0.00015)
        total_tokens = prompt_tokens + completion_tokens
        
        return (total_tokens / 1000) * cost_per_1k
    
 