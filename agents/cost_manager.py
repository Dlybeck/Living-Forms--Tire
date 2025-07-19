from typing import Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Available model types with simplified pricing"""
    O4_MINI = "o4-mini-2025-04-16"                       # $1.10/$0.275 per 1M tokens (PRIMARY - REASONING)
    GPT_4_1 = "gpt-4.1-2025-04-14"                       # $2.00/$0.50 per 1M tokens (FALLBACK)
    GPT_4O_MINI = "gpt-4o-mini"                          # $0.15/$0.075 per 1M tokens (BUDGET)
    GPT_4_1_MINI = "gpt-4.1-mini"                        # $0.40/$0.10 per 1M tokens (BUDGET)
    CLAUDE_3_5_SONNET = "claude-3.5-sonnet"              # $3.00/$15.00 per 1M tokens (EMERGENCY)

class CostManager:
    """
    Simplified cost manager for the Living Form Tire Sales Assistant
    Tracks costs and manages model selection with minimal complexity
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.conversation_budget = config.get("conversation_budget", 0.20)
        
        # Simplified model costs (per 1K tokens)
        self.model_costs = {
            ModelType.O4_MINI: {
                'input_cost': 0.0011,    # $1.10 per 1M tokens
                'output_cost': 0.000275, # $0.275 per 1M tokens
                'best_for': ['conversation', 'form_generation', 'complex_reasoning', 'detailed_forms']
            },
            ModelType.GPT_4_1: {
                'input_cost': 0.002,     # $2.00 per 1M tokens
                'output_cost': 0.0005,   # $0.50 per 1M tokens
                'best_for': ['conversation', 'form_generation', 'complex_reasoning']
            },
            ModelType.GPT_4O_MINI: {
                'input_cost': 0.00015,   # $0.15 per 1M tokens
                'output_cost': 0.000075, # $0.075 per 1M tokens
                'best_for': ['conversation', 'web_search', 'fallback']
            },
            ModelType.GPT_4_1_MINI: {
                'input_cost': 0.0004,    # $0.40 per 1M tokens
                'output_cost': 0.0001,   # $0.10 per 1M tokens
                'best_for': ['conversation', 'budget_constrained']
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'input_cost': 0.003,     # $3.00 per 1M tokens
                'output_cost': 0.015,    # $15.00 per 1M tokens
                'best_for': ['emergency_fallback']
            }
        }
        
        logger.info(f"Cost manager initialized with budget: ${self.conversation_budget}")
    
    def can_afford_operation(self, operation_type: str, estimated_cost: float, conversation_state) -> bool:
        """Check if operation is within budget"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Always allow if we have plenty of budget
        if remaining_budget > 0.10:
            return True
        
        # Allow if it's a reasonable cost
        if estimated_cost < 0.05:
            return True
        
        return remaining_budget > estimated_cost
    
    def get_recommended_model(self, query_complexity: str = "medium", conversation_state=None) -> ModelType:
        """Get recommended model - use O4-mini as primary for complex reasoning and detailed forms"""
        # Use O4-mini as primary for best reasoning and detailed form generation
        return ModelType.O4_MINI
    
    def track_cost(self, operation_type: str, actual_cost: float, conversation_state):
        """Track actual cost of operation"""
        # Handle different types of conversation state objects
        if hasattr(conversation_state, 'shared_data'):
            # Old ConversationRoadmap style
            shared_data = conversation_state.shared_data
            shared_data['total_cost'] = shared_data.get('total_cost', 0.0) + actual_cost
            if 'cost_breakdown' not in shared_data:
                shared_data['cost_breakdown'] = {}
            shared_data['cost_breakdown'][operation_type] = shared_data['cost_breakdown'].get(operation_type, 0.0) + actual_cost
            logger.info(f"Cost tracked: {operation_type} = ${actual_cost:.4f}, Total: ${shared_data['total_cost']:.4f}")
        elif hasattr(conversation_state, 'total_cost'):
            # Object with total_cost attribute
            conversation_state.total_cost = getattr(conversation_state, 'total_cost', 0.0) + actual_cost
            if not hasattr(conversation_state, 'cost_breakdown'):
                conversation_state.cost_breakdown = {}
            conversation_state.cost_breakdown[operation_type] = conversation_state.cost_breakdown.get(operation_type, 0.0) + actual_cost
            logger.info(f"Cost tracked: {operation_type} = ${actual_cost:.4f}, Total: ${conversation_state.total_cost:.4f}")
        elif isinstance(conversation_state, dict):
            # Dictionary style (new session structure)
            conversation_state['total_cost'] = conversation_state.get('total_cost', 0.0) + actual_cost
            if 'cost_breakdown' not in conversation_state:
                conversation_state['cost_breakdown'] = {}
            conversation_state['cost_breakdown'][operation_type] = conversation_state['cost_breakdown'].get(operation_type, 0.0) + actual_cost
            logger.info(f"Cost tracked: {operation_type} = ${actual_cost:.4f}, Total: ${conversation_state['total_cost']:.4f}")
        else:
            # Fallback - just log the cost
            logger.info(f"Cost tracked: {operation_type} = ${actual_cost:.4f} (no state tracking available)")
    
    def estimate_cost(self, prompt: str, model_type: ModelType, expected_output_length: int = 200) -> float:
        """Estimate cost for a prompt"""
        # Rough token estimation
        input_tokens = len(prompt.split()) * 1.3  # Approximation
        output_tokens = expected_output_length * 1.3
        
        costs = self.model_costs[model_type]
        estimated_cost = (input_tokens / 1000) * costs['input_cost'] + (output_tokens / 1000) * costs['output_cost']
        
        return estimated_cost
    
    def get_remaining_budget(self, conversation_state) -> float:
        """Get remaining budget for this conversation"""
        if hasattr(conversation_state, 'shared_data'):
            total_cost = conversation_state.shared_data.get('total_cost', 0.0)
        else:
            total_cost = getattr(conversation_state, 'total_cost', 0.0)
        return max(0, self.conversation_budget - total_cost)
    
    def get_cost_summary(self, conversation_state) -> Dict[str, Any]:
        """Get cost summary"""
        if hasattr(conversation_state, 'shared_data'):
            shared_data = conversation_state.shared_data
            total_cost = shared_data.get('total_cost', 0.0)
            cost_breakdown = shared_data.get('cost_breakdown', {})
            conversation_history = getattr(conversation_state, 'conversation_history', [])
        else:
            total_cost = getattr(conversation_state, 'total_cost', 0.0)
            cost_breakdown = getattr(conversation_state, 'cost_breakdown', {})
            conversation_history = getattr(conversation_state, 'conversation_history', [])
        
        return {
            "total_cost": total_cost,
            "budget_remaining": self.get_remaining_budget(conversation_state),
            "budget_used_percentage": (total_cost / self.conversation_budget) * 100 if self.conversation_budget else 0.0,
            "cost_breakdown": cost_breakdown,
            "interactions_count": len(conversation_history),
            "average_cost_per_interaction": total_cost / max(1, len(conversation_history))
        } 