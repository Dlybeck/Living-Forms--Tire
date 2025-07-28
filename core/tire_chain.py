"""
Tire Agent Chain using LangChain components
Replaces manual prompt building with LangChain chains
"""

from typing import Dict, Any, Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLLM
from langchain_core.runnables import RunnableSequence
from langchain.memory import ConversationBufferWindowMemory
from core.memory_manager import LangChainMemoryManager
from core.output_parser import LangChainOutputParser
from core.form_builder import FormBuilder
import logging

logger = logging.getLogger(__name__)

class TireAgentChain:
    """
    LangChain chain for the tire agent
    """
    
    def __init__(self, llm: BaseLLM, form_builder: FormBuilder):
        self.llm = llm
        self.form_builder = form_builder
        self.memory_manager = LangChainMemoryManager()
        self.output_parser = LangChainOutputParser()
        
        # Create the prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["chat_history", "user_message", "form_data", "current_step", "function_docs", "parser_instructions", "chat_history_count", "agent_prompt"],
            template="""
            {agent_prompt}

            Current AI Notepad:
            {chat_history}

            User Message: {user_message}

            Form Data: {form_data}

            Conversation Context:
            - Current Step: {current_step}
            - Conversation History: {chat_history_count} interactions

            Function Documentation:
            {function_docs}

            {parser_instructions}

            Please complete your internal thinking process and generate your response.
            """
        )
        
        # Create the chain using RunnableSequence (modern approach)
        self.chain = self.prompt_template | self.llm
    
    async def process_message(self, user_message: str, session_id: str, 
                            form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message using the LangChain chain
        """
        try:
            # Get memory for this session
            memory = self.memory_manager.get_memory(session_id)
            memory_vars = memory.load_memory_variables({})
            
            # Prepare input variables
            input_vars = {
                "chat_history": memory_vars.get("chat_history", ""),
                "user_message": user_message,
                "form_data": form_data or {},
                "current_step": "tire_recommendation",
                "function_docs": self.form_builder.get_function_documentation(),
                "parser_instructions": self.output_parser.get_parser_instructions(),
                "chat_history_count": len(memory.chat_memory.messages) // 2,
                "agent_prompt": self._get_agent_prompt()
            }
            
            # Run the chain
            logger.debug(f"Running chain with input: {input_vars}")
            response = await self.chain.ainvoke(input_vars)
            
            # Parse the response - LangChain returns AIMessage objects
            response_text = response.content if hasattr(response, 'content') else str(response)
            parsed = self.output_parser.parse_response(response_text)
            
            # Generate form HTML if conversation contains embedded fields
            form_html = ""
            if parsed['conversation_text'] and self._has_embedded_fields(parsed['conversation_text']):
                form_html = self.form_builder.create_embedded_form(parsed['conversation_text'])
            
            # Update memory
            self.memory_manager.add_user_message(session_id, user_message, form_data)
            self.memory_manager.add_ai_message(session_id, parsed['conversation_text'], form_html)
            
            return {
                "response": parsed['conversation_text'],
                "form_html": form_html,
                "ai_notepad": parsed['internal_analysis'],
                "memory_vars": memory_vars
            }
            
        except Exception as e:
            logger.error(f"Error in TireAgentChain: {str(e)}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "form_html": "",
                "ai_notepad": "",
                "error": str(e)
            }
    
    def _has_embedded_fields(self, text: str) -> bool:
        """
        Check if text contains embedded form field function calls
        """
        import re
        return bool(re.search(r'\{create_\w+\([^}]*\)\}', text))
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        """
        return self.memory_manager.get_session_info(session_id)
    
    def clear_session(self, session_id: str):
        """
        Clear session memory
        """
        self.memory_manager.clear_memory(session_id)
    
    def _get_agent_prompt(self) -> str:
        """
        Get the agent prompt from config
        """
        try:
            from config.prompt import prompt
            return prompt
        except ImportError:
            return "You are a helpful tire sales assistant." 