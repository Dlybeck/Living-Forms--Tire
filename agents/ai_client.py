import os
import logging
import asyncio
from typing import Dict, Optional, Any
from agents.cost_manager import ModelType
import aiohttp

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
            # Claude models
            ModelType.CLAUDE_SONNET_4: {
                'provider': 'anthropic',
                'model_name': 'claude-sonnet-4-20250514',
                'max_tokens': 4096
            },
            ModelType.CLAUDE_3_7: {
                'provider': 'anthropic',
                'model_name': 'claude-3-7-sonnet-20250219',
                'max_tokens': 4096
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'provider': 'anthropic', 
                'model_name': 'claude-3-5-sonnet-latest',
                'max_tokens': 4096
            },
            
            # GPT models (primary choices)
            ModelType.GPT_4O: {
                'provider': 'openai',
                'model_name': 'gpt-4o',
                'max_tokens': 4096
            },
            ModelType.GPT_4O_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'max_tokens': 4096
            },
            ModelType.GPT_4O_MINI_SEARCH: {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini-search-preview',
                'max_tokens': 4096
            },
            ModelType.GPT_4O_SEARCH: {
                'provider': 'openai',
                'model_name': 'gpt-4o-search-preview',
                'max_tokens': 4096
            },
            ModelType.GPT_4_1_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4.1-mini',
                'max_tokens': 4096
            },
            ModelType.GPT_4_1_NANO: {
                'provider': 'openai',
                'model_name': 'gpt-4.1-nano',
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
                              model_type: ModelType, response_format: str = "text", function_documentation: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AI response using specified model
        """
        try:
            # Build the prompt based on context and format
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
            # Try fallback to a working model if the primary model fails
            if "404" in str(e) or "not_found" in str(e).lower() or "529" in str(e) or "overloaded" in str(e).lower():
                logger.info("🚨 PRIMARY MODEL FAILED - trying cost-effective GPT fallbacks")
                
                # Try GPT-4o-mini first (excellent value)
                try:
                    logger.info("🔄 FALLBACK 1: Trying GPT-4o-mini")
                    fallback_config = self.model_mappings[ModelType.GPT_4O_MINI]
                    response = await self._call_openai_api(prompt, fallback_config)
                    cost = self._calculate_cost(response['usage'], ModelType.GPT_4O_MINI)
                    
                    return {
                        'text': response['text'],
                        'cost': cost,
                        'usage': response['usage'],
                        'model': ModelType.GPT_4O_MINI.value,
                        'provider': fallback_config['provider']
                    }
                except Exception as fallback1_error:
                    logger.error(f"🚨 GPT-4o-mini FALLBACK FAILED: {str(fallback1_error)}")
                    
                    # Try GPT-4.1-nano (ultra-cheap)
                    try:
                        logger.info("🔄 FALLBACK 2: Trying GPT-4.1-nano")
                        fallback_config = self.model_mappings[ModelType.GPT_4_1_NANO]
                        response = await self._call_openai_api(prompt, fallback_config)
                        cost = self._calculate_cost(response['usage'], ModelType.GPT_4_1_NANO)
                        
                        return {
                            'text': response['text'],
                            'cost': cost,
                            'usage': response['usage'],
                            'model': ModelType.GPT_4_1_NANO.value,
                            'provider': fallback_config['provider']
                        }
                    except Exception as fallback2_error:
                        logger.error(f"🚨 GPT-4.1-nano FALLBACK FAILED: {str(fallback2_error)}")
                        
                        # Try GPT-4o-mini-search as web search fallback (cheaper than Claude!)
                        try:
                            logger.info("🆘 WEB SEARCH FALLBACK: Trying GPT-4o-mini-search")
                            search_config = self.model_mappings[ModelType.GPT_4O_MINI_SEARCH]
                            response = await self._call_openai_api(prompt, search_config)
                            cost = self._calculate_cost(response['usage'], ModelType.GPT_4O_MINI_SEARCH)
                            
                            return {
                                'text': response['text'],
                                'cost': cost,
                                'usage': response['usage'],
                                'model': ModelType.GPT_4O_MINI_SEARCH.value,
                                'provider': search_config['provider']
                            }
                        except Exception as search_error:
                            logger.error(f"GPT web search fallback also failed: {str(search_error)}")
                            
                            # Try Claude 3.5 Sonnet as absolute last resort
                            try:
                                logger.info("🆘 EMERGENCY FALLBACK: Trying Claude 3.5 Sonnet")
                                claude_config = self.model_mappings[ModelType.CLAUDE_3_5_SONNET]
                                response = await self._call_anthropic_api(prompt, claude_config)
                                cost = self._calculate_cost(response['usage'], ModelType.CLAUDE_3_5_SONNET)
                                
                                return {
                                    'text': response['text'],
                                    'cost': cost,
                                    'usage': response['usage'],
                                    'model': ModelType.CLAUDE_3_5_SONNET.value,
                                    'provider': claude_config['provider']
                                }
                            except Exception as claude_error:
                                logger.error(f"Claude fallback also failed: {str(claude_error)}")
                                # If even Claude fails, return a basic response
                                return {
                                    'text': "I'm experiencing some technical difficulties right now. Let me help you with basic tire information. What's your vehicle's make, model, and year?",
                                    'cost': 0.0,
                                    'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
                                    'model': 'fallback_rules',
                                    'provider': 'fallback'
                                }
            raise
    
    def _build_prompt(self, user_message: str, conversation_context: Dict[str, Any], response_format: str, function_documentation: Optional[str] = None) -> str:
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
        
        # Add function documentation if provided
        function_instructions = ""
        if function_documentation and response_format == "function_calls":
            function_instructions = f"""
            
            FORM BUILDING FUNCTIONS:
            {function_documentation}
            
            IMPORTANT: When you need to collect information from the user, use the function calls above.
            Format: [FUNCTION_CALL] function_name(name="field_name", label="User-friendly label", required=True)
            
            Examples:
            - [FUNCTION_CALL] create_text_field(name="vehicle_make", label="What is your vehicle's make?", required=True)
            - [FUNCTION_CALL] create_select_field(name="driving_style", label="How would you describe your driving style?", options=["Conservative", "Moderate", "Aggressive"], required=True)
            - [FUNCTION_CALL] create_budget_range_field(name="budget", label="What's your budget range for tires?", required=True)
            
            Only use function calls when you need to collect specific information. For general conversation, just respond normally.
            """
        
        # Build the full prompt with context
        system_prompt = SYSTEM_PROMPT + function_instructions + f"""
        
        **CRITICAL MEMORY CONTEXT - READ CAREFULLY:**
        
        CURRENT CONVERSATION CONTEXT:
        - Conversation step: {current_step}
        - User knowledge level: {user_knowledge_level}
        
        **INFORMATION ALREADY COLLECTED (DO NOT ASK FOR THIS AGAIN):**
        
        VEHICLE INFORMATION:
        {vehicle_info if vehicle_info else "No vehicle information collected yet"}
        
        TIRE SPECIFICATIONS:
        {tire_specs if tire_specs else "No tire specifications collected yet"}
        
        DRIVING PATTERNS:
        {driving_patterns if driving_patterns else "No driving patterns collected yet"}
        
        BUDGET PREFERENCES:
        {budget_preferences if budget_preferences else "No budget preferences collected yet"}
        
        CURRENT TIRE STATUS:
        {current_tire_status if current_tire_status else "No current tire status collected yet"}
        
        SPECIAL CONSIDERATIONS:
        {special_considerations if special_considerations else "No special considerations collected yet"}
        
        **MISSING INFORMATION (ONLY ASK FOR THIS):**
        - Missing vehicle info: {missing_vehicle_info}
        - Missing tire specs: {missing_tire_specs}
        
        **CONVERSATION HISTORY SUMMARY:**
        - Total interactions: {conversation_context.get('conversation_length', 0)}
        - Ready for recommendations: {conversation_context.get('ready_for_recommendations', False)}
        
        **RESEARCHED INFORMATION:**
        {conversation_context.get('researched_info', {})}
        
        **USER'S LATEST MESSAGE:**
        {user_message}
        
        **IMPORTANT: Always acknowledge what you already know before asking for new information. If the user has already provided vehicle details, acknowledge them and move to the next step.**
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
        
        # Enable web search for search-enabled models
        search_models = [
            'gpt-4o-mini-search-preview',
            'gpt-4o-search-preview'
        ]
        if model_config['model_name'] in search_models:
            data['tools'] = [
                {
                    "type": "web_search"
                }
            ]
            logger.info(f"🔍 Enabling web search for {model_config['model_name']}")
        
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
        """Make API call to Anthropic with retry logic"""
        if not self.api_keys['anthropic']:
            raise ValueError("Anthropic API key not configured")
        
        headers = {
            'x-api-key': self.api_keys['anthropic'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        # Base data structure
        data = {
            'model': model_config['model_name'],
            'max_tokens': model_config['max_tokens'],
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7
        }
        
        # Add web search capability for Claude models that support it
        web_search_models = [
            'claude-3-7-sonnet-20250219', 
            'claude-sonnet-4-20250514'
        ]
        if model_config['model_name'] in web_search_models:
            data['tools'] = [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 3  # Limit searches to control costs
                }
            ]
        
        # Retry logic for overloaded errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.base_urls['anthropic'], headers=headers, json=data) as response:
                        if response.status == 529:  # Overloaded
                            if attempt < max_retries - 1:
                                wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                                logger.warning(f"Anthropic API overloaded, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                error_text = await response.text()
                                raise Exception(f"Anthropic API error: {response.status} - {error_text}")
                        
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
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                if "529" in str(e) or "overloaded" in str(e).lower():
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Retry attempt {attempt + 1} failed, waiting {wait_time}s before next attempt")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
        
        # This should never be reached, but just in case
        raise Exception("Unexpected error in API call")
    
    def _calculate_cost(self, usage: Dict[str, int], model_type: ModelType) -> float:
        """Calculate cost based on token usage"""
        # Cost per 1K tokens (updated 2025 pricing)
        pricing = {
            ModelType.CLAUDE_SONNET_4: {'input': 0.003, 'output': 0.015},
            ModelType.CLAUDE_3_7: {'input': 0.003, 'output': 0.015},
            ModelType.CLAUDE_3_5_SONNET: {'input': 0.003, 'output': 0.015},
            ModelType.GPT_4O: {'input': 0.0025, 'output': 0.00125},
            ModelType.GPT_4O_MINI: {'input': 0.00015, 'output': 0.000075},
            ModelType.GPT_4O_MINI_SEARCH: {'input': 0.00015, 'output': 0.00015},
            ModelType.GPT_4O_SEARCH: {'input': 0.0025, 'output': 0.0025},
            ModelType.GPT_4_1_MINI: {'input': 0.0004, 'output': 0.0001},
            ModelType.GPT_4_1_NANO: {'input': 0.0001, 'output': 0.000025},
            ModelType.GPT_3_5_TURBO: {'input': 0.001, 'output': 0.002}
        }
        
        if model_type not in pricing:
            return 0.0
        
        prices = pricing[model_type]
        input_cost = (usage['prompt_tokens'] / 1000) * prices['input']
        output_cost = (usage['completion_tokens'] / 1000) * prices['output']
        
        return input_cost + output_cost
    
 