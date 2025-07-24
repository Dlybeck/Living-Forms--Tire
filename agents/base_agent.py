"""
Simplified Base Agent Class
Provides common functionality for the dual-agent system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from agents.ai_client import AIClient
from agents.cost_manager import CostManager, ModelType
from agents.function_call_parser import FunctionCallParser
from agents.form_builder import FormBuilder
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Simplified base class for agents
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
        Process a message and generate response with form
        """
        try:
            # Generate conversation and form
            response = await self._generate_response(user_message, roadmap, conversation_context)
            
            return {
                "response": response.get("response", ""),
                "conversation_text": response.get("conversation_text", ""),
                "form_html": response.get("form_html", ""),
                "enhanced_notepad": conversation_context.get("enhanced_notepad", ""),
                "cost_info": {
                    "total_cost": response.get("cost", 0.0),
                    "model_used": response.get("model_used", "unknown")
                },
                "current_agent": self.agent_name,
                "agent_display_name": self._get_agent_display_name()
            }
        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _generate_response(self, 
                               user_message: str,
                               roadmap: Dict[str, Any],
                               conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response with conversation and form"""
        
        # Use GPT-4o-mini for cost efficiency
        model = ModelType.GPT_4O_MINI
        
        try:
            # Add context
            conversation_context["current_goal"] = "Find the right tires for the user's vehicle"
            conversation_context["needs_form"] = True
            
            # Generate response
            response = await self.ai_client.generate_response(
                user_message=user_message,
                conversation_context=conversation_context,
                model_type=model,
                agent_prompt=self.get_agent_prompt(),
                response_format="function_calls_and_chat",
                function_documentation=self.function_parser.get_function_documentation()
            )
            
            # Track cost
            self.cost_manager.track_cost("conversation", response["cost"], roadmap)
            
            # Parse response for conversation text and form
            conversation_text, form_html = self.function_parser.parse_function_calls(response["text"])
            
            return {
                "response": conversation_text,
                "conversation_text": conversation_text,
                "form_html": form_html,
                "cost": response["cost"],
                "model_used": model.value
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Return a proper error response instead of raising
            return {
                "response": f"I'm experiencing some technical difficulties: {str(e)}",
                "conversation_text": f"I'm experiencing some technical difficulties: {str(e)}",
                "form_html": "",
                "cost": 0.0,
                "model_used": "error"
            }
    
    def _get_agent_display_name(self) -> str:
        """Get user-friendly agent name"""
        if self.agent_name == "UnifiedTireAgent":
            return "Tire Sales Assistant"
        else:
            return self.agent_name
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "response": "I'm experiencing some technical difficulties. Please try again.",
            "conversation_text": "I'm experiencing some technical difficulties. Please try again.",
            "form_html": "",
            "cost_info": {"total_cost": 0.0, "model_used": "error"},
            "current_agent": self.agent_name,
            "agent_display_name": self._get_agent_display_name()
        } 