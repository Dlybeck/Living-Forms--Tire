"""
Prompts package for the Living Form Tire Sales Assistant
Import all prompts from their individual files for easy access.
"""

# Import all prompts from their separate files
from .system_prompt import SYSTEM_PROMPT
from .tire_size_agent_prompt import TIRE_SIZE_AGENT_PROMPT
from .driving_info_agent_prompt import DRIVING_INFO_AGENT_PROMPT
from .preferences_agent_prompt import PREFERENCES_AGENT_PROMPT
from .recommendation_agent_prompt import RECOMMENDATION_AGENT_PROMPT
from .scribe_agent_prompt import SCRIBE_AGENT_PROMPT

# Convenience functions for backward compatibility
def get_main_system_prompt():
    return SYSTEM_PROMPT

def get_tire_size_agent_prompt():
    return TIRE_SIZE_AGENT_PROMPT

def get_driving_info_agent_prompt():
    return DRIVING_INFO_AGENT_PROMPT

def get_preferences_agent_prompt():
    return PREFERENCES_AGENT_PROMPT

def get_recommendation_agent_prompt():
    return RECOMMENDATION_AGENT_PROMPT

def get_scribe_system_prompt_wrapper():
    return SCRIBE_AGENT_PROMPT

def get_scribe_agent_prompt_wrapper():
    return "Extract and record any important information from this conversation." 