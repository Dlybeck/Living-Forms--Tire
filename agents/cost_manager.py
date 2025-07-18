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
    """Available model types with updated 2025 pricing"""
    # Claude models (for comparison)
    CLAUDE_SONNET_4 = "claude-sonnet-4"
    CLAUDE_3_7 = "claude-3.7"
    CLAUDE_3_5_SONNET = "claude-3.5-sonnet"
    
    # GPT models (primary choices with built-in web search)
    GPT_4O = "gpt-4o"                                    # $2.50/$1.25 per 1M tokens (WITH WEB SEARCH)
    GPT_4O_MINI = "gpt-4o-mini"                          # $0.15/$0.075 per 1M tokens (WITH WEB SEARCH - BEST VALUE)
    GPT_4_1_MINI = "gpt-4.1-mini"                        # $0.40/$0.10 per 1M tokens
    GPT_4_1_NANO = "gpt-4.1-nano"                        # $0.10/$0.025 per 1M tokens (CHEAPEST)
    GPT_3_5_TURBO = "gpt-3.5-turbo"                      # Legacy fallback

class CostManagerInterface(ABC):
    """Abstract interface for cost management strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conversation_budget = config.get("conversation_budget", 0.20)
        
        # Updated 2025 model pricing (per 1K tokens)
        self.model_costs = {
            # Claude models (for comparison)
            ModelType.CLAUDE_SONNET_4: {
                'input_cost': 0.003,    # $3.00 per 1M tokens
                'output_cost': 0.015,   # $15.00 per 1M tokens
                'best_for': ['balanced_tasks', 'web_search', 'tire_recommendations']
            },
            ModelType.CLAUDE_3_7: {
                'input_cost': 0.003,    # $3.00 per 1M tokens
                'output_cost': 0.015,   # $15.00 per 1M tokens
                'best_for': ['complex_reasoning', 'agentic_workflows', 'web_search']
            },
            ModelType.CLAUDE_3_5_SONNET: {
                'input_cost': 0.003,    # $3.00 per 1M tokens
                'output_cost': 0.015,   # $15.00 per 1M tokens
                'best_for': ['balanced_tasks', 'tire_recommendations']
            },
            
            # GPT models (primary choices - much cheaper, with built-in web search!)
            ModelType.GPT_4O: {
                'input_cost': 0.0025,   # $2.50 per 1M tokens
                'output_cost': 0.00125, # $1.25 per 1M tokens
                'best_for': ['conversational_flow', 'structured_output', 'reliability', 'web_search']
            },
            ModelType.GPT_4O_MINI: {
                'input_cost': 0.00015,  # $0.15 per 1M tokens (EXCELLENT VALUE!)
                'output_cost': 0.000075,# $0.075 per 1M tokens
                'best_for': ['cost_effective', 'tire_recommendations', 'general_chat', 'web_search']
            },
            ModelType.GPT_4_1_MINI: {
                'input_cost': 0.0004,   # $0.40 per 1M tokens
                'output_cost': 0.0001,  # $0.10 per 1M tokens
                'best_for': ['balanced_cost', 'good_quality']
            },
            ModelType.GPT_4_1_NANO: {
                'input_cost': 0.0001,   # $0.10 per 1M tokens (CHEAPEST!)
                'output_cost': 0.000025,# $0.025 per 1M tokens
                'best_for': ['ultra_cheap', 'simple_tasks']
            },
            ModelType.GPT_3_5_TURBO: {
                'input_cost': 0.001,    # $1.00 per 1M tokens (legacy)
                'output_cost': 0.002,   # $2.00 per 1M tokens
                'best_for': ['legacy_fallback']
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
        """Track actual cost of operation (compatible with ConversationRoadmap)"""
        # Use shared_data for cost tracking
        if hasattr(conversation_state, 'shared_data'):
            shared_data = conversation_state.shared_data
            shared_data['total_cost'] = shared_data.get('total_cost', 0.0) + actual_cost
            if 'cost_breakdown' not in shared_data:
                shared_data['cost_breakdown'] = {}
            shared_data['cost_breakdown'][operation_type] = shared_data['cost_breakdown'].get(operation_type, 0.0) + actual_cost
            logger.info(f"Cost tracked: {operation_type} = ${actual_cost:.4f}, Total: ${shared_data['total_cost']:.4f}")
        else:
            # Fallback for legacy ConversationState
            conversation_state.total_cost = getattr(conversation_state, 'total_cost', 0.0) + actual_cost
            if not hasattr(conversation_state, 'cost_breakdown'):
                conversation_state.cost_breakdown = {}
            conversation_state.cost_breakdown[operation_type] = conversation_state.cost_breakdown.get(operation_type, 0.0) + actual_cost
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
        """Get remaining budget for this conversation (compatible with ConversationRoadmap)"""
        if hasattr(conversation_state, 'shared_data'):
            total_cost = conversation_state.shared_data.get('total_cost', 0.0)
        else:
            total_cost = getattr(conversation_state, 'total_cost', 0.0)
        return max(0, self.conversation_budget - total_cost)
    
    def get_cost_summary(self, conversation_state) -> Dict[str, Any]:
        """Get comprehensive cost summary (compatible with ConversationRoadmap)"""
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
        """Cost-effective GPT model selection with web search capability"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        needs_web_search = self._needs_web_search(query_complexity, conversation_state)
        
        # Use two middle-tier models instead of high/low combination
        # Primary: GPT-4o-mini (middle tier with web search)
        # Secondary: GPT-4.1-mini (middle tier for simpler tasks)
        
        if needs_web_search or query_complexity in ["medium", "high"]:
            logger.info("🔍 Using GPT-4o-mini for web search or medium/high complexity (middle-tier)")
            return ModelType.GPT_4O_MINI
        
        # Use GPT-4.1-mini for low complexity tasks (still middle-tier)
        if query_complexity == "low" and remaining_budget >= 0.01:
            logger.info("Using GPT-4.1-mini for low complexity (middle-tier)")
            return ModelType.GPT_4_1_MINI
        
        # Fallback to GPT-4o-mini as default (still middle-tier)
        logger.info("Using GPT-4o-mini as default middle-tier fallback")
        return ModelType.GPT_4O_MINI
    
    def _needs_web_search(self, query_complexity: str, conversation_state) -> bool:
        """Determine when to search for tire size information"""
        
        vehicle_info = conversation_state.vehicle_info
        last_message = getattr(conversation_state, 'last_user_message', '').lower()
        
        # Don't search for initial welcome interactions
        if 'form submission with: info_method:' in last_message and 'not_sure' in last_message:
            logger.info("🚫 No web search needed: Initial form interaction")
            return False
        
        # Don't search if we already have tire size
        if conversation_state.tire_specs.get('current_tire_size'):
            logger.info("🚫 No web search needed: Already have tire size")
            return False
        
        # Search if we have complete vehicle info (make, model, year) and no tire size
        if (vehicle_info.get('make') and vehicle_info.get('model') and vehicle_info.get('year')):
            logger.info(f"🔍 Web search needed: Have complete vehicle info ({vehicle_info.get('year')} {vehicle_info.get('make')} {vehicle_info.get('model')}) but no tire size")
            return True
        
        # Search if user explicitly asks for tire size
        tire_size_keywords = ['tire size', 'what size', 'size tire', 'factory tire', 'oem tire']
        if any(keyword in last_message for keyword in tire_size_keywords):
            logger.info("🔍 Web search needed: User explicitly asking for tire size")
            return True
        
        # Search if user asks about trim levels or specifications
        spec_keywords = ['trim', 'trim level', 'package', 'specification', 'spec']
        if any(keyword in last_message for keyword in spec_keywords):
            logger.info("🔍 Web search needed: User asking about specifications")
            return True
        
        logger.info("🚫 No web search needed: Conditions not met")
        return False
    
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
        """Use two middle-tier models for optimized cost management"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Use GPT-4o-mini as primary middle-tier choice
        if remaining_budget >= 0.02:
            return ModelType.GPT_4O_MINI
        
        # Use GPT-4.1-mini as secondary middle-tier choice
        return ModelType.GPT_4_1_MINI
    
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
        """Use two middle-tier models for aggressive cost management"""
        remaining_budget = self.get_remaining_budget(conversation_state)
        
        # Use GPT-4o-mini as primary middle-tier choice
        if remaining_budget >= 0.01:
            return ModelType.GPT_4O_MINI
        
        # Use GPT-4.1-mini as secondary middle-tier choice
        return ModelType.GPT_4_1_MINI
    
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