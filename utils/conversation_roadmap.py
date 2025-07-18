"""
Conversation Roadmap System
Tracks conversation state, goals, and progression through the tire selection process
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationStep(Enum):
    """Steps in the tire selection conversation"""
    GREETING = "greeting"
    TIRE_SIZE_DISCOVERY = "tire_size_discovery"
    DRIVING_INFO_COLLECTION = "driving_info_collection"
    PREFERENCES_GATHERING = "preferences_gathering"
    RECOMMENDATION_GENERATION = "recommendation_generation"
    COMPARISON_ANALYSIS = "comparison_analysis"
    FINAL_SELECTION = "final_selection"
    COMPLETED = "completed"

class DataCategory(Enum):
    """Categories of data needed for tire recommendations"""
    VEHICLE_INFO = "vehicle_info"
    TIRE_SPECS = "tire_specs"
    DRIVING_PATTERNS = "driving_patterns"
    BUDGET_PREFERENCES = "budget_preferences"
    CURRENT_TIRE_STATUS = "current_tire_status"
    SPECIAL_CONSIDERATIONS = "special_considerations"

@dataclass
class ConversationGoal:
    """Represents a specific goal in the conversation"""
    step: ConversationStep
    description: str
    required_data: List[DataCategory]
    optional_data: List[DataCategory] = field(default_factory=list)
    completed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ConversationRoadmap:
    """Manages the conversation flow and state"""
    
    current_step: ConversationStep = ConversationStep.GREETING
    goals: List[ConversationGoal] = field(default_factory=list)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    user_situation: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the roadmap with default goals"""
        self._initialize_goals()
    
    def _initialize_goals(self):
        """Set up the conversation goals in order"""
        self.goals = [
            ConversationGoal(
                step=ConversationStep.GREETING,
                description="Welcome user and understand their initial situation",
                required_data=[],
                optional_data=[DataCategory.VEHICLE_INFO]
            ),
            ConversationGoal(
                step=ConversationStep.TIRE_SIZE_DISCOVERY,
                description="Discover the user's tire size through various methods",
                required_data=[DataCategory.TIRE_SPECS],
                optional_data=[DataCategory.VEHICLE_INFO]
            ),
            ConversationGoal(
                step=ConversationStep.DRIVING_INFO_COLLECTION,
                description="Understand how the user drives and uses their vehicle",
                required_data=[DataCategory.DRIVING_PATTERNS],
                optional_data=[DataCategory.CURRENT_TIRE_STATUS]
            ),
            ConversationGoal(
                step=ConversationStep.PREFERENCES_GATHERING,
                description="Gather budget and performance preferences",
                required_data=[DataCategory.BUDGET_PREFERENCES],
                optional_data=[DataCategory.SPECIAL_CONSIDERATIONS]
            ),
            ConversationGoal(
                step=ConversationStep.RECOMMENDATION_GENERATION,
                description="Generate personalized tire recommendations",
                required_data=[DataCategory.TIRE_SPECS, DataCategory.DRIVING_PATTERNS, DataCategory.BUDGET_PREFERENCES],
                optional_data=[DataCategory.SPECIAL_CONSIDERATIONS]
            ),
            ConversationGoal(
                step=ConversationStep.COMPARISON_ANALYSIS,
                description="Compare different tire options and explain differences",
                required_data=[],
                optional_data=[]
            ),
            ConversationGoal(
                step=ConversationStep.FINAL_SELECTION,
                description="Help user make final tire selection",
                required_data=[],
                optional_data=[]
            ),
            ConversationGoal(
                step=ConversationStep.COMPLETED,
                description="Conversation completed successfully",
                required_data=[],
                optional_data=[]
            )
        ]
    
    def get_current_goal(self) -> ConversationGoal:
        """Get the current conversation goal"""
        for goal in self.goals:
            if goal.step == self.current_step:
                return goal
        raise ValueError(f"No goal found for step: {self.current_step}")
    
    def advance_to_next_step(self) -> ConversationStep:
        """Move to the next conversation step"""
        current_index = None
        for i, goal in enumerate(self.goals):
            if goal.step == self.current_step:
                current_index = i
                break
        
        if current_index is None:
            raise ValueError(f"Current step {self.current_step} not found in goals")
        
        # Mark current goal as completed
        self.goals[current_index].completed = True
        self.goals[current_index].completed_at = datetime.now()
        
        # Move to next step
        if current_index + 1 < len(self.goals):
            next_step = self.goals[current_index + 1].step
            self.current_step = next_step
            self.goals[current_index + 1].started_at = datetime.now()
            logger.info(f"Advanced conversation from {self.goals[current_index].step.value} to {next_step.value}")
            return next_step
        else:
            # Already at the end
            return self.current_step
    
    def can_advance_to_step(self, target_step: ConversationStep) -> bool:
        """Check if we can advance to a specific step based on data completeness"""
        target_goal = None
        for goal in self.goals:
            if goal.step == target_step:
                target_goal = goal
                break
        
        if not target_goal:
            return False
        
        # Check if required data is available
        for data_category in target_goal.required_data:
            if not self.has_data_for_category(data_category):
                return False
        
        return True
    
    def has_data_for_category(self, category: DataCategory) -> bool:
        """Check if we have data for a specific category"""
        category_key = category.value
        return category_key in self.shared_data and self.shared_data[category_key]
    
    def get_missing_data(self) -> List[DataCategory]:
        """Get list of missing data categories for current goal"""
        current_goal = self.get_current_goal()
        missing = []
        
        for category in current_goal.required_data:
            if not self.has_data_for_category(category):
                missing.append(category)
        
        return missing
    
    def update_shared_data(self, category: DataCategory, data: Any):
        """Update shared data for a category"""
        self.shared_data[category.value] = data
        logger.info(f"Updated shared data for {category.value}: {data}")
    
    def get_shared_data(self, category: DataCategory) -> Any:
        """Get shared data for a category"""
        return self.shared_data.get(category.value)
    
    def add_conversation_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event to the conversation history"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "step": self.current_step.value,
            "data": data
        }
        self.conversation_history.append(event)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation state"""
        return {
            "current_step": self.current_step.value,
            "current_goal": self.get_current_goal().description,
            "missing_data": [cat.value for cat in self.get_missing_data()],
            "completed_goals": [goal.step.value for goal in self.goals if goal.completed],
            "shared_data_keys": list(self.shared_data.keys()),
            "conversation_length": len(self.conversation_history)
        } 