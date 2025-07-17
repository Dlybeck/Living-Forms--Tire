import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import re

from utils.state_manager import ConversationState, UserKnowledgeLevel
from database.tire_database import TireDatabase
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
            "ready_for_recommendations": conversation_state.is_ready_for_recommendations()
        }

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