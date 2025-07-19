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
from utils.conversation_roadmap import ConversationRoadmap, ConversationStep, DataCategory
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
                            roadmap: ConversationRoadmap,
                            conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message using a single thinking model approach:
        1. Use a single model to generate both conversation and form
        2. Parse the response to extract conversation text and form HTML
        3. Ensure we always have both conversation and form
        """
        try:
            # Add conversation event for user message
            roadmap.add_conversation_event("user_message", {
                "agent": self.agent_name,
                "message_length": len(user_message),
                "has_form_data": bool(conversation_context.get("form_data"))
            })
            
            # Use a single model for both conversation and form generation
            response = await self._generate_conversation_and_form(
                user_message, roadmap, conversation_context
            )
            
            # Add conversation event for AI response
            roadmap.add_conversation_event("ai_response", {
                "agent": self.agent_name,
                "response_length": len(response.get("response", "")),
                "has_form": bool(response.get("form_html")),
                "model_used": response.get("model_used", "unknown")
            })
            
            return {
                "response": response.get("response", ""),
                "conversation_text": response.get("conversation_text", ""),
                "form_html": response.get("form_html", ""),
                "inline_guidance": response.get("inline_guidance", None),
                "cost_info": {
                    "total_cost": response.get("cost", 0.0),
                    "model_used": response.get("model_used", "unknown")
                },
                "source": f"{self.agent_name}_single_model"
            }
        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _generate_conversation_and_form(self, 
                                            user_message: str,
                                            roadmap: ConversationRoadmap,
                                            conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate both conversation and form using a single model"""
        
        # Determine if we need web search
        needs_web_search = self._needs_web_search(user_message, roadmap)
        
        # Use GPT-4.1 for better responses
        model = ModelType.GPT_4_1_MINI
        
        # Check if we can afford the model
        estimated_cost = self.cost_manager.estimate_cost(
            user_message + str(conversation_context),
            model
        )
        
        if not self.cost_manager.can_afford_operation("conversation", estimated_cost, roadmap):
            # Fallback to smaller model
            model = ModelType.GPT_4O_MINI
            logger.info(f"Using fallback model {model.value} for conversation due to cost constraints")
        else:
            logger.info(f"Using GPT-4.1 for conversation")
        
        try:
            # Add context about the current goal
            conversation_context["current_goal"] = roadmap.get_current_goal().description
            conversation_context["current_step"] = roadmap.current_step.value
            conversation_context["needs_form"] = True
            conversation_context["form_purpose"] = self._get_form_purpose(roadmap)
            
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
    
    def _needs_web_search(self, user_message: str, roadmap: ConversationRoadmap) -> bool:
        """Determine if web search is needed"""
        # Override in subclasses for specific logic
        return False
    
    def _get_form_purpose(self, roadmap: ConversationRoadmap) -> str:
        """Get the purpose of form generation for this agent"""
        # Override in subclasses for specific logic
        return "collect_information"
    
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
            "source": f"{self.agent_name}_error"
        }
    
    def update_roadmap_data(self, roadmap: ConversationRoadmap, category: DataCategory, data: Any):
        """Update roadmap with new data"""
        roadmap.update_shared_data(category, data)
        roadmap.add_conversation_event(
            "data_updated",
            {"category": category.value, "agent": self.agent_name, "data": data}
        ) 