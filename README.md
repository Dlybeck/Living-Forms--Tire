# 🚗 Tire Sales Assistant

An intelligent AI tire sales assistant that uses dynamic forms and natural conversation to help users find the perfect tires.

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
│   ├── ai_client.py          # AI service client

│   ├── form_builder.py       # Form generation
│   ├── function_call_parser.py # AI response parsing
│   ├── simplified_coordinator.py # Main coordinator
│   └── unified_tire_agent.py # AI agent logic
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

- **Session Memory**: Remembers conversation context and user preferences

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
2. **AI Processing**: AI analyzes context and generates response with form elements
3. **Form Generation**: Dynamic forms are created based on conversation needs
4. **Response Delivery**: User receives conversational text with interactive forms
5. **State Update**: System remembers context for next interaction

The AI uses function calls to generate forms, ensuring reliable and consistent user experience.