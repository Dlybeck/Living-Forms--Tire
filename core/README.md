# Core Module Overview

The `core/` directory contains the main business logic and AI agent components of the Tire Sales Assistant. This is where the intelligent conversation processing, form generation, and session management happen.

## 📁 File Descriptions

### 🤖 `tire_agent.py` (143 lines)
**Purpose**: Main AI agent that orchestrates the entire tire recommendation process

**Key Responsibilities**:
- Processes user messages with internal thinking and external response generation
- Implements the "Living Form" concept with embedded form fields in conversation
- Manages the unified response format: `[INTERNAL_ANALYSIS]`, `[CONVERSATION]`, `[FORM]`
- Parses AI responses to extract internal thoughts, conversation text, and form HTML

**Key Methods**:
- `process_message()` - Main entry point for message processing
- `_generate_unified_response()` - Creates comprehensive AI prompts
- `_parse_unified_response()` - Extracts structured components from AI response

**Integration**: Works with `ai_client.py` for model communication and `form_builder.py` for form generation

---

### 🧠 `ai_client.py` (174 lines)
**Purpose**: Handles all communication with AI models (OpenAI, Anthropic)

**Key Responsibilities**:
- Manages API keys and model configurations
- Provides unified interface for different AI providers
- Handles prompt construction and API calls
- Implements fallback mechanisms for error handling

**Supported Models**:
- **O4-Mini** (`o4-mini-2025-04-16`) - Primary model for reasoning
- **Claude 3.5 Sonnet** (`claude-3-5-sonnet-latest`) - Alternative model

**Key Methods**:
- `generate_response()` - Main method for AI response generation
- `_build_prompt()` - Constructs comprehensive prompts with context
- `_call_api()` - Handles provider-specific API communication

**Configuration**: Uses environment variables for API keys and supports multiple model types

---

### 🎯 `coordinator.py` (144 lines)
**Purpose**: Manages conversation sessions and routes messages between components

**Key Responsibilities**:
- Session lifecycle management (creation, retrieval, updates)
- Conversation history tracking
- Message routing to the tire agent
- System status monitoring

**Session Structure**:
```python
session = {
    'session_id': 'unique_id',
    'conversation_history': [...],  # Previous interactions
    'ai_notepad': 'internal_analysis',  # AI's internal thoughts
    'current_step': 'initial'  # Current conversation stage
}
```

**Key Methods**:
- `process_message()` - Main entry point for message processing
- `_get_or_create_session()` - Session management
- `_update_session_history()` - Tracks conversation flow
- `get_system_status()` - Health monitoring

**Thread Safety**: Uses async locks for concurrent session access

---

### 🏗️ `form_builder.py` (279 lines)
**Purpose**: Generates dynamic HTML forms from AI function calls

**Key Responsibilities**:
- Converts embedded function calls to HTML form fields
- Provides comprehensive form field types (text, textarea, select, checkbox, year)
- Handles form validation and accessibility
- Automatically includes "Additional Thoughts" field

**Available Form Functions**:
- `create_text_field()` - Single line text input
- `create_textarea_field()` - Multi-line text input  
- `create_select_field()` - Dropdown selection
- `create_checkbox_field()` - Multiple choice checkboxes
- `create_year_field()` - Year selection

**Key Methods**:
- `create_embedded_form()` - Main method for form generation
- `_process_function_calls()` - Parses and converts function calls
- `_parse_and_create_field()` - Individual field processing
- `get_function_documentation()` - Provides function specs to AI

**Features**:
- Responsive design for mobile compatibility
- ARIA labels for accessibility
- Client-side validation
- Automatic field numbering

---

### 🛠️ `utils.py` (26 lines)
**Purpose**: Shared utility functions and helper methods

**Key Responsibilities**:
- Provides common error response formatting
- Contains shared helper functions
- Maintains consistent error handling patterns

**Key Functions**:
- `create_error_response()` - Standardized error response creation
- Additional utility functions for common operations

**Usage**: Imported by other core modules for consistent error handling

---

## 🔄 Module Interactions

### Data Flow
```
coordinator.py → tire_agent.py → ai_client.py
                    ↓
              form_builder.py
```

### Dependencies
- **tire_agent.py** depends on: `ai_client.py`, `form_builder.py`, `utils.py`
- **coordinator.py** depends on: `tire_agent.py`, `ai_client.py`, `form_builder.py`, `utils.py`
- **ai_client.py** depends on: External APIs (OpenAI, Anthropic)
- **form_builder.py** depends on: None (self-contained)
- **utils.py** depends on: None (utility functions only)

## 🎯 Design Patterns

### 1. **Agent Pattern**
- `TireAgent` encapsulates AI behavior and reasoning
- Clear separation between internal thinking and external interaction

### 2. **Coordinator Pattern**
- `Coordinator` manages component interactions
- Centralized session and state management

### 3. **Builder Pattern**
- `FormBuilder` constructs complex HTML forms
- Step-by-step form generation process

### 4. **Client Pattern**
- `AIClient` abstracts external API communication
- Provider-agnostic interface

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY` - OpenAI API credentials
- `ANTHROPIC_API_KEY` - Anthropic API credentials

### Model Selection
- Primary: O4-Mini for reasoning and analysis
- Fallback: Claude 3.5 Sonnet for alternative processing

## 🚀 Performance Considerations

### Async Processing
- All major operations use async/await
- Non-blocking API calls and form generation
- Concurrent session handling

### Memory Management
- Session data stored in memory (configurable for persistence)
- Efficient conversation history tracking
- Automatic cleanup of completed sessions

### Error Handling
- Graceful degradation on API failures
- Comprehensive logging for debugging
- User-friendly error messages

This core module provides the foundation for intelligent, conversational tire sales assistance with robust error handling and scalable architecture. 