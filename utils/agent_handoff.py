"""
Agent Handoff Protocol for Living Form Tire Sales Assistant
Manages proper handoffs between agents with state validation
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from utils.state_manager import ConversationState, StateValidationError
from utils.conversation_enums import ConversationStep, DataCategory

logger = logging.getLogger(__name__)

class HandoffValidationError(Exception):
    """Raised when handoff validation fails"""
    pass

class HandoffStatus(Enum):
    """Status of handoff operations"""
    PENDING = "pending"
    VALIDATED = "validated"
    EXECUTED = "executed"
    FAILED = "failed"

@dataclass
class HandoffMessage:
    """Represents a handoff message between agents"""
    handoff_id: str
    from_agent: str
    to_agent: str
    state_snapshot: ConversationState
    context: Dict[str, Any]
    validation_result: Dict[str, Any]
    timestamp: datetime
    status: HandoffStatus = HandoffStatus.PENDING

@dataclass
class HandoffValidation:
    """Validation result for handoff"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    required_data: List[str]
    optional_data: List[str]
    handoff_reason: str

class AgentHandoff:
    """
    Manages agent handoffs with proper validation and state management
    """
    
    def __init__(self):
        self.handoff_queue = asyncio.Queue()
        self.handoff_history: List[HandoffMessage] = []
        self._handoff_lock = asyncio.Lock()
        
        # Agent mapping for handoffs
        self.agent_mapping = {
            ConversationStep.GREETING: "TireSizeAgent",
            ConversationStep.TIRE_SIZE_DISCOVERY: "TireSizeAgent",
            ConversationStep.DRIVING_INFO_COLLECTION: "DrivingInfoAgent",
            ConversationStep.PREFERENCES_GATHERING: "PreferencesAgent",
            ConversationStep.RECOMMENDATION_GENERATION: "RecommendationAgent",
            ConversationStep.COMPARISON_ANALYSIS: "RecommendationAgent",
            ConversationStep.FINAL_SELECTION: "RecommendationAgent",
            ConversationStep.COMPLETED: "RecommendationAgent"
        }
        
        logger.info("AgentHandoff initialized")
    
    async def prepare_handoff(self, 
                            from_agent: str, 
                            to_agent: str, 
                            state: ConversationState,
                            context: Dict[str, Any]) -> HandoffMessage:
        """Prepare handoff with comprehensive validation"""
        
        handoff_id = str(uuid.uuid4())
        
        # Validate handoff
        validation_result = await self._validate_handoff(from_agent, to_agent, state, context)
        
        # Create handoff message
        handoff_msg = HandoffMessage(
            handoff_id=handoff_id,
            from_agent=from_agent,
            to_agent=to_agent,
            state_snapshot=state,
            context=context,
            validation_result=validation_result,
            timestamp=datetime.now()
        )
        
        if validation_result['is_valid']:
            handoff_msg.status = HandoffStatus.VALIDATED
            logger.info(f"Handoff validated: {from_agent} -> {to_agent}")
        else:
            handoff_msg.status = HandoffStatus.FAILED
            logger.error(f"Handoff validation failed: {validation_result['errors']}")
        
        # Add to history
        async with self._handoff_lock:
            self.handoff_history.append(handoff_msg)
        
        return handoff_msg
    
    async def execute_handoff(self, handoff_msg: HandoffMessage) -> Dict[str, Any]:
        """Execute the handoff"""
        
        if handoff_msg.status != HandoffStatus.VALIDATED:
            raise HandoffValidationError(f"Handoff not validated: {handoff_msg.status}")
        
        try:
            # Log handoff execution
            logger.info(f"Executing handoff: {handoff_msg.from_agent} -> {handoff_msg.to_agent}")
            
            # Update handoff status
            handoff_msg.status = HandoffStatus.EXECUTED
            
            # Create handoff result
            result = {
                'handoff_id': handoff_msg.handoff_id,
                'status': 'handoff_completed',
                'from_agent': handoff_msg.from_agent,
                'to_agent': handoff_msg.to_agent,
                'timestamp': handoff_msg.timestamp.isoformat(),
                'validation_passed': handoff_msg.validation_result['is_valid'],
                'handoff_reason': handoff_msg.validation_result.get('handoff_reason', ''),
                'context_summary': self._summarize_context(handoff_msg.context)
            }
            
            logger.info(f"Handoff completed successfully: {result}")
            return result
            
        except Exception as e:
            handoff_msg.status = HandoffStatus.FAILED
            logger.error(f"Handoff execution failed: {e}")
            raise HandoffValidationError(f"Handoff execution failed: {e}")
    
    async def _validate_handoff(self, from_agent: str, to_agent: str, state: ConversationState, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate handoff with comprehensive checks"""
        
        errors = []
        warnings = []
        required_data = []
        optional_data = []
        
        # Check if handoff is necessary
        if from_agent == to_agent:
            warnings.append(f"Handoff to same agent: {from_agent}")
        
        # Validate state completeness for target agent
        target_step = state.current_step
        target_agent_expected = self.agent_mapping.get(target_step)
        
        if target_agent_expected != to_agent:
            errors.append(f"Agent mismatch: expected {target_agent_expected} for step {target_step.value}, got {to_agent}")
        
        # Check required data for current step
        missing_data = await self._get_missing_data_for_step(target_step, state)
        if missing_data:
            errors.append(f"Missing required data for step {target_step.value}: {missing_data}")
        else:
            required_data = await self._get_required_data_for_step(target_step)
        
        # Check optional data
        optional_data = await self._get_optional_data_for_step(target_step)
        
        # Validate context completeness
        context_validation = self._validate_context(context)
        if context_validation['errors']:
            errors.extend(context_validation['errors'])
        if context_validation['warnings']:
            warnings.extend(context_validation['warnings'])
        
        # Determine handoff reason
        handoff_reason = self._determine_handoff_reason(from_agent, to_agent, state, context)
        
        # Check if handoff makes sense
        if not self._is_handoff_logical(from_agent, to_agent, state):
            errors.append(f"Illogical handoff: {from_agent} -> {to_agent} for current state")
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'required_data': required_data,
            'optional_data': optional_data,
            'handoff_reason': handoff_reason,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    async def _get_missing_data_for_step(self, step: ConversationStep, state: ConversationState) -> List[str]:
        """Get missing data for a specific step"""
        missing_data = []
        
        if step == ConversationStep.TIRE_SIZE_DISCOVERY:
            if not state.has_data(DataCategory.TIRE_SPECS):
                missing_data.append('tire_specs')
        
        elif step == ConversationStep.DRIVING_INFO_COLLECTION:
            if not state.has_data(DataCategory.DRIVING_PATTERNS):
                missing_data.append('driving_patterns')
        
        elif step == ConversationStep.PREFERENCES_GATHERING:
            if not state.has_data(DataCategory.BUDGET_PREFERENCES):
                missing_data.append('budget_preferences')
        
        elif step == ConversationStep.RECOMMENDATION_GENERATION:
            required_categories = [DataCategory.TIRE_SPECS, DataCategory.DRIVING_PATTERNS, DataCategory.BUDGET_PREFERENCES]
            for category in required_categories:
                if not state.has_data(category):
                    missing_data.append(category.value)
        
        return missing_data
    
    async def _get_required_data_for_step(self, step: ConversationStep) -> List[str]:
        """Get required data categories for a step"""
        step_requirements = {
            ConversationStep.TIRE_SIZE_DISCOVERY: ['tire_specs'],
            ConversationStep.DRIVING_INFO_COLLECTION: ['driving_patterns'],
            ConversationStep.PREFERENCES_GATHERING: ['budget_preferences'],
            ConversationStep.RECOMMENDATION_GENERATION: ['tire_specs', 'driving_patterns', 'budget_preferences']
        }
        return step_requirements.get(step, [])
    
    async def _get_optional_data_for_step(self, step: ConversationStep) -> List[str]:
        """Get optional data categories for a step"""
        step_optional = {
            ConversationStep.TIRE_SIZE_DISCOVERY: ['vehicle_info', 'current_tire_status'],
            ConversationStep.DRIVING_INFO_COLLECTION: ['current_tire_status', 'special_considerations'],
            ConversationStep.PREFERENCES_GATHERING: ['special_considerations'],
            ConversationStep.RECOMMENDATION_GENERATION: ['special_considerations', 'current_tire_status']
        }
        return step_optional.get(step, [])
    
    def _validate_context(self, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate context completeness"""
        errors = []
        warnings = []
        
        # Check for required context fields
        required_fields = ['session_id', 'current_step']
        for field in required_fields:
            if field not in context:
                errors.append(f"Missing required context field: {field}")
        
        # Check for conversation history
        if 'conversation_history' not in context:
            warnings.append("No conversation history in context")
        
        # Check for form data if present
        if 'form_data' in context:
            form_data = context['form_data']
            if not isinstance(form_data, dict):
                errors.append("Form data must be a dictionary")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _determine_handoff_reason(self, from_agent: str, to_agent: str, state: ConversationState, context: Dict[str, Any]) -> str:
        """Determine the reason for handoff"""
        
        if from_agent == to_agent:
            return "Same agent, no handoff needed"
        
        # Check if step is complete
        if state.is_step_complete(state.current_step):
            return f"Step {state.current_step.value} complete, advancing to next agent"
        
        # Check if user provided new information
        if 'form_data' in context and context['form_data']:
            return "User provided new information, switching to appropriate agent"
        
        # Check if there's an error or issue
        if 'error' in context or 'issue' in context:
            return "Error occurred, switching to error handling agent"
        
        return f"Standard handoff from {from_agent} to {to_agent}"
    
    def _is_handoff_logical(self, from_agent: str, to_agent: str, state: ConversationState) -> bool:
        """Check if handoff makes logical sense"""
        
        # Same agent handoffs are always logical
        if from_agent == to_agent:
            return True
        
        # Check agent-step mapping
        expected_agent = self.agent_mapping.get(state.current_step)
        if expected_agent != to_agent:
            return False
        
        # Check if current agent should be handling this step
        if from_agent != self.agent_mapping.get(state.current_step):
            return False
        
        return True
    
    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of context for logging"""
        summary = {
            'has_conversation_history': 'conversation_history' in context,
            'has_form_data': 'form_data' in context and bool(context['form_data']),
            'has_error': 'error' in context,
            'context_keys': list(context.keys())
        }
        
        if 'conversation_history' in context:
            summary['history_length'] = len(context['conversation_history'])
        
        if 'form_data' in context:
            summary['form_fields'] = list(context['form_data'].keys())
        
        return summary
    
    async def get_handoff_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent handoff history"""
        async with self._handoff_lock:
            recent_handoffs = self.handoff_history[-limit:] if self.handoff_history else []
            
            return [{
                'handoff_id': h.handoff_id,
                'from_agent': h.from_agent,
                'to_agent': h.to_agent,
                'timestamp': h.timestamp.isoformat(),
                'status': h.status.value,
                'validation_passed': h.validation_result['is_valid'],
                'handoff_reason': h.validation_result.get('handoff_reason', '')
            } for h in recent_handoffs]
    
    async def get_agent_for_step(self, step: ConversationStep) -> str:
        """Get the appropriate agent for a step"""
        return self.agent_mapping.get(step, "TireSizeAgent")  # Default fallback
    
    async def should_handoff(self, current_agent: str, state: ConversationState, context: Dict[str, Any]) -> bool:
        """Simple handoff logic based on agent completion signals"""
        
        # Simple rule: handoff if agent signals completion
        agent_complete = context.get('agent_complete', False)
        
        if agent_complete:
            logger.info(f"Agent {current_agent} signals completion - proceeding with handoff")
            return True
        
        # Don't handoff if agent is not complete
        logger.info(f"Agent {current_agent} not complete - no handoff")
        return False
    
    async def _get_next_step(self, current_step: ConversationStep) -> Optional[ConversationStep]:
        """Get the next step in the sequence"""
        step_sequence = [
            ConversationStep.GREETING,
            ConversationStep.TIRE_SIZE_DISCOVERY,
            ConversationStep.DRIVING_INFO_COLLECTION,
            ConversationStep.PREFERENCES_GATHERING,
            ConversationStep.RECOMMENDATION_GENERATION,
            ConversationStep.COMPARISON_ANALYSIS,
            ConversationStep.FINAL_SELECTION,
            ConversationStep.COMPLETED
        ]
        
        try:
            current_index = step_sequence.index(current_step)
            if current_index + 1 < len(step_sequence):
                return step_sequence[current_index + 1]
        except ValueError:
            logger.error(f"Current step {current_step} not found in sequence")
        
        return None 
        return None 