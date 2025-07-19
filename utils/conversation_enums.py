"""
Conversation enums for the Living Form Tire Sales Assistant
"""

from enum import Enum

class ConversationStep(Enum):
    """Steps in the conversation flow"""
    GREETING = "greeting"
    TIRE_SIZE_DISCOVERY = "tire_size_discovery"
    DRIVING_INFO_COLLECTION = "driving_info_collection"
    PREFERENCES_GATHERING = "preferences_gathering"
    RECOMMENDATION_GENERATION = "recommendation_generation"
    COMPARISON_ANALYSIS = "comparison_analysis"
    FINAL_SELECTION = "final_selection"
    COMPLETED = "completed"

class DataCategory(Enum):
    """Categories for data organization"""
    VEHICLE_INFO = "vehicle_info"
    TIRE_SPECS = "tire_specs"
    DRIVING_PATTERNS = "driving_patterns"
    BUDGET_PREFERENCES = "budget_preferences"
    SPECIAL_CONSIDERATIONS = "special_considerations" 