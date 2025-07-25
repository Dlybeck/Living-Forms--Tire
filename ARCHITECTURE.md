# Tire Sales Assistant Architecture (Simplified)

## Overview

This is a **simplified unified agent system** for tire sales assistance. All legacy components, database functionality, and web search features have been removed for maintainability and simplicity.

## Core Components

### 1. **SimplifiedCoordinator** (`agents/simplified_coordinator.py`)
- **Purpose**: Manages the unified agent and coordinates all work
- **Key Functions**:
  - Processes user messages
  - Routes messages to the unified agent
  - Manages session state
  - Handles form submissions

### 2. **UnifiedTireAgent** (`agents/unified_tire_agent.py`)
- **Purpose**: Handles ALL user interactions, internal thinking, and tire sales logic
- **Key Functions**:
  - Internal "Living Form's Mind" thinking process
  - Generates responses using the unified prompt
  - Creates forms for data collection
  - Provides tire recommendations
  - Manages the entire conversation flow

## Supporting Components

### 3. **FormBuilder** (`agents/form_builder.py`)
- **Purpose**: Creates HTML form fields
- **Key Functions**:
  - Text fields, textareas, selects, checkboxes
  - Automatic form completion
  - Smart placeholders

### 4. **AIClient** (`agents/ai_client.py`)
- **Purpose**: Handles AI model communication
- **Key Functions**:
  - OpenAI and Anthropic API calls
  - Model selection and cost optimization
  - Simplified prompt building

### 5. **CostManager** (`agents/cost_manager.py`)
- **Purpose**: Tracks conversation costs
- **Key Functions**:
  - Cost tracking for different operations
  - Budget management
  - Model cost estimation

### 6. **StateManager** (`utils/state_manager.py`)
- **Purpose**: Basic session state tracking
- **Key Functions**:
  - Session initialization
  - State updates
  - Data storage

## Removed Components

### ❌ **Eliminated Legacy:**
- **Database system** - No longer uses tire_database.py or car-models.json
- **Web search functionality** - Removed from AI client and prompts
- **BaseAgent class** - Merged functionality directly into UnifiedTireAgent
- **Complex cost tracking** - Simplified to work with dictionary-style states only
- **Debug print statements** - Cleaned up verbose logging
- **Unused dependencies** - Removed pandas, numpy, structlog, aiofiles, etc.

## How It Works

### Message Flow:
1. **User sends message** → `main.py`
2. **Coordinator receives message** → `SimplifiedCoordinator`
3. **UnifiedTireAgent processes** → Internal thinking + generates response + form
4. **Response sent to user** → With AI notepad content

### Key Features Maintained:
- ✅ Living Form methodology
- ✅ Internal "Riley's Head" thinking process
- ✅ Dynamic form generation
- ✅ Cost tracking
- ✅ Session management
- ✅ Emotional intelligence
- ✅ Conversation memory

## File Structure

```
agents/
├── simplified_coordinator.py         # Main coordinator
├── unified_tire_agent.py             # Complete unified agent
├── form_builder.py                   # Form generation
├── function_call_parser.py           # Parse AI function calls
├── ai_client.py                      # AI API communication
└── cost_manager.py                   # Cost tracking

utils/
└── state_manager.py                  # Session state management

prompts/
└── prompt.py                         # Main AI prompt

main.py                                # FastAPI web server
requirements.txt                       # Simplified dependencies
```

## Benefits of Simplification

- **Easier to understand** - Removed complex inheritance and legacy patterns
- **Faster to modify** - Fewer interdependencies and cleaner code
- **Lower maintenance** - No database or external service dependencies
- **Reduced costs** - Eliminated unnecessary AI model calls and features
- **Better performance** - Streamlined execution flow
├── state_manager.py                   # Basic state management
└── memory_manager.py                  # Conversation memory

prompts/
├── unified_tire_prompt.py            # Unified agent prompt

main.py                               # FastAPI application
```

## For New Developers

### **Getting Started:**
1. **Start with `main.py`** - Entry point
2. **Look at `SimplifiedCoordinator`** - Main logic
3. **Understand `UnifiedTireAgent`** - Complete system
4. **Check the unified prompt** - Internal thinking + external interaction

### **Key Concepts:**
- **Single agent**: The unified agent handles everything
- **Simple state**: Just session data, no complex transitions
- **Internal thinking**: "Living Form's Mind" process guides responses
- **Maintained features**: All original functionality preserved

### **Adding Features:**
- **New form fields**: Add to `FormBuilder`
- **New AI prompts**: Add to `prompts/` directory
- **New functionality**: Extend `UnifiedTireAgent`
- **New data tracking**: Update the unified agent

## Benefits of Simplification

1. **Easier to understand** - Clear, linear flow
2. **Easier to debug** - Fewer moving parts
3. **Easier to maintain** - Less complex code
4. **Easier to extend** - Clear separation of concerns
5. **Same functionality** - All features preserved

The system is now much more maintainable while preserving all the sophisticated AI capabilities! 