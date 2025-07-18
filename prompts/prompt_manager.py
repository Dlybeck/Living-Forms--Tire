"""
Centralized prompt management for the Living Form Tire Sales Assistant
This module contains all prompts used throughout the system for easy tracking and management.
"""

from .system_prompt import SYSTEM_PROMPT
from .agent_prompt import AGENT_SYSTEM_PROMPT
from .tire_size_agent_prompt import TIRE_SIZE_AGENT_SYSTEM_PROMPT, TIRE_SIZE_AGENT_PROMPT
from .driving_info_agent_prompt import DRIVING_INFO_AGENT_SYSTEM_PROMPT, DRIVING_INFO_AGENT_PROMPT
from .preferences_agent_prompt import PREFERENCES_AGENT_SYSTEM_PROMPT, PREFERENCES_AGENT_PROMPT
from .recommendation_agent_prompt import RECOMMENDATION_AGENT_SYSTEM_PROMPT, RECOMMENDATION_AGENT_PROMPT

class PromptManager:
    """
    Centralized prompt management system
    Makes it easy to track and update all prompts used by different models
    """
    
    def __init__(self):
        self.prompts = {
            'main_system': SYSTEM_PROMPT,
            'agent_system': AGENT_SYSTEM_PROMPT,
            'tire_size_system': TIRE_SIZE_AGENT_SYSTEM_PROMPT,
            'tire_size_agent': TIRE_SIZE_AGENT_PROMPT,
            'driving_info_system': DRIVING_INFO_AGENT_SYSTEM_PROMPT,
            'driving_info_agent': DRIVING_INFO_AGENT_PROMPT,
            'preferences_system': PREFERENCES_AGENT_SYSTEM_PROMPT,
            'preferences_agent': PREFERENCES_AGENT_PROMPT,
            'recommendation_system': RECOMMENDATION_AGENT_SYSTEM_PROMPT,
            'recommendation_agent': RECOMMENDATION_AGENT_PROMPT,
        }
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get a specific prompt by name"""
        if prompt_name not in self.prompts:
            raise ValueError(f"Unknown prompt: {prompt_name}. Available: {list(self.prompts.keys())}")
        return self.prompts[prompt_name]
    
    def list_prompts(self) -> list:
        """List all available prompts"""
        return list(self.prompts.keys())
    
    def update_prompt(self, prompt_name: str, new_prompt: str):
        """Update a specific prompt"""
        if prompt_name not in self.prompts:
            raise ValueError(f"Unknown prompt: {prompt_name}. Available: {list(self.prompts.keys())}")
        self.prompts[prompt_name] = new_prompt
    
    def get_prompt_info(self) -> dict:
        """Get information about all prompts"""
        info = {}
        for name, prompt in self.prompts.items():
            info[name] = {
                'length': len(prompt),
                'word_count': len(prompt.split()),
                'line_count': len(prompt.split('\n')),
                'preview': prompt[:200] + '...' if len(prompt) > 200 else prompt
            }
        return info

# Global prompt manager instance
prompt_manager = PromptManager()

# Convenience functions for backward compatibility
def get_main_system_prompt() -> str:
    """Get the main system prompt used by the AI client"""
    return prompt_manager.get_prompt('main_system')

def get_agent_system_prompt() -> str:
    """Get the agent system prompt used by the tire sales agent"""
    return prompt_manager.get_prompt('agent_system')

def get_tire_size_system_prompt() -> str:
    """Get the tire size agent system prompt"""
    return prompt_manager.get_prompt('tire_size_system')

def get_tire_size_agent_prompt() -> str:
    """Get the tire size agent prompt"""
    return prompt_manager.get_prompt('tire_size_agent')

def get_driving_info_system_prompt() -> str:
    """Get the driving info agent system prompt"""
    return prompt_manager.get_prompt('driving_info_system')

def get_driving_info_agent_prompt() -> str:
    """Get the driving info agent prompt"""
    return prompt_manager.get_prompt('driving_info_agent')

def get_preferences_system_prompt() -> str:
    """Get the preferences agent system prompt"""
    return prompt_manager.get_prompt('preferences_system')

def get_preferences_agent_prompt() -> str:
    """Get the preferences agent prompt"""
    return prompt_manager.get_prompt('preferences_agent')

def get_recommendation_system_prompt() -> str:
    """Get the recommendation agent system prompt"""
    return prompt_manager.get_prompt('recommendation_system')

def get_recommendation_agent_prompt() -> str:
    """Get the recommendation agent prompt"""
    return prompt_manager.get_prompt('recommendation_agent') 