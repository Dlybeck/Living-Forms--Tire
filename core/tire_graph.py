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
    current_stage: Annotated[str, "Current workflow stage determined by analysis"]
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
        workflow.add_node("research_and_synthesize", self._research_and_synthesize)
        
        # Define the workflow
        workflow.set_entry_point("analyze_information")
        workflow.add_edge("analyze_information", "plan_research")
        workflow.add_edge("plan_research", "research_and_synthesize")
        workflow.add_edge("research_and_synthesize", END)
        
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
            
            # Parse response to get stage and information gaps
            import json
            try:
                analysis_result = json.loads(response.content)
                if isinstance(analysis_result, dict):
                    current_stage = analysis_result.get("current_stage", "1")
                    gaps = analysis_result.get("missing_fields", [])
                else:
                    # Fallback for old format
                    current_stage = "1"
                    gaps = analysis_result
                logger.debug(f"Successfully parsed JSON: stage={current_stage}, gaps={gaps}")
            except Exception as parse_error:
                logger.debug(f"JSON parsing failed: {parse_error}, using fallback")
                # Fallback parsing
                current_stage = "1"
                gaps = self._extract_gaps_from_text(response.content)
                logger.debug(f"Fallback parsing result: stage={current_stage}, gaps={gaps}")
            
            state["current_stage"] = current_stage
            state["information_gaps"] = gaps
            
            # Enhanced AI notepad with detailed analysis
            stage_names = {
                "1": "Vehicle & Tire Specification Discovery",
                "2": "Driving Preferences & Usage Understanding", 
                "3": "Tire Recommendation Generation",
                "4": "Decision Support & Refinement"
            }
            stage_name = stage_names.get(current_stage, f"Stage {current_stage}")
            
            state["ai_notepad"] = f"""🤔 **AI Analysis**
**Current Stage:** {stage_name} (Stage {current_stage})
**User Message:** "{state['user_message']}"
**Current Form Data:** {state.get('form_data', {})}
**Missing Information:** {gaps}
**Analysis:** Identified {len(gaps)} critical gaps for current stage"""
            
            logger.debug(f"Information gaps identified: {gaps}")
            return state
            
        except Exception as e:
            logger.error(f"Error in information analysis: {e}")
            state["information_gaps"] = []
            state["ai_notepad"] = f"Error in analysis: {str(e)}"
            return state
    
    async def _plan_research(self, state: TireState) -> TireState:
        """
        Step 2: Plan what research to conduct based on gaps
        """
        try:
            # Simple research planning - translate gaps into search queries
            research_plan = []
            form_data = state.get("form_data", {})
            gaps = state.get("information_gaps", [])
            
            for gap in gaps:
                if "vehicle_model" in gap and form_data.get("vehicle_make"):
                    # Need to find models for this make
                    research_plan.append({
                        "objective": "find_vehicle_models",
                        "tool": "vehicle_specs_search",
                        "query": f"{form_data['vehicle_make']} car models list",
                        "priority": "high"
                    })
                
                elif "vehicle_trim" in gap and form_data.get("vehicle_make") and form_data.get("vehicle_model") and form_data.get("vehicle_year"):
                    # Need to find trims for this specific vehicle
                    research_plan.append({
                        "objective": "find_vehicle_trims",
                        "tool": "vehicle_specs_search", 
                        "query": f"{form_data['vehicle_year']} {form_data['vehicle_make']} {form_data['vehicle_model']} trim levels",
                        "priority": "high"
                    })
                
                elif "tire_size" in gap and form_data.get("vehicle_make") and form_data.get("vehicle_model") and form_data.get("vehicle_year"):
                    # Need to find tire sizes for this vehicle
                    research_plan.append({
                        "objective": "find_tire_sizes",
                        "tool": "tire_size_lookup",
                        "query": f"{form_data['vehicle_year']} {form_data['vehicle_make']} {form_data['vehicle_model']} tire size specifications",
                        "priority": "high"
                    })
                    
                    # Also search for trim-specific tire sizes if we have trim
                    if form_data.get("vehicle_trim"):
                        research_plan.append({
                            "objective": "find_trim_tire_sizes",
                            "tool": "tire_size_lookup",
                            "query": f"{form_data['vehicle_year']} {form_data['vehicle_make']} {form_data['vehicle_model']} {form_data['vehicle_trim']} tire size",
                            "priority": "high"
                        })
            
            state["research_plan"] = research_plan
            
            # Log research planning
            if research_plan:
                plan_details = []
                for action in research_plan:
                    plan_details.append(f"• {action['objective']}: {action['query']}")
                
                state["ai_notepad"] += f"""

🔍 **Research Planning**
**Planned Actions:** {len(research_plan)}
{chr(10).join(plan_details)}"""
            else:
                state["ai_notepad"] += f"""

🔍 **Research Planning**
**No research needed** - all information available"""
            
            logger.debug(f"Research plan created: {research_plan}")
            return state
            
        except Exception as e:
            logger.error(f"Error in research planning: {e}")
            state["research_plan"] = []
            state["ai_notepad"] += f"\nError in planning: {str(e)}"
            return state

    async def _research_and_synthesize(self, state: TireState) -> TireState:
        """
        Step 2: Do research if needed and synthesize response
        """
        try:
            # Execute research plan
            research_results = {}
            research_plan = state.get("research_plan", [])
            
            for action in research_plan:
                tool_name = action.get("tool")
                query = action.get("query")
                objective = action.get("objective", "unknown")
                
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
                            research_results[objective] = result
                            logger.debug(f"Research completed for {objective}: {result[:100]}...")
                        else:
                            research_results[objective] = f"Tool {tool_name} not found"
                            logger.error(f"Tool {tool_name} not found for {objective}")
                            
                    except Exception as e:
                        research_results[objective] = f"Error executing {tool_name}: {str(e)}"
                        logger.error(f"Research error for {objective}: {e}")
            
            state["research_results"] = research_results
            
            # Now synthesize the response
            memory = self.memory_manager.get_memory(state["session_id"])
            memory_vars = memory.load_memory_variables({})
            conversation_history = memory_vars.get("chat_history", "")
            
            # Prepare input
            input_vars = {
                "user_message": state["user_message"],
                "form_data": state.get("form_data", {}),
                "research_results": research_results,
                "conversation_history": conversation_history,
                "current_stage": state.get("current_stage", "1"),
                "information_gaps": state.get("information_gaps", []),
                "function_docs": self.form_builder.get_function_documentation()
            }
            
            # Get response
            chain = SYNTHESIS_PROMPT | self.llm
            try:
                response = await chain.ainvoke(input_vars)
                logger.debug(f"Successfully generated synthesis response: {len(response.content)} chars")
            except Exception as e:
                logger.error(f"Error in synthesis chain: {e}")
                # Fallback response
                response = type('Response', (), {'content': f"Sorry, I encountered an error generating a response: {str(e)}"})()
            
            # Generate form HTML if needed
            response_text = response.content
            form_html = ""
            if self._has_embedded_fields(response_text):
                form_html = self.form_builder.create_embedded_form(response_text)
            
            state["final_response"] = response_text
            state["form_html"] = form_html
            
            # Enhanced synthesis notes
            has_form = len(form_html) > 0
            response_preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
            
            # Log research details
            research_summary = []
            for key, result in research_results.items():
                result_preview = result[:100] + "..." if len(result) > 100 else result
                research_summary.append(f"• {key}: {result_preview}")
            
            research_log = f"""
🔬 **Research & Response**
**Research Results:** {len(research_results)} items found
{chr(10).join(research_summary) if research_summary else "No research performed"}
**Generated:** {len(response_text)} character response
**Form Fields:** {"Yes" if has_form else "No"}
**Response Preview:** "{response_preview}"
**Next Action:** {"Gathering information via form" if has_form else "Providing information/guidance"}"""
            
            state["ai_notepad"] += research_log
            
            logger.debug(f"Research and synthesis completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in research and synthesis: {e}")
            state["final_response"] = f"Sorry, I encountered an error: {str(e)}"
            state["form_html"] = ""
            state["ai_notepad"] += f"\nError in research and synthesis: {str(e)}"
            return state
    
    
    
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
        return "\n".join(history[-20:])  # Last 20 messages for better context
    
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
    
    def _substitute_template_variables(self, query: str, form_data: Dict[str, Any]) -> str:
        """
        Substitute template variables in research queries with actual form data
        """
        # Common variable mappings
        variable_mappings = {
            "{make}": form_data.get("vehicle_make", ""),
            "{model}": form_data.get("vehicle_model", ""),
            "{year}": form_data.get("vehicle_year", ""),
            "{trim}": form_data.get("vehicle_trim", ""),
            "{tire_size}": form_data.get("tire_size", ""),
            "{user_location}": form_data.get("location", "United States"),
            "{Make}": form_data.get("vehicle_make", "").title(),
            "{Model}": form_data.get("vehicle_model", "").title(),
            "{Year}": form_data.get("vehicle_year", ""),
            "{Trim}": form_data.get("vehicle_trim", "").upper(),
            "{Tire_size}": form_data.get("tire_size", ""),
            # Handle more complex patterns
            "{vehicle_make}": form_data.get("vehicle_make", ""),
            "{vehicle_model}": form_data.get("vehicle_model", ""),
            "{vehicle_year}": form_data.get("vehicle_year", ""),
            "{vehicle_trim}": form_data.get("vehicle_trim", ""),
            "{tire_size}": form_data.get("tire_size", ""),
            "{location}": form_data.get("location", "United States"),
        }
        
        # Substitute variables
        for placeholder, value in variable_mappings.items():
            if value:  # Only substitute if we have a value
                query = query.replace(placeholder, str(value))
        
        # Handle any remaining template patterns that might be missed
        import re
        # Remove any remaining {variable} patterns that weren't substituted
        query = re.sub(r'\{[^}]*\}', '', query)
        
        return query
    
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
                current_stage="1",
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