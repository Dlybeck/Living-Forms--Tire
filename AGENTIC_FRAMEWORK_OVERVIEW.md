# Agentic Framework Overview

## Introduction
This document describes the **agentic (double-agent/two-model) framework** used in the Living Form Tire Sales Assistant. It covers the architecture, agent roles, model usage, data flow, and design philosophy, so you can recreate or extend the system as needed.

---

## 1. **Core Principles**
- **Separation of Reasoning and Formatting:**
  - Use a powerful "reasoning" model for planning, context, and conversation logic (hidden from the user).
  - Use a separate "formatting" model for all user-facing output (chat + form), leveraging the reasoning model's output as context.
- **Agent Specialization:**
  - Each step in the roadmap is handled by a specialized agent with a clear, concrete purpose.
- **Living Form Experience:**
  - The system adapts to user responses, always presents actionable forms, and never gets stuck.

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
   - Calls `_generate_reasoning_response` (large model, hidden).
   - Calls `_generate_form_and_chat_response` (mini model, user-facing), passing the large model's output as context.
   - Returns only the mini model's output to the user.
5. **FunctionCallParser** extracts and renders form fields from the mini model's output (supports flexible formats: `[FUNCTION_CALL]`, code blocks, or plain text).
6. **Frontend** displays the chat and form to the user.

---

## 4. **Model Selection**
- **Large Model:**
  - Typically GPT-4o or GPT-4o-mini (for best reasoning and context handling).
- **Mini Model:**
  - Can be GPT-4o-mini, GPT-4.1-mini, or even full GPT-4o, depending on reliability and cost.
  - Should be chosen for its ability to follow formatting instructions and generate both chat and form fields.

---

## 5. **Prompting Philosophy**
- **Large Model Prompt:**
  - Focuses on reasoning, planning, and context.
  - Output is for the mini model, not the user.
- **Mini Model Prompt:**
  - Instructs the model to generate both a friendly chat message and actionable form fields.
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
  - Update the mini model prompt and the function call parser as needed.

---

## 7. **Debugging and Best Practices**
- Always log or print the raw output from both models for debugging.
- If forms stop rendering, check the mini model's output format and the parser.
- Use strict prompting and flexible parsing for best results.
- Never show the large model's output to the user (except in debug mode).

---

## 8. **Summary Table**

| Step                | Agent                | Large Model (Reasoning) | Mini Model (Formatting) | Output to User |
|---------------------|----------------------|-------------------------|------------------------|----------------|
| Tire Size Discovery | TireSizeAgent        | GPT-4o / 4o-mini        | GPT-4o-mini / 4.1-mini | Mini only      |
| Driving Info        | DrivingInfoAgent     | GPT-4o / 4o-mini        | GPT-4o-mini / 4.1-mini | Mini only      |
| Preferences         | PreferencesAgent     | GPT-4o / 4o-mini        | GPT-4o-mini / 4.1-mini | Mini only      |
| Recommendations     | RecommendationAgent  | GPT-4o / 4o-mini        | GPT-4o-mini / 4.1-mini | Mini only      |

---

## 9. **Design Philosophy**
- **Agentic:** Each step is handled by a specialized agent for modularity and clarity.
- **Double-Agent:** Two models per step: one for reasoning, one for formatting.
- **Living Form:** The system adapts, never gets stuck, and always presents actionable forms.
- **Separation of Concerns:** Reasoning and formatting are handled by different models for maximum flexibility and reliability.

---

## 10. **Recreating the Framework**
- Follow the architecture and data flow above.
- Use strict prompting for the mini model and flexible parsing.
- Always keep the large model’s output hidden from the user.
- Modularize each step as its own agent for easy extension.

---

**This framework is designed for maximum flexibility, reliability, and a truly “living” form experience.** 