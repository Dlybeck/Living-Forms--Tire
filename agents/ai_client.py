import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
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
        completion_status = conversation_context.get('completion_status', {})
        
        # Calculate what's missing for better AI guidance
        missing_vehicle_info = []
        required_vehicle_fields = ['make', 'model', 'year']
        for field in required_vehicle_fields:
            if not vehicle_info.get(field):
                missing_vehicle_info.append(field)
        
        missing_tire_specs = []
        if not tire_specs.get('quantity_needed'):
            missing_tire_specs.append('quantity_needed')
        

        
        # Base system prompt for tire sales agent - focused on collecting tire purchasing information
        system_prompt = """You are a helpful tire sales assistant using a "Living Form" approach to collect tire purchasing information. 
        Your goal is to gather all necessary information a tire seller needs to provide the best recommendations.
        
        INFORMATION TO COLLECT:
        1. Vehicle Information: Make, model, year, trim level
        2. Tire Specifications: Current size, quantity needed (1, 2, 4 tires)
        3. Driving Patterns: Daily mileage, highway vs city driving, seasonal needs
        4. Budget/Preferences: Price range, preferred brands, warranty preferences
        5. Current Tire Status: Condition, age, reason for replacement
        6. Special Considerations: Performance needs, weather conditions, towing requirements
        
        Your approach:
        - Be conversational and helpful
        - ALWAYS acknowledge and use information already provided - don't ask for it again
        - When you have partial information, confirm it and ask for what's missing
        - If information is unclear, wrong, or missing, help correct it naturally
        - Always include a free-form text area for user questions/clarification
        - When users make mistakes, don't just ask again - provide specific guidance and suggestions
        - If user seems confused, offer multiple options or explain what you're looking for
        - Focus on collecting useful information, not rigid form completion
        - Help users who are struggling with detailed explanations and specific examples
        
        CRITICAL MEMORY RULE:
        - Before asking for ANY information, check if you already have it in the context
        - If you have vehicle info (make, model, year), ALWAYS mention it and don't ask again
        - If you have tire quantity, ALWAYS use it and don't ask again
        - Only ask for information that is truly missing or needs clarification
        
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
        - Researched information: {researched_info}
        
        VEHICLE KNOWLEDGE (for natural corrections):
        - Forte is a Kia model, not Toyota
        - Camry, Corolla, RAV4, Highlander, Sienna, Prius are Toyota models
        - Civic, Accord, CR-V, Pilot, Odyssey are Honda models
        - F-150, Escape, Explorer, Mustang, Focus, Fusion are Ford models
        - Be conversational about corrections: "I think you might mean..." or "Just to clarify..."
        """.format(
            current_step=current_step,
            user_knowledge_level=user_knowledge_level,
            vehicle_info=vehicle_info,
            tire_specs=tire_specs,
            driving_patterns=driving_patterns,
            budget_preferences=budget_preferences,
            current_tire_status=current_tire_status,
            special_considerations=special_considerations,
            missing_vehicle_info=missing_vehicle_info,
            missing_tire_specs=missing_tire_specs,
            user_message=user_message,
            researched_info=conversation_context.get('researched_info', {})
        )
        
        # Add format-specific instructions
        if response_format == "living_form":
            system_prompt += """
            
            LIVING FORM INSTRUCTIONS:
            You are creating a revolutionary "Living Form" experience - ALL your conversational text must be embedded within the form itself.
            
            CRITICAL REQUIREMENTS:
            - NO separate chat responses - everything must be within the form
            - Your conversational text should be part of the form structure (before, between, after form elements)
            - Address corrections, explanations, and guidance within the form context
            - Always include a free-text area for user questions/uncertainties
            - Encourage users to express uncertainties rather than guess
            - Always reassure users it's okay to leave fields blank or write "I don't know"
            - When users provide wrong info, don't just ask again - provide specific help:
              * Explain what the issue is
              * Suggest what they might have meant
              * Offer multiple options or examples
              * Give guidance on how to find the right information
            
            RESPONSE STRUCTURE:
            1. Acknowledge what the user provided (be specific and personal)
            2. Confirm any information you already have from previous interactions
            3. Provide conversational guidance and explanations
            4. Embed form elements naturally within your response (only for missing info)
            5. Continue the conversation after the form elements
            6. Be encouraging and helpful throughout
            
            FORM ELEMENT INTEGRATION:
            - Embed form elements directly in your conversational response
            - Use proper HTML: <input>, <textarea>, <select>, <button>
            - Always include a submit button (type="submit")
            - Make form elements feel like natural conversation tools
            - Provide context and explanations around form elements
            - Use placeholders that are helpful and encouraging
            
            EXAMPLE LIVING FORM RESPONSE:
            "<form class="living-form">
                <div class="form-header">
                    <h3>Let me help clarify your vehicle information</h3>
                    <p class="help-text">I notice you mentioned a 2020 Kia Camry. Here's what I can help with:</p>
                    <ul style="margin:10px 0;padding-left:20px;">
                        <li><strong>Camry is a Toyota model</strong> - Did you mean a 2020 Toyota Camry?</li>
                        <li><strong>Popular Kia models for 2020</strong> include: Forte, Soul, Sportage, Sorento</li>
                        <li><strong>Not sure?</strong> Check your vehicle registration or the badge on your car</li>
                    </ul>
                    <p>Let me help you get the right information:</p>
                </div>
                
                <div class="form-body">
                    <div class="form-group">
                        <label for="make">Vehicle Make:</label>
                        <input type="text" id="make" name="make" placeholder="e.g., Kia, Toyota, Honda">
                    </div>
                    
                    <div class="form-group">
                        <label for="model">Model:</label>
                        <input type="text" id="model" name="model" placeholder="e.g., Forte, Camry, Civic">
                    </div>
                    
                    <div class="form-group">
                        <label for="tire_count">How many tires do you need?</label>
                        <select id="tire_count" name="tire_count">
                            <option value="">Select...</option>
                            <option value="1">1 tire</option>
                            <option value="2">2 tires</option>
                            <option value="4">4 tires (full set)</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom:20px;padding:15px;background:#fff3cd;border-radius:6px;border:1px solid #ffeeba;">
                        <p style="margin:0;color:#856404;font-size:14px;">💡 <strong>Don't know something?</strong> That's totally okay! You can:</p>
                        <ul style="margin:5px 0;padding-left:20px;color:#856404;font-size:14px;">
                            <li>Leave fields blank if you're unsure</li>
                            <li>Write "I don't know" or "IDK" in the notes</li>
                            <li>Ask questions below - I'm here to help!</li>
                        </ul>
                    </div>
                    
                    <div class="form-group">
                        <label for="notes">Questions or additional info:</label>
                        <textarea id="notes" name="notes" placeholder="Ask me anything or tell me about your driving needs..." rows="3"></textarea>
                    </div>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn-primary">Continue</button>
                </div>
                
                <div style="margin-top:15px;text-align:center;color:#666;font-size:14px;">
                    I'm here to help you find the perfect tires! 😊
                </div>
            </form>"
            
            IMPORTANT RULES:
            - NEVER EVER use markdown code blocks (```html, ```, or any backticks)
            - NEVER include the word "html" in your response unless talking about HTML as a concept
            - Always use proper HTML tags directly in your response
            - Use CSS classes for styling: "living-form", "form-header", "form-body", "form-group", "form-actions", "btn-primary"
            - DO NOT use inline styles except for specific content styling (like help boxes)
            - Make the conversation flow naturally around form elements
            - Be specific and personal in your acknowledgments
            - Adapt your language to the user's knowledge level
            - Always include a submit button with class="btn-primary"
            - Keep form elements simple and focused
            - Provide helpful placeholders and examples
            - When users are confused, provide specific guidance, examples, and multiple options
            - Be encouraging and supportive throughout
            
            CONVERSATION FLOW:
            - Always acknowledge what the user just provided
            - Confirm and summarize what you already know from previous interactions
            - Explain why you need the next piece of information (only if missing)
            - Provide form elements for collecting ONLY missing information
            - Give alternatives and help options
            - Continue being conversational and helpful
            - Move naturally toward tire recommendations
            
            EXAMPLE PROGRESSIVE COLLECTION:
            "Thanks for providing your vehicle information! I now have:
            - Vehicle: 2020 Kia (confirmed)
            - Tire quantity: 2 tires (confirmed)
            
            Now I need to know the specific model to find the right tire size..."
            """
        
        # Add user knowledge level specific instructions
        if user_knowledge_level == "novice":
            system_prompt += """
            
            USER KNOWLEDGE LEVEL: NOVICE
            - Use friendly, simple language
            - Explain tire concepts naturally as you go
            - Provide helpful examples and analogies
            - Be encouraging and patient
            - Break things down into digestible pieces
            """
        elif user_knowledge_level == "expert":
            system_prompt += """
            
            USER KNOWLEDGE LEVEL: EXPERT
            - Use appropriate technical terms
            - Be direct and efficient
            - Focus on specs and performance details
            - Assume they know tire basics
            """
        
        # Add conversation step specific context
        if current_step == "greeting":
            system_prompt += """
            
            CONVERSATION STEP: GREETING
            - Welcome the user warmly and personally
            - If they mentioned vehicle info, acknowledge it specifically
            - Explain how you can help in a conversational way
            - Provide form elements for collecting basic vehicle information
            - Be encouraging about the process
            """
        elif current_step == "vehicle_info":
            system_prompt += """
            
            CONVERSATION STEP: VEHICLE INFO
            - Acknowledge any vehicle info they've provided specifically
            - Explain what you need next and why
            - Provide form elements for missing vehicle information
            - Help them find information they might not know
            - Be supportive and encouraging
            """
        elif current_step == "needs_analysis":
            system_prompt += """
            
            CONVERSATION STEP: NEEDS ANALYSIS
            - ALWAYS acknowledge any preferences the user has already mentioned
            - Start with: "Thanks for sharing your driving preferences..." or "I see you're looking for..."
            - Understand their driving patterns and preferences
            - Explain how different tires suit different needs
            - ALWAYS provide a form for budget and priority info
            - Forms are the primary way to collect information
            - If you have enough info, move to recommendations
            """
        elif current_step == "recommendation":
            system_prompt += """
            
            CONVERSATION STEP: RECOMMENDATION
            - Provide specific tire recommendations with clear reasoning
            - Include price, performance, and suitability info
            - Explain pros and cons of each option
            - Help them compare options effectively
            - Generate a form for final selection or additional questions
            - Chat is for questions about the recommendations
            """
        
        # Add form generation instructions
        system_prompt += """
        
        FORM GENERATION RULES:
        - Generate ONLY ONE form per response
        - Use proper HTML formatting, NOT markdown
        - Include helpful explanations in the form
        - Use checkboxes for multiple choice questions
        - Provide text inputs for custom answers
        - Make forms optional - users can skip and ask directly
        - Include a "Continue" or "Submit" button
        - Add helpful tips and examples in the form
        
        HTML FORM EXAMPLES:
        
        For vehicle trim selection:
        <form class="living-form">
            <div class="form-header">
                <h3>What trim level is your 2020 Kia Forte?</h3>
                <p>This helps me find the exact tire size for your car.</p>
            </div>
            <div class="form-body">
                <div class="form-group">
                    <label>Select your trim level:</label>
                    <div class="radio-group">
                        <label class="radio-option">
                            <input type="radio" name="trim" value="LX" />
                            <span class="radio-label">LX</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="trim" value="FE" />
                            <span class="radio-label">FE</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="trim" value="GT-Line" />
                            <span class="radio-label">GT-Line</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="trim" value="EX" />
                            <span class="radio-label">EX</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="trim" value="GT" />
                            <span class="radio-label">GT</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="trim" value="not_sure" />
                            <span class="radio-label">Not sure (I can help identify it!)</span>
                        </label>
                    </div>
                </div>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn-primary">Continue</button>
            </div>
        </form>
        
        For budget selection:
        <form class="living-form">
            <div class="form-header">
                <h3>What's your budget for all 4 tires?</h3>
                <p>This helps me recommend options that fit your budget.</p>
            </div>
            <div class="form-body">
                <div class="form-group">
                    <label>Select your budget range (select all that apply):</label>
                    <div class="checkbox-group">
                        <label class="checkbox-option">
                            <input type="checkbox" name="budget" value="economy" />
                            <span class="checkbox-label">Economy ($400-600)</span>
                        </label>
                        <label class="checkbox-option">
                            <input type="checkbox" name="budget" value="mid_range" />
                            <span class="checkbox-label">Mid-range ($600-800)</span>
                        </label>
                        <label class="checkbox-option">
                            <input type="checkbox" name="budget" value="premium" />
                            <span class="checkbox-label">Premium ($800+)</span>
                        </label>
                        <label class="checkbox-option">
                            <input type="checkbox" name="budget" value="not_sure" />
                            <span class="checkbox-label">Not sure yet</span>
                        </label>
                    </div>
                </div>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn-primary">Continue</button>
            </div>
        </form>
        
        For usage patterns (multiple selection):
        <form class="living-form">
            <div class="form-header">
                <h3>How do you mainly use your car?</h3>
                <p>Select all that apply to help me recommend the best tires for your driving style.</p>
            </div>
            <div class="form-body">
                <div class="form-group">
                    <label>Select your driving patterns:</label>
                    <div class="checkbox-group">
                        <label class="checkbox-option">
                            <input type="checkbox" name="usage" value="daily_commuting" />
                            <span class="checkbox-label">Daily commuting</span>
                        </label>
                        <label class="checkbox-option">
                            <input type="checkbox" name="usage" value="highway" />
                            <span class="checkbox-label">Highway driving</span>
                        </label>
                        <label class="checkbox-option">
                            <input type="checkbox" name="usage" value="city" />
                            <span class="checkbox-label">City driving</span>
                        </label>
                        <label class="checkbox-option">
                            <input type="checkbox" name="usage" value="family" />
                            <span class="checkbox-label">Family transport</span>
                        </label>
                    </div>
                    <div class="custom-input">
                        <label>Other (please specify):</label>
                        <input type="text" name="custom_usage" placeholder="Tell me about your driving..." />
                    </div>
                </div>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn-primary">Continue</button>
            </div>
        </form>
        
        IMPORTANT: Always use proper HTML tags, NOT markdown. The form should be complete HTML that can be rendered directly.
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
    
    async def test_connection(self, model_type: ModelType) -> bool:
        """Test connection to a specific model"""
        try:
            test_response = await self.generate_response(
                user_message="Hello, this is a test message.",
                conversation_context={
                    'current_step': 'greeting',
                    'user_knowledge_level': 'intermediate',
                    'vehicle_info': {},
                    'tire_preferences': {}
                },
                model_type=model_type,
                response_format="text"
            )
            
            return test_response['text'] is not None
        except Exception as e:
            logger.error(f"Connection test failed for {model_type.value}: {str(e)}")
            return False
    
    def get_available_models(self) -> List[ModelType]:
        """Get list of available models based on API keys"""
        available_models = []
        
        if self.api_keys['openai']:
            available_models.extend([ModelType.GPT_4O, ModelType.GPT_3_5_TURBO])
        
        if self.api_keys['anthropic']:
            available_models.extend([ModelType.CLAUDE_3_7, ModelType.CLAUDE_3_5_SONNET])
        
        return available_models
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def get_model_info(self, model_type: ModelType) -> Dict[str, Any]:
        """Get information about a specific model"""
        if model_type not in self.model_mappings:
            return {}
        
        config = self.model_mappings[model_type]
        return {
            'provider': config['provider'],
            'model_name': config['model_name'],
            'max_tokens': config['max_tokens'],
            'available': self.api_keys[config['provider']] is not None
        }
    
    async def generate_fallback_response(self, user_message: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response when AI models are unavailable"""
        # Simple rule-based fallback
        user_lower = user_message.lower()
        
        if "hello" in user_lower or "hi" in user_lower:
            response = "Hello! I'm here to help you find the perfect tires for your vehicle. What can I help you with today?"
        elif "recommend" in user_lower or "suggest" in user_lower:
            response = "I'd be happy to recommend tires for you! To get started, I'll need to know your vehicle's make, model, and year. What car do you drive?"
        elif "price" in user_lower or "cost" in user_lower:
            response = "Tire prices vary based on size, brand, and type. Generally, you can expect to pay anywhere from $75 to $200+ per tire. What's your budget range?"
        else:
            response = "I'm here to help you find the right tires! Could you tell me more about what you're looking for or what questions you have?"
        
        return {
            'text': response,
            'cost': 0.0,
            'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
            'model': 'fallback',
            'provider': 'internal'
        } 