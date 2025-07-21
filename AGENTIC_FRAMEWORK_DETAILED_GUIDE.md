# 🚗 Living Form Tire Sales Assistant - Agentic Framework Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [External User Experience](#external-user-experience)
3. [Internal Architecture](#internal-architecture)
4. [Agent Handoff Process](#agent-handoff-process)
5. [Data Flow](#data-flow)
6. [Agent Specializations](#agent-specializations)
7. [Memory Management](#memory-management)
8. [State Management](#state-management)
9. [Form Generation](#form-generation)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

The Living Form Tire Sales Assistant is a multi-agent AI system that provides personalized tire recommendations through conversational forms. The system uses specialized agents that hand off to each other based on completion criteria, creating a seamless user experience.

### Core Principles
- **Agentic Workflows**: Each agent has a specific expertise area
- **Intelligent Handoffs**: Agents signal completion and hand off to the next specialist
- **Context Preservation**: All information flows between agents seamlessly
- **Living Forms**: Dynamic form generation based on conversation context
- **Memory Management**: AI-powered conversation compression and context management

---

## 👥 External User Experience

### User Journey Flow

#### 1. **Initial Contact**
```
User opens chat → System asks: "How would you like to find your tire size?"
Options: Wheel size, VIN, Make/Model/Year/Trim, or "I don't know"
```

#### 2. **Tire Size Discovery** (TireSizeAgent)
```
User provides vehicle info → Agent determines exact tire specifications
Agent asks for: Make, Model, Year, Trim (if needed)
Agent extracts: Tire size, load rating, speed rating
Agent signals completion when tire specs are confirmed
```

#### 3. **Driving Information Collection** (DrivingInfoAgent)
```
Agent asks about: Location/climate, annual mileage, driving surfaces
Agent collects: Ownership timeline, driving style, environmental factors
Agent signals completion when all driving factors are understood
```

#### 4. **Preferences Gathering** (PreferencesAgent)
```
Agent asks about: Brand preferences, key aspects (performance/cost/longevity)
Agent collects: Budget considerations, specific requirements
Agent signals completion when preferences are clear
```

#### 5. **Recommendation Generation** (RecommendationAgent)
```
Agent provides: Personalized tire recommendations with explanations
Agent continues: Taking user feedback and refining recommendations
Agent never hands off: Stays active until user is satisfied
```

### User Interface Elements

#### **Agent Display**
- Blue bar above AI responses showing current specialist
- Format: "🚗 [Agent Name] - [Current Task]"
- Updates automatically when agents hand off

#### **Form Elements**
- Dynamic forms generated based on conversation context
- Dropdown menus for structured choices
- Text fields with helpful placeholders
- "Additional Thoughts" field automatically included

#### **Chat Interface**
- Conversation history with user messages and AI responses
- Auto-scrolling to keep latest messages visible
- Form submission with green "Verify" button
- Check mark confirmation upon completion

---

## 🏗️ Internal Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Agent         │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   Coordinator   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Specialized   │
                       │     Agents      │
                       └─────────────────┘
```

### Core Files and Responsibilities

#### **Backend Entry Point**
- `main.py`: FastAPI server, chat endpoint, response formatting

#### **Agent Coordination**
- `agents/improved_agent_coordinator.py`: Main orchestrator, handoff management
- `utils/agent_handoff.py`: Handoff logic and validation
- `utils/state_manager.py`: Conversation state management

#### **Specialized Agents**
- `agents/tire_size_agent.py`: Vehicle and tire specification discovery
- `agents/driving_info_agent.py`: Driving patterns and environmental factors
- `agents/preferences_agent.py`: User preferences and requirements
- `agents/recommendation_agent.py`: Tire recommendations and refinement
- `agents/scribe_agent.py`: Information extraction and recording

#### **Supporting Systems**
- `utils/memory_manager.py`: Conversation compression and context management
- `agents/form_builder.py`: Dynamic form generation
- `agents/ai_client.py`: AI model integration
- `database/tire_database.py`: Tire data and recommendations

---

## 🔄 Agent Handoff Process

### **Improved Handoff Flow (Post-Processing)**

The system now uses a more efficient handoff process that eliminates wasteful intermediate steps:

#### **Step-by-Step Flow**

1. **User Submits Form**
   ```python
   # Frontend sends form data to /chat endpoint
   POST /chat
   {
     "message": "user input",
     "form_data": {...},
     "session_id": "unique_id"
   }
   ```

2. **ScribeAgent Extracts Information**
   ```python
   # Coordinator calls ScribeAgent first
   scribe_result = await self.scribe_agent.extract_and_record(
       user_message=user_message,
       roadmap=session,
       conversation_context=conversation_context
   )
   
   # Update state with extracted information
   await self._update_state_with_extracted_info(state, scribe_result["extracted_info"])
   ```

3. **Current Agent Processes**
   ```python
   # Process with current agent
   response = await current_agent.process_message(
       user_message=user_message,
       roadmap=session,
       conversation_context=conversation_context
   )
   ```

4. **Check for Handoff (AFTER Processing)**
   ```python
   # Check if current agent signals completion
   should_handoff = response.get('agent_complete', False)
   
   if should_handoff:
       # Determine next agent
       target_agent_name = await self.handoff_manager.get_agent_for_step(state.current_step)
       
       # Switch to next agent
       state = await self.state_manager.update_state(current_agent=target_agent_name)
       
       # Process with next agent using SAME user message
       next_response = await next_agent.process_message(
           user_message=user_message,
           roadmap=session,
           conversation_context=conversation_context
       )
       
       # Use next agent's response
       response = next_response
   ```

5. **Return Response to User**
   ```python
   # Response includes agent identification and completion status
   return {
       "message": response["message"],
       "form": response.get("form"),
       "current_agent": response.get("current_agent"),
       "agent_display_name": response.get("agent_display_name"),
       "coordinator_info": {...}
   }
   ```

### **Key Improvements**

#### **Before (Problematic)**
```
User submits → Check handoff → Switch agent → Process same data → Ask for info already provided
```

#### **After (Improved)**
```
User submits → Process with current agent → If complete → Switch to next agent → Process again
```

#### **Benefits**
- **No wasted steps**: Eliminates intermediate processing of same data
- **Seamless UX**: User gets next agent's response immediately
- **Context preserved**: All extracted info available to next agent
- **Efficient**: ScribeAgent extracts once, all agents share context

### **Agent Completion Criteria**

Each agent has intelligent completion criteria based on their expertise:

#### **TireSizeAgent**
```python
# Done when agent knows EXACTLY what tires fit and work for user's car
is_complete = has_vehicle_info and has_tire_specs
reason = "Vehicle and tire specifications complete"
```

#### **DrivingInfoAgent**
```python
# Done when agent can recommend objectively good tires considering ALL factors
is_complete = has_location_climate and has_mileage and has_driving_surfaces and has_ownership_timeline
reason = "All driving factors understood"
```

#### **PreferencesAgent**
```python
# Done when agent is certain about user's preferences
is_complete = has_brand_preferences and has_key_aspects and has_price_considerations
reason = "User preferences clear"
```

#### **RecommendationAgent**
```python
# NEVER done - stays active until user is satisfied
is_complete = False  # Always false
reason = "Continuing to provide recommendations"
```

---

## 📊 Data Flow

### **Information Extraction and Storage**

#### **ScribeAgent Extraction**
```python
# Extracts structured information from user messages
extracted_info = {
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry", 
    "vehicle_year": "2020",
    "tire_size": "225/45R17",
    "driving_location": "California",
    "annual_mileage": 12000,
    # ... more structured data
}
```

#### **State Management**
```python
# ConversationState tracks current progress
state = ConversationState(
    current_step=ConversationStep.TIRE_SIZE,
    current_agent="TireSizeAgent",
    important_data={...},
    conversation_history=[...],
    metadata={...}
)
```

#### **Memory Management**
```python
# AI-powered conversation compression
compressed_summary = await memory_manager.compress_conversation_if_needed(session)
# Reduces context size while preserving important information
```

### **Context Propagation**

#### **Between Agents**
```python
# All agents receive the same conversation_context
conversation_context = {
    "extracted_info": scribe_result["extracted_info"],
    "current_state": state,
    "conversation_history": session["history"],
    "important_data": state.important_data,
    "agent_complete": previous_response.get("agent_complete"),
    "completion_reason": previous_response.get("completion_reason")
}
```

#### **Form Generation Context**
```python
# FormBuilder uses context to generate relevant forms
form = await form_builder.build_form(
    agent_name=current_agent_name,
    conversation_context=conversation_context,
    current_step=state.current_step
)
```

---

## 🎭 Agent Specializations

### **TireSizeAgent**
**Purpose**: Determine exact tire specifications for user's vehicle

**Key Responsibilities**:
- Extract vehicle information (make, model, year, trim)
- Determine tire size, load rating, speed rating
- Handle VIN decoding and wheel size calculations
- Validate tire compatibility

**Completion Criteria**: Has complete vehicle and tire specifications

**Form Fields**:
- Vehicle make, model, year
- Vehicle trim (if needed)
- VIN number (alternative method)
- Wheel size (alternative method)

### **DrivingInfoAgent**
**Purpose**: Understand driving patterns and environmental factors

**Key Responsibilities**:
- Assess driving environment (city/highway, road surfaces)
- Determine climate and weather conditions
- Calculate annual mileage and usage patterns
- Understand ownership timeline and future plans

**Completion Criteria**: Can recommend objectively good tires considering all factors

**Form Fields**:
- Location/region (for climate understanding)
- Total vehicle mileage and model year
- Driving environment (city/highway mix, road surfaces)
- Weather conditions relevant to region
- Driving style and primary vehicle use
- How long they plan to keep the car
- Specific performance expectations

### **PreferencesAgent**
**Purpose**: Understand user preferences and requirements

**Key Responsibilities**:
- Identify brand preferences and priorities
- Determine key aspects (performance, cost, longevity)
- Assess budget considerations
- Understand specific requirements and constraints

**Completion Criteria**: Certain about user's preferences including brand, key aspects, and price

**Form Fields**:
- Brand preferences (specific brands or "no preference")
- Key aspects (performance, cost, longevity, comfort)
- Budget considerations
- Specific requirements or constraints
- Seasonal tire planning needs

### **RecommendationAgent**
**Purpose**: Provide personalized tire recommendations

**Key Responsibilities**:
- Generate tire recommendations based on all collected information
- Explain recommendations and trade-offs
- Handle user feedback and refine recommendations
- Provide pricing and availability information

**Completion Criteria**: Never completes - stays active until user is satisfied

**Form Fields**:
- User feedback on recommendations
- Specific questions about tires
- Additional requirements or concerns

### **ScribeAgent**
**Purpose**: Extract and record information from user messages

**Key Responsibilities**:
- Parse user messages for structured information
- Update conversation state with extracted data
- Maintain conversation history and context
- Provide strategic command and emotional intelligence

**Completion Criteria**: Information extraction is ongoing

---

## 🧠 Memory Management

### **Conversation Compression**

The system uses AI-powered memory management to handle long conversations:

```python
# MemoryManager compresses conversations when they get too long
compression_occurred = await self.memory_manager.compress_conversation_if_needed(session)

if compression_occurred:
    # Conversation history is summarized while preserving important details
    # Context size is reduced to maintain performance
```

### **Context Preservation**

Important information is preserved across compressions:
- Vehicle specifications
- User preferences
- Critical decisions
- Current agent state
- Extracted information

### **Memory Statistics**

The system tracks memory usage:
```python
memory_stats = {
    "total_messages": len(session["history"]),
    "compressed_messages": compressed_count,
    "context_size": current_context_size,
    "compression_ratio": compression_ratio
}
```

---

## 🔧 State Management

### **ConversationState**

The system maintains conversation state across all interactions:

```python
class ConversationState:
    current_step: ConversationStep
    current_agent: str
    important_data: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str
    created_at: datetime
    updated_at: datetime
```

### **Step Progression**

```python
class ConversationStep(Enum):
    TIRE_SIZE = "tire_size"
    DRIVING_INFO = "driving_info"
    PREFERENCES = "preferences"
    RECOMMENDATIONS = "recommendations"
```

### **State Updates**

State is updated throughout the conversation:
- When information is extracted by ScribeAgent
- When agents complete their tasks
- When handoffs occur
- When user provides new information

---

## 📝 Form Generation

### **Dynamic Form Building**

Forms are generated dynamically based on:
- Current agent and step
- Conversation context
- Previously collected information
- User's current needs

### **FormBuilder Process**

```python
# FormBuilder generates contextually relevant forms
form = await form_builder.build_form(
    agent_name=current_agent_name,
    conversation_context=conversation_context,
    current_step=state.current_step
)
```

### **Form Elements**

Forms include various input types:
- **Text fields**: For free-form input with helpful placeholders
- **Dropdown menus**: For structured choices
- **Multiple choice**: For preference selection
- **Additional Thoughts**: Automatically included for extra context

### **Context-Aware Generation**

Forms adapt based on:
- What information has already been collected
- Current conversation flow
- User's previous responses
- Agent's specific needs

---

## 🐛 Troubleshooting

### **Common Issues**

#### **Agent Display Not Showing**
- Check that `coordinator_info` is included in response
- Verify `current_agent_name` and `agent_display_name` are set
- Ensure frontend is reading the correct response fields

#### **Handoff Not Occurring**
- Verify agent is signaling completion (`agent_complete: true`)
- Check handoff validation in `agent_handoff.py`
- Ensure next agent exists in agent mapping

#### **Context Loss Between Agents**
- Confirm ScribeAgent is extracting information correctly
- Check that `conversation_context` is being passed to all agents
- Verify state updates are occurring properly

#### **Form Not Generating**
- Check FormBuilder is receiving correct context
- Verify agent name and step are valid
- Ensure conversation context includes necessary information

### **Debug Information**

The system includes comprehensive logging:

```python
# Debug logging in coordinator
logger.info(f"Coordinator info: current_agent={state.current_agent}, handoff_occurred={should_handoff}")
logger.info(f"Response keys: {list(response.keys())}")
logger.info(f"Agent display name: {response.get('agent_display_name', 'NOT FOUND')}")
```

### **Testing Tools**

Use the test script to verify agent display:
```bash
python test_agent_display.py
```

---

## 🚀 Performance Considerations

### **AI Model Selection**
- System uses cost-effective models (Claude Sonnet series)
- Avoids expensive models like Claude Opus 4
- Balances performance with cost

### **Memory Optimization**
- Conversation compression reduces context size
- Important information is preserved across compressions
- Context size is monitored and managed

### **Handoff Efficiency**
- Post-processing handoff eliminates wasteful steps
- Single ScribeAgent extraction for all agents
- Context sharing reduces duplicate processing

---

## 📈 Future Enhancements

### **Potential Improvements**
- Enhanced emotional intelligence in agent responses
- More sophisticated completion criteria
- Advanced memory management techniques
- Integration with additional tire databases
- Real-time pricing and availability updates

### **Scalability Considerations**
- Horizontal scaling of agent instances
- Database optimization for large conversation histories
- Caching strategies for frequently accessed data
- Load balancing for high-traffic scenarios

---

*This guide provides a comprehensive overview of the Living Form Tire Sales Assistant's agentic framework. For specific implementation details, refer to the individual component files and their documentation.* 