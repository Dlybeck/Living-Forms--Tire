# Configuration Module Overview

The `config/` directory contains all configuration files, system prompts, and AI behavior definitions that control how the Tire Sales Assistant operates and interacts with users.

## 📁 File Descriptions

### 🧠 `prompt.py` (133 lines)
**Purpose**: Defines the AI agent's personality, behavior, and conversation flow

**Key Components**:

#### **System Personality**
- **Living Form Tire Sales Agent**: The AI's core identity as an intelligent, empathetic tire salesperson
- **Mission-Driven**: Focused on getting accurate tire recommendations quickly while ensuring 5-star user experience
- **Conversational Style**: Clear, engaging, and professional without being overly formal

#### **Internal Thinking Process: "Riley's Head"**
The AI uses a sophisticated internal thinking system inspired by the movie "Inside Out":

**Emotions**:
- **Logic**: Analyzes facts and current situation, empowered to search web for information
- **Empathy**: Focuses on user emotional state, reduces friction and confusion
- **Urgency**: Drives efficiency, hates repetitive questions
- **Curiosity**: Explores unknowns, identifies missing information
- **Joy**: Celebrates progress, builds trust
- **Fear**: Identifies risks and potential misunderstandings
- **Productivity**: Optimizes efficiency, prefers looking up info rather than asking repeatedly

**Memory System**:
- **Memory Wall**: Stores all user information and discovered facts
- **Memory Display**: Shows current user interactions
- **Console**: Coordinates emotional responses and decision-making

#### **Mission Stages**
The agent follows a progressive 4-stage flow:

1. **Discovering Tire Size & Vehicle Specs**
   - Collect make, model, year, trim
   - Guide users who don't know their specs
   - Look up information when possible

2. **Understanding Preferences & Usage**
   - Gather driving habits and conditions
   - Understand climate and weather exposure
   - Identify performance priorities

3. **Recommending Ideal Tires**
   - Provide tailored suggestions
   - Explain reasoning and benefits
   - Offer multiple options when appropriate

4. **Decision Support**
   - Answer follow-up questions
   - Compare options in detail
   - Guide to confident final choice

#### **Form Integration Rules**
- **Embedded Functions**: Form fields are embedded directly in conversation text
- **Function Format**: `{create_text_field(name="field_name", label="Question", placeholder="example")}`
- **Available Functions**:
  - `create_text_field()` - Single line text input
  - `create_textarea_field()` - Multi-line text input
  - `create_select_field()` - Dropdown selection
  - `create_checkbox_field()` - Multiple choice checkboxes
  - `create_year_field()` - Year selection

#### **Response Format**
The AI generates structured responses with three sections:
```
[INTERNAL_ANALYSIS]
Riley's internal thinking process...

[CONVERSATION]
User-facing conversational text with embedded form fields...

[FORM]
Additional form HTML if needed...
```

#### **Key Behavioral Rules**
- **Be Decisive**: Take action when you have enough information
- **Acknowledge & Progress**: Always acknowledge what users provide (or don't provide)
- **Form-Only Interaction**: Generate forms for all information gathering
- **Avoid Repetition**: Never ask for information already known
- **Look Up Information**: Research details rather than asking users repeatedly

**Usage**: Imported by `tire_agent.py` to define AI behavior and response generation

---

## 🔧 Configuration Management

### Environment-Based Configuration
The system uses environment variables for sensitive configuration:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Prompt Versioning
- **Current Version**: Living Form Tire Sales Agent v1.0
- **Update Strategy**: Version-controlled prompt changes
- **Testing**: Prompts tested with various user scenarios

### Model-Specific Adaptations
The prompt system adapts to different AI models:

- **O4-Mini**: Optimized for reasoning and analysis
- **Claude 3.5 Sonnet**: Adapted for conversation flow
- **Fallback Handling**: Graceful degradation on model failures

## 🎯 Design Principles

### 1. **Conversation-First Design**
- Natural, flowing conversations
- Forms embedded seamlessly in dialogue
- Context-aware responses

### 2. **User-Centric Approach**
- Empathetic and helpful tone
- Clear explanations and guidance
- Reduced friction and confusion

### 3. **Efficiency Optimization**
- Avoid repetitive questions
- Proactive information gathering
- Quick progression through stages

### 4. **Reliability and Consistency**
- Structured response formats
- Error handling and fallbacks
- Predictable behavior patterns

## 🔄 Integration Points

### Core Module Integration
- **tire_agent.py**: Uses prompt for AI behavior definition
- **ai_client.py**: Incorporates prompt in API calls
- **form_builder.py**: Aligns with form generation rules

### External Dependencies
- **AI Models**: Prompt optimized for OpenAI and Anthropic models
- **Web Search**: Integration with research capabilities
- **Form Functions**: Alignment with available form field types

## 🚀 Customization and Extension

### Adding New Form Fields
1. Define function in `form_builder.py`
2. Update function documentation
3. Add to prompt examples if needed

### Modifying AI Behavior
1. Update prompt sections in `prompt.py`
2. Test with various user scenarios
3. Validate response format consistency

### Adding New Mission Stages
1. Define stage in prompt
2. Update coordinator logic
3. Add appropriate form functions

## 📊 Monitoring and Analytics

### Prompt Performance
- **Response Quality**: Monitor AI response accuracy
- **User Satisfaction**: Track form completion rates
- **Error Rates**: Monitor parsing and generation failures

### Optimization Opportunities
- **Common Patterns**: Identify frequently asked questions
- **User Pain Points**: Areas where users struggle
- **Efficiency Gains**: Opportunities to reduce interaction steps

This configuration module provides the foundation for consistent, intelligent, and user-friendly tire sales assistance while maintaining flexibility for future enhancements and customizations. 