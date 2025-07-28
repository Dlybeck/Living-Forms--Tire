"""
Simplified Coordinator using LangChain chain
Replaces the complex manual coordination with a simple LangChain-based approach
"""

from typing import Dict, Any, Optional
from core.tire_chain import TireAgentChain
from core.ai_client import AIClient, ModelType
from core.form_builder import FormBuilder
import logging

logger = logging.getLogger(__name__)

class SimplifiedCoordinator:
    """
    Simplified coordinator using LangChain chain
    """
    
    def __init__(self):
        self.ai_client = AIClient()
        self.form_builder = FormBuilder()
        
        # Create the tire agent chain with O4-mini
        o4_mini_model = self.ai_client.langchain_models.get('openai')
        if not o4_mini_model:
            raise ValueError("O4-mini model not available")
        
        self.tire_chain = TireAgentChain(o4_mini_model, self.form_builder)
        
        logger.info("SimplifiedCoordinator initialized with LangChain chain")
    
    async def process_message(self, user_message: str, session_id: str, 
                            form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message using the LangChain chain
        """
        try:
            logger.debug(f"Processing message for session {session_id}")
            
            # Process with the tire chain
            response = await self.tire_chain.process_message(
                user_message=user_message,
                session_id=session_id,
                form_data=form_data
            )
            
            # Add coordinator metadata
            response["coordinator_info"] = {
                "type": "simplified_langchain",
                "session_id": session_id
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SimplifiedCoordinator: {str(e)}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "form_html": "",
                "error": str(e),
                "coordinator_info": {
                    "type": "simplified_langchain",
                    "error": True
                }
            }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        """
        return self.tire_chain.get_session_info(session_id)
    
    async def clear_session(self, session_id: str):
        """
        Clear session
        """
        self.tire_chain.clear_session(session_id)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status
        """
        return {
            "coordinator_type": "simplified_langchain",
            "ai_client_status": "operational",
            "form_builder_status": "operational"
        } 