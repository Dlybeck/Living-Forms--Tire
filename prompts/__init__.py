"""
Prompts package for the Living Form Tire Sales Assistant
Contains all prompts for easy viewing and refinement.
"""

from .system_prompt import SYSTEM_PROMPT
from .agent_prompt import AGENT_SYSTEM_PROMPT
from .prompt_manager import (
    prompt_manager, 
    get_main_system_prompt, 
    get_agent_system_prompt,
    get_tire_size_system_prompt,
    get_tire_size_agent_prompt,
    get_driving_info_system_prompt,
    get_driving_info_agent_prompt,
    get_preferences_system_prompt,
    get_preferences_agent_prompt,
    get_recommendation_system_prompt,
    get_recommendation_agent_prompt
)

__all__ = [
    'SYSTEM_PROMPT',
    'AGENT_SYSTEM_PROMPT', 
    'prompt_manager',
    'get_main_system_prompt',
    'get_agent_system_prompt',
    'get_tire_size_system_prompt',
    'get_tire_size_agent_prompt',
    'get_driving_info_system_prompt',
    'get_driving_info_agent_prompt',
    'get_preferences_system_prompt',
    'get_preferences_agent_prompt',
    'get_recommendation_system_prompt',
    'get_recommendation_agent_prompt'
] 