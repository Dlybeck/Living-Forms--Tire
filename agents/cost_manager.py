from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CostStrategy(Enum):
    """Available cost management strategies"""
    GENEROUS = "generous"
    OPTIMIZED = "optimized"
    AGGRESSIVE = "aggressive"
    FIXED_BUDGET = "fixed_budget"

class ModelType(Enum):
    """Available model types with July 2025 pricing"""
    CLAUDE_3_7 = "claude-3.7"
    CLAUDE_3_5_SONNET = "claude-3.5-sonnet"
    GPT_4O = "gpt-4o"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class CostManagerInterface(ABC):
    """Abstract interface for cost management strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conversation_budget = config.get("conversation_budget", 0.20)
        
        # Modern 2025 model pricing (estimated)
        self.model_costs = {
            ModelType.CLAUDE_3_7: {
                'input_cost': 0.015,    # per 1K tokens
                'output_cost': 0.075,   # per 1K tokens
                'best_for': ['complex_reasoning', 'agentic_workflows']
            },
            ModelType.GPT_4O: {
                'input_cost': 0.005,    # per 1K tokens  
                'output_cost': 0.015,   # per 1K tokens
                'best_for': ['conversational_flow', 'structured_output']
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'input_cost': 0.003,    # per 1K tokens
                'output_cost': 0.015,   # per 1K tokens
                'best_for': ['balanced_tasks', 'tire_recommendations']
            },
            ModelType.GPT_3_5_TURBO: {
                'input_cost': 0.001,    # per 1K tokens
                'output_cost': 0.002,   # per 1K tokens
                'best_for': ['simple_tasks', 'basic_chat']
            }
        }
    
    @abstractmethod
    def can_afford_operation(self, operation_type: str, estimated_cost: float, conversation_state) -> bool:
        """Check if operation is within budget"""
        pass
    
    @abstractmethod
    def get_recommended_model(self, query_complexity: str, conversation_state) -> ModelType:
        """Get recommended model for this query"""
        pass
    
    @abstractmethod
    def should_use_fallback(self, conversation_state) -> bool:
        """Determine if should use fallback response"""
        pass
    
    def track_cost(self, operation_type: str, actual_cost: float, conversation_state):
        """Track actual cost of operation"""
        conversation_state.total_cost += actual_cost
        conversation_state.cost_breakdown[operation_type] = conversation_state.cost_breakdown.get(operation_type, 0) + actual_cost
        
        logger.info(f"Cost tracked: {operation_type} = ${actual_cost:.4f}, Total: ${conversation_state.total_cost:.4f}")
    
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
        return max(0, self.conversation_budget - conversation_state.total_cost)
    
    def get_cost_summary(self, conversation_state) -> Dict[str, Any]:
        """Get comprehensive cost summary"""
        return {
            "total_cost": conversation_state.total_cost,
            "budget_remaining": self.get_remaining_budget(conversation_state),
            "budget_used_percentage": (conversation_state.total_cost / self.conversation_budget) * 100,
            "cost_breakdown": conversation_state.cost_breakdown,
            "interactions_count": len(conversation_state.conversation_history),
            "average_cost_per_interaction": conversation_state.total_cost / max(1, len(conversation_state.conversation_history))
        }

class GenerousCostManager(CostManagerInterface):
    """
    Generous cost management strategy for development
    - High budget allowance (20 cents per conversation)
    - Quality-first model selection
    - Allows expensive operations for learning
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.conversation_budget = config.get("conversation_budget", 0.20)
        self.quality_threshold = 0.85
        self.cost_warning_threshold = 0.15  # Warn at 15 cents
    
    def can_afford_operation(self, operation_type: str, estimated_cost: float, conversation_state) -> bool:
        """Generous budget - allow most operations"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Always allow if we have plenty of budget
        if remaining_budget > 0.10:
            return True
        
        # Allow if it's a reasonable cost
        if estimated_cost < 0.05:
            return True
        
        # Warn if we're approaching budget limit
        if conversation_state.total_cost > self.cost_warning_threshold:
            logger.warning(f"Approaching budget limit: ${conversation_state.total_cost:.4f} / ${self.conversation_budget:.4f}")
        
        return remaining_budget > estimated_cost
    
    def get_recommended_model(self, query_complexity: str, conversation_state) -> ModelType:
        """Quality-first model selection"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Use best model for complex queries
        if query_complexity == "high":
            return ModelType.CLAUDE_3_7
        
        # Use good balance for medium complexity
        elif query_complexity == "medium":
            return ModelType.GPT_4O
        
        # Use efficient model for simple queries
        elif query_complexity == "low":
            return ModelType.CLAUDE_3_5_SONNET
        
        # Default to balanced option
        return ModelType.CLAUDE_3_5_SONNET
    
    def should_use_fallback(self, conversation_state) -> bool:
        """Only use fallback if budget is completely exhausted"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        return remaining_budget < 0.01  # Less than 1 cent remaining

class OptimizedCostManager(CostManagerInterface):
    """
    Optimized cost management strategy for production
    - Moderate budget (10 cents per conversation)
    - Smart model selection based on complexity
    - Balances quality and cost
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.conversation_budget = config.get("conversation_budget", 0.10)
        self.cost_efficiency_threshold = 0.02  # 2 cents per interaction
    
    def can_afford_operation(self, operation_type: str, estimated_cost: float, conversation_state) -> bool:
        """Balanced budget management"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Check if operation fits within remaining budget
        if estimated_cost > remaining_budget:
            return False
        
        # Check if this operation would exceed per-interaction budget
        interactions_count = len(conversation_state.conversation_history)
        if interactions_count > 0:
            average_cost = conversation_state.total_cost / interactions_count
            if estimated_cost > average_cost * 2:  # Don't allow costs 2x average
                return False
        
        return True
    
    def get_recommended_model(self, query_complexity: str, conversation_state) -> ModelType:
        """Cost-optimized model selection"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # If budget is tight, use cheaper models
        if remaining_budget < 0.05:
            return ModelType.CLAUDE_3_5_SONNET
        
        # Use premium model sparingly for complex queries
        if query_complexity == "high" and remaining_budget > 0.08:
            return ModelType.CLAUDE_3_7
        
        # Balanced choice for most queries
        return ModelType.CLAUDE_3_5_SONNET
    
    def should_use_fallback(self, conversation_state) -> bool:
        """Use fallback when budget is low"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        return remaining_budget < 0.02  # Less than 2 cents remaining

class AggressiveCostManager(CostManagerInterface):
    """
    Aggressive cost management strategy
    - Low budget (5 cents per conversation)
    - Prefers cheaper models
    - Quick fallback to static responses
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.conversation_budget = config.get("conversation_budget", 0.05)
    
    def can_afford_operation(self, operation_type: str, estimated_cost: float, conversation_state) -> bool:
        """Strict budget management"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        return estimated_cost <= remaining_budget
    
    def get_recommended_model(self, query_complexity: str, conversation_state) -> ModelType:
        """Always prefer cheaper models"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Use cheapest model most of the time
        if remaining_budget < 0.03:
            return ModelType.GPT_3_5_TURBO
        
        # Use mid-tier model sparingly
        return ModelType.CLAUDE_3_5_SONNET
    
    def should_use_fallback(self, conversation_state) -> bool:
        """Use fallback frequently"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        return remaining_budget < 0.03  # Less than 3 cents remaining

class CostManager:
    """
    Factory class for creating cost managers
    Allows easy switching between strategies
    """
    
    _strategies = {
        CostStrategy.GENEROUS: GenerousCostManager,
        CostStrategy.OPTIMIZED: OptimizedCostManager,
        CostStrategy.AGGRESSIVE: AggressiveCostManager
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        strategy_name = config.get("strategy", "generous")
        
        # Convert string to enum
        if isinstance(strategy_name, str):
            strategy = CostStrategy(strategy_name.lower())
        else:
            strategy = strategy_name
        
        # Create appropriate strategy
        if strategy not in self._strategies:
            logger.warning(f"Unknown cost strategy: {strategy}, defaulting to generous")
            strategy = CostStrategy.GENEROUS
        
        self.strategy = self._strategies[strategy](config)
        logger.info(f"Initialized cost manager with strategy: {strategy.value}")
    
    def can_afford_operation(self, operation_type: str, estimated_cost: float, conversation_state) -> bool:
        """Delegate to strategy"""
        return self.strategy.can_afford_operation(operation_type, estimated_cost, conversation_state)
    
    def get_recommended_model(self, query_complexity: str, conversation_state) -> ModelType:
        """Delegate to strategy"""
        return self.strategy.get_recommended_model(query_complexity, conversation_state)
    
    def should_use_fallback(self, conversation_state) -> bool:
        """Delegate to strategy"""
        return self.strategy.should_use_fallback(conversation_state)
    
    def track_cost(self, operation_type: str, actual_cost: float, conversation_state):
        """Delegate to strategy"""
        return self.strategy.track_cost(operation_type, actual_cost, conversation_state)
    
    def estimate_cost(self, prompt: str, model_type: ModelType, expected_output_length: int = 200) -> float:
        """Delegate to strategy"""
        return self.strategy.estimate_cost(prompt, model_type, expected_output_length)
    
    def get_remaining_budget(self, conversation_state) -> float:
        """Delegate to strategy"""
        return self.strategy.get_remaining_budget(conversation_state)
    
    def get_cost_summary(self, conversation_state) -> Dict[str, Any]:
        """Delegate to strategy"""
        return self.strategy.get_cost_summary(conversation_state)
    
    def switch_strategy(self, new_strategy: CostStrategy, config: Dict[str, Any]):
        """Switch to a different cost strategy"""
        if new_strategy in self._strategies:
            self.strategy = self._strategies[new_strategy](config)
            logger.info(f"Switched to cost strategy: {new_strategy.value}")
        else:
            logger.error(f"Invalid cost strategy: {new_strategy}")
    
    def get_current_strategy(self) -> str:
        """Get current strategy name"""
        return self.config.get("strategy", "generous") 