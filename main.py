from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from agents.agent_coordinator import AgentCoordinator
from agents.cost_manager import CostManager
from utils.conversation_roadmap import ConversationRoadmap, DataCategory
from database.tire_database import TireDatabase
from agents.ai_client import AIClient
from agents.cost_manager import ModelType
from agents.form_builder import FormBuilder

app = FastAPI(title="Living Form Tire Sales Agent", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize core components
tire_db = TireDatabase()
cost_manager = CostManager(config={"strategy": "generous", "conversation_budget": 0.20})
ai_client = AIClient()
form_builder = FormBuilder()  # Initialize the form builder properly
agent_coordinator = AgentCoordinator(ai_client, cost_manager, form_builder, tire_db)

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

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/welcome", response_model=ChatResponse)
async def get_welcome_message():
    """Get the preset welcome message with initial form"""
    # Instead of a hardcoded form, let the AI generate the first message and form
    # Simulate an empty conversation and let the agent handle the greeting
    # We'll call the agent coordinator with an empty roadmap and no user message
    roadmap = ConversationRoadmap()
    conversation_context = {"session_id": "welcome"}
    response_data = await agent_coordinator.process_message(
        user_message="",
        roadmap=roadmap,
        conversation_context=conversation_context
    )
    return ChatResponse(
        response=response_data.get("response") or "",
        form_html=None,
        inline_guidance=response_data.get("inline_guidance"),
        conversation_state=roadmap.current_step.value,
        cost_info=response_data.get("cost_info", {"total_cost": 0.0}),
        session_id="welcome"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint for the living form conversation"""
    try:
        # Get or create conversation roadmap
        if chat_request.session_id not in active_sessions:
            active_sessions[chat_request.session_id] = ConversationRoadmap()
        
        roadmap = active_sessions[chat_request.session_id]
        
        # Update form data if provided
        if chat_request.form_data:
            # Process form data and update roadmap
            for key, value in chat_request.form_data.items():
                if key == "info_method":
                    if value == "tire_size":
                        roadmap.update_shared_data(DataCategory.TIRE_SPECS, {"method": "direct_input"})
                    elif value == "vin":
                        roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {"method": "vin"})
                    elif value == "make_model_year":
                        roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {"method": "make_model_year"})
                    elif value == "not_sure":
                        roadmap.update_shared_data(DataCategory.VEHICLE_INFO, {"method": "need_help"})
        
        # Build conversation context with initial answer if present
        conversation_context = {"session_id": chat_request.session_id}
        info_method = roadmap.get_shared_data(DataCategory.VEHICLE_INFO)
        if info_method and info_method.get('method'):
            conversation_context['info_method'] = info_method['method']
        
        # Process message through agent coordinator
        response_data = await agent_coordinator.process_message(
            user_message=chat_request.message,
            roadmap=roadmap,
            conversation_context=conversation_context
        )
        
        # Update session storage
        active_sessions[chat_request.session_id] = roadmap
        
        # DEBUG: Add AI response box for debugging (remove this later)
        debug_ai_response = ""
        if response_data.get("conversation_text"):
            debug_ai_response = f"""
            <div style="background:#f0f0f0;padding:10px;margin-bottom:10px;border-left:4px solid #ff6b6b;font-family:monospace;font-size:12px;">
                <strong>🔍 DEBUG: AI Response</strong><br>
                {response_data.get("conversation_text", "")}
            </div>
            """
        
        # Combine the debug response with the main response
        combined_response = debug_ai_response + (response_data.get("response") or "")
        
        return ChatResponse(
            response=combined_response,
            form_html=None,  # Form HTML is already included in the response
            inline_guidance=response_data.get("inline_guidance"),
            conversation_state=roadmap.current_step.value,
            cost_info=response_data.get("cost_info", {"total_cost": 0.0}),
            session_id=chat_request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/cost")
async def get_session_costs(session_id: str):
    """Get cost breakdown for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    roadmap = active_sessions[session_id]
    return {
        "total_cost": 0.0,  # Will be tracked in cost manager
        "interactions": len(roadmap.conversation_history),
        "cost_breakdown": {},  # Will be tracked in cost manager
        "budget_remaining": cost_manager.get_remaining_budget({"session_id": session_id})
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
    
    # Test Anthropic Claude 3.5 Sonnet
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
    
    # Test OpenAI GPT-4o
    try:
        response = await ai_client.generate_response(
            user_message="Hello, this is a test message.",
            conversation_context={"current_step": "test"},
            model_type=ModelType.GPT_4O
        )
        test_results["openai_gpt_4o"] = {
            "status": "success",
            "model": response.get("model", "unknown"),
            "cost": response.get("cost", 0.0)
        }
    except Exception as e:
        test_results["openai_gpt_4o"] = {
            "status": "failed",
            "error": str(e)
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results
    }



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 