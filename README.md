# 🚗 Tire Sales Assistant - Living Form AI

An intelligent conversational tire sales assistant that uses the innovative "Living Form" approach to guide users through finding the perfect tires for their vehicle.

## 🎯 What is the "Living Form" Approach?

The Living Form is a revolutionary way of building AI interfaces that combines:
- **Conversational AI** that thinks and responds naturally
- **Dynamic Forms** that adapt based on the conversation
- **Contextual Guidance** that helps users succeed in their goals

Instead of rigid chatbots or static forms, the Living Form creates an experience where:
- Every AI response includes interactive form elements
- The AI builds on previous responses and remembers context
- Users can express themselves naturally while being guided toward success
- The interface adapts to user confusion and provides appropriate help

## 🏗️ System Architecture

### Core Components

1. **Conversation Orchestrator** (`agents/conversation_orchestrator.py`)
   - Main controller that processes user messages
   - Manages conversation flow and state
   - Coordinates between AI client and form generation

2. **AI Client** (`agents/ai_client.py`)
   - Handles communication with multiple AI models (Claude, GPT)
   - Manages cost optimization and model selection
   - Builds conversation context and prompts

3. **Form Builder** (`agents/form_builder.py`)
   - Generates dynamic HTML forms based on AI function calls
   - Creates interactive elements that match conversation context
   - Handles form validation and submission

4. **State Manager** (`utils/state_manager.py`)
   - Tracks conversation state and user progress
   - Stores vehicle information, preferences, and responses
   - Manages conversation history and context

5. **Cost Manager** (`agents/cost_manager.py`)
   - Optimizes AI model selection based on query complexity
   - Tracks spending and enforces budget limits
   - Balances cost vs. quality for different interaction types

## 🧠 How It Works

### The Living Form Process

1. **User Interaction**: User submits a form or sends a message
2. **Context Building**: System gathers conversation history, form data, and user state
3. **AI Processing**: AI analyzes the context and generates a thoughtful response
4. **Form Generation**: AI uses function calls to create appropriate form elements
5. **Response Delivery**: User receives conversational text with interactive forms
6. **State Update**: System updates conversation state and prepares for next interaction

### Key Innovation: Function-Based Form Generation

Instead of parsing text to create forms, the AI uses structured function calls:

```python
[FUNCTION_CALL] create_text_field(name="vehicle_make", label="What is your vehicle's make?", required=False)
[FUNCTION_CALL] create_radio_field(name="driving_style", label="How would you describe your driving style?", options=["Conservative", "Moderate", "Aggressive"], required=False)
```

This ensures:
- ✅ Reliable form generation
- ✅ Consistent user experience
- ✅ Proper form validation
- ✅ Seamless conversation flow

## 🎨 User Experience Features

### Adaptive Intelligence
- **Diagnostic Approach**: When users are confused, the AI asks diagnostic questions to understand their situation
- **Contextual Memory**: AI remembers what users have told them and builds on previous responses
- **Progressive Guidance**: System provides more detailed help when users struggle
- **Creative Problem-Solving**: AI suggests alternative approaches when standard methods don't work

### Smart Form Design
- **Optional Fields**: All form fields are optional to avoid restricting user expression
- **Contextual Forms**: Form elements match the conversation context
- **Escape Routes**: "Confused? Need help?" field provides a way out of any situation
- **Visual Feedback**: Clear submission confirmations and progress indicators

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- API keys for AI models (OpenAI, Anthropic)
- Modern web browser

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Tires
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file with your API keys
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Open browser**:
   Navigate to `http://localhost:8000` to use the Living Form interface

## 🔧 Recent Simplifications

The system has been significantly simplified by removing:
- ❌ Database dependencies (tire_database.py, car-models.json)
- ❌ Web search functionality 
- ❌ Complex inheritance patterns (BaseAgent)
- ❌ Unused dependencies (pandas, numpy, etc.)
- ❌ Verbose debug logging

**Benefits**: Easier to understand, faster to modify, lower maintenance overhead, and reduced costs.

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Create .env file
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

5. **Run the application**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

6. **Open your browser** to `http://localhost:8000`

## 🔧 Configuration

### Cost Management
The system includes sophisticated cost management:
- **Budget Control**: Set conversation-level spending limits
- **Model Selection**: Automatic selection of appropriate AI models based on query complexity
- **Cost Tracking**: Real-time monitoring of spending across sessions

### AI Model Support
- **Claude Models**: Sonnet 4, Claude 3.7, Claude 3.5 Sonnet
- **GPT Models**: GPT-4o, GPT-4o Mini, GPT-4.1 variants
- **Automatic Fallbacks**: System gracefully handles API failures

## 📊 Project Structure

```
Tires/
├── agents/                 # Core AI and conversation logic
│   ├── ai_client.py       # AI model communication
│   ├── conversation_orchestrator.py  # Main conversation controller
│   ├── cost_manager.py    # Cost optimization
│   ├── form_builder.py    # Dynamic form generation
│   └── function_call_parser.py  # AI function call processing
├── database/              # Data storage and retrieval
│   └── tire_database.py   # Tire information database
├── prompts/               # AI system prompts
│   └── system_prompt.py   # Main AI behavior definition
├── utils/                 # Utilities and state management
│   └── state_manager.py   # Conversation state tracking
├── templates/             # HTML templates
│   └── chat.html         # Main chat interface
├── static/               # Static assets (CSS, JS)
├── main.py              # FastAPI application entry point
└── requirements.txt     # Python dependencies
```

## 🎯 Key Features

### For Users
- **Natural Conversation**: Talk to the AI like you would a knowledgeable tire salesperson
- **Adaptive Help**: System adjusts to your knowledge level and situation
- **Multiple Input Methods**: Provide vehicle info via tire size, VIN, make/model/year, or get help figuring it out
- **No Dead Ends**: Always have a way to continue or get help