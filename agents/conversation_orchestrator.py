import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from utils.state_manager import ConversationState, ConversationStep, UserKnowledgeLevel, DataCategory
from database.tire_database import TireDatabase, VehicleInfo
from agents.cost_manager import CostManager, ModelType
from agents.ai_client import AIClient

logger = logging.getLogger(__name__)

class ConversationOrchestrator:
    """
    Orchestrates the living form conversation flow
    This is the main controller that manages the conversation state,
    determines what questions to ask, and coordinates between agents
    """
    
    def __init__(self, tire_database: TireDatabase, cost_manager: CostManager):
        self.tire_database = tire_database
        self.cost_manager = cost_manager
        self.ai_client = AIClient()
        
        # Cache for common responses
        self.response_cache = {}
        
        logger.info("Conversation orchestrator initialized")
    
    async def process_message(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Main entry point for processing user messages
        AI generates both conversational responses AND form elements together
        """
        start_time = datetime.now()
        
        try:
            # Step 0: Extract and update vehicle info from user message FIRST
            self._extract_and_update_vehicle_info(user_message, conversation_state)
            
            # Update user knowledge level based on message
            conversation_state.detect_user_knowledge_level(user_message)
            
            # Step 1: Always use AI to generate the complete response (conversation + forms)
            ai_response = await self._generate_ai_response(user_message, conversation_state)
            
            # Step 2: Extract form HTML from AI response if present
            form_html = self._extract_form_html(ai_response["response"])
            clean_response = self._clean_response_text(ai_response["response"])
            

            
            response_data = {
                "response": clean_response,
                "form_html": form_html,
                "inline_guidance": "",  # AI response includes guidance inline
                "cost_info": ai_response.get("cost_info", {"cost": ai_response.get("cost", 0.0), "model_used": ai_response.get("model_used", "ai"), "source": "ai"}),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "source": "ai_living_form"
            }
            
            # Add to conversation history
            conversation_state.add_interaction(
                user_message=user_message,
                ai_response=clean_response,
                cost=ai_response.get("cost", 0.0),
                model_used=ai_response.get("model_used", "ai")
            )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _is_question_or_clarification(self, user_message: str) -> bool:
        """Check if the user message is a question or clarification"""
        question_indicators = [
            "what", "how", "why", "when", "where", "which", "who",
            "?", "help", "explain", "clarify", "confused", "not sure",
            "don't know", "unsure", "mean", "understand"
        ]
        
        user_lower = user_message.lower()
        return any(indicator in user_lower for indicator in question_indicators)
    
    async def _generate_inline_guidance(self, user_message: str, conversation_state: ConversationState) -> str:
        """Generate inline guidance for forms (not chat responses)"""
        # Only use AI if there's a specific question or clarification needed
        if self._is_question_or_clarification(user_message):
            try:
                ai_response = await self._generate_ai_response(
                    f"User asked: {user_message}. Generate a brief, helpful response that can be shown as inline guidance in the form (not a chat message). Keep it under 2 sentences.",
                    conversation_state
                )
                return ai_response["response"]
            except Exception as e:
                logger.error(f"Error generating AI guidance: {str(e)}")
                return "I'm here to help with any questions you have!"
        
        return ""  # No inline guidance needed
    
    async def _handle_form_submission(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Handle form submissions with inline guidance only
        Forms are the primary interface - this is where most data collection happens
        """
        # Extract what was submitted from the form data
        vehicle_info = conversation_state.vehicle_info
        tire_preferences = conversation_state.tire_preferences
        form_data = conversation_state.form_data
        
        # Mark categories as completed based on what was submitted
        
        # Check if vehicle info is complete
        if vehicle_info.get('make') and vehicle_info.get('model') and vehicle_info.get('year'):
            conversation_state.mark_category_completed(DataCategory.VEHICLE_INFO)
        
        # Check if tire specs are complete
        if conversation_state.tire_specs.get('quantity_needed'):
            conversation_state.mark_category_completed(DataCategory.TIRE_SPECS)
        
        # Check if driving patterns are complete
        if conversation_state.driving_patterns:
            conversation_state.mark_category_completed(DataCategory.DRIVING_PATTERNS)
        
        # Check if budget preferences are complete
        if conversation_state.budget_preferences:
            conversation_state.mark_category_completed(DataCategory.BUDGET_PREFERENCES)
        
        # Check if current tire status is complete
        if conversation_state.current_tire_status:
            conversation_state.mark_category_completed(DataCategory.CURRENT_TIRE_STATUS)
        
        # Check if special considerations are complete
        if conversation_state.special_considerations:
            conversation_state.mark_category_completed(DataCategory.SPECIAL_CONSIDERATIONS)
        
        # Generate inline guidance for form submission acknowledgment
        inline_guidance = await self._generate_form_submission_guidance(form_data, conversation_state)
        
        # If we have complete vehicle info, try to find and store tire size
        has_complete_vehicle = (vehicle_info.get('make') and 
                               vehicle_info.get('model') and 
                               vehicle_info.get('year'))
        
        if has_complete_vehicle and not vehicle_info.get('current_tire_size'):
            vehicle_data = self.tire_database.find_vehicle_by_make_model_year(
                vehicle_info['make'], 
                vehicle_info['model'], 
                vehicle_info['year']
            )
            if vehicle_data:
                # Store the researched tire size
                tire_size_key = f"{vehicle_info['make']}_{vehicle_info['model']}_{vehicle_info['year']}_tire_size"
                conversation_state.store_researched_info(tire_size_key, vehicle_data.oem_tire_sizes[0])
                conversation_state.vehicle_info['current_tire_size'] = vehicle_data.oem_tire_sizes[0]
        
        # Always show the next form in the sequence
        form_html = self._generate_living_form(conversation_state)
        
        return {
            "response": "",  # No chat response
            "form_html": form_html,
            "inline_guidance": inline_guidance,
            "cost_info": {"cost": 0.0, "model_used": "form_only", "source": "form_interface"},
            "processing_time": 0.0,
            "source": "form_interface"
        }
    
    async def _generate_form_submission_guidance(self, form_data: Dict[str, Any], conversation_state: ConversationState) -> str:
        """This method is no longer needed - AI handles all responses now"""
        return ""

    async def _try_static_response(self, user_message: str, conversation_state: ConversationState) -> Optional[Dict[str, Any]]:
        """No more static responses - everything goes through AI for Living Form"""
        return None
    
    def _extract_and_update_vehicle_info(self, user_message: str, conversation_state: ConversationState):
        """Extract vehicle information from user message and update conversation state"""
        user_lower = user_message.lower()
        
        # Extract make
        makes = ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai', 'volkswagen', 'bmw', 'mercedes', 'audi']
        for make in makes:
            if make in user_lower:
                conversation_state.vehicle_info['make'] = make.title()
                break
        
        # Extract model (common models)
        models = {
            'kia': ['forte', 'soul', 'sportage', 'sorento', 'telluride', 'k5', 'rio'],
            'honda': ['civic', 'accord', 'cr-v', 'pilot', 'odyssey', 'fit'],
            'toyota': ['camry', 'corolla', 'rav4', 'highlander', 'sienna', 'prius'],
            'ford': ['f-150', 'escape', 'explorer', 'mustang', 'focus', 'fusion'],
            'chevrolet': ['silverado', 'equinox', 'tahoe', 'camaro', 'cruze', 'malibu']
        }
        
        current_make = conversation_state.vehicle_info.get('make', '').lower()
        if current_make in models:
            for model in models[current_make]:
                if model in user_lower:
                    conversation_state.vehicle_info['model'] = model.title()
                    break
        
        # Extract year (4-digit year)
        year_match = re.search(r'\b(19|20)\d{2}\b', user_message)
        if year_match:
            conversation_state.vehicle_info['year'] = year_match.group()
        
        # Extract tire size pattern
        tire_size_match = re.search(r'\b\d{3}/\d{2}R\d{2}\b', user_message.upper())
        if tire_size_match:
            conversation_state.tire_specs['current_tire_size'] = tire_size_match.group()
        

    
    def _is_vehicle_lookup_query(self, user_message: str) -> bool:
        """Check if the message is a simple vehicle lookup"""
        # Simple patterns that indicate vehicle information
        patterns = [
            "i have a",
            "i drive a",
            "my car is",
            "i own a",
            "for my",
            "on my",
            "in my",
            "with my"
        ]
        
        user_lower = user_message.lower()
        
        # Check for patterns
        if any(pattern in user_lower for pattern in patterns):
            return True
            
        # Check if message contains vehicle make/model words
        common_makes = [
            "honda", "toyota", "ford", "chevrolet", "chevy", "nissan", "mazda", 
            "subaru", "volkswagen", "vw", "bmw", "mercedes", "audi", "lexus",
            "acura", "infiniti", "cadillac", "buick", "gmc", "ram", "dodge",
            "chrysler", "jeep", "kia", "hyundai", "genesis", "volvo", "mitsubishi"
        ]
        
        # If the message contains a vehicle make and words like "tire" or "looking", treat as vehicle lookup
        if any(make in user_lower for make in common_makes) and any(word in user_lower for word in ["tire", "looking", "need", "want"]):
            return True
            
        return False
    
    def _extract_vehicle_from_message(self, message: str) -> tuple:
        """Extract make, model, year from message"""
        # This is a simplified extraction - in production, use NLP
        words = message.lower().split()
        
        make = None
        model = None
        year = None
        
        # Look for year (4-digit number)
        for word in words:
            if word.isdigit() and len(word) == 4:
                year_int = int(word)
                if 1990 <= year_int <= 2025:
                    year = year_int
                    break
        
        # Expanded list of common makes and models
        common_makes = [
            "honda", "toyota", "ford", "chevrolet", "chevy", "nissan", "mazda", 
            "subaru", "volkswagen", "vw", "bmw", "mercedes", "audi", "lexus",
            "acura", "infiniti", "cadillac", "buick", "gmc", "ram", "dodge",
            "chrysler", "jeep", "kia", "hyundai", "genesis", "volvo", "mitsubishi"
        ]
        
        common_models = [
            "accord", "camry", "civic", "corolla", "f-150", "silverado", "altima", 
            "sentra", "forte", "optima", "sonata", "elantra", "tucson", "santa fe",
            "crv", "rav4", "highlander", "pilot", "explorer", "escape", "focus",
            "mustang", "impala", "malibu", "cruze", "equinox", "traverse"
        ]
        
        # Look for make and model in the message
        for word in words:
            clean_word = word.strip('.,!?;:')
            if clean_word in common_makes:
                make = clean_word.title()
            elif clean_word in common_models:
                model = clean_word.title()
        
        return make, model, year
    
    def _extract_vehicle_info(self, conversation_state: ConversationState) -> Optional[VehicleInfo]:
        """Extract vehicle info from conversation state"""
        vehicle_data = conversation_state.vehicle_info
        
        if all(key in vehicle_data for key in ["make", "model", "year"]):
            return self.tire_database.find_vehicle_by_make_model_year(
                vehicle_data["make"],
                vehicle_data["model"],
                vehicle_data["year"]
            )
        
        return None
    
    def _format_static_recommendations(self, recommendations: List, conversation_state: ConversationState) -> str:
        """Format tire recommendations for static response"""
        response_parts = []
        
        if conversation_state.user_knowledge_level == UserKnowledgeLevel.NOVICE:
            response_parts.append("Great! I found some excellent tire options for you:")
        elif conversation_state.user_knowledge_level == UserKnowledgeLevel.EXPERT:
            response_parts.append("Based on your vehicle specs, here are the top recommendations:")
        else:
            response_parts.append("Here are my top 3 tire recommendations for your vehicle:")
        
        for i, rec in enumerate(recommendations[:3], 1):
            response_parts.append(f"""
            **{i}. {rec.brand} {rec.model}** ({rec.size})
            • Price: ${rec.price:.0f}
            • Type: {rec.type.title()}
            • Best for: {', '.join(rec.best_for)}
            • Why: {rec.pros[0] if rec.pros else 'Great overall tire'}
            """)
        
        response_parts.append("\nWould you like more details about any of these options, or do you have questions about installation?")
        
        return "\n".join(response_parts)
    
    def _format_vehicle_info_response(self, vehicle_info: VehicleInfo, conversation_state: ConversationState) -> str:
        """Format vehicle information response"""
        if conversation_state.user_knowledge_level == UserKnowledgeLevel.NOVICE:
            return f"""
            Perfect! I found your {vehicle_info.make} {vehicle_info.model}. 
            
            Your car typically uses these tire sizes:
            • {', '.join(vehicle_info.oem_tire_sizes)}
            
            To give you the best recommendations, I'd love to know:
            • What's your budget range?
            • How do you mainly use your car (daily driving, highway, etc.)?
            • Any specific preferences or concerns?
            """
        else:
            return f"""
            Found your {vehicle_info.make} {vehicle_info.model} ({vehicle_info.year_range}).
            
            **OEM Tire Sizes:** {', '.join(vehicle_info.oem_tire_sizes)}
            **Alternative Sizes:** {', '.join(vehicle_info.alternative_sizes)}
            **OEM Brands:** {', '.join(vehicle_info.oem_brands)}
            
            What's your budget and usage pattern?
            """
    
    async def _generate_ai_response(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Generate AI response using the most appropriate model
        """
        # Determine query complexity
        query_complexity = self._analyze_query_complexity(user_message, conversation_state)
        
        # Get recommended model from cost manager
        recommended_model = self.cost_manager.get_recommended_model(query_complexity, conversation_state)
        
        # Check if we can afford this operation
        estimated_cost = self.cost_manager.estimate_cost(
            user_message + str(conversation_state.get_conversation_context()),
            recommended_model
        )
        
        if not self.cost_manager.can_afford_operation("ai_response", estimated_cost, conversation_state):
            # Use fallback response
            return self._generate_fallback_response(user_message, conversation_state)
        
        # Generate AI response
        try:
            response = await self.ai_client.generate_response(
                user_message=user_message,
                conversation_context=conversation_state.get_conversation_context(),
                model_type=recommended_model,
                response_format="living_form"
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
        """Analyze the complexity of the user query"""
        user_lower = user_message.lower()
        
        # High complexity indicators
        high_complexity_indicators = [
            "compare", "difference", "vs", "versus", "better", "worse",
            "technical", "specification", "performance", "engineering",
            "why", "how", "explain", "detail", "complex"
        ]
        
        # Low complexity indicators
        low_complexity_indicators = [
            "yes", "no", "ok", "sure", "thanks", "hello", "hi",
            "price", "cost", "budget", "cheap", "expensive"
        ]
        
        # Check for high complexity
        if any(indicator in user_lower for indicator in high_complexity_indicators):
            return "high"
        
        # Check for low complexity
        if any(indicator in user_lower for indicator in low_complexity_indicators):
            return "low"
        
        # Check conversation context
        if len(conversation_state.conversation_history) > 3:
            return "medium"  # Longer conversations might need more context
        
        return "medium"  # Default
    
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
    
    def _generate_living_form(self, conversation_state: ConversationState) -> Optional[str]:
        """No longer needed - AI generates forms embedded in responses"""
        return "" 

    def _check_response_cache(self, user_message: str, conversation_state: ConversationState) -> Optional[Dict[str, Any]]:
        """Check if we have a cached response for this query"""
        # Create cache key based on message and relevant state
        cache_key = self._create_cache_key(user_message, conversation_state)
        
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            logger.info(f"Cache hit for query: {user_message[:50]}...")
            return cached_response
        
        return None
    
    def _create_cache_key(self, user_message: str, conversation_state: ConversationState) -> str:
        """Create a cache key for the response"""
        # Normalize message
        normalized_message = user_message.lower().strip()
        
        # Include relevant state information
        state_info = f"{conversation_state.current_step.value}_{conversation_state.user_knowledge_level.value}"
        
        # Include vehicle info if available
        if conversation_state.vehicle_info:
            vehicle_key = f"{conversation_state.vehicle_info.get('make', '')}_{conversation_state.vehicle_info.get('model', '')}"
            state_info += f"_{vehicle_key}"
        
        return f"{normalized_message}_{state_info}"
    
    def _cache_response(self, user_message: str, conversation_state: ConversationState, response_data: Dict[str, Any]):
        """Cache the response for future use"""
        cache_key = self._create_cache_key(user_message, conversation_state)
        
        # Only cache if it was an AI response (not static or fallback)
        if response_data["cost_info"]["source"] == "ai":
            self.response_cache[cache_key] = response_data
            logger.info(f"Cached response for: {user_message[:50]}...")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "response": "I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
            "form_html": None,
            "inline_guidance": "",
            "cost_info": {"cost": 0.0, "model_used": "error_handler", "source": "error"},
            "processing_time": 0.0,
            "source": "error"
        }
    
    def get_conversation_summary(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Get a summary of the conversation for debugging/monitoring"""
        return {
            "session_id": conversation_state.session_id,
            "current_step": conversation_state.current_step.value,
            "user_knowledge_level": conversation_state.user_knowledge_level.value,
            "total_interactions": len(conversation_state.conversation_history),
            "total_cost": conversation_state.total_cost,
            "vehicle_info_complete": bool(conversation_state.vehicle_info.get("make") and 
                                         conversation_state.vehicle_info.get("model") and 
                                         conversation_state.vehicle_info.get("year")),
            "ready_for_recommendations": conversation_state.is_ready_for_recommendations(),
            "cache_size": len(self.response_cache)
        } 

    def _needs_more_info_for_chat_response(self, user_message: str, conversation_state: ConversationState) -> bool:
        """Determine if we need more info to answer a chat question"""
        user_lower = user_message.lower()
        
        # Questions that need vehicle info to answer
        vehicle_dependent_questions = [
            "recommend", "suggest", "best tire", "what tire", "which tire",
            "price", "cost", "how much", "budget", "afford"
        ]
        
        # Questions that don't need additional info
        general_questions = [
            "what does", "explain", "help", "how to", "where to find",
            "difference", "compare", "why", "when", "how often"
        ]
        
        # If it's a vehicle-dependent question and we don't have complete vehicle info
        if any(phrase in user_lower for phrase in vehicle_dependent_questions):
            has_complete_vehicle = (conversation_state.vehicle_info.get('make') and 
                                   conversation_state.vehicle_info.get('model') and 
                                   conversation_state.vehicle_info.get('year'))
            return not has_complete_vehicle
        
        # If it's a general question, we probably don't need more info
        if any(phrase in user_lower for phrase in general_questions):
            return False
        
        # Default: show form if we're missing basic info
        return not conversation_state.is_ready_for_recommendations() 

    def _extract_form_html(self, ai_response: str) -> str:
        """Extract form HTML from AI response"""
        import re
        
        # Look for form tags in the AI response
        form_match = re.search(r'<form[^>]*>.*?</form>', ai_response, re.DOTALL | re.IGNORECASE)
        if form_match:
            return form_match.group(0)
        
        # If no complete form found, but there are form elements, wrap them
        if any(tag in ai_response.lower() for tag in ['<input', '<textarea', '<select', '<button']):
            # Extract form elements and wrap them
            form_elements = re.findall(r'<(?:input|textarea|select|button)[^>]*(?:>.*?</(?:textarea|select|button)>|>)', ai_response, re.DOTALL | re.IGNORECASE)
            if form_elements:
                form_html = '<form class="living-form ai-generated">'
                form_html += '<div class="form-body">'
                form_html += ''.join(form_elements)
                form_html += '</div>'
                form_html += '<div class="form-actions"><button type="submit" class="btn-primary">Continue</button></div>'
                form_html += '</form>'
                return form_html
        
        return ""

    def _clean_response_text(self, ai_response: str) -> str:
        """Remove form HTML from AI response to get clean text"""
        import re
        
        # Remove form tags and their contents
        cleaned = re.sub(r'<form[^>]*>.*?</form>', '', ai_response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove standalone form elements
        cleaned = re.sub(r'<(?:input|textarea|select|button)[^>]*(?:>.*?</(?:textarea|select|button)>|>)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned 