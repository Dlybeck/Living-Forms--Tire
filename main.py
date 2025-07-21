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
from agents.simple_dual_agent_coordinator import SimpleDualAgentCoordinator
from agents.ai_client import AIClient
from agents.cost_manager import CostManager, ModelType
from agents.form_builder import FormBuilder
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
agent_coordinator = SimpleDualAgentCoordinator(ai_client, cost_manager, form_builder, tire_db)

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
    current_agent: Optional[str] = None  # Current agent name
    agent_display_name: Optional[str] = None  # User-friendly agent name
    coordinator_info: Optional[Dict[str, Any]] = None  # Coordinator metadata

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint for the living form conversation"""
    try:
        logger.info(f"Processing chat request for session: {chat_request.session_id}")
        
        # Process message through improved agent coordinator
        response_data = await agent_coordinator.process_message(
            user_message=chat_request.message,
            session_id=chat_request.session_id,
            form_data=chat_request.form_data
        )
        
        # Debug logging
        logger.info(f"Response data keys: {list(response_data.keys())}")
        logger.info(f"Agent display name: {response_data.get('agent_display_name', 'NOT FOUND')}")
        logger.info(f"Current agent: {response_data.get('current_agent', 'NOT FOUND')}")
        logger.info(f"Coordinator info: {response_data.get('coordinator_info', 'NOT FOUND')}")
        
        # Get session info for response
        session_info = await agent_coordinator.get_session_info(chat_request.session_id)
        
        # Create response
        chat_response = ChatResponse(
            response=response_data.get("response") or "",
            form_html=response_data.get("form_html"),
            inline_guidance=response_data.get("inline_guidance"),
            conversation_state=response_data.get("coordinator_info", {}).get("current_step", "unknown"),
            cost_info=response_data.get("cost_info", {"total_cost": 0.0}),
            session_id=chat_request.session_id,
            notepad_content=response_data.get("enhanced_notepad", response_data.get("notepad_content", "")),
            current_agent=response_data.get("current_agent", "Unknown"),
            agent_display_name=response_data.get("agent_display_name", "Unknown Agent"),
            coordinator_info=response_data.get("coordinator_info", {})
        )
        
        # Debug logging
        logger.info(f"Final response - current_agent: {chat_response.current_agent}")
        logger.info(f"Final response - agent_display_name: {chat_response.agent_display_name}")
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/notepad")
async def get_session_notepad(session_id: str):
    """Get the Scribe AI notepad content for a session"""
    session_info = await agent_coordinator.get_session_info(session_id)
    
    if "error" in session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "notepad_content": session_info.get("notepad_content", ""),
        "conversation_length": session_info.get("conversation_length", 0),
        "last_updated": datetime.now().isoformat()
    }

@app.get("/session/{session_id}/cost")
async def get_session_costs(session_id: str):
    """Get cost breakdown for a session"""
    session_info = await agent_coordinator.get_session_info(session_id)
    
    if "error" in session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get cost summary from cost manager
    cost_summary = cost_manager.get_cost_summary(session_info)
    
    return {
        "total_cost": cost_summary.get("total_cost", 0.0),
        "interactions": cost_summary.get("interactions_count", 0),
        "cost_breakdown": cost_summary.get("cost_breakdown", {}),
        "budget_remaining": cost_summary.get("budget_remaining", 0.0)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    system_status = await agent_coordinator.get_system_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": system_status.get("active_sessions", 0),
        "system_health": system_status.get("system_health", "unknown")
    }

@app.get("/test-ai")
async def test_ai_endpoint():
    """Test AI endpoints to check if they're working"""
    test_results = {}
    
    # Test OpenAI O4-mini (primary model)
    try:
        response = await ai_client.generate_response(
            user_message="Hello, this is a test message.",
            conversation_context={"current_step": "test"},
            model_type=ModelType.O4_MINI
        )
        test_results["openai_o4_mini"] = {
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