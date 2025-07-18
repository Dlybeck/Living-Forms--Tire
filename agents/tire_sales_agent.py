from typing import Dict, List, Any
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import logging
import json
from datetime import datetime

from utils.state_manager import ConversationState, DataCategory
from agents.form_builder_tools import FormBuilderTools
from database.tire_database import TireDatabase
from agents.cost_manager import CostManager

logger = logging.getLogger(__name__)

class FormBuilderTool(BaseTool):
    """Tool for building form fields"""
    
    name: str = "form_builder"
    description: str = "Build form fields and complete forms for collecting user information"
    
    def __init__(self, form_builder: FormBuilderTools):
        super().__init__()
        self.form_builder = form_builder
    
    def _run(self, tool_input: str) -> str:
        """Execute the form builder tool"""
        try:
            # Parse the tool input as JSON
            input_data = json.loads(tool_input)
            action = input_data.get("action")
            
            if action == "create_text_field":
                return self.form_builder.create_text_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    required=input_data.get("required", False),
                    placeholder=input_data.get("placeholder"),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_textarea_field":
                return self.form_builder.create_textarea_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    required=input_data.get("required", False),
                    placeholder=input_data.get("placeholder"),
                    rows=input_data.get("rows", 3),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_select_field":
                return self.form_builder.create_select_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    options=input_data["options"],
                    required=input_data.get("required", False),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_radio_field":
                return self.form_builder.create_radio_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    options=input_data["options"],
                    required=input_data.get("required", False),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_checkbox_field":
                return self.form_builder.create_checkbox_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    options=input_data["options"],
                    required=input_data.get("required", False),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_number_field":
                return self.form_builder.create_number_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    required=input_data.get("required", False),
                    min_value=input_data.get("min_value"),
                    max_value=input_data.get("max_value"),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_year_field":
                return self.form_builder.create_year_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    required=input_data.get("required", False),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_budget_range_field":
                return self.form_builder.create_budget_range_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    required=input_data.get("required", False),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_mileage_range_field":
                return self.form_builder.create_mileage_range_field(
                    name=input_data["name"],
                    label=input_data["label"],
                    required=input_data.get("required", False),
                    help_text=input_data.get("help_text")
                )
            
            elif action == "create_vehicle_info_form":
                return self.form_builder.create_vehicle_info_form(
                    conversation_text=input_data.get("conversation_text", "")
                )
            
            elif action == "create_tire_specs_form":
                return self.form_builder.create_tire_specs_form(
                    conversation_text=input_data.get("conversation_text", "")
                )
            
            elif action == "create_driving_patterns_form":
                return self.form_builder.create_driving_patterns_form(
                    conversation_text=input_data.get("conversation_text", "")
                )
            
            elif action == "create_budget_preferences_form":
                return self.form_builder.create_budget_preferences_form(
                    conversation_text=input_data.get("conversation_text", "")
                )
            
            elif action == "create_current_tire_status_form":
                return self.form_builder.create_current_tire_status_form(
                    conversation_text=input_data.get("conversation_text", "")
                )
            
            elif action == "create_special_considerations_form":
                return self.form_builder.create_special_considerations_form(
                    conversation_text=input_data.get("conversation_text", "")
                )
            
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            logger.error(f"Error in form builder tool: {str(e)}")
            return f"Error building form: {str(e)}"

class TireSalesAgent:
    """
    A LangChain agent that handles tire sales conversations and form generation
    Uses tools to build forms dynamically while maintaining conversation state
    """
    
    def __init__(self, tire_database: TireDatabase, cost_manager: CostManager):
        self.tire_database = tire_database
        self.cost_manager = cost_manager
        self.form_builder = FormBuilderTools()
        
        # Create the form builder tool
        self.form_builder_tool = FormBuilderTool(self.form_builder)
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        # Create the agent
        self.agent = self._create_agent()
        
        logger.info("Tire Sales Agent initialized")
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools"""
        
        # Import the agent system prompt from the prompts module
        from prompts import get_agent_system_prompt
        system_prompt = get_agent_system_prompt()

        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=[self.form_builder_tool],
            prompt=prompt
        )
        
        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=[self.form_builder_tool],
            verbose=True,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    async def process_message(self, user_message: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Process a user message and return the response with any generated forms
        """
        start_time = datetime.now()
        
        try:
            # Extract vehicle info from user message
            self._extract_vehicle_info(user_message, conversation_state)
            
            # Update user knowledge level
            conversation_state.detect_user_knowledge_level(user_message)
            
            # Prepare the conversation context
            context = self._prepare_conversation_context(conversation_state)
            
            # Create the input for the agent
            agent_input = {
                "input": user_message,
                "chat_history": self._format_chat_history(conversation_state),
                "context": context
            }
            
            # Run the agent
            result = await self.agent.ainvoke(agent_input)
            
            # Extract the response
            ai_response = result.get("output", "")
            
            # Check if the agent used the form builder tool
            form_html = self._extract_form_from_agent_output(result)
            
            # Determine what to return
            if form_html:
                # Agent created a form
                response_data = {
                    "response": "",  # No separate text response
                    "form_html": form_html,
                    "inline_guidance": "",
                    "cost_info": {"cost": 0.0, "model_used": "agent", "source": "agent"},
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "agent_living_form"
                }
            else:
                # Agent provided conversational response only
                response_data = {
                    "response": ai_response,
                    "form_html": "",
                    "inline_guidance": "",
                    "cost_info": {"cost": 0.0, "model_used": "agent", "source": "agent"},
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "source": "agent_conversation_only"
                }
            
            # Add to conversation history
            conversation_state.add_interaction(
                user_message=user_message,
                ai_response=ai_response if not form_html else self._extract_conversation_from_form(form_html),
                cost=0.0,  # Agent costs are handled differently
                model_used="agent"
            )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message with agent: {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _extract_vehicle_info(self, user_message: str, conversation_state: ConversationState):
        """Extract vehicle information from user message"""
        user_lower = user_message.lower()
        
        # Extract make
        makes = ['kia', 'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'mazda', 'hyundai', 'volkswagen', 'bmw', 'mercedes', 'audi']
        for make in makes:
            if make in user_lower:
                conversation_state.vehicle_info['make'] = make.title()
                logger.info(f"Extracted vehicle make: {make.title()}")
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
                    logger.info(f"Extracted vehicle model: {model.title()}")
                    break
        
        # Extract year (4-digit year)
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', user_message)
        if year_match:
            conversation_state.vehicle_info['year'] = year_match.group()
            logger.info(f"Extracted vehicle year: {year_match.group()}")
        
        # Extract tire size pattern
        tire_size_match = re.search(r'\b\d{3}/\d{2}R\d{2}\b', user_message.upper())
        if tire_size_match:
            conversation_state.tire_specs['current_tire_size'] = tire_size_match.group()
            logger.info(f"Extracted tire size: {tire_size_match.group()}")
    
    def _prepare_conversation_context(self, conversation_state: ConversationState) -> str:
        """Prepare conversation context for the agent"""
        context_parts = []
        
        # Vehicle information
        if conversation_state.vehicle_info:
            vehicle_info = conversation_state.vehicle_info
            context_parts.append(f"Vehicle: {vehicle_info.get('year', '')} {vehicle_info.get('make', '')} {vehicle_info.get('model', '')}")
        
        # Missing information
        missing_categories = []
        if not conversation_state.is_category_completed(DataCategory.VEHICLE_INFO):
            missing_categories.append("vehicle information")
        if not conversation_state.is_category_completed(DataCategory.TIRE_SPECS):
            missing_categories.append("tire specifications")
        if not conversation_state.is_category_completed(DataCategory.DRIVING_PATTERNS):
            missing_categories.append("driving patterns")
        if not conversation_state.is_category_completed(DataCategory.BUDGET_PREFERENCES):
            missing_categories.append("budget preferences")
        if not conversation_state.is_category_completed(DataCategory.CURRENT_TIRE_STATUS):
            missing_categories.append("current tire status")
        if not conversation_state.is_category_completed(DataCategory.SPECIAL_CONSIDERATIONS):
            missing_categories.append("special considerations")
        
        if missing_categories:
            context_parts.append(f"Still need to collect: {', '.join(missing_categories)}")
        
        # User knowledge level
        context_parts.append(f"User knowledge level: {conversation_state.user_knowledge_level.value}")
        
        return " | ".join(context_parts) if context_parts else "Starting fresh conversation"
    
    def _format_chat_history(self, conversation_state: ConversationState) -> List[BaseMessage]:
        """Format conversation history for the agent"""
        messages = []
        
        for interaction in conversation_state.conversation_history[-5:]:  # Last 5 interactions
            messages.append(HumanMessage(content=interaction.user_message))
            messages.append(AIMessage(content=interaction.ai_response))
        
        return messages
    
    def _extract_form_from_agent_output(self, result: Dict[str, Any]) -> str:
        """Extract form HTML from agent output if it used the form builder tool"""
        # Check if the agent used the form builder tool
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if step[0].tool == "form_builder":
                    return step[1]  # Return the form HTML
        
        return ""
    
    def _extract_conversation_from_form(self, form_html: str) -> str:
        """Extract conversation text from form HTML"""
        # Simple extraction - look for text before the form tag
        import re
        form_match = re.search(r'<form', form_html)
        if form_match:
            return form_html[:form_match.start()].strip()
        return form_html
    
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