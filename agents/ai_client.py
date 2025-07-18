import os
import logging
import asyncio
from typing import Dict, Optional, Any
from agents.cost_manager import ModelType
# Web search is handled by AI models directly
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
            
            # GPT models (primary choices with built-in web search)
            ModelType.GPT_4O: {
                'provider': 'openai',
                'model_name': 'gpt-4o',
                'max_tokens': 4096,
                'web_search': True  # Built-in web search capability
            },
            ModelType.GPT_4O_MINI: {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'max_tokens': 4096,
                'web_search': True  # Built-in web search capability
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
                              model_type: ModelType, response_format: str = "text", function_documentation: Optional[str] = None, needs_web_search: bool = False) -> Dict[str, Any]:
        """
        Generate AI response using specified model, with optional web search
        """
        try:
            # Web search is handled by the AI models themselves (GPT-4o, Claude)
            # We don't need to perform external web search - the models do it automatically
            
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
                    
                    # Try GPT-4.1-mini (middle-tier)
                    try:
                        logger.info("🔄 FALLBACK 2: Trying GPT-4.1-mini (middle-tier)")
                        fallback_config = self.model_mappings[ModelType.GPT_4_1_MINI]
                        response = await self._call_openai_api(prompt, fallback_config)
                        cost = self._calculate_cost(response['usage'], ModelType.GPT_4_1_MINI)
                        
                        return {
                            'text': response['text'],
                            'cost': cost,
                            'usage': response['usage'],
                            'model': ModelType.GPT_4_1_MINI.value,
                            'provider': fallback_config['provider']
                        }
                    except Exception as fallback2_error:
                        logger.error(f"🚨 GPT-4.1-mini FALLBACK FAILED: {str(fallback2_error)}")
                        
                        # Try Claude 3.5 Sonnet as web search fallback (cheaper than Claude!)
                        try:
                            logger.info("🆘 WEB SEARCH FALLBACK: Trying Claude 3.5 Sonnet")
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
        from prompts import get_main_system_prompt
        
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
        system_prompt = get_main_system_prompt() + function_instructions + f"""
        
        **CRITICAL MEMORY CONTEXT - READ CAREFULLY:**
        
        CURRENT CONVERSATION CONTEXT:
        - Conversation step: {current_step}
        - User knowledge level: {user_knowledge_level}
        
        **INFORMATION ALREADY COLLECTED (DO NOT ASK FOR THIS AGAIN):**
        
        VEHICLE INFORMATION:
        {vehicle_info if vehicle_info else "No vehicle information collected yet"}
        
        TIRE SPECIFICATIONS:
        {tire_specs if tire_specs else "No tire specifications collected yet"}
        **TIRE SIZE STATUS**: {"✅ TIRE SIZE FOUND: " + tire_specs.get('current_tire_size', 'NOT FOUND') if tire_specs.get('current_tire_size') else "❌ TIRE SIZE MISSING - SEARCH REQUIRED"}
        
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
        
        **RECENT FORM SUBMISSIONS:**
        {conversation_context.get('form_data', {}) if conversation_context.get('form_data') else "No recent form submissions"}
        
        **CONVERSATION PATTERN:**
        {self._format_conversation_history(conversation_context)}
        
        **CRITICAL - WHAT THE USER HAS ALREADY TOLD YOU:**
        {self._format_user_responses(conversation_context)}
        
        **RESEARCHED INFORMATION:**
        {conversation_context.get('researched_info', {})}
        
        **CONVERSATIONAL CONTEXT:**
        - User needs help with vehicle info: {conversation_context.get('needs_help_with_vehicle_info', False)}
        - User situation: {conversation_context.get('user_situation', {})}
        - Approaches we've tried: {conversation_context.get('attempted_approaches', [])}
        - Conversational insights: {conversation_context.get('conversational_insights', {})}
        - Suggested form approach: {conversation_context.get('suggested_form_approach', {})}
        
        **🚨 CURRENT USER CHOICE (CRITICAL):**
        - User chosen path: {conversation_context.get('conversational_insights', {}).get('user_chosen_path', 'None')}
        - Last specific response: {conversation_context.get('conversational_insights', {}).get('last_specific_response', 'None')}
        - Should build on response: {conversation_context.get('conversational_insights', {}).get('should_build_on_response', False)}
        - Form type: {conversation_context.get('suggested_form_approach', {}).get('form_type', 'unknown')}
        - Context reminder: {conversation_context.get('suggested_form_approach', {}).get('context_reminder', 'None')}
        
        **🎯 MANDATORY ACTION BASED ON USER CHOICE:**
        {self._get_mandatory_action(conversation_context)}
        
        **CRITICAL INSTRUCTIONS:**
        1. If you see "✅ TIRE SIZE FOUND" above, DO NOT search for tire size again - proceed to next step
        2. If you see "❌ TIRE SIZE MISSING" and have vehicle make/model/year, search for tire size immediately
        3. Only ask for information that is truly missing from the context above
        4. Acknowledge what you already know before asking for new information
        5. Never repeat tire size searches if you already have the tire size
        6. If user chose "info_method: not_sure", they're unsure HOW to provide vehicle info - help them understand their options
        7. ADAPT YOUR APPROACH: If user keeps asking for help (multiple interactions), provide more detailed, step-by-step guidance
        8. READ THE USER RESPONSES ABOVE - Don't ask questions they've already answered
        9. If they said "I don't know" or "None of the above" multiple times, try completely different approaches
        
        **NATURAL CONVERSATION GUIDANCE:**
        - Use the conversational insights to understand what tone and approach to take
        - Look at "next_logical_approaches" to see what makes sense to try next  
        - Use the "suggested_form_approach" to create contextually appropriate forms
        - If user seems stuck, be creative and suggest alternatives naturally
        - Don't repeat approaches from "attempted_approaches" unless you're building on them
        - Adapt your questioning style based on their situation (near car, has documents, etc.)
        - Always end with a form that makes sense given their current situation
        - Think like a helpful person who naturally pivots when something isn't working
        - Form should match the suggested "form_type" (exploratory, situational_help, preferences_gathering, etc.)
        - Use the "context_reminder" to acknowledge what you already know about their situation
        
        **🚨 CRITICAL: BUILDING ON USER RESPONSES - FOLLOW THIS OR FAIL 🚨**
        - If "should_build_on_response: True" - the user gave a specific actionable response
        - If "user_chosen_path" is set - they chose a specific method, help them with THAT method
        - If "last_specific_response" shows they said something like "I can ask a friend" - build on that specific choice
        - DON'T offer more options if they've already chosen a path - help them with their chosen path
        - When form_type is "path_assistance" - focus entirely on helping with their chosen method
        - NEVER say "in the meantime" or "while we're waiting" - this is a form-based system, not a conversation
        - If user chose a path like "ask friend", help them with that path ONLY - don't ask about other things
        
        **🔥 ABSOLUTE RULE: NO MORE GENERIC LISTS WHEN USER HAS CHOSEN A PATH 🔥**
        - If user chose "Ask a family member" - HELP THEM WITH THAT. Don't list more options.
        - If user chose "Insurance app" - HELP THEM WITH THAT. Don't list more options.
        - If user chose ANY specific path - HELP WITH THAT PATH ONLY.
        - STOP OFFERING ALTERNATIVES WHEN USER HAS ALREADY CHOSEN.
        
        **CONVERSATION PROGRESSION GUIDANCE**
        - If "conversation_progressing_well: False" - user may be stuck, try a completely different approach
        - If "has_made_progress: True" - they've provided some vehicle info, move forward with tire preferences
        - If "conversation_length" is high but no progress - be more directive and helpful
        - Always acknowledge their specific responses and build on them naturally
        - Move the conversation forward rather than repeating the same types of questions
        
        User message: {user_message}
        """
        
        # Build the full prompt
        full_prompt = f"{system_prompt}\n\nUser message: {user_message}\n\nResponse:"
        
        return full_prompt
    
    def _get_mandatory_action(self, conversation_context: Dict[str, Any]) -> str:
        """Generate mandatory action based on user's chosen path"""
        insights = conversation_context.get('conversational_insights', {})
        chosen_path = insights.get('user_chosen_path')
        should_build = insights.get('should_build_on_response', False)
        last_response = insights.get('last_specific_response', '')
        
        if should_build and chosen_path:
            if chosen_path == 'ask_friend':
                return f"""
                🔥 USER CHOSE TO ASK FAMILY MEMBER/FRIEND 🔥
                They said: "{last_response}"
                
                YOU MUST:
                1. Acknowledge their choice specifically
                2. Help them figure out what to ask their family member/friend
                3. Create a form to get their response after they talk to them
                4. DO NOT list more options or alternatives
                5. FOCUS ENTIRELY on helping with family member approach
                
                EXAMPLE RESPONSE:
                "Perfect! Let me help you with what to ask your family member. You'll want to ask them for your vehicle's make, model, and year. Here's exactly what to say..."
                """
            elif chosen_path == 'insurance_app':
                return f"""
                🔥 USER CHOSE INSURANCE APP/RECORDS 🔥
                They said: "{last_response}"
                
                YOU MUST:
                1. Help them navigate their insurance app/records
                2. Tell them exactly where to look for vehicle info
                3. Create a form for them to enter what they find
                4. DO NOT list alternatives
                """
            elif chosen_path == 'service_records':
                return f"""
                🔥 USER CHOSE SERVICE RECORDS 🔥
                They said: "{last_response}"
                
                YOU MUST:
                1. Help them find and use their service records
                2. Tell them what to look for specifically
                3. Create a form for them to enter what they find
                4. DO NOT list alternatives
                """
            else:
                return f"""
                🔥 USER CHOSE SPECIFIC PATH: {chosen_path} 🔥
                They said: "{last_response}"
                
                YOU MUST HELP WITH THIS PATH ONLY - NO MORE OPTIONS!
                """
        
        return "No specific path chosen yet - you may explore options."
    
    def _format_conversation_history(self, conversation_context: Dict[str, Any]) -> str:
        """Format conversation history to show natural conversation patterns"""
        conversation_length = conversation_context.get('conversation_length', 0)
        conversational_insights = conversation_context.get('conversational_insights', {})
        
        if conversation_length == 0:
            return "No previous interactions"
        elif conversation_length == 1:
            return "First interaction - user is starting the process"
        elif conversation_length >= 2:
            # Use conversational insights to understand the flow
            user_situation = conversational_insights.get('user_situation_summary', 'progressing normally')
            conversation_tone = conversational_insights.get('conversation_tone', 'friendly and helpful')
            attempted_approaches = conversational_insights.get('what_weve_tried', [])
            
            pattern_description = f"Multiple interactions ({conversation_length}) - User situation: {user_situation}"
            
            if attempted_approaches:
                pattern_description += f" | Approaches tried: {', '.join(attempted_approaches)}"
            
            pattern_description += f" | Suggested tone: {conversation_tone}"
            
            return pattern_description
        
        return f"Total interactions: {conversation_length}"

    def _format_user_responses(self, conversation_context: Dict[str, Any]) -> str:
        """Format user responses from conversation history to show what they've already told the AI."""
        form_data = conversation_context.get('form_data', {})
        conversation_length = conversation_context.get('conversation_length', 0)
        user_situation = conversation_context.get('user_situation', {})
        conversational_insights = conversation_context.get('conversational_insights', {})
        
        if not form_data and conversation_length == 0:
            return "No previous responses from user"
        
        user_responses = []
        
        # Add what we know about their situation
        if user_situation:
            situation_summary = conversational_insights.get('user_situation_summary', 'situation unclear')
            user_responses.append(f"User situation: {situation_summary}")
        
        # Add key form data responses (not all the noise)
        if form_data:
            important_responses = []
            for key, value in form_data.items():
                if value and str(value).strip() and key not in ['additional_notes', 'submit']:
                    important_responses.append(f"{key}: {value}")
            
            if important_responses:
                user_responses.append(f"Key responses: {', '.join(important_responses)}")
        
        # Add conversation flow summary
        if conversation_length > 0:
            user_responses.append(f"Conversation length: {conversation_length} interactions")
            
        # Add what approaches we've tried
        attempted_approaches = conversational_insights.get('what_weve_tried', [])
        if attempted_approaches:
            user_responses.append(f"Approaches tried: {', '.join(attempted_approaches)}")
        
        # Add tone guidance
        conversation_tone = conversational_insights.get('conversation_tone', 'friendly and helpful')
        user_responses.append(f"Recommended tone: {conversation_tone}")
        
        return "\n".join(user_responses) if user_responses else "No clear responses from user yet"

    # Web search is now handled by AI models directly - no external service needed
    
    # Web search augmentation is no longer needed - AI models handle this internally
    
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
        
        # Note: GPT-4o and GPT-4o-mini have built-in web search capabilities
        # They don't need explicit tools configuration - they automatically search when needed
        if model_config.get('web_search'):
            logger.info(f"🔍 Using {model_config['model_name']} with built-in web search capabilities")
        
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
    
 