# 🚗 Living Form Tire Sales Agent

An intelligent AI tire sales assistant that uses dynamic forms and natural conversation to help users find the perfect tires, built with LangChain for robust AI interactions.

## 🏗️ Architecture

This application uses LangChain components for simplified, maintainable AI interactions:

- **LangChain Memory**: Automatic conversation history management
- **LangChain Chains**: Structured prompt templates and response generation  
- **LangChain Output Parsers**: Structured response parsing with fallback
- **LangChain Models**: Unified interface for multiple AI providers

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- API keys for AI models (OpenAI, Anthropic)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd Tires
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

5. **Run the application:**
   ```bash
   uvicorn main:app --reload --host localhost --port 8000
   ```

6. **Open your browser** to `http://localhost:8000`

## 📁 Project Structure

```
Tires/
├── main.py                    # FastAPI application
├── core/                      # Core business logic
│   ├── ai_client.py          # AI service client (LangChain models)
│   ├── form_builder.py       # Form generation
│   ├── simplified_coordinator.py # Main coordinator (LangChain-based)
│   ├── tire_chain.py         # LangChain chain for tire logic
│   ├── memory_manager.py     # LangChain memory management
│   └── output_parser.py      # LangChain output parsing
├── config/                    # Configuration
│   └── prompt.py             # AI system prompt
├── web/                       # Web assets
│   └── chat.html             # Frontend template
├── requirements.txt           # Python dependencies
└── Dockerfile                 # Container configuration
```

## 🎯 Key Features

- **Natural Conversation**: Talk to the AI like a knowledgeable tire salesperson
- **Dynamic Forms**: Interactive forms that adapt to the conversation
- **Smart Guidance**: AI helps users who don't know their vehicle details
- **Session Memory**: Automatic conversation history management with LangChain
- **Structured Output**: Reliable response parsing with fallback mechanisms
- **Simplified Architecture**: Reduced complexity with LangChain components

## 🔧 Development

### Running with Docker
```bash
docker build -t tire-assistant .
docker run -p 8000:8000 --env-file .env tire-assistant
```

### Running in Development Mode
```bash
uvicorn main:app --reload --host localhost --port 8000
```

### API Endpoints
- `GET /` - Main chat interface
- `POST /chat` - Process user messages
- `GET /health` - Health check
- `GET /session/{session_id}/notepad` - Get session notes


## 🧠 How It Works

1. **User Interaction**: User submits a form or sends a message
2. **LangChain Processing**: AI analyzes context using LangChain chains and memory
3. **Structured Output**: Response is parsed using LangChain output parsers
4. **Form Generation**: Dynamic forms are created from embedded function calls
5. **Response Delivery**: User receives conversational text with interactive forms
6. **Memory Update**: LangChain automatically manages conversation history

The system uses LangChain components for reliable, maintainable AI interactions with automatic memory management and structured output parsing.