# 🚗 Living Form Tire Sales Agent - Technical Flow

## 🛠️ Tools & Components

### **Backend Tools:**
- **FastAPI** - Web server that handles HTTP requests
- **LangChain** - AI conversation management and memory
- **OpenAI/Anthropic APIs** - AI models for generating responses
- **Pydantic** - Data validation for requests/responses

### **Frontend Tools:**
- **HTML/CSS/JavaScript** - Web interface
- **Fetch API** - Sends data to backend
- **DOM manipulation** - Updates page content dynamically

### **Data Storage:**
- **In-memory session storage** - Stores conversation history
- **LangChain memory buffers** - Manages AI context

## 📊 Data Flow Between Components

### 1️⃣ **User Input → Frontend**
```
User types in form → JavaScript captures form data → Creates JSON payload
```

**Data Structure:**
```json
{
  "request_type": "form_submission",
  "session_id": "abc123",
  "form_data": {
    "make": "Honda",
    "model": "Civic",
    "year": "2019"
  }
}
```

### 2️⃣ **Frontend → Backend**
```
JavaScript fetch() → POST to /chat endpoint → FastAPI receives request
```

**HTTP Request:**
```javascript
fetch('/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(payload)
})
```

### 3️⃣ **Backend Processing Chain**
```
FastAPI → SimplifiedCoordinator → TireAgentChain → AI Client → AI Model
```

**Data Passed Between:**
- **FastAPI** receives JSON, validates with Pydantic models
- **SimplifiedCoordinator** extracts user_message, session_id, form_data
- **TireAgentChain** combines with conversation history from memory
- **AI Client** formats prompt and sends to OpenAI/Anthropic
- **AI Model** returns raw text response

### 4️⃣ **AI Response Processing**
```
AI Model → Output Parser → Form Builder → Response Assembly
```

**Data Transformations:**
- **Raw AI text** → **Parsed response** (conversation + internal analysis)
- **Parsed response** → **HTML forms** (if contains form function calls)
- **Final response** → **JSON payload** for frontend

### 5️⃣ **Backend → Frontend**
```
FastAPI returns JSON → JavaScript receives response → DOM updates
```

**Response Structure:**
```json
{
  "response": "Great! I see you have a 2019 Honda Civic...",
  "form_html": "<form>...</form>",
  "conversation_state": "vehicle_details",
  "session_id": "abc123",
  "notepad_content": "AI's internal analysis..."
}
```

## 🔄 Memory & Session Management

### **Session Data Storage:**
```
User starts conversation → Generate unique session_id → Store in memory
```

**Memory Structure:**
```python
# LangChain memory buffer stores:
{
  "chat_history": [
    "Human: I need winter tires",
    "AI: Let me help you find winter tires...",
    "Human: I have a Honda Civic",
    "AI: Great! What year is your Honda Civic?"
  ],
  "form_data": {
    "make": "Honda",
    "model": "Civic"
  }
}
```

### **Context Building:**
```
Each request → Load previous conversation → Add new data → Update memory
```

## 🏗️ Form Generation Process

### **AI Response with Form Calls:**
```
AI generates: "Let me help you! {create_text_field(name='make', label='Vehicle Make')}"
```

### **Form Builder Processing:**
```
Parse function calls → Generate HTML → Embed in response
```

**Transformation:**
```python
# Input: {create_text_field(name='make', label='Vehicle Make')}
# Output: <input type="text" name="make" label="Vehicle Make" />
```

## 🔧 API Endpoints & Data Exchange

### **POST /chat**
**Input:** User message and form data
**Output:** AI response with optional forms
**Data flow:** Frontend → Backend → AI → Response

### **GET /session/{session_id}/notepad**
**Input:** Session ID
**Output:** AI's internal notes
**Data flow:** Frontend → Backend → Memory → Notes

### **GET /health**
**Input:** None
**Output:** System status
**Data flow:** Frontend → Backend → Component status

## 📝 Key Data Structures

### **Request Models (Pydantic):**
```python
class ChatMessage(BaseModel):
    request_type: str
    session_id: str
    form_data: Optional[Dict[str, Any]] = None
```

### **Response Models (Pydantic):**
```python
class ChatResponse(BaseModel):
    response: str
    form_html: Optional[str] = None
    conversation_state: str
    session_id: str
    notepad_content: Optional[str] = None
```

### **AI Prompt Template:**
```python
template = """
{agent_prompt}
Current AI Notepad: {chat_history}
User Message: {user_message}
Form Data: {form_data}
Conversation Context: {current_step}
Function Documentation: {function_docs}
{parser_instructions}
"""
```

## 🔄 Error Handling & Data Flow

### **Frontend Errors:**
```
Network error → Show error message → Retry option
Form validation error → Highlight invalid fields → Prevent submission
```

### **Backend Errors:**
```
AI API error → Return error response → Frontend shows message
Memory error → Create new session → Continue conversation
```

### **Data Validation:**
```
Pydantic validates request → Invalid data rejected → Error response
Session ID validation → Invalid session → New session created
```

## 🚀 Getting Started - Technical Setup

### **1. Install Dependencies:**
```bash
pip install fastapi uvicorn langchain openai anthropic pydantic
```

### **2. Set Environment Variables:**
```bash
export OPENAI_API_KEY="your_key"
export ANTHROPIC_API_KEY="your_key"
```

### **3. Run Server:**
```bash
python main.py
# Server starts on http://localhost:8000
```

### **4. Test Data Flow:**
```bash
# Test API endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"request_type":"initial","session_id":"test123","form_data":{}}'
```

---

*This system uses FastAPI + LangChain + AI APIs to create dynamic forms within AI conversations, with in-memory session management and real-time frontend updates.* 