"""
Base Agent Class
Provides common functionality for all specialized agents in the multi-agent system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from agents.ai_client import AIClient
from agents.cost_manager import CostManager, ModelType
from agents.function_call_parser import FunctionCallParser
from agents.form_builder import FormBuilder
# Removed conversation enums - simplified system
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all specialized agents
    Uses a single thinking model to generate both conversation and forms
    """
    
    def __init__(self, 
                 ai_client: AIClient,
                 cost_manager: CostManager,
                 form_builder: FormBuilder,
                 agent_name: str):
        self.ai_client = ai_client
        self.cost_manager = cost_manager
        self.form_builder = form_builder
        self.function_parser = FunctionCallParser()
        self.agent_name = agent_name
        
        logger.info(f"Initialized {agent_name}")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this specific agent"""
        pass
    
    @abstractmethod
    def get_agent_prompt(self) -> str:
        """Get the agent-specific prompt for this agent"""
        pass
    
    async def process_message(self, 
                            user_message: str, 
                            roadmap: Dict[str, Any],
                            conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message using a single thinking model approach:
        1. Use a single model to generate both conversation and form
        2. Parse the response to extract conversation text and form HTML
        3. Ensure we always have both conversation and form
        """
        try:
            # Use a single model for both conversation and form generation
            response = await self._generate_conversation_and_form(
                user_message, roadmap, conversation_context
            )
            
            # Assess task completion based on agent-specific criteria
            completion_assessment = await self._assess_task_completion(conversation_context)
            
            return {
                "response": response.get("response", ""),
                "conversation_text": response.get("conversation_text", ""),
                "form_html": response.get("form_html", ""),
                "inline_guidance": response.get("inline_guidance", None),
                "enhanced_notepad": conversation_context.get("enhanced_notepad", ""),
                "cost_info": {
                    "total_cost": response.get("cost", 0.0),
                    "model_used": response.get("model_used", "unknown")
                },
                "source": f"{self.agent_name}_single_model",
                # Agent identification
                "current_agent": self.agent_name,
                "agent_display_name": self._get_agent_display_name(),
                # Agent completion signaling
                "agent_complete": completion_assessment.get("is_complete", False),
                "completion_reason": completion_assessment.get("reason", "Continuing assistance"),
                "data_quality_score": completion_assessment.get("quality_score", 0.0),
                "missing_critical_data": completion_assessment.get("missing_data", []),
                "recommendation_readiness": completion_assessment.get("recommendation_readiness", False)
            }
        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _generate_conversation_and_form(self, 
                                            user_message: str,
                                            roadmap: Dict[str, Any],
                                            conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate both conversation and form using a single model"""
        
        # Determine if we need web search
        needs_web_search = self._needs_web_search(user_message, roadmap)
        
        # Use O4-mini for complex reasoning and detailed form generation
        model = ModelType.O4_MINI
        
        # Check if we can afford the model
        estimated_cost = self.cost_manager.estimate_cost(
            user_message + str(conversation_context),
            model
        )
        
        if not self.cost_manager.can_afford_operation("conversation", estimated_cost, {}):
            # Fallback to smaller model
            model = ModelType.GPT_4O_MINI
            logger.info(f"Using fallback model {model.value} for conversation due to cost constraints")
        else:
            logger.info(f"Using GPT-4.1 for conversation")
        
        try:
            # Transform basic ScribeAgent output into rich Control Headquarters scene
            enhanced_notepad = await self._create_control_headquarters_scene(roadmap, conversation_context)
            conversation_context["enhanced_notepad"] = enhanced_notepad
            
            # Add context about the current goal
            conversation_context["current_goal"] = "Find the right tires for the user's vehicle"
            conversation_context["current_step"] = conversation_context.get("current_step", "greeting")
            conversation_context["needs_form"] = True
            conversation_context["form_purpose"] = self._get_form_purpose(roadmap)
            
            # Log the context being sent to AI for debugging (only in development)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Context being sent to AI: {conversation_context}")
            
            # Generate response with function calls
            response = await self.ai_client.generate_response(
                user_message=user_message,
                conversation_context=conversation_context,
                model_type=model,
                response_format="function_calls_and_chat",
                function_documentation=self.function_parser.get_function_documentation(),
                needs_web_search=needs_web_search
            )
            
            # Track cost
            self.cost_manager.track_cost("conversation", response["cost"], roadmap)
            
            # Debug logging
            logger.info(f"AI generated response: {response['text'][:500]}...")
            
            # Parse function calls and extract conversation text and form HTML
            conversation_text, form_html = self.function_parser.parse_function_calls(response["text"])
            
            logger.info(f"Parsed conversation text: {conversation_text[:200]}...")
            logger.info(f"Form HTML generated: {form_html is not None}")
            
            # Ensure we always have a response - never return None or empty
            if not conversation_text or conversation_text.strip() == "":
                conversation_text = "I'm here to help you find the right tires. Let me ask you a few questions to get started."
            
            # Ensure we always have a form - create a fallback if needed
            if not form_html:
                logger.warning("No form HTML generated, creating fallback form")
                fallback_field = self.form_builder.create_textarea_field(
                    name="additional_notes",
                    label="Additional Thoughts: (Optional)",
                    required=False,
                    placeholder="Ask a question, add details, or tell me anything..."
                )
                form_html = self.form_builder.create_complete_form([fallback_field], conversation_text)
            
            # Return conversation text and form HTML separately - let frontend handle combination
            return {
                "response": conversation_text,  # Just the conversation text
                "conversation_text": conversation_text,
                "form_html": form_html,
                "model_used": response["model"],
                "cost": response["cost"]
            }
            
        except Exception as e:
            logger.error(f"Conversation generation failed: {str(e)}")
            # Create a fallback response that always works
            fallback_text = "I'm here to help you find the right tires. Let me ask you a few questions to get started."
            fallback_field = self.form_builder.create_textarea_field(
                name="additional_notes",
                label="Additional Thoughts: (Optional)",
                required=False,
                placeholder="Ask a question, add details, or tell me anything..."
            )
            fallback_form = self.form_builder.create_complete_form([fallback_field], fallback_text)
            
            return {
                "response": fallback_text,  # Just the conversation text
                "conversation_text": fallback_text,
                "form_html": fallback_form,
                "model_used": "fallback",
                "cost": 0.0
            }
    
    def _needs_web_search(self, user_message: str, roadmap: Dict[str, Any]) -> bool:
        """Determine if web search is needed"""
        # Override in subclasses for specific logic
        return False
    
    def _get_form_purpose(self, roadmap: Dict[str, Any]) -> str:
        """Get the purpose of form generation for this agent"""
        # Override in subclasses for specific logic
        return "collect_information"
    
    def _get_agent_display_name(self) -> str:
        """Get a user-friendly display name for this agent"""
        display_names = {
            "TireSizeAgent": "Tire Size Specialist",
            "DrivingInfoAgent": "Driving Pattern Analyst", 
            "PreferencesAgent": "Preference Advisor",
            "RecommendationAgent": "Tire Recommendation Expert",
            "ScribeAgent": "Conversation Manager"
        }
        return display_names.get(self.agent_name, self.agent_name)
    
    async def _assess_task_completion(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligent completion assessment based on agent expertise"""
        
        # Let each agent use its intelligence to decide when it's done
        # This replaces rigid systematic rules with expert judgment
        
        if self.agent_name == "TireSizeAgent":
            # Done when we know exactly what tires will fit and work
            important_data = conversation_context.get("important_data", {})
            has_vehicle_info = all(important_data.get(field) for field in ["vehicle_make", "vehicle_model", "vehicle_year"])
            has_tire_specs = important_data.get("tire_size") or important_data.get("vehicle_trim")
            
            is_complete = has_vehicle_info and has_tire_specs
            reason = "Vehicle and tire specifications complete" if is_complete else "Need more vehicle/tire information"
            
        elif self.agent_name == "DrivingInfoAgent":
            # Done when we can recommend objectively good tires
            important_data = conversation_context.get("important_data", {})
            has_driving_pattern = important_data.get("driving_pattern")
            has_climate = important_data.get("climate_considerations")
            has_mileage = important_data.get("mileage_per_year")
            
            is_complete = has_driving_pattern and has_climate and has_mileage
            reason = "Driving information sufficient for recommendations" if is_complete else "Need more driving context"
            
        elif self.agent_name == "PreferencesAgent":
            # Done when we know what the user is looking for
            important_data = conversation_context.get("important_data", {})
            has_performance_priorities = important_data.get("performance_priorities")
            has_tire_type = important_data.get("tire_type")
            
            is_complete = has_performance_priorities and has_tire_type
            reason = "User preferences understood" if is_complete else "Need more preference information"
            
        elif self.agent_name == "RecommendationAgent":
            # Never done until user is done
            is_complete = False
            reason = "Continuing to help user with recommendations"
            
        elif self.agent_name == "ComprehensiveTireAgent":
            # Never done until user is done - handles entire conversation
            is_complete = False
            reason = "Continuing comprehensive tire assistance"
            
        else:
            # Default: let the agent decide
            is_complete = False
            reason = "Agent-specific completion logic"
        
        return {
            "is_complete": is_complete,
            "reason": reason,
            "quality_score": 1.0 if is_complete else 0.0,
            "missing_data": [],
            "recommendation_readiness": is_complete
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "response": f"""
            <div style="background:#fff3cd;padding:15px;border-radius:8px;border:1px solid #ffeaa7;margin-bottom:15px;">
                <p style="margin:0;color:#856404;">I'm experiencing some technical difficulties. Please try again or let me know if you need help with something specific.</p>
            </div>
            """,
            "conversation_text": "I'm experiencing some technical difficulties. Please try again.",
            "form_html": "",
            "cost_info": {"total_cost": 0.0, "model_used": "error"},
            "source": f"{self.agent_name}_error",
            # Agent identification
            "current_agent": self.agent_name,
            "agent_display_name": self._get_agent_display_name(),
            # Agent completion signaling
            "agent_complete": False,
            "completion_reason": "Error occurred",
            "data_quality_score": 0.0,
            "missing_critical_data": ["error_occurred"],
            "recommendation_readiness": False
        }
    
    def update_roadmap_data(self, roadmap: Dict[str, Any], category: str, data: Any):
        """Update roadmap with new data"""
        # For now, just log the data update
        logger.info(f"Data update: {category} = {data}")
    
    async def _create_control_headquarters_scene(self, roadmap: Dict[str, Any], conversation_context: Dict[str, Any]) -> str:
        """Transform basic ScribeAgent output into rich Control Headquarters scene"""
        
        # Get the basic notepad from ScribeAgent
        basic_notepad = roadmap.get('ai_notepad', '')
        form_data = conversation_context.get('form_data', {})
        current_step = conversation_context.get('current_step', 'unknown')
        
        # Create the Control Headquarters scene prompt
        scene_prompt = f"""
You are creating a "Control Headquarters" scene for the Living Form Tire Sales Assistant, similar to the Inside Out movie's command center. This scene should be rich, emotional, and strategic.

BASIC INFORMATION FROM SCRIBE:
{basic_notepad}

CURRENT CONTEXT:
- Current Step: {current_step}
- Form Data: {form_data}
- User Message: {conversation_context.get('user_message', '')}

Create a Control Headquarters scene with the following structure:

# 🎬 Control Headquarters Scene

## 🎭 The Emotions' Debate
Create a lively debate between the emotions (Logic, Empathy, Urgency, Frustration, Curiosity, Joy, Caution) about the current situation. Each emotion should have a distinct perspective and personality.

## 🌟 Memory Wall
Show key memories and patterns from the conversation so far.

## 👤 User Profile Dashboard
Display the user's current state, known information, and emotional needs.

## 📊 Strategic Command Decision
Provide specific tactical guidance including:
- Mission Commander's Directive
- Target Agent (which agent should handle this)
- Tactical Approach (tone and method)
- Exact Action (what to do)
- Success Metrics (how to measure success)
- Contingency (what to do if it fails)

Make this scene dynamic, emotional, and strategically useful. The emotions should debate based on the actual conversation context and provide actionable intelligence.
"""
        
        try:
            # Generate the Control Headquarters scene using a smaller model for cost efficiency
            response = await self.ai_client.generate_response(
                user_message=scene_prompt,
                conversation_context={"current_step": "control_headquarters_creation"},
                model_type=ModelType.GPT_4O_MINI,  # Use smaller model for scene creation
                response_format="text"
            )
            
            enhanced_scene = response.get("text", "").strip()
            
            # Track cost
            self.cost_manager.track_cost("control_headquarters_creation", response["cost"], roadmap)
            
            logger.info(f"Created Control Headquarters scene: {enhanced_scene[:100]}...")
            return enhanced_scene
            
        except Exception as e:
            logger.error(f"Error creating Control Headquarters scene: {str(e)}")
            # Fallback to basic notepad if scene creation fails
            return basic_notepad 