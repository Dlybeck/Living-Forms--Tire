"""
Graph Coordinator using LangGraph workflow
Uses step-by-step processing with research capabilities
"""

from typing import Dict, Any, Optional
from core.tire_graph import TireRecommendationGraph
from core.ai_client import AIClient, ModelType
from core.form_builder import FormBuilder
import logging

logger = logging.getLogger(__name__)

class GraphCoordinator:
    """
    Coordinator using LangGraph workflow for step-by-step processing
    """
    
    def __init__(self, use_claude: bool = True):
        self.ai_client = AIClient()
        self.form_builder = FormBuilder()
        
        # Choose model - Claude Sonnet 3.5 for step-by-step processing
        if use_claude and self.ai_client.api_keys['anthropic']:
            model = self.ai_client.langchain_models.get('anthropic')
            logger.info("Using Claude Sonnet 3.5 for graph workflow")
        else:
            # Fallback to O4-mini
            model = self.ai_client.langchain_models.get('openai')
            logger.info("Using O4-mini for graph workflow")
        
        if not model:
            raise ValueError("No suitable model available")
        
        # Create the graph workflow
        self.tire_graph = TireRecommendationGraph(model, self.form_builder)
        
        logger.info("GraphCoordinator initialized with LangGraph workflow")
    
    async def process_message(self, user_message: str, session_id: str, 
                            form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message using the LangGraph workflow
        """
        try:
            logger.debug(f"Processing message for session {session_id} with graph workflow")
            
            # Process with the tire graph
            response = await self.tire_graph.process_message(
                user_message=user_message,
                session_id=session_id,
                form_data=form_data
            )
            
            # Add coordinator metadata
            response["coordinator_info"] = {
                "type": "langgraph_workflow",
                "session_id": session_id,
                "workflow_steps": ["analyze", "plan", "research", "synthesize"]
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in GraphCoordinator: {str(e)}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "form_html": "",
                "error": str(e),
                "coordinator_info": {
                    "type": "langgraph_workflow",
                    "error": True
                }
            }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        """
        return {
            "session_id": session_id,
            "coordinator_type": "langgraph_workflow",
            "workflow_available": True
        }
    
    async def clear_session(self, session_id: str):
        """
        Clear session (graph doesn't maintain persistent state)
        """
        logger.debug(f"Clearing session {session_id} (graph workflow)")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status
        """
        return {
            "coordinator_type": "langgraph_workflow",
            "ai_client_status": "operational",
            "form_builder_status": "operational",
            "graph_workflow_status": "operational",
            "research_tools_available": True
        }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get information about the workflow
        """
        return {
            "workflow_steps": [
                "analyze_information",
                "plan_research", 
                "execute_research",
                "synthesize_response"
            ],
            "available_tools": self.tire_graph.tire_tools.get_tool_names(),
            "model_type": "claude_sonnet_3_5" if self.ai_client.api_keys['anthropic'] else "o4_mini"
        } 