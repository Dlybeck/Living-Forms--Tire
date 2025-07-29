# Core Components

This directory contains the main business logic and core functionality of the Living Form Tire Sales Agent.

## Files Overview

### **`tire_graph.py`** - LangGraph Workflow Engine
The heart of the system implementing a 4-stage workflow for tire recommendations:
- **Stage 1**: Information Analysis - Determines what information is missing
- **Stage 2**: Research Planning - Creates strategic research plans
- **Stage 3**: Research Execution - Gathers information using web search tools
- **Stage 4**: Response Synthesis - Generates conversational responses with forms

**Key Features**:
- Uses LangGraph StateGraph for structured workflow management
- Implements TypedDict state management for type safety
- Integrates with tire tools for web research
- Maintains conversation context across workflow stages

### **`graph_coordinator.py`** - Main System Coordinator
Orchestrates the entire system and manages AI model selection:
- Initializes and manages the LangGraph workflow
- Handles model selection between Claude Sonnet 3.5 and O4-mini
- Provides session management and system status endpoints
- Coordinates between different system components

**Key Features**:
- Automatic model fallback based on availability
- Session tracking and management
- Error handling and recovery
- System health monitoring

### **`form_builder.py`** - Dynamic Form Generator
Creates HTML forms with embedded fields within conversational text:
- Parses embedded function calls like `{create_text_field(...)}`
- Generates responsive HTML forms with proper validation
- Supports multiple field types (text, dropdown, radio, checkbox, textarea)
- Automatically includes "Additional Thoughts" field

**Key Features**:
- Regex-based function call parsing
- Contextual field labels and placeholders
- Mobile-responsive form layouts
- Clean, maintainable HTML generation

### **`ai_client.py`** - Multi-Model AI Client
Manages communication with different AI models using LangChain:
- Supports OpenAI (O4-mini) and Anthropic (Claude) models
- Handles API key management and model initialization
- Provides unified interface for AI interactions
- Tracks token usage and API costs

**Key Features**:
- Automatic model switching and fallback
- LangChain integration for standardized AI interactions
- Usage tracking and cost monitoring
- Error handling for API failures

### **`tire_tools.py`** - Web Search and Research Tools
Provides specialized tools for tire and vehicle research:
- **tire_size_lookup**: Find tire sizes for specific vehicles
- **vehicle_specs_search**: Research vehicle specifications and trim levels
- **tire_review_search**: Find tire reviews, ratings, and comparisons
- **weather_condition_search**: Research local weather conditions
- **vin_decoder_search**: Decode VIN numbers for vehicle details

**Key Features**:
- DuckDuckGo web search integration
- Specialized search queries for better results
- Error handling for search failures
- Result parsing and formatting

### **`memory_manager.py`** - Conversation Memory Management
Manages conversation history and session context:
- Maintains chat history across multiple interactions
- Preserves important details and user preferences
- Provides session isolation for different users
- Integrates with LangChain memory systems

**Key Features**:
- LangChain memory integration
- Context preservation across sessions
- Automatic memory cleanup
- Session isolation and security

### **`output_parser.py`** - Response Parsing Utilities
Handles parsing and extraction of structured data from AI responses:
- Parses AI responses for form field extraction
- Handles JSON parsing with fallback mechanisms
- Extracts conversation state and workflow information
- Provides error handling for malformed responses

**Key Features**:
- Robust JSON parsing with fallbacks
- Error handling for malformed responses
- Structured data extraction
- Validation and sanitization

## Architecture Flow

```
User Request → GraphCoordinator → TireRecommendationGraph
                                            ↓
                                    [4-Stage Workflow]
                                            ↓
Response ← FormBuilder ← AI Client ← Memory Manager
    ↓
Tire Tools (Web Research)
```

## Dependencies

- **LangGraph**: Workflow orchestration and state management
- **LangChain**: AI model integration and memory management
- **FastAPI**: Web framework for API endpoints
- **DuckDuckGo**: Web search capabilities
- **Pydantic**: Data validation and serialization

## Best Practices

1. **Error Handling**: All components include comprehensive error handling
2. **Logging**: Structured logging for debugging and monitoring
3. **Type Safety**: Uses TypedDict and type hints throughout
4. **Modularity**: Each component has a single, well-defined responsibility
5. **Fallback Mechanisms**: Automatic fallbacks for failed operations 