"""
State Manager for Living Form Tire Sales Assistant
Provides immutable state management with proper async handling
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, replace
from enum import Enum
from utils.conversation_enums import ConversationStep, DataCategory

logger = logging.getLogger(__name__)

class StateValidationError(Exception):
    """Raised when state validation fails"""
    pass

@dataclass(frozen=True)
class ConversationState:
    """
    Immutable conversation state
    All updates create new state objects
    """
    current_step: ConversationStep
    current_agent: str
    shared_data: Dict[str, Any]
    important_data: Dict[str, Any]
    conversation_summary: str
    session_start_time: datetime
    last_updated: datetime
    handoff_info: Optional[Dict[str, Any]] = None
    
    def update(self, **kwargs) -> 'ConversationState':
        """Create new state with updates"""
        return replace(self, **kwargs, last_updated=datetime.now())
    
    def get_data(self, category: DataCategory) -> Any:
        """Get data for a specific category"""
        return self.shared_data.get(category.value)
    
    def has_data(self, category: DataCategory) -> bool:
        """Check if data exists for a category"""
        return category.value in self.shared_data and self.shared_data[category.value]
    
    def get_important_data(self, key: str) -> Any:
        """Get important data by key"""
        return self.important_data.get(key)
    
    def is_step_complete(self, step: ConversationStep) -> bool:
        """Check if a step is complete based on data availability"""
        if step == ConversationStep.GREETING:
            return self.has_data(DataCategory.VEHICLE_INFO) or self.has_data(DataCategory.TIRE_SPECS)
        elif step == ConversationStep.TIRE_SIZE_DISCOVERY:
            return self.has_data(DataCategory.TIRE_SPECS)
        elif step == ConversationStep.DRIVING_INFO_COLLECTION:
            return self.has_data(DataCategory.DRIVING_PATTERNS)
        elif step == ConversationStep.PREFERENCES_GATHERING:
            return self.has_data(DataCategory.BUDGET_PREFERENCES)
        elif step == ConversationStep.RECOMMENDATION_GENERATION:
            return (self.has_data(DataCategory.TIRE_SPECS) and 
                   self.has_data(DataCategory.DRIVING_PATTERNS) and 
                   self.has_data(DataCategory.BUDGET_PREFERENCES))
        return False

class StateManager:
    """
    Thread-safe state manager with immutable state objects
    """
    
    def __init__(self):
        self._state: Optional[ConversationState] = None
        self._lock = asyncio.Lock()
        self._validation_rules = self._setup_validation_rules()
        
        logger.info("StateManager initialized")
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules for state transitions"""
        return {
            'step_transitions': {
                ConversationStep.GREETING: [ConversationStep.TIRE_SIZE_DISCOVERY],
                ConversationStep.TIRE_SIZE_DISCOVERY: [ConversationStep.DRIVING_INFO_COLLECTION],
                ConversationStep.DRIVING_INFO_COLLECTION: [ConversationStep.PREFERENCES_GATHERING],
                ConversationStep.PREFERENCES_GATHERING: [ConversationStep.RECOMMENDATION_GENERATION],
                ConversationStep.RECOMMENDATION_GENERATION: [ConversationStep.COMPARISON_ANALYSIS],
                ConversationStep.COMPARISON_ANALYSIS: [ConversationStep.FINAL_SELECTION],
                ConversationStep.FINAL_SELECTION: [ConversationStep.COMPLETED]
            },
            'required_data': {
                ConversationStep.TIRE_SIZE_DISCOVERY: [DataCategory.TIRE_SPECS],
                ConversationStep.DRIVING_INFO_COLLECTION: [DataCategory.DRIVING_PATTERNS],
                ConversationStep.PREFERENCES_GATHERING: [DataCategory.BUDGET_PREFERENCES],
                ConversationStep.RECOMMENDATION_GENERATION: [
                    DataCategory.TIRE_SPECS, 
                    DataCategory.DRIVING_PATTERNS, 
                    DataCategory.BUDGET_PREFERENCES
                ]
            }
        }
    
    async def initialize_session(self, session_id: str) -> ConversationState:
        """Initialize a new session state"""
        async with self._lock:
            if self._state is not None:
                logger.warning("Session already initialized, returning existing state")
                return self._state
            
            self._state = ConversationState(
                current_step=ConversationStep.GREETING,
                current_agent="TireSizeAgent",
                shared_data={},
                important_data={},
                conversation_summary="",
                session_start_time=datetime.now(),
                last_updated=datetime.now()
            )
            
            logger.info(f"Initialized new session state: {session_id}")
            return self._state
    
    async def get_state(self) -> Optional[ConversationState]:
        """Get current state (thread-safe)"""
        async with self._lock:
            return self._state
    
    async def update_state(self, **kwargs) -> ConversationState:
        """Update state (thread-safe, creates new state object)"""
        async with self._lock:
            if self._state is None:
                raise StateValidationError("No state initialized")
            
            # Validate updates if they include step changes
            if 'current_step' in kwargs:
                await self._validate_step_transition(self._state.current_step, kwargs['current_step'])
            
            # Create new state
            new_state = self._state.update(**kwargs)
            
            # Validate new state
            await self._validate_state(new_state)
            
            # Update internal state
            self._state = new_state
            
            logger.info(f"State updated: {list(kwargs.keys())}")
            return new_state
    
    async def update_shared_data(self, category: DataCategory, data: Any, agent: str) -> ConversationState:
        """Update shared data for a category"""
        async with self._lock:
            if self._state is None:
                raise StateValidationError("No state initialized")
            
            # Create new shared data dict
            new_shared_data = self._state.shared_data.copy()
            new_shared_data[category.value] = data
            
            # Create new state
            new_state = self._state.update(
                shared_data=new_shared_data,
                current_agent=agent
            )
            
            # Update internal state
            self._state = new_state
            
            logger.info(f"Updated shared data for {category.value}: {data}")
            return new_state
    
    async def update_important_data(self, key: str, value: Any, agent: str) -> ConversationState:
        """Update important data"""
        async with self._lock:
            if self._state is None:
                raise StateValidationError("No state initialized")
            
            # Create new important data dict
            new_important_data = self._state.important_data.copy()
            new_important_data[key] = value
            
            # Create new state
            new_state = self._state.update(
                important_data=new_important_data,
                current_agent=agent
            )
            
            # Update internal state
            self._state = new_state
            
            logger.info(f"Updated important data: {key} = {value}")
            return new_state
    
    async def advance_step(self, new_step: ConversationStep, agent: str) -> ConversationState:
        """Advance to next step with validation"""
        async with self._lock:
            if self._state is None:
                raise StateValidationError("No state initialized")
            
            # Validate step transition
            await self._validate_step_transition(self._state.current_step, new_step)
            
            # Create new state
            new_state = self._state.update(
                current_step=new_step,
                current_agent=agent,
                handoff_info={
                    'from_step': self._state.current_step.value,
                    'to_step': new_step.value,
                    'from_agent': self._state.current_agent,
                    'to_agent': agent,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Update internal state
            self._state = new_state
            
            logger.info(f"Advanced step: {self._state.current_step.value} -> {new_step.value}")
            return new_state
    
    async def _validate_step_transition(self, current_step: ConversationStep, new_step: ConversationStep):
        """Validate step transition"""
        allowed_transitions = self._validation_rules['step_transitions'].get(current_step, [])
        
        if new_step not in allowed_transitions:
            raise StateValidationError(
                f"Invalid step transition: {current_step.value} -> {new_step.value}. "
                f"Allowed: {[step.value for step in allowed_transitions]}"
            )
    
    async def _validate_state(self, state: ConversationState):
        """Validate state completeness"""
        current_step = state.current_step
        required_data = self._validation_rules['required_data'].get(current_step, [])
        
        missing_data = []
        for data_category in required_data:
            if not state.has_data(data_category):
                missing_data.append(data_category.value)
        
        if missing_data:
            raise StateValidationError(
                f"Step {current_step.value} requires data: {missing_data}"
            )
    
    async def can_advance_to_step(self, target_step: ConversationStep) -> bool:
        """Check if we can advance to a specific step"""
        async with self._lock:
            if self._state is None:
                return False
            
            try:
                await self._validate_step_transition(self._state.current_step, target_step)
                return True
            except StateValidationError:
                return False
    
    async def get_next_step(self) -> Optional[ConversationStep]:
        """Get the next logical step"""
        async with self._lock:
            if self._state is None:
                return None
            
            allowed_transitions = self._validation_rules['step_transitions'].get(self._state.current_step, [])
            return allowed_transitions[0] if allowed_transitions else None
    
    async def get_missing_data(self) -> List[str]:
        """Get list of missing data for current step"""
        async with self._lock:
            if self._state is None:
                return []
            
            current_step = self._state.current_step
            required_data = self._validation_rules['required_data'].get(current_step, [])
            
            missing_data = []
            for data_category in required_data:
                if not self._state.has_data(data_category):
                    missing_data.append(data_category.value)
            
            return missing_data
    
    async def create_state_snapshot(self) -> Dict[str, Any]:
        """Create immutable snapshot of current state"""
        async with self._lock:
            if self._state is None:
                return {}
            
            return {
                'current_step': self._state.current_step.value,
                'current_agent': self._state.current_agent,
                'shared_data': self._state.shared_data.copy(),
                'important_data': self._state.important_data.copy(),
                'conversation_summary': self._state.conversation_summary,
                'session_start_time': self._state.session_start_time.isoformat(),
                'last_updated': self._state.last_updated.isoformat(),
                'handoff_info': self._state.handoff_info,
                'snapshot_timestamp': datetime.now().isoformat()
            }
    
    async def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state"""
        async with self._lock:
            if self._state is None:
                return {'status': 'no_state'}
            
            return {
                'current_step': self._state.current_step.value,
                'current_agent': self._state.current_agent,
                'data_categories': list(self._state.shared_data.keys()),
                'important_data_keys': list(self._state.important_data.keys()),
                'session_duration_minutes': int((datetime.now() - self._state.session_start_time).total_seconds() / 60),
                'last_updated': self._state.last_updated.isoformat()
            } 