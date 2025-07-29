# 🧠 Tire Sales Assistant - Simple Agent Flow

## 🎯 The Core Process

The Tire Sales Assistant uses a simple 2-step agent process:

### Step 1: AI Gets Context
The AI receives all the information it needs to understand the current situation:

```python
context = {
    'session_id': 'abc123',
    'conversation_history': [...],  # Previous messages
    'ai_notepad': 'Previous internal thoughts...',  # AI's memory
    'form_data': {'vehicle_make': 'Kia', 'vehicle_model': 'Forte'},  # User's latest input
    'current_step': 'vehicle_discovery'  # Where we are in the process
}
```

**What happens:**
- User submits a form or sends a message
- System builds this context object with everything the AI needs to know
- Context is sent to the AI model (O4-Mini or Claude)

### Step 2: AI Thinks and Responds
The AI processes the context and generates a response with two parts:

```python
# AI generates this structured response:
response = """
[INTERNAL_ANALYSIS]
User has a 2020 Kia Forte. Need to get the trim level to determine tire size.
They seem confident about their vehicle details. Should ask for trim next.

[CONVERSATION]
Great! I can see you have a 2020 Kia Forte. To find the perfect tires, I just need to know your trim level.
{create_text_field(name="vehicle_trim", label="What's your vehicle trim level?", placeholder="EX, LX, GT...")}
"""
```

**What happens:**
- AI analyzes the context and thinks through what to do next
- AI writes its internal thoughts in `[INTERNAL_ANALYSIS]`
- AI writes the user-facing response in `[CONVERSATION]`
- AI embeds form fields directly in the conversation text
- System parses the response and extracts the parts

## 🔄 That's It!

The entire agent process is just these two steps repeated:

1. **Get Context** → 2. **Think & Respond** → 1. **Get Context** → 2. **Think & Respond**...

Each cycle moves the conversation forward, gathering more information until the user has their tire recommendation.

## 📁 File Structure

```
Tires/
├── main.py                    # Receives user input, sends to coordinator
├── core/
│   ├── coordinator.py         # Step 1: Builds context, manages sessions
│   ├── tire_agent.py          # Step 2: Sends context to AI, parses response
│   ├── ai_client.py           # Talks to AI models (O4-Mini, Claude)
│   └── form_builder.py        # Converts AI form functions to HTML
├── config/
│   └── prompt.py              # Tells AI how to behave and think
└── web/
    ├── chat.html              # User interface
    ├── app.js                 # Sends user input to backend
    └── styles.css             # Makes it look good
```

## 🎯 The 4 Stages

The AI goes through 4 stages, but each stage uses the same 2-step process:

1. **Vehicle Discovery** - Get make, model, year, trim
2. **Preferences** - Get driving conditions, weather, priorities  
3. **Recommendations** - Suggest tires based on collected info
4. **Decision Support** - Answer questions, compare options

Each stage is just: **Get Context** → **Think & Respond** → Repeat until complete.

That's the entire agent system! Simple and effective. 