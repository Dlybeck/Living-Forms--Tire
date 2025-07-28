"""
Tire Recommendation Graph using LangGraph
Step-by-step workflow for tire recommendations with research capabilities
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.language_models import BaseLLM
from core.tire_tools import TireTools
from core.form_builder import FormBuilder
from core.memory_manager import LangChainMemoryManager
from config.graph_prompts import ANALYSIS_PROMPT, PLANNING_PROMPT, SYNTHESIS_PROMPT
import logging

logger = logging.getLogger(__name__)

# State definition for the graph
class TireState(TypedDict):
    """State for the tire recommendation workflow"""
    messages: Annotated[List, "The conversation messages"]
    user_message: Annotated[str, "The current user message"]
    form_data: Annotated[Dict, "Form data from user"]
    session_id: Annotated[str, "Session identifier"]
    information_gaps: Annotated[List[str], "Missing information identified"]
    research_plan: Annotated[List[Dict], "Planned research actions"]
    research_results: Annotated[Dict, "Results from tool executions"]
    final_response: Annotated[str, "Final response to user"]
    form_html: Annotated[str, "Generated form HTML"]
    ai_notepad: Annotated[str, "Internal analysis and notes"]

class TireRecommendationGraph:
    """
    LangGraph workflow for tire recommendations
    """
    
    def __init__(self, llm: BaseLLM, form_builder: FormBuilder):
        self.llm = llm
        self.form_builder = form_builder
        self.tire_tools = TireTools()
        self.memory_manager = LangChainMemoryManager()
        
        # Create the graph
        self.graph = self._create_graph()
        
        logger.info("TireRecommendationGraph initialized")
    
    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph workflow
        """
        # Create the state graph
        workflow = StateGraph(TireState)
        
        # Add nodes
        workflow.add_node("analyze_information", self._analyze_information)
        workflow.add_node("plan_research", self._plan_research)
        workflow.add_node("execute_research", self._execute_research)
        workflow.add_node("synthesize_response", self._synthesize_response)
        
        # Add tool execution node
        workflow.add_node("tools", self._execute_tools)
        
        # Define the workflow
        workflow.set_entry_point("analyze_information")
        
        # Add edges
        workflow.add_edge("analyze_information", "plan_research")
        workflow.add_edge("plan_research", "execute_research")
        
        # Add conditional edges for research
        workflow.add_conditional_edges(
            "execute_research",
            self._should_do_research,
            {
                "research": "tools",
                "skip": "synthesize_response"
            }
        )
        
        workflow.add_edge("tools", "synthesize_response")
        workflow.add_edge("synthesize_response", END)
        
        return workflow.compile()
    
    async def _analyze_information(self, state: TireState) -> TireState:
        """
        Step 1: Analyze what information is missing or uncertain
        """
        try:
            # Use centralized analysis prompt
            
            # Get memory for this session
            memory = self.memory_manager.get_memory(state["session_id"])
            memory_vars = memory.load_memory_variables({})
            conversation_history = memory_vars.get("chat_history", "")
            
            # Prepare input
            input_vars = {
                "user_message": state["user_message"],
                "form_data": state.get("form_data", {}),
                "conversation_history": conversation_history
            }
            
            # Get analysis
            chain = ANALYSIS_PROMPT | self.llm
            response = await chain.ainvoke(input_vars)
            
            # Debug: Log the raw response
            logger.debug(f"Analysis response: {response.content}")
            
            # Parse response to get information gaps
            import json
            try:
                gaps = json.loads(response.content)
                logger.debug(f"Successfully parsed JSON gaps: {gaps}")
            except Exception as parse_error:
                logger.debug(f"JSON parsing failed: {parse_error}, using fallback")
                # Fallback parsing
                gaps = self._extract_gaps_from_text(response.content)
                logger.debug(f"Fallback parsing result: {gaps}")
            
            state["information_gaps"] = gaps
            state["ai_notepad"] = f"Information Analysis: Identified gaps - {gaps}"
            
            logger.debug(f"Information gaps identified: {gaps}")
            return state
            
        except Exception as e:
            logger.error(f"Error in information analysis: {e}")
            state["information_gaps"] = []
            state["ai_notepad"] = f"Error in analysis: {str(e)}"
            return state
    
    async def _plan_research(self, state: TireState) -> TireState:
        """
        Step 2: Plan what research to conduct
        """
        try:
            if not state["information_gaps"]:
                state["research_plan"] = []
                return state
            
            # Use centralized planning prompt
            
            # Get available tools
            available_tools = self._get_tools_description()
            
            # Prepare input
            input_vars = {
                "information_gaps": state["information_gaps"],
                "available_tools": available_tools
            }
            
            # Get research plan
            chain = PLANNING_PROMPT | self.llm
            response = await chain.ainvoke(input_vars)
            
            # Parse response
            import json
            try:
                research_plan = json.loads(response.content)
            except:
                research_plan = []
            
            state["research_plan"] = research_plan
            state["ai_notepad"] += f"\nResearch Planning: Planned {len(research_plan)} research actions"
            
            logger.debug(f"Research plan created: {research_plan}")
            return state
            
        except Exception as e:
            logger.error(f"Error in research planning: {e}")
            state["research_plan"] = []
            state["ai_notepad"] += f"\nError in planning: {str(e)}"
            return state
    
    async def _execute_research(self, state: TireState) -> TireState:
        """
        Step 3: Execute the research plan
        """
        try:
            if not state["research_plan"]:
                state["research_results"] = {}
                return state
            
            # Convert research plan to tool messages
            tool_messages = []
            for action in state["research_plan"]:
                tool_name = action["tool"]
                query = action["query"]
                
                # Find the tool
                tool = None
                for t in self.tire_tools.get_tools():
                    if t.name == tool_name:
                        tool = t
                        break
                
                if tool:
                    # Execute tool
                    try:
                        result = tool.func(query)
                        tool_messages.append(ToolMessage(
                            content=result,
                            tool_call_id=f"{tool_name}_{len(tool_messages)}"
                        ))
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        tool_messages.append(ToolMessage(
                            content=f"Error: {str(e)}",
                            tool_call_id=f"{tool_name}_{len(tool_messages)}"
                        ))
            
            # Add tool messages to state
            state["messages"].extend(tool_messages)
            state["research_results"] = {
                msg.tool_call_id: msg.content for msg in tool_messages
            }
            
            state["ai_notepad"] += f"\nResearch Execution: Completed {len(tool_messages)} research actions"
            
            logger.debug(f"Research executed: {len(tool_messages)} tools run")
            return state
            
        except Exception as e:
            logger.error(f"Error in research execution: {e}")
            state["research_results"] = {}
            state["ai_notepad"] += f"\nError in execution: {str(e)}"
            return state

    async def _execute_tools(self, state: TireState) -> TireState:
        """
        Execute tools and return results (for newer LangGraph version)
        """
        try:
            # This is a simplified tool execution for the newer LangGraph version
            research_results = {}
            
            for action in state.get("research_plan", []):
                tool_name = action.get("tool")
                query = action.get("query")
                
                if tool_name and query:
                    try:
                        # Find and execute the tool
                        tool = None
                        for t in self.tire_tools.get_tools():
                            if t.name == tool_name:
                                tool = t
                                break
                        
                        if tool:
                            result = tool.func(query)
                            research_results[tool_name] = result
                        else:
                            research_results[tool_name] = f"Tool {tool_name} not found"
                            
                    except Exception as e:
                        research_results[tool_name] = f"Error executing {tool_name}: {str(e)}"
            
            state["research_results"] = research_results
            return state
            
        except Exception as e:
            logger.error(f"Error in tool execution: {e}")
            state["research_results"] = {"error": str(e)}
            return state
    
    async def _synthesize_response(self, state: TireState) -> TireState:
        """
        Step 4: Synthesize final response with research results
        """
        try:
            # Use centralized synthesis prompt
            
            # Get memory for this session
            memory = self.memory_manager.get_memory(state["session_id"])
            memory_vars = memory.load_memory_variables({})
            conversation_history = memory_vars.get("chat_history", "")
            
            # Prepare input
            input_vars = {
                "user_message": state["user_message"],
                "form_data": state.get("form_data", {}),
                "research_results": state.get("research_results", {}),
                "conversation_history": conversation_history,
                "function_docs": self.form_builder.get_function_documentation()
            }
            
            # Get response
            chain = SYNTHESIS_PROMPT | self.llm
            response = await chain.ainvoke(input_vars)
            
            # Generate form HTML if needed
            response_text = response.content
            form_html = ""
            if self._has_embedded_fields(response_text):
                form_html = self.form_builder.create_embedded_form(response_text)
            
            state["final_response"] = response_text
            state["form_html"] = form_html
            state["ai_notepad"] += f"\nResponse Synthesis: Generated response with {len(form_html)} chars of form HTML"
            
            logger.debug(f"Response synthesized: {len(response_text)} chars")
            return state
            
        except Exception as e:
            logger.error(f"Error in response synthesis: {e}")
            state["final_response"] = f"Sorry, I encountered an error: {str(e)}"
            state["form_html"] = ""
            state["ai_notepad"] += f"\nError in synthesis: {str(e)}"
            return state
    
    def _should_do_research(self, state: TireState) -> str:
        """
        Determine if research should be conducted
        """
        if state["research_plan"]:
            return "research"
        return "skip"
    
    def _get_conversation_history(self, messages: List) -> str:
        """
        Extract conversation history from messages
        """
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                history.append(f"Assistant: {msg.content}")
        return "\n".join(history[-10:])  # Last 10 messages
    
    def _get_tools_description(self) -> str:
        """
        Get description of available tools
        """
        tools_desc = []
        for tool in self.tire_tools.get_tools():
            tools_desc.append(f"- {tool.name}: {tool.description}")
        return "\n".join(tools_desc)
    
    def _has_embedded_fields(self, text: str) -> bool:
        """
        Check if text contains embedded form field function calls
        """
        import re
        return bool(re.search(r'\{create_\w+\([^}]*\)\}', text))
    
    def _extract_gaps_from_text(self, text: str) -> List[str]:
        """
        Fallback method to extract gaps from text response
        """
        import re
        
        # First try to find JSON-like patterns
        json_match = re.search(r'\[([^\]]+)\]', text)
        if json_match:
            content = json_match.group(1)
            # Extract quoted strings
            items = re.findall(r'"([^"]+)"', content)
            if items:
                return items
        
        # Look for patterns like "missing_vehicle_year", "uncertain_", etc.
        gaps = re.findall(r'\b(missing|uncertain|no|unknown)_\w+', text, re.IGNORECASE)
        if gaps:
            return list(set(gaps))
        
        # If just "missing" is found, infer the most likely missing field
        if "missing" in text.lower():
            if "year" in text.lower() or "kia" in text.lower():
                return ["missing_vehicle_year"]
            elif "model" in text.lower():
                return ["missing_vehicle_model"]
            elif "make" in text.lower():
                return ["missing_vehicle_make"]
            else:
                return ["missing_vehicle_year"]  # Default to most common missing field
        
        return []
    
    async def process_message(self, user_message: str, session_id: str, 
                            form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message through the graph workflow
        """
        try:
            # Save user message to memory
            self.memory_manager.add_user_message(session_id, user_message, form_data)
            
            # Initialize state
            initial_state = TireState(
                messages=[],  # Start with empty messages for newer LangGraph
                user_message=user_message,
                form_data=form_data or {},
                session_id=session_id,
                information_gaps=[],
                research_plan=[],
                research_results={},
                final_response="",
                form_html="",
                ai_notepad=""
            )
            
            # Execute the graph
            logger.debug(f"Executing graph for session {session_id}")
            final_state = await self.graph.ainvoke(initial_state)
            
            # Save AI response to memory
            self.memory_manager.add_ai_message(session_id, final_state["final_response"])
            
            # Return results
            return {
                "response": final_state["final_response"],
                "form_html": final_state["form_html"],
                "ai_notepad": final_state["ai_notepad"],
                "research_results": final_state.get("research_results", {}),
                "information_gaps": final_state.get("information_gaps", [])
            }
            
        except Exception as e:
            logger.error(f"Error in graph execution: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "form_html": "",
                "ai_notepad": f"Error: {str(e)}",
                "research_results": {},
                "information_gaps": []
            } 