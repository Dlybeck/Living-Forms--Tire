# Living Form Tire Sales Assistant

A revolutionary AI-powered tire sales assistant that uses a "Living Form" approach to collect customer information and provide tire recommendations.

## What is a Living Form?

A Living Form is a conversational AI interface that seamlessly integrates form elements within natural conversation. Unlike traditional forms or chatbots, the AI generates responses that contain both conversational text AND embedded HTML form elements, creating a fluid, adaptive experience.

## System Overview

This tire sales assistant helps customers find the perfect tires by collecting all necessary information a tire seller needs through intelligent, conversational forms.

### Information Collected

The system gathers comprehensive tire purchasing information:

1. **Vehicle Information**: Make, model, year, trim level
2. **Tire Specifications**: Current size, needed size (look up or ask user) quantity needed (1, 2, 4 tires)
3. **Driving Patterns**: Daily mileage, highway vs city driving, seasonal needs
4. **Current Tire Status**: Condition, age, reason for replacement
5. **Special Considerations**: Performance needs, weather conditions, towing requirements

### How It Works

1. **Preset Welcome**: Users start with a friendly welcome form collecting basic vehicle info
2. **AI-Driven Conversation**: After initial submission, AI takes over with Living Form responses
3. **Adaptive Forms**: AI generates contextual forms based on user input and needs
4. **Natural Corrections**: AI gently corrects mistakes (like "Toyota Forte" → "Kia Forte")
5. **Flexible Collection**: Only collects information that's actually useful
6. **Always Available Help**: Every form includes a free-text area for questions

### Key Features

- **Conversational Intelligence**: AI understands context and adapts responses
- **Form History**: Previous forms remain visible but disabled after submission
- **Natural Error Handling**: Mistakes are corrected conversationally, not systematically
- **Cost Tracking**: Monitors AI usage costs in real-time
- **Responsive Design**: Works seamlessly on desktop and mobile

## Architecture

### Backend Components

- **FastAPI Server** (`main.py`): Main API server handling requests
- **Conversation Orchestrator** (`agents/conversation_orchestrator.py`): Manages conversation flow
- **AI Client** (`agents/ai_client.py`): Handles AI model interactions (Claude, GPT-4)
- **Cost Manager** (`agents/cost_manager.py`): Tracks and manages AI usage costs
- **Tire Database** (`database/tire_database.py`): Vehicle and tire information database
- **State Manager** (`utils/state_manager.py`): Manages conversation state

### Frontend

- **HTML/CSS/JavaScript** (`templates/chat.html`): Single-page application
- **Living Form Rendering**: Displays AI responses with embedded forms
- **Form Submission**: Handles form data and API communication
- **History Management**: Shows conversation flow with disabled previous forms

## API Endpoints

- `GET /`: Main chat interface
- `GET /welcome`: Preset welcome message with initial form
- `POST /chat`: Process user messages and form submissions
- `GET /session/{session_id}/cost`: Get session cost information

## Installation & Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd Tires
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```

5. **Run Server**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```

6. **Access Application**
   Open `http://localhost:8000` in your browser

## Usage Example

1. **Initial Welcome**: User sees friendly welcome form asking for basic vehicle info
2. **Form Submission**: User fills out year, make, model, tire count, and any notes
3. **AI Response**: AI processes input and responds with next contextual form
4. **Natural Corrections**: If user entered "Toyota Forte", AI gently corrects to "Kia Forte"
5. **Progressive Collection**: AI continues collecting tire-specific information
6. **Final Recommendations**: Once enough info is gathered, AI provides tire recommendations

## Configuration

### Cost Management
- Configurable budget limits per session
- Model selection based on query complexity
- Real-time cost tracking and alerts

### AI Models
- Claude 3.5 Sonnet (primary)
- GPT-4o (secondary)
- Automatic model selection based on cost and complexity

### Database
- Vehicle information with tire specifications
- Tire catalog with prices and characteristics
- Easily extensible JSON-based storage

## Development

### Adding New Vehicle Data
Edit `database/tire_data.json` to add new vehicles and tire specifications.

### Customizing AI Behavior
Modify prompts in `agents/ai_client.py` to adjust AI personality and collection strategy.

### Extending Form Fields
Update the information collection list in the AI prompt to gather additional data points.

## Key Principles

1. **Conversational First**: Everything feels like talking to a knowledgeable friend
2. **Adaptive Intelligence**: AI decides what information to collect and how
3. **Natural Error Handling**: Mistakes are corrected in conversation, not through rigid validation
4. **User-Centric**: Always includes help options and free-form input areas
5. **Cost Conscious**: Efficient AI usage with intelligent model selection

## Future Enhancements

- Integration with tire inventory systems
- Real-time pricing updates
- Customer account management
- Order processing and fulfillment
- Mobile app version
- Multi-language support

---

This Living Form approach revolutionizes how customers interact with sales systems, making tire shopping as easy as having a conversation with an expert friend. 