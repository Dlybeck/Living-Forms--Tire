# Agentic Framework Overview

## Introduction
This document describes the **agentic framework** used in the Living Form Tire Sales Assistant. It covers the architecture, agent roles, model usage, data flow, and design philosophy, so you can recreate or extend the system as needed.

---

## 1. **Core Principles**
- **Single Model Per Goal:**
  - Each conversation goal is handled by a specialized agent with a single thinking model
  - The model generates both conversation text and form fields in one response
  - No complex double-model coordination needed
- **Agent Specialization:**
  - Each step in the roadmap is handled by a specialized agent with a clear, concrete purpose
- **Living Form Experience:**
  - The system adapts to user responses, always presents actionable forms, and never gets stuck

---

## 2. **Architecture Overview**

### **A. Roadmap & State**
- The conversation is managed by a `ConversationRoadmap` object, which tracks:
  - The current step (e.g., greeting, tire size discovery, etc.)
  - Shared data (vehicle info, tire specs, driving patterns, etc.)
  - Conversation history

### **B. Agent Coordinator**
- The `AgentCoordinator` delegates each user message to the appropriate specialized agent based on the current roadmap step.

### **C. Specialized Agents (Explicit List)**

#### 1. **TireSizeAgent**
- **Purpose:**
  - Handles the discovery and collection of the user's tire size.
  - Guides the user through providing their tire size directly, or helps them find it using vehicle make/model/year, VIN, documents, or creative alternatives.
  - Uses web search and reasoning to suggest the best method for the user's situation.

#### 2. **DrivingInfoAgent**
- **Purpose:**
  - Collects detailed information about the user's driving patterns and habits.
  - Asks about commute distance, driving frequency, city vs. highway use, driving style, environmental conditions (weather, road types), and any current tire issues.
  - This information is used to recommend tires that match the user's real-world needs.

#### 3. **PreferencesAgent**
- **Purpose:**
  - Gathers the user's budget, performance priorities, brand preferences, and any special requirements.
  - Asks about budget range, desired balance of comfort/handling/longevity, brand loyalty, installation/service preferences, and any unique needs (e.g., all-season, winter, noise sensitivity).
  - Ensures recommendations are tailored to what matters most to the user.

#### 4. **RecommendationAgent**
- **Purpose:**
  - Analyzes all collected data (vehicle, tire size, driving info, preferences) to generate personalized tire recommendations.
  - Explains the reasoning behind each recommendation, compares options, and helps the user make a final selection.
  - Can collect feedback on recommendations, answer follow-up questions, and guide the user through the final decision.

---

## 3. **Data Flow**

1. **User submits a message or form.**
2. **AgentCoordinator** selects the appropriate agent for the current roadmap step.
3. **Specialized Agent**:
   - Optionally extracts info from the message and updates the roadmap.
   - Advances the roadmap if needed.
   - Calls `BaseAgent.process_message(...)`.
4. **BaseAgent.process_message**:
   - Calls `_generate_conversation_and_form` (single model).
   - Parses the response to extract conversation text and form HTML.
   - Returns the combined response to the user.
5. **FunctionCallParser** extracts and renders form fields from the model's output.
6. **Frontend** displays the chat and form to the user.

---

## 4. **Model Selection**
- **Primary Model:**
  - GPT-4o-mini (for best reasoning and form generation capability).
- **Fallback Models:**
  - GPT-4.1-mini (if budget constraints apply)
  - Claude 3.5 Sonnet (if OpenAI models fail)

---

## 5. **Prompting Philosophy**
- **Single Model Prompt:**
  - Focuses on both reasoning and form generation.
  - Output is directly for the user.
  - Requires function calls to be output in a flexible, parser-friendly format (e.g., `[FUNCTION_CALL] create_radio_field(...)`).
  - Chat and form must be clearly separated (e.g., with a divider like `---`).
  - No code blocks, bullets, or markdown for function calls unless parser supports it.

---

## 6. **Extending or Recreating the Framework**
- **To add a new step:**
  1. Create a new specialized agent inheriting from `BaseAgent`.
  2. Implement any step-specific extraction or roadmap advancement logic.
  3. Ensure `process_message` calls `super().process_message(...)`.
  4. Add the agent to the roadmap and coordinator.
- **To change models:**
  - Update the model type in the agent or base agent logic.
- **To change output format:**
  - Update the model prompt and the function call parser as needed.

---

## 7. **Debugging and Best Practices**
- Always log or print the raw output from the model for debugging.
- If forms stop rendering, check the model's output format and the parser.
- Use strict prompting and flexible parsing for best results.
- The model's output is shown directly to the user.

---

## 8. **Summary Table**

| Step                | Agent                | Model                | Output to User |
|---------------------|----------------------|----------------------|----------------|
| Tire Size Discovery | TireSizeAgent        | GPT-4o-mini          | Single model   |
| Driving Info        | DrivingInfoAgent     | GPT-4o-mini          | Single model   |
| Preferences         | PreferencesAgent     | GPT-4o-mini          | Single model   |
| Recommendations     | RecommendationAgent  | GPT-4o-mini          | Single model   |

---

## 9. **Design Philosophy**
- **Agentic:** Each step is handled by a specialized agent for modularity and clarity.
- **Single Model:** One model per step handles both reasoning and form generation.
- **Living Form:** The system adapts, never gets stuck, and always presents actionable forms.
- **Simplified:** No complex double-model coordination, just clean single-model responses.

---

## 10. **Recreating the Framework**
- Follow the architecture and data flow above.
- Use strict prompting for the model and flexible parsing.
- Always ensure the model generates both conversation and forms.
- Modularize each step as its own agent for easy extension.

---

**This framework is designed for maximum simplicity, reliability, and a truly "living" form experience.** 