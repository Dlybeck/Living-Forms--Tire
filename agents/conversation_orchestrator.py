import logging
from typing import Dict, Any
from datetime import datetime
import re

from utils.state_manager import ConversationState
from database.tire_database import TireDatabase
from agents.cost_manager import CostManager
from agents.ai_client import AIClient
from agents.function_call_parser import FunctionCallParser

logger = logging.getLogger(__name__)

class ConversationOrchestrator:
    """
    Orchestrates the living form conversation flow using function-based form generation
    This replaces the unreliable parsing approach with direct function execution
    """
    
    def __init__(self, tire_database: TireDatabase, cost_manager: CostManager):
        self.tire_database = tire_database
        self.cost_manager = cost_manager
        self.ai_client = AIClient()
        self.function_parser = FunctionCallParser()
        
        logger.info("Conversation orchestrator initialized with function-based approach")
    
    async def process_message(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Main entry point for processing user messages using function-based form generation
        """
        start_time = datetime.now()
        
        try:
            # Step 0: Store last user message for web search detection
            conversation_state.last_user_message = user_message
            
            # Step 0.5: Extract and update vehicle info from user message FIRST
            self._extract_and_update_vehicle_info(user_message, conversation_state)
            
            # Update user knowledge level based on message
            conversation_state.detect_user_knowledge_level(user_message)
            
            # Step 1: Generate AI response with function call instructions
            # Include form data in the context if this is a form submission
            enhanced_message = user_message
            if conversation_state.form_data and user_message.lower() == "form submission":
                # This is a form submission, include the form data in the message
                form_info = []
                for key, value in conversation_state.form_data.items():
                    if value and str(value).strip():
                        form_info.append(f"{key}: {value}")
                
                if form_info:
                    enhanced_message = f"Form submission with: {', '.join(form_info)}"
                    logger.info(f"Enhanced message for AI: {enhanced_message}")
            
            # Add tire context reminder to keep AI focused
            if "help" in enhanced_message.lower() or "find" in enhanced_message.lower() or "where" in enhanced_message.lower():
                enhanced_message += " (Remember: Stay focused on helping find tire-related information and vehicle details for tire recommendations)"
            
            ai_response = await self._generate_ai_response_with_functions(enhanced_message, conversation_state)
            
            # Debug: Log the full AI response
            logger.info(f"Full AI response: {ai_response['response'][:500]}...")
            
            # Step 2: Parse function calls and generate forms
            conversation_text, form_html = self.function_parser.parse_function_calls(ai_response["response"])
            
            # Step 2.5: Extract and apply AI corrections to conversation state
            self._extract_ai_corrections(conversation_text, conversation_state)
            
            # Step 2.6: Extract and store web search results
            self._extract_web_search_results(conversation_text, conversation_state)
            
            # Debug: Log parsing results
            logger.info(f"Parsed conversation text: {conversation_text[:100]}...")
            logger.info(f"Form HTML generated: {bool(form_html)}")
            
            # Step 3: Determine response format
            if form_html:
                # AI created a form using function calls
                # The conversation text is already included in the form_html
                response_data = {
                    "response": "",  # No separate conversation text since it's in the form
                    "form_html": form_html,
                    "inline_guidance": "",
                    "cost_info": ai_response.get("cost_info", {"cost": ai_response.get("cost", 0.0), "model_used": ai_response.get("model_used", "ai"), "source": "ai"}),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "function_based_form"
                }
            else:
                # AI provided conversational response only - ALWAYS include a form to prevent soft lock
                # Create a simple form with just the "Additional Thoughts" field
                from agents.form_builder import FormBuilder
                form_builder = FormBuilder()
                fallback_form = form_builder.create_complete_form(
                    fields_html=[],  # No additional fields, just the automatic "Additional Thoughts"
                    conversation_text=conversation_text,
                    submit_text="Continue"
                )
                
                response_data = {
                    "response": "",  # No separate response since it's in the form
                    "form_html": fallback_form,
                    "inline_guidance": "",
                    "cost_info": ai_response.get("cost_info", {"cost": ai_response.get("cost", 0.0), "model_used": ai_response.get("model_used", "ai"), "source": "ai"}),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "conversation_with_fallback_form"
                }
            
            # Add to conversation history
            conversation_state.add_interaction(
                user_message=user_message,
                ai_response=conversation_text,
                cost=ai_response.get("cost", 0.0),
                model_used=ai_response.get("model_used", "ai")
            )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _extract_and_update_vehicle_info(self, user_message: str, conversation_state: ConversationState):
        """Extract vehicle information from user message and update conversation state"""
        user_lower = user_message.lower()
        
        # Check if this is the initial form submission with info_method
        if 'info_method' in conversation_state.form_data:
            info_method = conversation_state.form_data['info_method']
            
            # Handle the chosen method
            if info_method == 'tire_size':
                # User chose tire size method - extract tire size if provided
                tire_size_match = re.search(r'\b\d{3}/\d{2}R\d{2}\b', user_message.upper())
                if tire_size_match:
                    conversation_state.tire_specs['current_tire_size'] = tire_size_match.group()
                    logger.info(f"Extracted tire size: {tire_size_match.group()}")
                return  # Let AI handle the response for tire size input
                
            elif info_method == 'vin':
                # User chose VIN method - extract VIN if provided
                vin_match = re.search(r'\b[A-Z0-9]{17}\b', user_message.upper())
                if vin_match:
                    conversation_state.vehicle_info['vin'] = vin_match.group()
                    logger.info(f"Extracted VIN: {vin_match.group()}")
                return  # Let AI handle the response for VIN input
                
            elif info_method == 'make_model_year':
                # User chose make/model/year method - extract vehicle info
                self._extract_vehicle_details(user_message, conversation_state)
                return
                
            elif info_method == 'not_sure':
                # User is not sure - let AI assess their knowledge and guide them
                # Mark them as novice to get more guidance
                conversation_state.user_knowledge_level = conversation_state.detect_user_knowledge_level(user_message)
                logger.info(f"User chose 'not sure' - detected knowledge level: {conversation_state.user_knowledge_level.value}")
                return  # Let AI handle the response with appropriate guidance
                
            # Clear the info_method from form data after processing
            conversation_state.form_data.pop('info_method', None)
        
        # Fallback to regular extraction if no info_method
        self._extract_vehicle_details(user_message, conversation_state)
    
    def _extract_vehicle_details(self, user_message: str, conversation_state: ConversationState):
        """Extract vehicle details from user message"""
        user_lower = user_message.lower()
        
        # Extract make and model, but be very conservative about storing anything
        # when there might be conflicts or errors
        
        makes = ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai', 'volkswagen', 'bmw', 'mercedes', 'audi']
        models = {
            'kia': ['forte', 'soul', 'sportage', 'sorento', 'telluride', 'k5', 'rio', 'optima', 'cadenza', 'stinger'],
            'honda': ['civic', 'accord', 'cr-v', 'pilot', 'odyssey', 'fit', 'hr-v', 'passport', 'ridgeline', 'insight'],
            'toyota': ['camry', 'corolla', 'rav4', 'highlander', 'sienna', 'prius', 'tacoma', 'tundra', '4runner', 'sequoia'],
            'ford': ['f-150', 'escape', 'explorer', 'mustang', 'focus', 'fusion', 'edge', 'expedition', 'ranger', 'bronco'],
            'chevrolet': ['silverado', 'equinox', 'tahoe', 'camaro', 'cruze', 'malibu', 'traverse', 'colorado', 'suburban', 'impala'],
            'nissan': ['altima', 'sentra', 'rogue', 'murano', 'pathfinder', 'frontier', 'titan', 'versa', 'maxima'],
            'mazda': ['cx-5', 'cx-30', 'mazda3', 'mazda6', 'cx-9', 'mx-5', 'cx-50'],
            'hyundai': ['sonata', 'elantra', 'tucson', 'santa fe', 'palisade', 'kona', 'veloster', 'accent'],
            'volkswagen': ['golf', 'jetta', 'passat', 'tiguan', 'atlas', 'id.4', 'taos'],
            'bmw': ['3-series', '5-series', 'x3', 'x5', 'i3', 'i8', 'x1', 'x7', 'm3', 'm5'],
            'mercedes': ['c-class', 'e-class', 's-class', 'gla', 'glc', 'gle', 'gls', 'a-class', 'cla'],
            'audi': ['a3', 'a4', 'a6', 'q3', 'q5', 'q7', 'q8', 's3', 's4', 'rs3']
        }
        
        # Find all makes and models mentioned
        mentioned_makes = [make for make in makes if make in user_lower]
        mentioned_models = []
        for make, model_list in models.items():
            for model in model_list:
                if model in user_lower:
                    mentioned_models.append((model, make))
        
        # Also look for any model-like words that might be mentioned but not in our list
        # Common model patterns: single letter + number (I8, M3, X5), or word patterns
        model_patterns = [
            r'\b[a-z]\d+\b',  # I8, M3, X5, etc.
            r'\b[a-z]+\d*\b',  # Civic, Accord, etc.
        ]
        
        potential_models = []
        for pattern in model_patterns:
            matches = re.findall(pattern, user_lower)
            for match in matches:
                # Skip if it's already in our known models
                if not any(match == model for model, _ in mentioned_models):
                    potential_models.append(match)
        
        # Validate combinations
        if len(mentioned_makes) == 1 and len(mentioned_models) == 1:
            make, (model, expected_make) = mentioned_makes[0], mentioned_models[0]
            if make == expected_make:
                # Valid combination - store it
                conversation_state.vehicle_info['make'] = make.title()
                conversation_state.vehicle_info['model'] = model.title()
                logger.info(f"Extracted valid vehicle: {make.title()} {model.title()}")
            else:
                # Invalid combination - don't store anything, let AI handle it
                logger.info(f"Found invalid combination '{make.title()} {model.title()}' - letting AI handle correction")
        elif len(mentioned_makes) == 1 and len(potential_models) == 1:
            # Make + potential model (not in our list) - be conservative
            make = mentioned_makes[0]
            potential_model = potential_models[0]
            
            # Check if this model belongs to a different make
            model_belongs_to = None
            for model_make, model_list in models.items():
                if potential_model in model_list:
                    model_belongs_to = model_make
                    break
            
            if model_belongs_to and model_belongs_to != make:
                # Model belongs to different make - invalid combination
                logger.info(f"Found invalid combination '{make.title()} {potential_model.title()}' (model belongs to {model_belongs_to.title()}) - letting AI handle correction")
            else:
                # Unknown model or valid combination - store both
                conversation_state.vehicle_info['make'] = make.title()
                conversation_state.vehicle_info['model'] = potential_model.title()
                logger.info(f"Extracted vehicle with unknown model: {make.title()} {potential_model.title()}")
        elif len(mentioned_makes) == 1 and len(mentioned_models) == 0 and len(potential_models) == 0:
            # Only make mentioned, no model - store make only
            conversation_state.vehicle_info['make'] = mentioned_makes[0].title()
            logger.info(f"Extracted make only: {mentioned_makes[0].title()}")
        elif len(mentioned_makes) == 0 and len(mentioned_models) == 1:
            # Only model mentioned, no make - store model only
            model, make = mentioned_models[0]
            conversation_state.vehicle_info['model'] = model.title()
            logger.info(f"Extracted model only: {model.title()}")
        else:
            # Multiple makes/models or conflicts - don't store anything, let AI handle it
            logger.info(f"Found multiple or conflicting vehicle info - letting AI handle: makes={mentioned_makes}, models={mentioned_models}, potential_models={potential_models}")
        
        # Extract year (4-digit year)
        year_match = re.search(r'\b(19|20)\d{2}\b', user_message)
        if year_match:
            conversation_state.vehicle_info['year'] = year_match.group()
            logger.info(f"Extracted vehicle year: {year_match.group()}")
        
        # Extract tire size pattern
        tire_size_match = re.search(r'\b\d{3}/\d{2}R\d{2}\b', user_message.upper())
        if tire_size_match:
            conversation_state.tire_specs['current_tire_size'] = tire_size_match.group()
            logger.info(f"Extracted tire size: {tire_size_match.group()}")
        
        # Log the final vehicle info
        if conversation_state.vehicle_info:
            logger.info(f"Final vehicle info: {conversation_state.vehicle_info}")
    
    def _extract_ai_corrections(self, ai_response: str, conversation_state: ConversationState):
        """Extract vehicle information corrections from AI response and update conversation state"""
        import re
        
        # Look for common correction patterns in AI responses
        correction_patterns = [
            # Pattern: "The Camry is actually a Toyota model, not Kia"
            r'(?:actually|actually a|is actually)\s+(\w+)\s+model',
            # Pattern: "Did you mean Toyota Camry, or perhaps a Kia model like the K5 or Forte?"
            r'(?:did you mean|perhaps)\s+(\w+)\s+(\w+)',
            # Pattern: "The correct make is Toyota"
            r'(?:correct|right)\s+(?:make|brand)\s+is\s+(\w+)',
            # Pattern: "You have a Toyota Camry"
            r'(?:you have|you drive|your vehicle is)\s+(?:a\s+)?(\w+)\s+(\w+)',
        ]
        
        for pattern in correction_patterns:
            matches = re.findall(pattern, ai_response, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Multiple groups captured
                    if len(match) == 2:
                        make, model = match
                        if make.lower() in ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai']:
                            conversation_state.vehicle_info['make'] = make.title()
                            conversation_state.vehicle_info['model'] = model.title()
                            logger.info(f"AI correction applied: {make.title()} {model.title()}")
                else:
                    # Single group captured
                    if match.lower() in ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai']:
                        conversation_state.vehicle_info['make'] = match.title()
                        logger.info(f"AI correction applied: make = {match.title()}")
        
        # Also look for explicit corrections in the conversation text
        # Pattern: "Thanks for providing the corrected vehicle information: Kia Forte"
        correction_match = re.search(r'corrected\s+vehicle\s+information:\s+(\w+)\s+(\w+)', ai_response, re.IGNORECASE)
        if correction_match:
            make, model = correction_match.groups()
            conversation_state.vehicle_info['make'] = make.title()
            conversation_state.vehicle_info['model'] = model.title()
            logger.info(f"AI correction applied from explicit mention: {make.title()} {model.title()}")
    
    def _extract_web_search_results(self, ai_response: str, conversation_state: ConversationState):
        """Extract and store web search results from AI response"""
        import re
        
        # Look for web search result patterns
        # Pattern: "Based on my search, the 2020 Kia Forte comes in these trim levels:"
        search_patterns = [
            # Trim level information
            r'(?:trim levels?|trims?|packages?|editions?)(?:\s+for\s+|\s+of\s+|\s+on\s+)?(?:the\s+)?(\d{4})\s+(\w+)\s+(\w+)',
            # Tire size information
            r'(?:tire size|tire sizes?|fits?|fitted with)(?:\s+for\s+|\s+of\s+|\s+on\s+)?(?:the\s+)?(\d{4})\s+(\w+)\s+(\w+)',
            # Vehicle specifications
            r'(?:specifications?|specs?|details?)(?:\s+for\s+|\s+of\s+|\s+on\s+)?(?:the\s+)?(\d{4})\s+(\w+)\s+(\w+)',
        ]
        
        for pattern in search_patterns:
            matches = re.findall(pattern, ai_response, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:
                    year, make, model = match
                    vehicle_key = f"{year}_{make}_{model}".lower()
                    
                    # Extract the relevant information from the response
                    # Look for lists, bullet points, or specific data after the search result
                    lines = ai_response.split('\n')
                    search_data = []
                    
                    for i, line in enumerate(lines):
                        if any(pattern in line.lower() for pattern in ['trim', 'package', 'edition', 'tire size', 'spec']):
                            # Collect the next few lines that might contain the actual data
                            for j in range(i+1, min(i+10, len(lines))):
                                next_line = lines[j].strip()
                                if next_line and not next_line.startswith('**') and len(next_line) > 3:
                                    search_data.append(next_line)
                                elif next_line.startswith('**') and j > i+2:
                                    break
                    
                    if search_data:
                        conversation_state.store_researched_info(vehicle_key, {
                            'year': year,
                            'make': make.title(),
                            'model': model.title(),
                            'search_data': search_data,
                            'timestamp': datetime.now().isoformat()
                        })
                        logger.info(f"Stored web search results for {vehicle_key}: {len(search_data)} data points")
        
        # Also look for specific tire recommendations or reviews
        tire_recommendation_patterns = [
            r'(?:recommended|best|top|popular)\s+(?:tires?|tire brands?)',
            r'(?:tire reviews?|tire ratings?|tire comparisons?)',
        ]
        
        for pattern in tire_recommendation_patterns:
            if re.search(pattern, ai_response, re.IGNORECASE):
                # Extract tire recommendation data
                lines = ai_response.split('\n')
                tire_data = []
                
                for line in lines:
                    if any(tire_term in line.lower() for tire_term in ['michelin', 'bridgestone', 'goodyear', 'continental', 'pirelli', 'tire']):
                        tire_data.append(line.strip())
                
                if tire_data:
                    conversation_state.store_researched_info('tire_recommendations', {
                        'recommendations': tire_data,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.info(f"Stored tire recommendations: {len(tire_data)} recommendations")
    
    async def _generate_ai_response_with_functions(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Generate AI response with function call instructions
        """
        # Determine query complexity
        query_complexity = self._analyze_query_complexity(user_message, conversation_state)
        
        # Get recommended model from cost manager
        recommended_model = self.cost_manager.get_recommended_model(query_complexity, conversation_state)
        logger.info(f"🎯 COST MANAGER RECOMMENDATION: {recommended_model.value} for complexity: {query_complexity}")
        logger.info(f"💰 Budget remaining: ${self.cost_manager.get_remaining_budget(conversation_state):.4f}")
        
        # Check if we can afford this operation
        estimated_cost = self.cost_manager.estimate_cost(
            user_message + str(conversation_state.get_conversation_context()),
            recommended_model
        )
        
        if not self.cost_manager.can_afford_operation("ai_response", estimated_cost, conversation_state):
            # Use fallback response
            logger.info("Cannot afford operation, using fallback response")
            return self._generate_fallback_response(user_message, conversation_state)
        
        # Generate AI response with function call instructions
        try:
            logger.info(f"🤖 CALLING AI: {recommended_model.value}")
            response = await self.ai_client.generate_response(
                user_message=user_message,
                conversation_context=conversation_state.get_conversation_context(),
                model_type=recommended_model,
                response_format="function_calls",
                function_documentation=self.function_parser.get_function_documentation()
            )
            
            # Track the cost
            self.cost_manager.track_cost("ai_response", response["cost"], conversation_state)
            
            return {
                "response": response["text"],
                "cost": response["cost"],
                "model_used": recommended_model.value,
                "source": "ai"
            }
            
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            return self._generate_fallback_response(user_message, conversation_state)
    
    def _analyze_query_complexity(self, user_message: str, conversation_state: ConversationState) -> str:
        """Analyze complexity based on conversation context and AI's previous responses"""
        
        # Get conversation context
        conversation_length = len(conversation_state.conversation_history)
        current_step = conversation_state.current_step.value
        user_knowledge = conversation_state.user_knowledge_level.value
        
        # Look at the AI's last response to understand what we're dealing with
        last_ai_response = ""
        if conversation_state.conversation_history:
            last_interaction = conversation_state.conversation_history[-1]
            last_ai_response = last_interaction.ai_response
        
        # Analyze the conversation context for complexity indicators
        complexity_score = 0
        
        # 1. Conversation stage analysis
        if current_step in ['greeting', 'vehicle_info']:
            complexity_score += 1  # Simple collection phase
        elif current_step in ['recommendation', 'comparison']:
            complexity_score += 3  # Complex analysis phase
        elif current_step in ['final_selection', 'completed']:
            complexity_score += 2  # Finalization phase
        
        # 2. User knowledge level
        if user_knowledge == 'novice':
            complexity_score += 1  # Simple explanations needed
        elif user_knowledge == 'expert':
            complexity_score += 3  # Technical details expected
        
        # 3. Conversation length and depth
        if conversation_length <= 2:
            complexity_score += 1  # Early in conversation
        elif conversation_length >= 8:
            complexity_score += 2  # Deep conversation, might need more context
        
        # 4. Analyze AI's last response for complexity indicators
        if last_ai_response:
            ai_response_lower = last_ai_response.lower()
            
            # Check if AI was asking for complex information
            if any(term in ai_response_lower for term in [
                'compare', 'difference', 'versus', 'technical', 'specification',
                'performance', 'engineering', 'detailed', 'analysis'
            ]):
                complexity_score += 3
            
            # Check if AI was providing simple guidance
            elif any(term in ai_response_lower for term in [
                'basic', 'simple', 'just', 'only', 'easy', 'straightforward'
            ]):
                complexity_score += 1
            
            # Check if AI was asking for multiple pieces of information
            if ai_response_lower.count('?') > 2:
                complexity_score += 2
            
            # Check if AI was providing detailed explanations
            if len(ai_response_lower.split()) > 100:
                complexity_score += 2
        
        # 5. User message analysis (but much more nuanced)
        user_lower = user_message.lower()
        
        # Check for confusion or need for clarification
        if any(term in user_lower for term in [
            'confused', 'not sure', 'don\'t understand', 'what do you mean',
            'can you explain', 'i don\'t know', 'help'
        ]):
            complexity_score += 2  # User needs more detailed explanation
        
        # Check for specific technical requests
        if any(term in user_lower for term in [
            'specs', 'specifications', 'technical', 'performance', 'compare',
            'difference', 'versus', 'vs', 'better', 'worse', 'why'
        ]):
            complexity_score += 3
        
        # Check for simple acknowledgments
        if any(term in user_lower for term in [
            'yes', 'no', 'ok', 'sure', 'thanks', 'got it', 'understood'
        ]):
            complexity_score -= 1  # Reduce complexity for simple responses
        
        # 6. Information completeness analysis
        missing_info = []
        if not conversation_state.vehicle_info.get('make'):
            missing_info.append('vehicle_make')
        if not conversation_state.vehicle_info.get('model'):
            missing_info.append('vehicle_model')
        if not conversation_state.vehicle_info.get('year'):
            missing_info.append('vehicle_year')
        if not conversation_state.tire_specs.get('current_tire_size'):
            missing_info.append('tire_size')
        
        # If we're missing basic info, keep complexity low
        if len(missing_info) >= 2:
            complexity_score = max(1, complexity_score - 2)
        
        # Determine complexity level based on score
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 5:
            return "medium"
        else:
            return "high"
    
    def _generate_fallback_response(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """Generate fallback response when AI is not available"""
        user_lower = user_message.lower()
        
        # Rule-based fallback responses
        if "recommend" in user_lower or "suggest" in user_lower:
            response = "I'd be happy to recommend tires! To give you the best suggestions, I need to know your vehicle's make, model, and year. What car do you drive?"
        elif "price" in user_lower or "cost" in user_lower:
            response = "Tire prices vary based on size, brand, and type. Generally, you can expect to pay $75-$200 per tire. What's your budget range?"
        elif "size" in user_lower:
            response = "Tire size is usually found on the sidewall of your current tires. It looks like '225/60R16'. Can you check your current tires, or tell me your vehicle's make, model, and year?"
        else:
            response = "I'm here to help you find the perfect tires! What specific information would you like to know about tires for your vehicle?"
        
        return {
            "response": response,
            "cost": 0.0,
            "model_used": "fallback_rules",
            "source": "fallback"
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response that never soft locks"""
        # Always include a form to prevent soft lock
        from agents.form_builder import FormBuilder
        form_builder = FormBuilder()
        error_form = form_builder.create_complete_form(
            fields_html=[],  # Just the automatic "Additional Thoughts" field
            conversation_text="I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
            submit_text="Continue"
        )
        
        return {
            "response": "",  # No separate response since it's in the form
            "form_html": error_form,
            "inline_guidance": "",
            "cost_info": {"cost": 0.0, "model_used": "error_handler", "source": "error"},
            "processing_time": 0.0,
            "source": "error_with_form"
        }
    
    def get_conversation_summary(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Get a summary of the conversation for debugging/monitoring"""
        return {
            "session_id": conversation_state.session_id,
            "current_step": conversation_state.current_step.value,
            "user_knowledge_level": conversation_state.user_knowledge_level.value,
            "vehicle_info": conversation_state.vehicle_info,
            "tire_specs": conversation_state.tire_specs,
            "driving_patterns": conversation_state.driving_patterns,
            "budget_preferences": conversation_state.budget_preferences,
            "current_tire_status": conversation_state.current_tire_status,
            "special_considerations": conversation_state.special_considerations,
            "completion_status": conversation_state.get_category_completion_status(),
            "ready_for_recommendations": conversation_state.is_ready_for_recommendations(),
            "conversation_length": len(conversation_state.conversation_history),
            "total_cost": conversation_state.total_cost,
            "researched_info": conversation_state.researched_info
        } 