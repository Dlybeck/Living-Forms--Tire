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
            # Step 0: Extract and update vehicle info from user message FIRST
            self._extract_and_update_vehicle_info(user_message, conversation_state)
            
            # Update user knowledge level based on message
            conversation_state.detect_user_knowledge_level(user_message)
            
            # Step 1: Generate AI response with function call instructions
            ai_response = await self._generate_ai_response_with_functions(user_message, conversation_state)
            
            # Step 2: Parse function calls and generate forms
            conversation_text, form_html = self.function_parser.parse_function_calls(ai_response["response"])
            
            # Step 3: Determine response format
            if form_html:
                # AI created a form using function calls
                response_data = {
                    "response": "",  # No separate text response
                    "form_html": form_html,
                    "inline_guidance": "",
                    "cost_info": ai_response.get("cost_info", {"cost": ai_response.get("cost", 0.0), "model_used": ai_response.get("model_used", "ai"), "source": "ai"}),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "function_based_form"
                }
            else:
                # AI provided conversational response only
                response_data = {
                    "response": conversation_text,
                    "form_html": "",
                    "inline_guidance": "",
                    "cost_info": ai_response.get("cost_info", {"cost": ai_response.get("cost", 0.0), "model_used": ai_response.get("model_used", "ai"), "source": "ai"}),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "conversation_only"
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
        
        # Extract make
        makes = ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai', 'volkswagen', 'bmw', 'mercedes', 'audi']
        for make in makes:
            if make in user_lower:
                conversation_state.vehicle_info['make'] = make.title()
                logger.info(f"Extracted vehicle make: {make.title()}")
                break
        
        # Extract model (common models) with fact checking
        models = {
            'kia': ['forte', 'soul', 'sportage', 'sorento', 'telluride', 'k5', 'rio'],
            'honda': ['civic', 'accord', 'cr-v', 'pilot', 'odyssey', 'fit'],
            'toyota': ['camry', 'corolla', 'rav4', 'highlander', 'sienna', 'prius'],
            'ford': ['f-150', 'escape', 'explorer', 'mustang', 'focus', 'fusion'],
            'chevrolet': ['silverado', 'equinox', 'tahoe', 'camaro', 'cruze', 'malibu']
        }
        
        # Let the AI handle fact checking - don't pre-determine what's wrong
        # Just extract what we can and let the AI be smart about it
        
        current_make = conversation_state.vehicle_info.get('make', '').lower()
        if current_make in models:
            for model in models[current_make]:
                if model in user_lower:
                    conversation_state.vehicle_info['model'] = model.title()
                    logger.info(f"Extracted vehicle model: {model.title()}")
                    break
        
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
    
    async def _generate_ai_response_with_functions(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Generate AI response with function call instructions
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
        
        # Generate AI response with function call instructions
        try:
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