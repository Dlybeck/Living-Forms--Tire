"""
Shared utilities for the Living Form Tire Sales Agent
"""

from typing import Dict, Any

def create_error_response(error_message: str, include_coordinator_info: bool = False) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        error_message: The error message to include
        include_coordinator_info: Whether to include coordinator metadata
    """
    response = {
        "response": f"I apologize, but I encountered an error: {error_message}. Please try again.",
        "form_html": "",
        "ai_notepad": ""
    }
    
    if include_coordinator_info:
        response["coordinator_info"] = {
            "current_step": "error"
        }
    
    return response 