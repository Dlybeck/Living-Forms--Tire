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
    ai_notepad: str = ""  # Flexible markdown-style notepad for AI to record important information
    
    def __post_init__(self):
        """Initialize the roadmap with default goals"""
        self._initialize_goals()
        # Ensure ai_notepad is always a string
        if self.ai_notepad is None:
            self.ai_notepad = ""
    
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

    def write_to_notepad(self, content: str, section: Optional[str] = None):
        """Write content to the AI notepad in a flexible markdown-style format"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if not self.ai_notepad:
            # Initialize notepad
            self.ai_notepad = f"# AI Notepad\n\n*Started at {timestamp}*\n\n"
        
        if section:
            # Add section if it doesn't exist
            if f"## {section}" not in self.ai_notepad:
                self.ai_notepad += f"\n## {section}\n\n"
            
            # Add content to section
            self.ai_notepad += f"- **{timestamp}:** {content}\n"
        else:
            # Add general note
            self.ai_notepad += f"\n**{timestamp}:** {content}\n"
        
        # Add to conversation history
        self.add_conversation_event("notepad_updated", {
            "content": content,
            "section": section,
            "timestamp": timestamp
        })
        
        logger.info(f"Added to notepad: {content[:50]}...")
    
    def update_notepad_section(self, section: str, content: str):
        """Update or create a specific section in the notepad"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if not self.ai_notepad:
            self.ai_notepad = f"# AI Notepad\n\n*Started at {timestamp}*\n\n"
        
        # Check if section exists
        if f"## {section}" in self.ai_notepad:
            # Find the section and add to it
            lines = self.ai_notepad.split('\n')
            section_index = None
            
            for i, line in enumerate(lines):
                if line.strip() == f"## {section}":
                    section_index = i
                    break
            
            if section_index is not None:
                # Insert new content after section header
                lines.insert(section_index + 1, f"\n- **{timestamp}:** {content}")
                self.ai_notepad = '\n'.join(lines)
        else:
            # Create new section
            self.ai_notepad += f"\n## {section}\n\n- **{timestamp}:** {content}\n"
        
        # Add to conversation history
        self.add_conversation_event("notepad_section_updated", {
            "section": section,
            "content": content,
            "timestamp": timestamp
        })
        
        logger.info(f"Updated notepad section [{section}]: {content[:50]}...")
    
    def update_notepad_entry(self, section: str, key: str, value: str, replace_existing: bool = True):
        """Update a specific entry in the notepad, replacing existing entries if needed"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if not self.ai_notepad:
            self.ai_notepad = f"# AI Notepad\n\n*Started at {timestamp}*\n\n"
        
        # Check if section exists
        if f"## {section}" in self.ai_notepad:
            lines = self.ai_notepad.split('\n')
            section_start = None
            section_end = None
            
            # Find section boundaries
            for i, line in enumerate(lines):
                if line.strip() == f"## {section}":
                    section_start = i
                elif section_start is not None and line.startswith('## ') and i > section_start:
                    section_end = i
                    break
            
            if section_end is None:
                section_end = len(lines)
            
            # Check if key already exists in section
            key_exists = False
            for i in range(section_start + 1, section_end):
                if lines[i].strip().startswith(f"- **") and f"{key}:" in lines[i]:
                    if replace_existing:
                        lines[i] = f"- **{timestamp}:** {key}: {value}"
                        key_exists = True
                        break
                    else:
                        return  # Don't replace existing entry
            
            if not key_exists:
                # Add new entry to section
                lines.insert(section_start + 1, f"- **{timestamp}:** {key}: {value}")
            
            self.ai_notepad = '\n'.join(lines)
        else:
            # Create new section with entry
            self.ai_notepad += f"\n## {section}\n\n- **{timestamp}:** {key}: {value}\n"
        
        # Add to conversation history
        self.add_conversation_event("notepad_entry_updated", {
            "section": section,
            "key": key,
            "value": value,
            "timestamp": timestamp
        })
        
        logger.info(f"Updated notepad entry [{section}][{key}]: {value[:50]}...")
    
    def clean_notepad(self):
        """Clean up the notepad by removing outdated or redundant information"""
        if not self.ai_notepad:
            return
        
        lines = self.ai_notepad.split('\n')
        cleaned_lines = []
        current_section = None
        seen_entries = set()
        
        for line in lines:
            line = line.strip()
            
            # Keep section headers
            if line.startswith('## '):
                current_section = line
                cleaned_lines.append(line)
                continue
            
            # Keep non-entry lines (empty lines, timestamps, etc.)
            if not line.startswith('- **'):
                cleaned_lines.append(line)
                continue
            
            # Process entry lines
            if line.startswith('- **'):
                # Extract the content part (after timestamp)
                content_start = line.find(':** ') + 4
                if content_start > 4:
                    content = line[content_start:]
                    
                    # Create a unique identifier for this entry
                    entry_id = f"{current_section}:{content}"
                    
                    # Only keep if we haven't seen this exact content before
                    if entry_id not in seen_entries:
                        seen_entries.add(entry_id)
                        cleaned_lines.append(line)
        
        self.ai_notepad = '\n'.join(cleaned_lines)
        logger.info("Cleaned notepad - removed redundant entries")
    
    def get_notepad_content(self) -> str:
        """Get the full notepad content"""
        # Clean the notepad before returning
        self.clean_notepad()
        return self.ai_notepad if self.ai_notepad else "# AI Notepad\n\n*No information recorded yet.*\n"
    
    def search_notepad(self, query: str) -> List[str]:
        """Search the notepad for specific information"""
        if not self.ai_notepad:
            return []
        
        lines = self.ai_notepad.split('\n')
        matches = []
        
        for line in lines:
            if query.lower() in line.lower():
                matches.append(line.strip())
        
        return matches
    
    def get_notepad_summary(self) -> str:
        """Get a summary of the notepad for context"""
        if not self.ai_notepad:
            return "No information recorded yet."
        
        # Return the full notepad content for context
        return self.ai_notepad 