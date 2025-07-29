# Configuration

This directory contains all configuration files, prompts, and system settings for the Living Form Tire Sales Agent.

## Files Overview

### **`graph_prompts.py`** - LangGraph Workflow Prompts
Centralized prompt templates for the 4-stage LangGraph workflow:

#### **ANALYSIS_PROMPT**
- **Purpose**: Analyzes current conversation state and identifies missing information
- **Input Variables**: `user_message`, `form_data`, `conversation_history`
- **Output**: JSON with `current_stage` (1-4) and `missing_fields` list
- **Key Features**:
  - Determines exact workflow stage based on conversation context
  - Identifies critical information gaps for current stage
  - Uses "Riley's Head" principles (Logic, Curiosity, Productivity, Fear)
  - Prevents redundant questions through thorough gap analysis

#### **PLANNING_PROMPT**
- **Purpose**: Creates strategic research plans using available tools
- **Input Variables**: `information_gaps`, `form_data`, `available_tools`, `current_stage`
- **Output**: JSON list of research actions with objectives, tools, queries, and priorities
- **Key Features**:
  - Proactive research planning to minimize user questions
  - Natural search query formulation
  - Priority-based action planning (high/medium/low)
  - Tool-specific query optimization

#### **SYNTHESIS_PROMPT**
- **Purpose**: Generates conversational responses with embedded form fields
- **Input Variables**: `user_message`, `form_data`, `research_results`, `conversation_history`, `function_docs`, `current_stage`, `information_gaps`
- **Output**: Conversational text with embedded form function calls
- **Key Features**:
  - Embeds form fields naturally within conversation text
  - Incorporates research results into explanations
  - Maintains empathetic, helpful tone
  - Provides context-aware form field suggestions

### **`prompt.py`** - General System Prompts
General AI system prompts and configurations for various components:

#### **System Prompts**
- **AI Agent Prompts**: Base prompts for different AI agents in the system
- **Form Generation Prompts**: Templates for dynamic form creation
- **Error Handling Prompts**: Prompts for graceful error recovery
- **Validation Prompts**: Prompts for data validation and verification

#### **Configuration Settings**
- **Model Parameters**: Temperature, max tokens, and other AI model settings
- **Workflow Settings**: Stage-specific configurations and thresholds
- **Form Settings**: Default form field configurations and validation rules
- **Tool Settings**: Web search and research tool configurations

## Prompt Design Principles

### 1. **Contextual Awareness**
- Prompts include relevant context from conversation history
- Form data and user preferences are incorporated into decision-making
- Research results are integrated into response generation

### 2. **Progressive Disclosure**
- Information is gathered based on current workflow stage
- Prompts adapt to user's knowledge level and comfort
- Complex information is broken down into digestible pieces

### 3. **Empathetic Interaction**
- Prompts maintain helpful, understanding tone
- User struggles are anticipated and addressed proactively
- Clear explanations are provided for technical concepts

### 4. **Efficiency Focus**
- Prompts minimize redundant questions
- Research is planned proactively to gather information users might not know
- Natural conversation flow is maintained throughout the process

## Workflow Stage Integration

### Stage 1: Vehicle & Tire Specification Discovery
- **Analysis**: Identifies missing vehicle details and tire specifications
- **Planning**: Researches vehicle specs and standard tire sizes
- **Synthesis**: Gathers essential vehicle information through forms

### Stage 2: Driving Preferences & Usage Understanding
- **Analysis**: Determines missing driving condition and preference information
- **Planning**: Researches local weather conditions and driving patterns
- **Synthesis**: Elicits driving preferences and usage patterns

### Stage 3: Tire Recommendation Generation
- **Analysis**: Identifies gaps in recommendation criteria
- **Planning**: Researches tire options, reviews, and market availability
- **Synthesis**: Presents personalized tire recommendations with explanations

### Stage 4: Decision Support & Refinement
- **Analysis**: Identifies final decision factors and concerns
- **Planning**: Researches specific tire models and alternatives
- **Synthesis**: Provides decision support and addresses final questions

## Best Practices

### 1. **Prompt Engineering**
- Clear, specific instructions for each workflow stage
- Consistent formatting and structure across all prompts
- Error handling and fallback mechanisms built into prompts
- Regular testing and refinement based on user interactions

### 2. **Context Management**
- Relevant context is passed between workflow stages
- Conversation history is maintained and utilized appropriately
- Form data is integrated into decision-making processes
- Research results are synthesized with existing information

### 3. **User Experience**
- Prompts maintain natural, conversational tone
- Technical information is explained in accessible language
- User preferences and constraints are respected
- Progressive disclosure prevents information overload

### 4. **System Reliability**
- Prompts include error handling and validation
- Fallback mechanisms for unexpected situations
- Graceful degradation when information is incomplete
- Consistent behavior across different scenarios

## Maintenance and Updates

### 1. **Version Control**
- All prompts are version controlled for tracking changes
- Changes are tested thoroughly before deployment
- Rollback mechanisms are available for prompt updates

### 2. **Performance Monitoring**
- Prompt effectiveness is monitored through user interactions
- Response quality and user satisfaction are tracked
- Prompt optimization is based on real-world usage data

### 3. **Continuous Improvement**
- Prompts are regularly reviewed and refined
- New scenarios and edge cases are incorporated
- User feedback is used to improve prompt effectiveness 