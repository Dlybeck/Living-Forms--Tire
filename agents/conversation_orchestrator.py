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
            
            # Debug: Log current conversation state
            logger.info(f"📊 CONVERSATION STATE SUMMARY:")
            logger.info(f"   Vehicle Info: {conversation_state.vehicle_info}")
            logger.info(f"   Tire Specs: {conversation_state.tire_specs}")
            logger.info(f"   Tire Size Status: {'✅ FOUND' if conversation_state.tire_specs.get('current_tire_size') else '❌ MISSING'}")
            logger.info(f"   Conversation Length: {len(conversation_state.conversation_history)}")
            
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
            
            # Prepare search indicator for frontend loading bar (after AI response)
            search_indicator_message = ""
            if conversation_state.vehicle_info.get('make') and conversation_state.vehicle_info.get('model') and conversation_state.vehicle_info.get('year'):
                if not conversation_state.tire_specs.get('current_tire_size'):
                    search_indicator_message = f"🔍 Searching for tire size information for your {conversation_state.vehicle_info.get('year')} {conversation_state.vehicle_info.get('make')} {conversation_state.vehicle_info.get('model')}..."
            
            # Debug: Log the full AI response
            logger.info(f"Full AI response: {ai_response['response'][:500]}...")
            
            # Step 2: Parse function calls and generate forms
            conversation_text, form_html = self.function_parser.parse_function_calls(ai_response["response"])
            
            # Step 2.5: Extract and apply AI corrections to conversation state
            self._extract_ai_corrections(conversation_text, conversation_state)
            
            # Step 2.6: Extract and store web search results
            self._extract_web_search_results(conversation_text, conversation_state)
            
            # Step 2.7: Clear search indicator if we found tire size
            if conversation_state.tire_specs.get('current_tire_size'):
                search_indicator_message = ""  # Clear search indicator once we have tire size
                logger.info(f"✅ TIRE SIZE FOUND: {conversation_state.tire_specs.get('current_tire_size')} - clearing search indicator")
            
            # Debug: Log parsing results
            logger.info(f"Parsed conversation text: {conversation_text[:100]}...")
            logger.info(f"Form HTML generated: {bool(form_html)}")
            
            # Step 3: Determine response format
            if form_html:
                # AI created a form using function calls
                # The conversation text is already embedded in the form_html, so don't send it separately
                response_data = {
                    "response": "",  # No separate conversation text since it's in the form
                    "form_html": form_html,
                    "inline_guidance": "",
                    "cost_info": ai_response.get("cost_info", {"cost": ai_response.get("cost", 0.0), "model_used": ai_response.get("model_used", "ai"), "source": "ai"}),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "function_based_form",
                    "search_indicator": search_indicator_message
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
                    "source": "conversation_with_fallback_form",
                    "search_indicator": search_indicator_message
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
        
        # Always check for vehicle info in additional_notes field first
        additional_notes = conversation_state.form_data.get('additional_notes', '')
        if additional_notes:
            logger.info(f"Checking additional_notes for vehicle info: {additional_notes}")
            self._extract_vehicle_details(additional_notes, conversation_state)
        
        # Handle user situation responses if they need help
        if conversation_state.needs_help_with_vehicle_info:
            self._process_user_situation_responses(conversation_state)
        
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
                # Also check additional_notes for tire size
                if additional_notes:
                    tire_size_match = re.search(r'\b\d{3}/\d{2}R\d{2}\b', additional_notes.upper())
                    if tire_size_match:
                        conversation_state.tire_specs['current_tire_size'] = tire_size_match.group()
                        logger.info(f"Extracted tire size from additional_notes: {tire_size_match.group()}")
                return  # Let AI handle the response for tire size input
                
            elif info_method == 'vin':
                # User chose VIN method - extract VIN if provided
                vin_match = re.search(r'\b[A-Z0-9]{17}\b', user_message.upper())
                if vin_match:
                    conversation_state.vehicle_info['vin'] = vin_match.group()
                    logger.info(f"Extracted VIN: {vin_match.group()}")
                # Also check additional_notes for VIN
                if additional_notes:
                    vin_match = re.search(r'\b[A-Z0-9]{17}\b', additional_notes.upper())
                    if vin_match:
                        conversation_state.vehicle_info['vin'] = vin_match.group()
                        logger.info(f"Extracted VIN from additional_notes: {vin_match.group()}")
                return  # Let AI handle the response for VIN input
                
            elif info_method == 'make_model_year':
                # User chose make/model/year method - extract vehicle info
                self._extract_vehicle_details(user_message, conversation_state)
                return
                
            elif info_method == 'not_sure':
                # User is not sure - note that they need help figuring out their situation
                conversation_state.note_user_needs_help("not_sure")
                logger.info(f"User chose 'not sure' - noted they need help")
                return  # Let AI handle the response with natural guidance
                
            # Clear the info_method from form data after processing
            conversation_state.form_data.pop('info_method', None)
        
        # Fallback to regular extraction if no info_method
        self._extract_vehicle_details(user_message, conversation_state)
    
    def _process_user_situation_responses(self, conversation_state: ConversationState):
        """Process user situation form responses and update conversation state naturally"""
        form_data = conversation_state.form_data
        
        # Track specific user responses for conversation intelligence
        self._track_user_responses(form_data, conversation_state)
        
        # Map form field names to user situation keys
        situation_mappings = {
            'vehicle_access': 'has_vehicle_access',
            'near_vehicle': 'has_vehicle_access',
            'have_vehicle_access': 'has_vehicle_access',
            'documents': 'has_documents',
            'have_documents': 'has_documents',
            'vehicle_documents': 'has_documents',
            'internet_access': 'has_internet_access',
            'have_internet': 'has_internet_access',
            'online_access': 'has_internet_access'
        }
        
        # Update user situation based on form responses
        updates = {}
        for form_key, form_value in form_data.items():
            if form_key in situation_mappings:
                situation_key = situation_mappings[form_key]
                # Convert responses to boolean
                if form_value in ['Yes', 'yes', 'YES', True]:
                    updates[situation_key] = True
                elif form_value in ['No', 'no', 'NO', False]:
                    updates[situation_key] = False
                elif form_value in ['I don\'t know', 'Not sure', 'Maybe']:
                    updates[situation_key] = None
        
        # Update the conversation state with user situation
        if updates:
            conversation_state.update_user_situation(**updates)
            logger.info(f"Updated user situation: {updates}")
        
        # Track approaches we've tried based on the questions asked
        if any(field in form_data for field in ['vehicle_access', 'near_vehicle']):
            conversation_state.add_attempted_approach("asked_about_vehicle_access")
        if any(field in form_data for field in ['documents', 'have_documents']):
            conversation_state.add_attempted_approach("asked_about_documents")
        if any(field in form_data for field in ['internet_access', 'have_internet']):
            conversation_state.add_attempted_approach("asked_about_internet")
        
        # Check if user has provided vehicle info through other means
        if conversation_state.vehicle_info.get('make') and conversation_state.vehicle_info.get('model'):
            # User has provided vehicle info - they no longer need help
            conversation_state.needs_help_with_vehicle_info = False
            conversation_state.clear_chosen_path()  # Clear chosen path since they've progressed
            logger.info("User provided vehicle info - no longer needs help")
    
    def _track_user_responses(self, form_data: Dict[str, Any], conversation_state: ConversationState):
        """Track specific user responses to build conversation intelligence"""
        # Look for ANY text-based response that indicates user choices
        # Check all fields for meaningful text responses
        for field, value in form_data.items():
            if field == 'submit':  # Skip submit button
                continue
                
            if value and len(str(value).strip()) > 3:
                response = str(value).strip()
                
                # Skip generic/non-actionable responses
                if response.lower() in ['i don\'t know', 'none of the above', 'not sure', 'maybe', 'no', 'yes']:
                    continue
                
                # Skip if it's just a basic selection that doesn't indicate a path
                basic_selections = ['I\'m near my car', 'I have documents', 'I can access my insurance']
                if response in basic_selections:
                    continue
                
                # This looks like a meaningful response - track it
                conversation_state.track_user_response(response)
                logger.info(f"Tracked user response from field '{field}': {response}")
                break  # Only track the first meaningful response
        
        # Also track selection-based responses that indicate a path choice
        choice_fields = ['current_access', 'explore_options', 'preferred_method', 'chosen_approach']
        
        for field in choice_fields:
            if field in form_data and form_data[field]:
                choice = str(form_data[field])
                if choice not in ['I don\'t know', 'None of the above', 'Not sure']:
                    conversation_state.track_user_response(choice)
                    logger.info(f"Tracked user choice: {choice}")
                    break
    
    def _extract_vehicle_details(self, user_message: str, conversation_state: ConversationState):
        """Extract vehicle details from user message"""
        # CRITICAL: Don't extract from system messages or form submissions
        if user_message.lower() in ['form submission', 'form submitted', '']:
            return
            
        user_lower = user_message.lower()
        logger.info(f"Extracting vehicle details from: '{user_message}'")
        
        # Load car models from JSON file
        import json
        import os
        
        try:
            car_models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'car-models.json')
            with open(car_models_path, 'r') as f:
                car_data = json.load(f)
            
            # Create lookup dictionaries
            makes = {}
            models = {}
            
            for brand_info in car_data:
                brand = brand_info['brand'].lower()
                makes[brand] = brand_info['brand']  # Store proper case
                
                for model in brand_info['models']:
                    model_lower = model.lower()
                    models[model_lower] = (model, brand_info['brand'])  # Store (proper_case_model, proper_case_brand)
            
            logger.info(f"Loaded {len(makes)} makes and {len(models)} models from car-models.json")
            
        except Exception as e:
            logger.error(f"Error loading car-models.json: {e}")
            # Fallback to basic extraction if file can't be loaded
            makes = {}
            models = {}
        
        # Find all makes and models mentioned
        mentioned_makes = []
        mentioned_models = []
        
        for make_lower, make_proper in makes.items():
            # Use word boundaries to avoid false positives like "ion" in "submission"
            if re.search(r'\b' + re.escape(make_lower) + r'\b', user_lower):
                mentioned_makes.append((make_lower, make_proper))
        
        for model_lower, (model_proper, brand_proper) in models.items():
            # Skip single-letter models that are likely pronouns or common words
            if len(model_lower) <= 1:
                continue
                
            # Skip common words that might be in model names but aren't actually models in this context
            common_words = ['a', 'is', 'it', 'in', 'on', 'at', 'to', 'for', 'of', 'the', 'and', 'or', 'but', 'so', 'my', 'me', 'we', 'us', 'he', 'she', 'they', 'have', 'has', 'had', 'do', 'did', 'will', 'can', 'could', 'would', 'should']
            if model_lower in common_words:
                continue
                
            # Use word boundaries to avoid false positives like "ion" in "submission"
            if re.search(r'\b' + re.escape(model_lower) + r'\b', user_lower):
                mentioned_models.append((model_lower, model_proper, brand_proper))
        
        logger.info(f"Found makes: {mentioned_makes}, models: {mentioned_models}")
        
        # Validate combinations
        if len(mentioned_makes) == 1 and len(mentioned_models) == 1:
            make_lower, make_proper = mentioned_makes[0]
            model_lower, model_proper, expected_brand = mentioned_models[0]
            
            if make_proper.lower() == expected_brand.lower():
                # Valid combination - store it
                conversation_state.vehicle_info['make'] = make_proper
                conversation_state.vehicle_info['model'] = model_proper
                logger.info(f"Extracted valid vehicle: {make_proper} {model_proper}")
            else:
                # Invalid combination - don't store anything, let AI handle it
                logger.info(f"Found invalid combination '{make_proper} {model_proper}' (model belongs to {expected_brand}) - letting AI handle correction")
        elif len(mentioned_makes) == 0 and len(mentioned_models) == 1:
            # Only model mentioned, no make - store both from model lookup
            model_lower, model_proper, brand_proper = mentioned_models[0]
            conversation_state.vehicle_info['make'] = brand_proper
            conversation_state.vehicle_info['model'] = model_proper
            logger.info(f"Extracted vehicle from model: {brand_proper} {model_proper}")
        elif len(mentioned_makes) == 1 and len(mentioned_models) == 0:
            # Only make mentioned, no model - store make only
            make_lower, make_proper = mentioned_makes[0]
            conversation_state.vehicle_info['make'] = make_proper
            logger.info(f"Extracted make only: {make_proper}")
        else:
            # Multiple makes/models or conflicts - don't store anything, let AI handle it
            logger.info(f"Found multiple or conflicting vehicle info - letting AI handle: makes={mentioned_makes}, models={mentioned_models}")
        
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
        if conversation_state.tire_specs:
            logger.info(f"Final tire specs: {conversation_state.tire_specs}")
    
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
        
        # CRITICAL: Extract tire size information from AI response and store it properly
        # Look for tire size patterns in AI response - BUT AVOID EXAMPLES
        tire_size_patterns = [
            r'uses?\s+(\d{3}/\d{2}R\d{2})\s+tires?',
            r'tire\s+size\s+is\s+(\d{3}/\d{2}R\d{2})',
            r'fitted\s+with\s+(\d{3}/\d{2}R\d{2})',
            r'comes\s+with\s+(\d{3}/\d{2}R\d{2})',
            r'typically\s+uses?\s+(\d{3}/\d{2}R\d{2})',
            r'standard\s+tire\s+size\s+is\s+(\d{3}/\d{2}R\d{2})',
            r'found\s+it.*?(\d{3}/\d{2}R\d{2})',
            r'✅.*?(\d{3}/\d{2}R\d{2})',
            r'your.*?(\d{3}/\d{2}R\d{2})\s+tires?'
        ]
        
        # Patterns to AVOID (these are examples, not actual tire sizes)
        example_patterns = [
            r'like\s+[\'"]?(\d{3}/\d{2}R\d{2})[\'"]?',
            r'such\s+as\s+[\'"]?(\d{3}/\d{2}R\d{2})[\'"]?',
            r'e\.g\.\s*,?\s*[\'"]?(\d{3}/\d{2}R\d{2})[\'"]?',
            r'for\s+example\s+[\'"]?(\d{3}/\d{2}R\d{2})[\'"]?',
            r'something\s+like\s+[\'"]?(\d{3}/\d{2}R\d{2})[\'"]?',
            r'see\s+something\s+like\s+[\'"]?(\d{3}/\d{2}R\d{2})[\'"]?'
        ]
        
        # First check if this is just an example tire size
        is_example = False
        for pattern in example_patterns:
            if re.search(pattern, ai_response, re.IGNORECASE):
                is_example = True
                logger.info(f"🚫 SKIPPING example tire size in AI response")
                break
        
        # Only extract if it's not an example
        if not is_example:
            for pattern in tire_size_patterns:
                matches = re.findall(pattern, ai_response, re.IGNORECASE)
                if matches:
                    tire_size = matches[0]
                    # Store in tire_specs so AI knows we have this information
                    conversation_state.tire_specs['current_tire_size'] = tire_size
                    logger.info(f"🔧 EXTRACTED TIRE SIZE from AI response: {tire_size}")
                    
                    # Also store in researched_info for backup
                    vehicle_key = f"{conversation_state.vehicle_info.get('year', '')}_{conversation_state.vehicle_info.get('make', '')}_{conversation_state.vehicle_info.get('model', '')}".lower()
                    conversation_state.store_researched_info(f"{vehicle_key}_tire_size", tire_size)
                    
                    break
        
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
        
        # Get recommended model and web search determination from cost manager
        recommended_model = self.cost_manager.get_recommended_model(query_complexity, conversation_state)
        needs_web_search = self.cost_manager.strategy._needs_web_search(query_complexity, conversation_state)
        logger.info(f"🎯 COST MANAGER RECOMMENDATION: {recommended_model.value} for complexity: {query_complexity}")
        logger.info(f"🔍 Web search needed: {needs_web_search}")
        logger.info(f"💰 Budget remaining: ${self.cost_manager.get_remaining_budget(conversation_state):.4f}")
        
        # Web search indicator will be prepared after AI response generation
        
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
                function_documentation=self.function_parser.get_function_documentation(),
                needs_web_search=needs_web_search
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
            complexity_score += 2  # Increased from 1 - novice users need better AI
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
        
        # Check for confusion or need for clarification - BOOST complexity for better AI
        if any(term in user_lower for term in [
            'confused', 'not sure', 'don\'t understand', 'what do you mean',
            'can you explain', 'i don\'t know', 'help', 'don\'t know'
        ]):
            complexity_score += 3  # Increased from 2 - confused users need better AI
        
        # Check for form data indicating user chose "not sure" or similar help options
        if hasattr(conversation_state, 'form_data') and conversation_state.form_data:
            if (conversation_state.form_data.get('info_method') == 'not_sure' or 
                conversation_state.form_data.get('help_method') == "I don't know" or
                'need more specific help' in str(conversation_state.form_data.values())):
                complexity_score += 3  # Users needing guidance need better AI
        
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
        
        # 6. Information completeness analysis - MODIFIED LOGIC
        missing_info = []
        if not conversation_state.vehicle_info.get('make'):
            missing_info.append('vehicle_make')
        if not conversation_state.vehicle_info.get('model'):
            missing_info.append('vehicle_model')
        if not conversation_state.vehicle_info.get('year'):
            missing_info.append('vehicle_year')
        if not conversation_state.tire_specs.get('current_tire_size'):
            missing_info.append('tire_size')
        
        # If we're missing basic info AND user is struggling, use better AI
        if len(missing_info) >= 2 and complexity_score >= 3:
            # Don't reduce complexity - keep it high for better guidance
            pass
        elif len(missing_info) >= 2:
            # Only reduce if user isn't struggling
            complexity_score = max(1, complexity_score - 1)
        
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
        
        # Check if we have vehicle information that was extracted
        vehicle_info = conversation_state.vehicle_info
        has_vehicle_info = vehicle_info.get('make') and vehicle_info.get('model')
        
        # Rule-based fallback responses with vehicle context
        if has_vehicle_info:
            # We have vehicle info, acknowledge it and move forward
            make = vehicle_info.get('make', '')
            model = vehicle_info.get('model', '')
            year = vehicle_info.get('year', '')
            
            if year:
                vehicle_description = f"{year} {make} {model}"
            else:
                vehicle_description = f"{make} {model}"
            
            response = f"Great! I see you have a {vehicle_description}. Let me help you find the right tires for your vehicle."
            
            # Create a form to continue the conversation
            from agents.form_builder import FormBuilder
            form_builder = FormBuilder()
            
            # Ask for quantity needed if we don't have it
            if not conversation_state.tire_specs.get('quantity_needed'):
                fields_html = [
                    form_builder.create_radio_field(
                        name="quantity_needed",
                        label="How many tires do you need to replace?",
                        options=["All 4 tires", "2 tires (front or rear)", "1 tire (single replacement)"],
                        required=True
                    )
                ]
                
                fallback_form = form_builder.create_complete_form(
                    fields_html=fields_html,
                    conversation_text=response,
                    submit_text="Continue"
                )
                
                return {
                    "response": "",
                    "form_html": fallback_form,
                    "inline_guidance": "",
                    "cost_info": {"cost": 0.0, "model_used": "fallback_with_vehicle_info", "source": "fallback"},
                    "processing_time": 0.0,
                    "source": "fallback_with_form"
                }
            else:
                # Have vehicle and quantity, ask about driving patterns
                response += " What's your typical driving like?"
        else:
            # No vehicle info, ask for it
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