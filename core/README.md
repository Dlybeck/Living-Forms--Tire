# 🧠 Core Services - Technical Implementation

This folder contains the **backend processing components** that handle AI conversations, form generation, and data management.

## 📁 File Functions & Data Flow

### 🔄 **simplified_coordinator.py** - Request Router
**Tools Used:** LangChain, AIClient, FormBuilder

**Data Input:**
```python
{
    "user_message": "I need winter tires",
    "session_id": "abc123", 
    "form_data": {"make": "Honda", "model": "Civic"}
}
```

**Data Output:**
```python
{
    "response": "Let me help you find winter tires...",
    "form_html": "<form>...</form>",
    "ai_notepad": "Customer needs winter tires for Honda Civic",
    "coordinator_info": {"type": "simplified_langchain"}
}
```

**Data Flow:**
```
Receives request → Calls tire_chain.process_message() → Returns formatted response
```

---

### 🔗 **tire_chain.py** - LangChain Conversation Handler
**Tools Used:** LangChain chains, PromptTemplate, RunnableSequence

**Data Input:**
```python
{
    "chat_history": "Previous conversation...",
    "user_message": "I need winter tires",
    "form_data": {"make": "Honda"},
    "current_step": "tire_recommendation",
    "function_docs": "Available form functions...",
    "parser_instructions": "Parse response format..."
}
```

**Data Output:**
```python
{
    "response": "Let me help you! {create_text_field(name='model', label='Vehicle Model')}",
    "form_html": "<input type='text' name='model' />",
    "ai_notepad": "Internal analysis...",
    "memory_vars": {"chat_history": "Updated conversation..."}
}
```

**Data Flow:**
```
Input variables → LangChain chain → AI model → Parse response → Update memory
```

---

### 🏗️ **form_builder.py** - HTML Form Generator
**Tools Used:** Regex parsing, HTML generation

**Data Input:**
```python
conversation_with_fields = "Let me help you! {create_text_field(name='make', label='Vehicle Make')}"
```

**Data Output:**
```html
<form>
  <div class="form-group">
    <label>Vehicle Make</label>
    <input type="text" name="make" placeholder="e.g., Honda, Toyota" />
  </div>
  <button type="submit">Continue</button>
</form>
```

**Data Flow:**
```
Parse {create_field(...)} calls → Generate HTML → Return complete form
```

**Available Functions:**
- `{create_text_field(name, label, placeholder)}`
- `{create_select_field(name, label, options)}`
- `{create_checkbox_field(name, label, options)}`
- `{create_year_field(name, label)}`

---

### 🤖 **ai_client.py** - AI Model Interface
**Tools Used:** LangChain ChatOpenAI, ChatAnthropic

**Data Input:**
```python
{
    "user_message": "I need winter tires",
    "conversation_context": {"chat_history": "...", "form_data": {...}},
    "model_type": ModelType.O4_MINI,
    "agent_prompt": "You are a tire sales agent...",
    "function_documentation": "Available form functions..."
}
```

**Data Output:**
```python
{
    "response": "Let me help you find winter tires...",
    "usage": {"prompt_tokens": 150, "completion_tokens": 200},
    "model_info": {"provider": "openai", "model": "o4-mini"}
}
```

**Data Flow:**
```
Format prompt → Send to AI API → Parse response → Return structured data
```

---

### 🧠 **memory_manager.py** - Session Memory Handler
**Tools Used:** LangChain ConversationBufferWindowMemory

**Data Input:**
```python
session_id = "abc123"
message = "I have a Honda Civic"
form_data = {"make": "Honda", "model": "Civic"}
```

**Data Output:**
```python
{
    "chat_history": [
        "Human: I need winter tires",
        "AI: Let me help you...",
        "Human: I have a Honda Civic"
    ],
    "form_data": {"make": "Honda", "model": "Civic"}
}
```

**Data Flow:**
```
Store message → Update memory buffer → Retrieve history → Return context
```

---

### 📝 **output_parser.py** - Response Parser
**Tools Used:** Regex parsing, text extraction

**Data Input:**
```python
raw_response = """
Let me help you find winter tires!

[CONVERSATION]
I'd be happy to help you find the perfect winter tires for your Honda Civic.

[INTERNAL_ANALYSIS]
Customer has Honda Civic, needs winter tires. Should ask about year and driving conditions.
"""
```

**Data Output:**
```python
{
    "conversation_text": "I'd be happy to help you find the perfect winter tires...",
    "internal_analysis": "Customer has Honda Civic, needs winter tires...",
    "form_calls": ["{create_year_field(name='year', label='Vehicle Year')}"]
}
```

**Data Flow:**
```
Parse raw text → Extract conversation → Extract analysis → Return structured data
```

## 🔄 Component Data Flow

### **Complete Request Flow:**
```
1. simplified_coordinator.py receives request
2. Calls tire_chain.process_message()
3. tire_chain loads memory from memory_manager.py
4. tire_chain calls ai_client.py with formatted prompt
5. ai_client.py returns AI response
6. tire_chain calls output_parser.py to parse response
7. tire_chain calls form_builder.py if forms needed
8. tire_chain updates memory via memory_manager.py
9. simplified_coordinator.py returns final response
```

### **Memory Management Flow:**
```
1. memory_manager.py stores each user message
2. memory_manager.py stores each AI response
3. tire_chain.py retrieves history for context
4. memory_manager.py maintains session state
```

### **Form Generation Flow:**
```
1. AI response contains {create_field(...)} calls
2. output_parser.py extracts form calls
3. form_builder.py parses function calls
4. form_builder.py generates HTML
5. HTML embedded in final response
```

## 📊 Data Structures

### **Session Memory Structure:**
```python
{
    "session_id": "abc123",
    "chat_memory": [
        "Human: I need winter tires",
        "AI: Let me help you...",
        "Human: I have a Honda Civic"
    ],
    "form_data": {
        "make": "Honda",
        "model": "Civic"
    }
}
```

### **AI Prompt Structure:**
```python
{
    "agent_prompt": "You are a tire sales agent...",
    "chat_history": "Previous conversation...",
    "user_message": "Current user input",
    "form_data": {"make": "Honda"},
    "current_step": "tire_recommendation",
    "function_docs": "Available form functions...",
    "parser_instructions": "Parse response format..."
}
```

### **Form Function Call Format:**
```python
# Input format
"{create_text_field(name='make', label='Vehicle Make', placeholder='e.g., Honda')}"

# Parsed parameters
{
    "field_type": "text_field",
    "name": "make",
    "label": "Vehicle Make", 
    "placeholder": "e.g., Honda",
    "required": False
}
```

## 🔧 API Integration Points

### **AI Model APIs:**
- **OpenAI:** `o4-mini-2025-04-16` model via LangChain ChatOpenAI
- **Anthropic:** `claude-3-5-sonnet-latest` via LangChain ChatAnthropic

### **LangChain Components:**
- **ConversationBufferWindowMemory:** Stores conversation history
- **PromptTemplate:** Formats prompts with variables
- **RunnableSequence:** Chains prompt → AI model

### **Data Validation:**
- **Pydantic models:** Validate request/response data
- **Type hints:** Ensure data type consistency
- **Error handling:** Graceful failure with fallbacks

---

*These components work together to process user requests through AI models, generate dynamic forms, and maintain conversation context using LangChain and modern AI APIs.* 