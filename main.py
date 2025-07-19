from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import Dict, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from agents.agent_coordinator import AgentCoordinator
from agents.scribe_agent import ScribeAgent
from agents.ai_client import AIClient
from agents.cost_manager import CostManager, ModelType
from agents.form_builder import FormBuilder
from utils.conversation_roadmap import ConversationRoadmap, DataCategory
from database.tire_database import TireDatabase

app = FastAPI(title="Living Form Tire Sales Agent", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components
tire_db = TireDatabase()
cost_manager = CostManager(config={"conversation_budget": 0.20})
ai_client = AIClient()
form_builder = FormBuilder()
agent_coordinator = AgentCoordinator(ai_client, cost_manager, form_builder, tire_db)
scribe_agent = ScribeAgent(ai_client, cost_manager, form_builder)

# In-memory session storage (replace with Redis/DB in production)
active_sessions: Dict[str, ConversationRoadmap] = {}

# Request/Response models
class ChatMessage(BaseModel):
    message: str
    session_id: str
    form_data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    form_html: Optional[str] = None
    inline_guidance: Optional[str] = None
    conversation_state: str
    cost_info: Dict[str, Any]
    session_id: str
    notepad_content: Optional[str] = None  # Add notepad content to response

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint for the living form conversation"""
    try:
        # Get or create conversation roadmap
        if chat_request.session_id not in active_sessions:
            active_sessions[chat_request.session_id] = ConversationRoadmap()
        
        roadmap = active_sessions[chat_request.session_id]
        
        # Build conversation context
        conversation_context: Dict[str, Any] = {"session_id": chat_request.session_id}
        
        # Add full conversation history to context
        if roadmap.conversation_history:
            conversation_context["conversation_history"] = roadmap.conversation_history
            logger.info(f"Added {len(roadmap.conversation_history)} conversation events to context")
        
        # Add current conversation summary
        conversation_context["conversation_summary"] = roadmap.get_conversation_summary()
        
        # Update form data if provided
        if chat_request.form_data:
            logger.info(f"Received form data: {chat_request.form_data}")
            
            # Add form submission to conversation history
            roadmap.add_conversation_event("form_submission", {
                "form_data": chat_request.form_data,
                "message": chat_request.message
            })
            
            # Process form data and update roadmap
            for key, value in chat_request.form_data.items():
                if key == "info_method":
                    logger.info(f"Processing info_method: {value}")
                    if value == "tire_size":
                        roadmap.update_shared_data(DataCategory.TIRE_SPECS, {"method": "direct_input"})
                        conversation_context["user_method"] = "tire_size"
                    elif value == "vin":
                        roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {"method": "vin"})
                        conversation_context["user_method"] = "vin"
                    elif value == "make_model_year":
                        roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {"method": "make_model_year"})
                        conversation_context["user_method"] = "make_model_year"
                    elif value == "not_sure":
                        roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {"method": "need_help"})
                        conversation_context["user_method"] = "not_sure"
                else:
                    # Store other form fields in shared data for context
                    roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {key: value})
                    conversation_context[f"form_field_{key}"] = value
        
        # Add any existing info method to context
        info_method = roadmap.get_shared_data(DataCategory.VEHICLE_INFO)
        if info_method and info_method.get('method'):
            conversation_context['info_method'] = info_method['method']
        
        # Add notepad summary to context
        conversation_context['notepad_summary'] = roadmap.get_notepad_summary()
        
        logger.info(f"Final conversation context: {conversation_context}")
        logger.info(f"User message: {chat_request.message}")
        
        # Use Scribe AI to extract and record important information
        scribe_result = await scribe_agent.extract_and_record(
            user_message=chat_request.message,
            roadmap=roadmap,
            conversation_context=conversation_context
        )
        
        if scribe_result.get("notepad_updated"):
            logger.info(f"Scribe AI updated notepad with: {scribe_result.get('extracted_info')}")
            # Update notepad summary in context after Scribe AI processing
            conversation_context['notepad_summary'] = roadmap.get_notepad_summary()
        
        # Process message through agent coordinator
        response_data = await agent_coordinator.process_message(
            user_message=chat_request.message,
            roadmap=roadmap,
            conversation_context=conversation_context
        )
        
        # Update session storage
        active_sessions[chat_request.session_id] = roadmap
        
        return ChatResponse(
            response=response_data.get("response") or "",
            form_html=response_data.get("form_html"),  # Return the form HTML from agent
            inline_guidance=response_data.get("inline_guidance"),
            conversation_state=roadmap.current_step.value,
            cost_info=response_data.get("cost_info", {"total_cost": 0.0}),
            session_id=chat_request.session_id,
            notepad_content=roadmap.get_notepad_content() # Add notepad content to response
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/notepad")
async def get_session_notepad(session_id: str):
    """Get the Scribe AI notepad content for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    roadmap = active_sessions[session_id]
    notepad_content = roadmap.get_notepad_content()
    
    return {
        "session_id": session_id,
        "notepad_content": notepad_content,
        "notepad_raw": roadmap.ai_notepad,
        "conversation_length": len(roadmap.conversation_history),
        "last_updated": datetime.now().isoformat()
    }

@app.get("/session/{session_id}/cost")
async def get_session_costs(session_id: str):
    """Get cost breakdown for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    roadmap = active_sessions[session_id]
    cost_summary = cost_manager.get_cost_summary(roadmap)
    
    return {
        "total_cost": cost_summary["total_cost"],
        "interactions": cost_summary["interactions_count"],
        "cost_breakdown": cost_summary["cost_breakdown"],
        "budget_remaining": cost_summary["budget_remaining"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    }

@app.get("/test-ai")
async def test_ai_endpoint():
    """Test AI endpoints to check if they're working"""
    test_results = {}
    
    # Test OpenAI GPT-4o-mini (primary model)
    try:
        response = await ai_client.generate_response(
            user_message="Hello, this is a test message.",
            conversation_context={"current_step": "test"},
            model_type=ModelType.GPT_4O_MINI
        )
        test_results["openai_gpt_4o_mini"] = {
            "status": "success",
            "model": response.get("model", "unknown"),
            "cost": response.get("cost", 0.0)
        }
    except Exception as e:
        test_results["openai_gpt_4o_mini"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Test Anthropic Claude 3.5 Sonnet (fallback)
    try:
        response = await ai_client.generate_response(
            user_message="Hello, this is a test message.",
            conversation_context={"current_step": "test"},
            model_type=ModelType.CLAUDE_3_5_SONNET
        )
        test_results["anthropic_claude_3_5"] = {
            "status": "success",
            "model": response.get("model", "unknown"),
            "cost": response.get("cost", 0.0)
        }
    except Exception as e:
        test_results["anthropic_claude_3_5"] = {
            "status": "failed",
            "error": str(e)
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 