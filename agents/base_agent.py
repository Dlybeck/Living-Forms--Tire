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
    Implements the two-model approach: large model for reasoning, small model for forms
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
        Process a message using the two-model approach:
        1. Large model for reasoning and conversation (hidden, for debug only)
        2. Small model for both chat and form generation (user-facing)
        """
        try:
            # Step 1: Use large model for reasoning and conversation (hidden)
            reasoning_response = await self._generate_reasoning_response(
                user_message, roadmap, conversation_context
            )
            # Step 2: Use small model for both chat and form generation
            form_response = await self._generate_form_and_chat_response(
                user_message, roadmap, conversation_context, reasoning_response
            )
            # Step 3: Only show the mini model's output to the user; large model is for debug only
            return {
                "response": form_response.get("response", ""),
                "conversation_text": reasoning_response.get('conversation_text', ''),  # for debug
                "form_html": form_response.get("form_html", ""),
                "inline_guidance": form_response.get("inline_guidance", None),
                "cost_info": {
                    "reasoning_cost": reasoning_response.get("cost", 0.0),
                    "form_cost": form_response.get("cost", 0.0),
                    "total_cost": reasoning_response.get("cost", 0.0) + form_response.get("cost", 0.0),
                    "reasoning_model": reasoning_response.get("model_used", "unknown"),
                    "form_model": form_response.get("model_used", "none")
                },
                "source": f"{self.agent_name}_two_model"
            }
        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _generate_reasoning_response(self, 
                                         user_message: str,
                                         roadmap: ConversationRoadmap,
                                         conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using large model for reasoning"""
        
        # Determine if we need web search
        needs_web_search = self._needs_web_search(user_message, roadmap)
        
        # Use large model (GPT-4o-mini) for reasoning
        reasoning_model = ModelType.GPT_4O_MINI
        
        # Check if we can afford the large model
        estimated_cost = self.cost_manager.estimate_cost(
            user_message + str(conversation_context),
            reasoning_model
        )
        
        if not self.cost_manager.can_afford_operation("reasoning", estimated_cost, roadmap):
            # Fallback to smaller model
            reasoning_model = ModelType.GPT_4_1_MINI
            logger.info(f"Using fallback model {reasoning_model.value} for reasoning")
        
        try:
            response = await self.ai_client.generate_response(
                user_message=user_message,
                conversation_context=conversation_context,
                model_type=reasoning_model,
                response_format="text",  # Just conversation, no function calls
                needs_web_search=needs_web_search
            )
            
            # Track cost
            self.cost_manager.track_cost("reasoning", response["cost"], roadmap)
            
            return {
                "conversation_text": response["text"],
                "model_used": response["model"],
                "cost": response["cost"],
                "source": "reasoning"
            }
            
        except Exception as e:
            logger.error(f"Reasoning generation failed: {str(e)}")
            return {
                "conversation_text": "I'm having trouble processing that right now. Let me help you with basic information.",
                "model_used": "fallback",
                "cost": 0.0,
                "source": "fallback"
            }
    
    async def _generate_form_and_chat_response(self,
                                    user_message: str,
                                    roadmap: ConversationRoadmap,
                                    conversation_context: Dict[str, Any],
                                    reasoning_response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate both chat and form using the upgraded mini model (GPT-4o-mini), using the large model's output as context"""
        # Use GPT-4o-mini for both chat and form
        form_model = ModelType.GPT_4O_MINI
        # Check if we can afford the form generation
        estimated_cost = self.cost_manager.estimate_cost(
            user_message + str(conversation_context),
            form_model
        )
        if not self.cost_manager.can_afford_operation("form_generation", estimated_cost, roadmap):
            logger.info("Skipping form generation due to budget constraints")
            return {"response": "", "form_html": "", "model_used": "skipped"}
        try:
            # Add the large model's output to the context for the mini model
            form_context = conversation_context.copy()
            form_context["reasoning_text"] = reasoning_response.get("conversation_text", "")
            form_context["needs_form"] = True
            form_context["form_purpose"] = self._get_form_purpose(roadmap)
            # Prompt the upgraded model to generate both chat and form
            response = await self.ai_client.generate_response(
                user_message=user_message,
                conversation_context=form_context,
                model_type=form_model,
                response_format="function_calls_and_chat",
                function_documentation=self.function_parser.get_function_documentation(),
                needs_web_search=False
            )
            self.cost_manager.track_cost("form_generation", response["cost"], roadmap)
            # Parse function calls and extract chat and form
            conversation_text, form_html = self.function_parser.parse_function_calls(response["text"])
            
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
            
            # Combine conversation text and form HTML into a single response
            combined_response = f"<div style='margin-bottom:18px'>{conversation_text}</div>{form_html}"
            
            return {
                "response": combined_response,
                "conversation_text": conversation_text,
                "form_html": form_html,
                "model_used": response["model"],
                "cost": response["cost"]
            }
        except Exception as e:
            logger.error(f"Form generation failed: {str(e)}")
            # Create a fallback response that always works
            fallback_text = "I'm here to help you find the right tires. Let me ask you a few questions to get started."
            fallback_field = self.form_builder.create_textarea_field(
                name="additional_notes",
                label="Additional Thoughts: (Optional)",
                required=False,
                placeholder="Ask a question, add details, or tell me anything..."
            )
            fallback_form = self.form_builder.create_complete_form([fallback_field], fallback_text)
            fallback_response = f"<div style='margin-bottom:18px'>{fallback_text}</div>{fallback_form}"
            
            return {
                "response": fallback_response,
                "conversation_text": fallback_text,
                "form_html": fallback_form,
                "model_used": "fallback",
                "cost": 0.0
            }
    
    def _combine_responses(self, 
                          reasoning_response: Dict[str, Any],
                          form_response: Dict[str, Any]) -> Dict[str, Any]:
        """Combine reasoning and form responses"""
        # Only show the form HTML in the main response; conversational text is for debug only
        combined_html = form_response.get("form_html", "")
        return {
            "response": combined_html,
            "conversation_text": reasoning_response.get('conversation_text', ''),
            "form_html": form_response.get("form_html", ""),
            "cost_info": {
                "reasoning_cost": reasoning_response.get("cost", 0.0),
                "form_cost": form_response.get("cost", 0.0),
                "total_cost": reasoning_response.get("cost", 0.0) + form_response.get("cost", 0.0),
                "reasoning_model": reasoning_response.get("model_used", "unknown"),
                "form_model": form_response.get("model_used", "none")
            },
            "source": f"{self.agent_name}_two_model"
        }
    
    def _needs_web_search(self, user_message: str, roadmap: ConversationRoadmap) -> bool:
        """Determine if web search is needed"""
        # Override in subclasses for specific logic
        return False
    
    def _needs_form_generation(self, 
                              user_message: str, 
                              roadmap: ConversationRoadmap,
                              reasoning_response: Dict[str, Any]) -> bool:
        """Determine if form generation is needed"""
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
            "cost_info": {"total_cost": 0.0, "reasoning_model": "error", "form_model": "none"},
            "source": f"{self.agent_name}_error"
        }
    
    def update_roadmap_data(self, roadmap: ConversationRoadmap, category: DataCategory, data: Any):
        """Update roadmap with new data"""
        roadmap.update_shared_data(category, data)
        roadmap.add_conversation_event(
            "data_updated",
            {"category": category.value, "agent": self.agent_name, "data": data}
        ) 