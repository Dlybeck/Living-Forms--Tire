from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import Dict, Optional, Any
import logging
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Import our modules
from core.coordinator import Coordinator
from core.ai_client import AIClient, ModelType

from core.form_builder import FormBuilder

app = FastAPI(title="Living Form Tire Sales Agent", version="1.0.0")

# Mount templates
templates = Jinja2Templates(directory="web")

# Initialize components
ai_client = AIClient()
form_builder = FormBuilder()
coordinator = Coordinator(ai_client, form_builder)

# Request/Response models
class ChatMessage(BaseModel):
    message: str
    session_id: str
    form_data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    form_html: Optional[str] = None
    conversation_state: str
    session_id: str
    notepad_content: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint for the living form conversation"""
    try:
        logger.info(f"Processing chat request for session: {chat_request.session_id}")
        
        # Process message through agent coordinator
        response_data = await coordinator.process_message(
            user_message=chat_request.message,
            session_id=chat_request.session_id,
            form_data=chat_request.form_data
        )
        
        # Get session info for response
        session_info = await coordinator.get_session_info(chat_request.session_id)
        
        # Create response
        chat_response = ChatResponse(
            response=response_data.get("response") or "",
            form_html=response_data.get("form_html"),
            conversation_state=response_data.get("coordinator_info", {}).get("current_step", "unknown"),
            session_id=chat_request.session_id,
            notepad_content=response_data.get("ai_notepad", "")
        )
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/notepad")
async def get_session_notepad(session_id: str):
    """Get the AI notepad content for a session"""
    session_info = await coordinator.get_session_info(session_id)
    
    if "error" in session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "notepad_content": session_info.get("ai_notepad", "")
    }



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    system_status = await coordinator.get_system_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": system_status.get("active_sessions", 0),
        "system_health": system_status.get("system_health", "unknown")
    }



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 