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
from agents.conversation_orchestrator import ConversationOrchestrator
from agents.cost_manager import CostManager
from utils.state_manager import ConversationState
from database.tire_database import TireDatabase

app = FastAPI(title="Living Form Tire Sales Agent", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize core components
tire_db = TireDatabase()
cost_manager = CostManager(config={"strategy": "generous", "conversation_budget": 0.20})
conversation_orchestrator = ConversationOrchestrator(tire_db, cost_manager)

# In-memory session storage (replace with Redis/DB in production)
active_sessions: Dict[str, ConversationState] = {}

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
    welcome_html = """
    <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
        <h3 style="color:#667eea;margin-bottom:15px;font-size:20px;">👋 Welcome to Your Tire Search Assistant!</h3>
        <p style="margin-bottom:15px;">I'm here to help you find the perfect tires for your vehicle. Whether you need new tires, have questions about tire types, or want to understand what's best for your driving needs - I'm here to guide you through the process.</p>
        <p style="margin-bottom:20px;"><strong>How can I help you today?</strong></p>
        
        <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
            <div style="margin-bottom:20px;">
                <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Tell me what you're looking for</label>
                <textarea name="user_request" placeholder="I want to get a set of new tires for my 2015 Honda Accord" style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;min-height:80px;resize:vertical;font-family: inherit;"></textarea>

            </div>
            
            <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                🚀 Let's Get Started
            </button>
        </form>
    </div>
    """
    
    return ChatResponse(
        response=welcome_html,
        form_html=None,
        inline_guidance=None,
        conversation_state="initial",
        cost_info={"cost": 0.0, "model": "preset", "tokens": 0},
        session_id="welcome"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint for the living form conversation"""
    try:
        # Get or create conversation state
        if chat_request.session_id not in active_sessions:
            active_sessions[chat_request.session_id] = ConversationState(
                session_id=chat_request.session_id
            )
        
        conversation_state = active_sessions[chat_request.session_id]
        
        # Update form data if provided
        if chat_request.form_data:
            conversation_state.update_form_data(chat_request.form_data)
        
        # Process message through conversation orchestrator
        response_data = await conversation_orchestrator.process_message(
            user_message=chat_request.message,
            conversation_state=conversation_state
        )
        
        # Update session storage
        active_sessions[chat_request.session_id] = conversation_state
        
        # Return response
        return ChatResponse(
            response=response_data["response"],
            form_html=response_data.get("form_html"),
            inline_guidance=response_data.get("inline_guidance"),
            conversation_state=conversation_state.current_step.value,
            cost_info=response_data["cost_info"],
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
    
    conversation_state = active_sessions[session_id]
    return {
        "total_cost": conversation_state.total_cost,
        "interactions": len(conversation_state.conversation_history),
        "cost_breakdown": conversation_state.cost_breakdown,
        "budget_remaining": cost_manager.get_remaining_budget(conversation_state)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    }



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 