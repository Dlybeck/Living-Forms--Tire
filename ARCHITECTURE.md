# Tire Sales Assistant Architecture

## Overview

This is a **unified agent system** for tire sales assistance. The system has been simplified from a complex dual-agent framework to make it easy for new developers to understand and maintain.

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

### 4. **BaseAgent** (`agents/base_agent.py`)
- **Purpose**: Common functionality for both agents
- **Key Functions**:
  - AI response generation
  - Form creation
  - Control Headquarters scene generation
  - Error handling

### 5. **FormBuilder** (`agents/form_builder.py`)
- **Purpose**: Creates HTML form fields
- **Key Functions**:
  - Text fields, textareas, selects, checkboxes
  - Automatic form completion
  - Smart placeholders

### 6. **MemoryManager** (`utils/memory_manager.py`)
- **Purpose**: Tracks conversation history and important data
- **Key Functions**:
  - Extracts important user data
  - Compresses long conversations
  - Session management

### 7. **StateManager** (`utils/state_manager.py`)
- **Purpose**: Basic session state tracking
- **Key Functions**:
  - Session initialization
  - State updates
  - Data storage

## How It Works

### Message Flow:
1. **User sends message** → `main.py`
2. **Coordinator receives message** → `SimplifiedCoordinator`
3. **UnifiedTireAgent processes** → Internal thinking + generates response + form
4. **Response sent to user** → With AI notepad content

### Key Simplifications Made:

#### ❌ **Removed Complex Components:**
- Multi-agent handoff system
- Complex state transitions
- Over-engineered memory compression
- Repetitive form field methods
- Unused completion assessment logic

#### ✅ **Simplified Components:**
- **Base Agent**: 367 lines → 150 lines (59% reduction)
- **Form Builder**: 502 lines → 200 lines (60% reduction)
- **Memory Manager**: 280 lines → 120 lines (57% reduction)
- **State Manager**: 315 lines → 95 lines (70% reduction)

#### ✅ **Maintained Functionality:**
- All form generation
- AI notepad with Control Headquarters
- Cost tracking
- Session management
- Tire recommendations
- Emotional intelligence

## File Structure

```
agents/
├── simplified_coordinator.py         # Main coordinator
├── unified_tire_agent.py             # Complete unified agent
├── base_agent.py                     # Common agent functionality
├── form_builder.py                   # Form generation
├── function_call_parser.py           # Parse AI function calls
├── ai_client.py                      # AI API communication
└── cost_manager.py                   # Cost tracking

utils/
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