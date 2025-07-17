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
        <p style="margin-bottom:15px;">I'm here to help you find the perfect tires for your vehicle. This process is simple and personalized - I'll guide you through finding tires that match your needs and budget.</p>
        <p style="margin-bottom:20px;"><strong>Let's start with some basic information about your vehicle:</strong></p>
        
        <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:20px;">
                <div>
                    <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Vehicle Year</label>
                    <input type="number" name="year" placeholder="e.g., 2020" min="1990" max="2025" style="width:100%;padding:10px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;" />
                </div>
                <div>
                    <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Make</label>
                    <input type="text" name="make" placeholder="e.g., Toyota, Honda, Ford" style="width:100%;padding:10px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;" />
                </div>
                <div>
                    <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Model</label>
                    <input type="text" name="model" placeholder="e.g., Camry, Civic, F-150" style="width:100%;padding:10px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;" />
                </div>
                <div>
                    <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Number of Tires</label>
                    <select name="tire_count" style="width:100%;padding:10px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;">
                        <option value="">Select...</option>
                        <option value="1">1 tire</option>
                        <option value="2">2 tires</option>
                        <option value="4">4 tires (full set)</option>
                    </select>
                </div>
            </div>
            
            <div style="margin-bottom:20px;">
                <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Additional Information (Optional)</label>
                <textarea name="additional_notes" placeholder="Tell me about your driving habits, budget preferences, or any specific tire needs you have..." style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;min-height:80px;resize:vertical;"></textarea>
            </div>
            
            <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                🔍 Start My Tire Search
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

@app.get("/test-form")
async def test_form_generation():
    """Test endpoint to directly test form generation"""
    try:
        from utils.state_manager import ConversationState
        from agents.living_form_generator import LivingFormGenerator
        
        # Create a new conversation state
        conversation_state = ConversationState(session_id="test123")
        
        # Create form generator
        form_generator = LivingFormGenerator()
        
        # Generate the first form
        form_html = form_generator.generate_living_form(conversation_state)
        
        return {
            "form_html": form_html,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 