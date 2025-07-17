from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid

class ConversationStep(Enum):
    """Enum for conversation steps in the living form"""
    GREETING = "greeting"
    VEHICLE_INFO = "vehicle_info"
    TIRE_SPECS = "tire_specs"
    DRIVING_PATTERNS = "driving_patterns"
    BUDGET_PREFERENCES = "budget_preferences"
    CURRENT_TIRE_STATUS = "current_tire_status"
    SPECIAL_CONSIDERATIONS = "special_considerations"
    RECOMMENDATION = "recommendation"
    COMPARISON = "comparison"
    FINAL_SELECTION = "final_selection"
    COMPLETED = "completed"

class UserKnowledgeLevel(Enum):
    """User's knowledge level about tires"""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class DataCategory(Enum):
    """Data collection categories"""
    VEHICLE_INFO = "vehicle_info"
    TIRE_SPECS = "tire_specs"
    DRIVING_PATTERNS = "driving_patterns"
    BUDGET_PREFERENCES = "budget_preferences"
    CURRENT_TIRE_STATUS = "current_tire_status"
    SPECIAL_CONSIDERATIONS = "special_considerations"

@dataclass
class InteractionLog:
    """Log entry for each interaction"""
    timestamp: datetime
    user_message: str
    ai_response: str
    cost: float
    model_used: str
    form_data: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0

@dataclass
class ConversationState:
    """
    Maintains the state of the living form conversation
    Tracks user progress, context, and form completion with structured data collection
    """
    session_id: str
    current_step: ConversationStep = ConversationStep.GREETING
    user_knowledge_level: UserKnowledgeLevel = UserKnowledgeLevel.INTERMEDIATE
    
    # Structured data collection - organized by category
    vehicle_info: Dict[str, Any] = field(default_factory=dict)  # Make, model, year, trim level
    tire_specs: Dict[str, Any] = field(default_factory=dict)    # Current size, quantity needed
    driving_patterns: Dict[str, Any] = field(default_factory=dict)  # Daily mileage, highway vs city, seasonal needs
    budget_preferences: Dict[str, Any] = field(default_factory=dict)  # Price range, preferred brands, warranty
    current_tire_status: Dict[str, Any] = field(default_factory=dict)  # Condition, age, reason for replacement
    special_considerations: Dict[str, Any] = field(default_factory=dict)  # Performance needs, weather, towing
    
    # Legacy fields for backward compatibility
    tire_preferences: Dict[str, Any] = field(default_factory=dict)
    current_tire_info: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, Any] = field(default_factory=dict)
    
    # Form data from embedded forms
    form_data: Dict[str, Any] = field(default_factory=dict)
    
    # Form submission tracking - track completion by category
    completed_categories: List[DataCategory] = field(default_factory=list)
    completed_forms: List[str] = field(default_factory=list)
    last_form_submission: Optional[str] = field(default=None)
    
    # Researched information
    researched_info: Dict[str, Any] = field(default_factory=dict)
    
    # Conversation tracking
    conversation_history: List[InteractionLog] = field(default_factory=list)
    
    # Cost tracking
    total_cost: float = 0.0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Quality tracking
    user_satisfaction_signals: List[str] = field(default_factory=list)
    confusion_signals: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize default values after creation"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        
        # Initialize cost breakdown
        self.cost_breakdown = {
            "api_calls": 0.0,
            "model_usage": 0.0,
            "total": 0.0
        }
    
    def update_form_data(self, new_form_data: Dict[str, Any]):
        """Update form data from user input and categorize it"""
        self.form_data.update(new_form_data)
        self.last_updated = datetime.now()
        
        # Parse form data into structured categories
        self._categorize_form_data(new_form_data)
    
    def _categorize_form_data(self, form_data: Dict[str, Any]):
        """Categorize form data into structured collection categories"""
        # Vehicle Information: Make, model, year, trim level
        vehicle_fields = ['make', 'model', 'year', 'trim', 'trim_level']
        for field in vehicle_fields:
            if field in form_data and form_data[field]:
                self.vehicle_info[field] = form_data[field]
        
        # Tire Specifications: Current size, quantity needed
        tire_spec_fields = ['current_tire_size', 'tire_size', 'quantity_needed', 'tire_quantity', 'number_of_tires', 'tire_count']
        for field in tire_spec_fields:
            if field in form_data and form_data[field]:
                # Normalize common field names
                if field in ['tire_count', 'tire_quantity', 'number_of_tires']:
                    self.tire_specs['quantity_needed'] = form_data[field]
                else:
                    self.tire_specs[field] = form_data[field]
        
        # Driving Patterns: Daily mileage, highway vs city driving, seasonal needs
        driving_fields = ['daily_mileage', 'mileage', 'highway_driving', 'city_driving', 'seasonal_needs', 'driving_type']
        for field in driving_fields:
            if field in form_data and form_data[field]:
                self.driving_patterns[field] = form_data[field]
        
        # Budget/Preferences: Price range, preferred brands, warranty preferences
        budget_fields = ['budget', 'price_range', 'budget_min', 'budget_max', 'preferred_brands', 'brand_preferences', 'warranty_preferences']
        for field in budget_fields:
            if field in form_data and form_data[field]:
                self.budget_preferences[field] = form_data[field]
        
        # Current Tire Status: Condition, age, reason for replacement
        status_fields = ['tire_condition', 'age', 'replacement_reason', 'current_tire_condition', 'tire_wear']
        for field in status_fields:
            if field in form_data and form_data[field]:
                self.current_tire_status[field] = form_data[field]
        
        # Special Considerations: Performance needs, weather conditions, towing requirements
        special_fields = ['performance_needs', 'weather_conditions', 'towing_requirements', 'special_needs', 'performance_priorities']
        for field in special_fields:
            if field in form_data and form_data[field]:
                self.special_considerations[field] = form_data[field]
        
        # Legacy compatibility - keep old fields updated
        self._update_legacy_fields()
    
    def _update_legacy_fields(self):
        """Update legacy fields for backward compatibility"""
        # Update tire_preferences from new structured fields
        if self.budget_preferences:
            self.tire_preferences.update(self.budget_preferences)
        if self.special_considerations:
            self.tire_preferences.update(self.special_considerations)
        
        # Update current_tire_info from new structured fields
        if self.tire_specs:
            self.current_tire_info.update(self.tire_specs)
        if self.current_tire_status:
            self.current_tire_info.update(self.current_tire_status)
        
        # Update user_context from new structured fields
        if self.driving_patterns:
            self.user_context.update(self.driving_patterns)
    
    def mark_category_completed(self, category: DataCategory):
        """Mark a data category as completed"""
        if category not in self.completed_categories:
            self.completed_categories.append(category)
        self.last_updated = datetime.now()
    
    def is_category_completed(self, category: DataCategory) -> bool:
        """Check if a data category has been completed"""
        return category in self.completed_categories
    
    def get_next_incomplete_category(self) -> Optional[DataCategory]:
        """Get the next incomplete category in the collection order"""
        category_order = [
            DataCategory.VEHICLE_INFO,
            DataCategory.TIRE_SPECS,
            DataCategory.DRIVING_PATTERNS,
            DataCategory.BUDGET_PREFERENCES,
            DataCategory.CURRENT_TIRE_STATUS,
            DataCategory.SPECIAL_CONSIDERATIONS
        ]
        
        for category in category_order:
            if not self.is_category_completed(category):
                return category
        
        return None
    
    def get_category_completion_status(self) -> Dict[DataCategory, bool]:
        """Get completion status for all categories"""
        return {
            DataCategory.VEHICLE_INFO: self.is_category_completed(DataCategory.VEHICLE_INFO),
            DataCategory.TIRE_SPECS: self.is_category_completed(DataCategory.TIRE_SPECS),
            DataCategory.DRIVING_PATTERNS: self.is_category_completed(DataCategory.DRIVING_PATTERNS),
            DataCategory.BUDGET_PREFERENCES: self.is_category_completed(DataCategory.BUDGET_PREFERENCES),
            DataCategory.CURRENT_TIRE_STATUS: self.is_category_completed(DataCategory.CURRENT_TIRE_STATUS),
            DataCategory.SPECIAL_CONSIDERATIONS: self.is_category_completed(DataCategory.SPECIAL_CONSIDERATIONS)
        }
    

    
    def store_researched_info(self, key: str, value: Any):
        """Store researched information (like tire sizes for specific trims)"""
        self.researched_info[key] = value
        self.last_updated = datetime.now()
    
    def get_researched_info(self, key: str) -> Optional[Any]:
        """Get researched information"""
        return self.researched_info.get(key)
    
    def has_researched_info(self, key: str) -> bool:
        """Check if we have researched information for a key"""
        return key in self.researched_info
    
    def get_missing_vehicle_info(self) -> List[str]:
        """Get list of missing vehicle information fields"""
        required_fields = ['make', 'model', 'year']
        optional_fields = ['trim', 'trim_level']
        
        missing_required = [field for field in required_fields if field not in self.vehicle_info or not self.vehicle_info[field]]
        missing_optional = [field for field in optional_fields if field not in self.vehicle_info or not self.vehicle_info[field]]
        
        return missing_required + missing_optional
    
    def get_missing_tire_specs(self) -> List[str]:
        """Get list of missing tire specification fields"""
        required_fields = ['quantity_needed']
        optional_fields = ['current_tire_size']
        
        missing_required = [field for field in required_fields if field not in self.tire_specs or not self.tire_specs[field]]
        missing_optional = [field for field in optional_fields if field not in self.tire_specs or not self.tire_specs[field]]
        
        return missing_required + missing_optional
    
    def get_missing_driving_patterns(self) -> List[str]:
        """Get list of missing driving pattern fields"""
        fields = ['daily_mileage', 'highway_driving', 'city_driving', 'seasonal_needs']
        return [field for field in fields if field not in self.driving_patterns or not self.driving_patterns[field]]
    
    def get_missing_budget_preferences(self) -> List[str]:
        """Get list of missing budget/preference fields"""
        fields = ['budget', 'price_range', 'preferred_brands']
        return [field for field in fields if field not in self.budget_preferences or not self.budget_preferences[field]]
    
    def get_missing_current_tire_status(self) -> List[str]:
        """Get list of missing current tire status fields"""
        fields = ['tire_condition', 'replacement_reason']
        return [field for field in fields if field not in self.current_tire_status or not self.current_tire_status[field]]
    
    def get_missing_special_considerations(self) -> List[str]:
        """Get list of missing special consideration fields"""
        fields = ['performance_needs', 'weather_conditions', 'towing_requirements']
        return [field for field in fields if field not in self.special_considerations or not self.special_considerations[field]]
    
    def is_ready_for_recommendations(self) -> bool:
        """Check if we have enough information for tire recommendations"""
        # Require at least vehicle info and some preferences
        has_vehicle_info = bool(self.vehicle_info.get('make') and self.vehicle_info.get('model') and self.vehicle_info.get('year'))
        has_some_preferences = bool(self.budget_preferences or self.driving_patterns or self.special_considerations)
        
        return has_vehicle_info and has_some_preferences
    

    
    def detect_user_knowledge_level(self, user_message: str) -> UserKnowledgeLevel:
        """Detect user's knowledge level from their message"""
        user_lower = user_message.lower()
        
        # Expert indicators
        expert_terms = ['sidewall', 'tread compound', 'load index', 'speed rating', 'utqg', 'DOT', 'ply rating']
        expert_score = sum(1 for term in expert_terms if term in user_lower)
        
        # Novice indicators
        novice_phrases = ['i dont know', 'what does that mean', 'i have no idea', 'explain', 'what is', 'help me understand']
        novice_score = sum(1 for phrase in novice_phrases if phrase in user_lower)
        
        if expert_score >= 2:
            self.user_knowledge_level = UserKnowledgeLevel.EXPERT
        elif novice_score >= 1:
            self.user_knowledge_level = UserKnowledgeLevel.NOVICE
        else:
            self.user_knowledge_level = UserKnowledgeLevel.INTERMEDIATE
        
        return self.user_knowledge_level
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get formatted conversation context for AI"""
        return {
            "session_id": self.session_id,
            "current_step": self.current_step.value,
            "user_knowledge_level": self.user_knowledge_level.value,
            "vehicle_info": self.vehicle_info,
            "tire_specs": self.tire_specs,
            "driving_patterns": self.driving_patterns,
            "budget_preferences": self.budget_preferences,
            "current_tire_status": self.current_tire_status,
            "special_considerations": self.special_considerations,
            "completion_status": self.get_category_completion_status(),
            "ready_for_recommendations": self.is_ready_for_recommendations(),
            "conversation_length": len(self.conversation_history),
            "total_cost": self.total_cost,
            "researched_info": self.researched_info
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "current_step": self.current_step.value,
            "user_knowledge_level": self.user_knowledge_level.value,
            "vehicle_info": self.vehicle_info,
            "tire_specs": self.tire_specs,
            "driving_patterns": self.driving_patterns,
            "budget_preferences": self.budget_preferences,
            "current_tire_status": self.current_tire_status,
            "special_considerations": self.special_considerations,
            "total_cost": self.total_cost,
            "cost_breakdown": self.cost_breakdown,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "conversation_history": [
                {
                    "timestamp": interaction.timestamp.isoformat(),
                    "user_message": interaction.user_message,
                    "ai_response": interaction.ai_response,
                    "cost": interaction.cost,
                    "model_used": interaction.model_used
                }
                for interaction in self.conversation_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create ConversationState from dictionary"""
        state = cls(session_id=data["session_id"])
        state.current_step = ConversationStep(data["current_step"])
        state.user_knowledge_level = UserKnowledgeLevel(data["user_knowledge_level"])
        state.vehicle_info = data["vehicle_info"]
        state.tire_specs = data["tire_specs"]
        state.driving_patterns = data["driving_patterns"]
        state.budget_preferences = data["budget_preferences"]
        state.current_tire_status = data["current_tire_status"]
        state.special_considerations = data["special_considerations"]
        state.total_cost = data["total_cost"]
        state.cost_breakdown = data["cost_breakdown"]
        state.created_at = datetime.fromisoformat(data["created_at"])
        state.last_updated = datetime.fromisoformat(data["last_updated"])
        
        # Reconstruct conversation history
        for interaction_data in data["conversation_history"]:
            interaction = InteractionLog(
                timestamp=datetime.fromisoformat(interaction_data["timestamp"]),
                user_message=interaction_data["user_message"],
                ai_response=interaction_data["ai_response"],
                cost=interaction_data["cost"],
                model_used=interaction_data["model_used"]
            )
            state.conversation_history.append(interaction)
        
        return state 

    def add_interaction(self, user_message: str, ai_response: str, cost: float, model_used: str, form_data: Optional[Dict[str, Any]] = None):
        """Add a new interaction to the conversation history"""
        interaction = InteractionLog(
            timestamp=datetime.now(),
            user_message=user_message,
            ai_response=ai_response,
            cost=cost,
            model_used=model_used,
            form_data=form_data
        )
        self.conversation_history.append(interaction)
        self.total_cost += cost
        self.cost_breakdown["total"] += cost
        self.cost_breakdown["api_calls"] += cost
        self.last_updated = datetime.now() 