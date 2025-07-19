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
            logger.info(f"Added function documentation to prompt: {function_documentation[:200]}...")
        
        # Add conversation context
        context_info = self._format_conversation_context(conversation_context)
        
        # Build the full prompt
        prompt = f"{system_prompt}\n\n{context_info}\n\nUser: {user_message}\n\nAssistant:"
        
        logger.info(f"Built prompt length: {len(prompt)} characters")
        logger.info(f"Prompt ends with: {prompt[-200:]}...")
        
        return prompt
    
    def _format_conversation_context(self, conversation_context: Dict[str, Any]) -> str:
        """Format conversation context for the AI"""
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
        
        # Add user selected method if available (CRITICAL for initial form handling)
        if 'user_selected_method' in conversation_context:
            method = conversation_context['user_selected_method']
            context_parts.append(f"User Selected Method: {method}")
            context_parts.append("Form Submission: True")
            
            # Add specific context based on method
            if method == 'not_sure':
                context_parts.append("User needs help figuring out vehicle information")
                context_parts.append("Guidance required: User is unsure how to find tire/vehicle info")
        
        # Check if proximity has been answered (regardless of method)
        if conversation_context.get('proximity_answered'):
            proximity = conversation_context.get('user_proximity', 'unknown')
            context_parts.append(f"User has answered proximity question: {proximity}")
            if proximity == 'yes':
                context_parts.append("User is near their vehicle - should ask where to check")
            elif proximity == 'no':
                context_parts.append("User is not near their vehicle - should ask about documents")
        
        # Add method-specific context if method is available
        if 'user_selected_method' in conversation_context:
            method = conversation_context['user_selected_method']
            if method == 'tire_size':
                if conversation_context.get('provided_tire_size'):
                    context_parts.append(f"User provided tire size: {conversation_context['provided_tire_size']}")
                else:
                    context_parts.append("User selected tire size method but needs to provide the size")
            elif method == 'make_model_year':
                if conversation_context.get('provided_vehicle_info'):
                    context_parts.append(f"User provided vehicle info: {conversation_context['provided_vehicle_info']}")
                else:
                    context_parts.append("User selected vehicle method but needs to provide details")
            elif method == 'vin':
                if conversation_context.get('provided_vin'):
                    context_parts.append(f"User provided VIN: {conversation_context['provided_vin']}")
                else:
                    context_parts.append("User selected VIN method but needs to provide the VIN")
        
        # Add driving info context
        if conversation_context.get('location_provided'):
            context_parts.append(f"User location: {conversation_context.get('user_location', 'unknown')}")
        if conversation_context.get('mileage_provided'):
            context_parts.append(f"Total mileage: {conversation_context.get('total_mileage', 'unknown')}")
            if conversation_context.get('calculated_annual_mileage'):
                context_parts.append(f"Calculated annual mileage: {conversation_context['calculated_annual_mileage']}")
        if conversation_context.get('environment_provided'):
            context_parts.append(f"Driving environment: {conversation_context.get('driving_environment', 'unknown')}")
        if conversation_context.get('weather_provided'):
            context_parts.append(f"Weather conditions: {conversation_context.get('weather_conditions', 'unknown')}")
        if conversation_context.get('style_provided'):
            context_parts.append(f"Driving style: {conversation_context.get('driving_style', 'unknown')}")
        if conversation_context.get('usage_provided'):
            context_parts.append(f"Vehicle usage: {conversation_context.get('vehicle_usage', 'unknown')}")
        if conversation_context.get('plans_provided'):
            context_parts.append(f"Ownership plans: {conversation_context.get('ownership_plans', 'unknown')}")
        
        # Add preferences context
        if conversation_context.get('budget_provided'):
            context_parts.append(f"Budget range: {conversation_context.get('budget_range', 'unknown')}")
        if conversation_context.get('category_provided'):
            context_parts.append(f"Budget category: {conversation_context.get('budget_category', 'unknown')}")
        if conversation_context.get('priorities_provided'):
            context_parts.append(f"Performance priorities: {conversation_context.get('performance_priorities', 'unknown')}")
        if conversation_context.get('tire_type_provided'):
            context_parts.append(f"Tire type preference: {conversation_context.get('tire_type_preference', 'unknown')}")
        if conversation_context.get('brands_provided'):
            context_parts.append(f"Brand preferences: {conversation_context.get('brand_preferences', 'unknown')}")
        if conversation_context.get('run_flat_provided'):
            context_parts.append(f"Run-flat preference: {conversation_context.get('run_flat_preference', 'unknown')}")
        if conversation_context.get('considerations_provided'):
            context_parts.append(f"Special considerations: {conversation_context.get('special_considerations', 'unknown')}")
        if conversation_context.get('installation_provided'):
            context_parts.append(f"Installation preferences: {conversation_context.get('installation_preferences', 'unknown')}")
        
        if 'form_submission' in conversation_context:
            context_parts.append("Form Submission: True")
        
        # Add conversation history if available
        if 'conversation_history' in conversation_context and conversation_context['conversation_history']:
            history = conversation_context['conversation_history']
            context_parts.append("Conversation History:")
            
            # Look for key events in recent history
            recent_events = history[-10:]  # Include last 10 events to avoid token limits
            
            # Check for method selection
            method_selected = None
            for event in recent_events:
                if event.get('type') == 'method_selected':
                    method_selected = event.get('data', {}).get('method')
                    break
                elif event.get('type') == 'form_submission':
                    form_data = event.get('form_data', {})
                    if 'info_method' in form_data:
                        method_selected = form_data['info_method']
                        break
            
            if method_selected:
                context_parts.append(f"  - User selected method: {method_selected}")
                
                # Add context based on method
                if method_selected == 'not_sure':
                    context_parts.append("  - User needs help finding vehicle information")
                    
                    # Check if they've already answered proximity question
                    for event in recent_events:
                        if event.get('type') == 'form_submission':
                            form_data = event.get('form_data', {})
                            # Check for both possible field names
                            if 'proximity' in form_data:
                                proximity = form_data['proximity']
                                context_parts.append(f"  - User is {proximity} their vehicle")
                                break
                            elif 'near_vehicle' in form_data:
                                proximity = form_data['near_vehicle']
                                context_parts.append(f"  - User is {proximity} their vehicle")
                                break
            
            # Show recent form submissions
            for event in recent_events:
                event_type = event.get('type', 'unknown')
                timestamp = event.get('timestamp', 'unknown')
                
                if event_type == 'form_submission':
                    form_data = event.get('form_data', {})
                    if form_data:
                        # Show what the user answered in the form
                        answers = []
                        for field, value in form_data.items():
                            if field not in ['additional_notes', 'info_method']:  # Skip auto-added fields
                                answers.append(f"{field}: {value}")
                        if answers:
                            context_parts.append(f"  - {timestamp}: User answered: {', '.join(answers)}")
                            
                        # Special handling for proximity answers
                        if 'near_vehicle' in form_data:
                            proximity = form_data['near_vehicle']
                            context_parts.append(f"  - User proximity answer: {proximity}")
                elif event_type == 'user_message':
                    message = event.get('message', '')
                    if message and len(message) < 100:  # Only show short messages
                        context_parts.append(f"  - {timestamp}: User said: {message}")
        
        # Add conversation summary if available
        if 'conversation_summary' in conversation_context:
            summary = conversation_context['conversation_summary']
            if isinstance(summary, str):
                context_parts.append(f"Conversation Summary: {summary}")
            elif isinstance(summary, dict):
                context_parts.append(f"Conversation Summary: {summary.get('current_goal', 'Unknown goal')}")
                if summary.get('completed_goals'):
                    context_parts.append(f"Completed Steps: {', '.join(summary['completed_goals'])}")
                if summary.get('missing_data'):
                    context_parts.append(f"Missing Data: {', '.join(summary['missing_data'])}")
        
        # Add notepad information if available
        if 'notepad_summary' in conversation_context:
            context_parts.append(f"AI Notepad:\n{conversation_context['notepad_summary']}")
        
        formatted_context = "Context:\n" + "\n".join(f"- {part}" for part in context_parts) if context_parts else ""
        logger.info(f"Formatted context: {formatted_context}")
        
        return formatted_context
    
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
            ModelType.O4_MINI: 0.001375,     # $1.375 per 1K tokens (input + output average)
            ModelType.GPT_4_1: 0.0025,       # $2.50 per 1K tokens (input + output average)
            ModelType.GPT_4O_MINI: 0.00015,  # $0.15 per 1K tokens
            ModelType.GPT_4_1_MINI: 0.00015,  # $0.15 per 1K tokens
            ModelType.CLAUDE_3_5_SONNET: 0.0003,  # $0.30 per 1K tokens
        }
        
        cost_per_1k = costs.get(model_type, 0.00015)
        total_tokens = prompt_tokens + completion_tokens
        
        return (total_tokens / 1000) * cost_per_1k
    
 