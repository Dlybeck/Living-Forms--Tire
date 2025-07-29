# 🚗 Living Form Tire Sales Agent

An intelligent AI tire sales assistant that uses dynamic forms and natural conversation to help users find the perfect tires, built with LangChain for robust AI interactions.

## 📚 Documentation Overview

This project includes comprehensive documentation to help you understand and work with the system:

- **[AGENT_FLOW.md](AGENT_FLOW.md)** - Complete system overview and information flow
- **[core/README.md](core/README.md)** - AI processing engine documentation
- **[config/README.md](config/README.md)** - Configuration and prompt system
- **[web/README.md](web/README.md)** - Frontend interface documentation

## 🏗️ Architecture

This application uses LangChain components for simplified, maintainable AI interactions:

- **LangChain Memory**: Automatic conversation history management
- **LangChain Chains**: Structured prompt templates and response generation  
- **LangChain Output Parsers**: Structured response parsing with fallback
- **LangChain Models**: Unified interface for multiple AI providers

## 🔄 How Information Flows

### 1️⃣ **User Starts Conversation**
```
User types request → Web Interface → FastAPI Server → Simplified Coordinator
```

### 2️⃣ **AI Processes & Responds**
```
Simplified Coordinator → Tire Agent Chain → AI Client → Response Generation
```

### 3️⃣ **Form Submission & Processing**
```
User fills form → Form data sent back → AI processes new info → Next form/response
```

## 🚀 Quick Start (2-Step Process)

### Step 1: Setup Environment
```bash
# Clone and navigate to the project
git clone <repository-url>
cd Tires

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_key_here"
export ANTHROPIC_API_KEY="your_anthropic_key_here"
```

### Step 2: Run the System
```bash
# Start the server
python main.py

# Open browser to http://localhost:8000
```

## 📁 Project Structure

```
Tires/
├── AGENT_FLOW.md              # 📖 Complete system documentation
├── main.py                    # 🚀 FastAPI application entry point
├── core/                      # 🧠 AI processing engine
│   ├── README.md             # 📖 Core services documentation
│   ├── ai_client.py          # 🤖 Multi-model AI interface
│   ├── form_builder.py       # 🏗️ Dynamic form generator
│   ├── simplified_coordinator.py # 🔄 Main conversation orchestrator
│   ├── tire_chain.py         # 🔗 LangChain conversation processor
│   ├── memory_manager.py     # 🧠 Conversation memory system
│   └── output_parser.py      # 📝 Response parsing and structuring
├── config/                    # ⚙️ System configuration
│   ├── README.md             # 📖 Configuration documentation
│   └── prompt.py             # 🧠 AI behavior and personality
├── web/                       # 🌐 User interface
│   ├── README.md             # 📖 Frontend documentation
│   ├── chat.html             # 🎨 Main interface template
│   ├── app.js                # ⚡ Interactive functionality
│   └── styles.css            # 🎨 Visual design and layout
├── requirements.txt           # 📦 Python dependencies
└── Dockerfile                 # 🐳 Container configuration
```

## 🎯 Key Features

### ✅ **Living Form Concept**
- Forms appear naturally within conversation
- No rigid question-answer format
- Contextual help and guidance
- Professional, engaging experience

### ✅ **Intelligent AI Processing**
- LangChain-based conversation management
- Multi-model AI support (OpenAI, Anthropic)
- Automatic memory and context management
- Structured response parsing

### ✅ **Professional User Interface**
- Modern, responsive design
- Mobile-optimized experience
- Real-time AI notepad sidebar
- Smooth animations and transitions

### ✅ **Robust Architecture**
- Modular, maintainable code structure
- Clear separation of concerns
- Easy to extend and customize
- Comprehensive error handling

## 🧠 The "Living Form" Experience

### Traditional Chatbot vs Living Form

**❌ Traditional Chatbot:**
```
Bot: "What's your vehicle make?"
User: "Honda"
Bot: "What's your vehicle model?"
User: "Civic"
Bot: "What year?"
User: "2019"
```

**✅ Living Form:**
```
Bot: "Let me help you find the perfect tires! First, I need to know about your vehicle:

{create_text_field(name="make", label="Vehicle Make", placeholder="e.g., Honda, Toyota")}
{create_text_field(name="model", label="Vehicle Model", placeholder="e.g., Civic, Camry")}
{create_year_field(name="year", label="Vehicle Year")}

Once you provide these details, I can look up the exact tire specifications for your vehicle."
```

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

## 🎨 System Benefits

1. **User Experience:** Natural conversation flow with embedded forms
2. **Developer Experience:** Clean, modular architecture with clear separation of concerns
3. **Maintainability:** Each component has a single responsibility
4. **Scalability:** Easy to add new AI models or form field types
5. **Cost Efficiency:** Smart model selection and usage tracking

## 🔍 Troubleshooting

### Common Issues
- **Forms not appearing:** Check AI response contains proper function calls
- **Memory not persisting:** Verify session_id is passed correctly
- **AI responses generic:** Check prompt configuration in `config/prompt.py`
- **Styling issues:** Verify CSS file paths and syntax

### Getting Help
- Check the comprehensive documentation in each folder's README
- Review the system overview in `AGENT_FLOW.md`
- Examine the code examples and data flow diagrams

## 📈 What Makes This Special

This system transforms the traditional chatbot experience into an intelligent, form-driven conversation that feels natural while gathering all necessary information for accurate tire recommendations. The "living form" concept creates a professional, engaging experience that builds trust and provides exceptional user satisfaction.

---

*Built with ❤️ using LangChain for reliable AI interactions and modern web technologies for a professional user experience.*