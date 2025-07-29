# Tire Recommendation Workflow Steps

## Overview

The tire recommendation system uses a **LangGraph workflow** with three specialized steps that work together to provide intelligent, research-driven tire recommendations. Each step has a focused responsibility and its own dedicated prompt.

## The Three-Step Process

### Step 1: Information Analysis (`analyze_information`)

**Purpose**: Determine what critical information is missing to advance the tire recommendation process.

**What it does**:
- Reviews the user's message, current form data, and conversation history
- Identifies the current workflow stage (1-4)
- Determines what specific information is missing for that stage
- Focuses only on the current stage (doesn't jump ahead)

**Input**:
- `user_message`: What the user just said
- `form_data`: Previously collected information
- `conversation_history`: Previous chat messages

**Output**:
- `current_stage`: Which stage the user is in (1-4)
- `missing_fields`: List of missing information like `["missing_vehicle_year", "missing_tire_size"]`

**Example Thinking**:
```
User: "I have a Kia"
Analysis: "They're in Stage 1 (Vehicle Discovery), missing year and model"
Output: {"current_stage": "1", "missing_fields": ["missing_vehicle_year", "missing_vehicle_model"]}
```

### Step 2: Research Planning (`plan_research`)

**Purpose**: Create a strategic plan for gathering missing information using available tools.

**What it does**:
- Takes the identified information gaps
- Maps them to available research tools
- Creates specific queries for each tool
- Prioritizes research actions (high/medium/low)
- Only plans research for information that can be found with existing data

**Input**:
- `information_gaps`: Missing fields from Step 1
- `available_tools`: List of research tools and descriptions

**Output**:
- `research_plan`: List of research actions with tool names, queries, and priorities

**Example Thinking**:
```
Gaps: ["missing_vehicle_year", "missing_vehicle_model", "missing_tire_size"]
Tools: tire_size_lookup, vehicle_specs_search
Plan: "Once I get year/model, I can look up tire size automatically"
Output: [{"gap": "missing_tire_size", "tool": "tire_size_lookup", "query": "Kia [year] [model] tire size", "priority": "high"}]
```

### Step 3: Response Synthesis (`synthesize_response`)

**Purpose**: Create the final conversational response with research findings and embedded form fields.

**What it does**:
- Combines user input, form data, research results, and conversation history
- Generates a warm, conversational response
- Embeds dynamic form fields where needed
- Aims to gather related information efficiently
- Adapts to user confusion by asking one question at a time if needed

**Input**:
- `user_message`: What the user just said
- `form_data`: Previously collected information
- `research_results`: Data found by research tools
- `conversation_history`: Previous chat messages
- `current_stage`: Which stage the user is in (1-4)
- `missing_fields`: What information is still needed
- `function_docs`: Form field creation functions

**Output**:
- `final_response`: Natural conversation with embedded form fields
- `form_html`: Generated HTML form for user input

**Example Thinking**:
```
Stage: 1 (Vehicle Discovery)
Missing: ["missing_vehicle_year", "missing_vehicle_model"]
Research: Found tire size options for Kia models
Response: "Great! I can help you find the perfect tires for your Kia. To get started, I'll need to know the year and model. I can then look up the exact tire size for you."
Form Fields: Year and model input fields
```

## Workflow Stages

The system operates through four distinct stages, each with specific requirements and considerations:

### Stage 1: Vehicle & Tire Specification Discovery
**Purpose**: Gather essential vehicle details (Make, Model, Year, Trim) and precise tire size.

**Why This Stage is Critical**: Tire compatibility depends on exact vehicle specifications. Even small differences in trim levels can affect tire size requirements. For example, a 2020 Kia Forte LX might use 205/55R16 tires while the EX trim uses 225/45R17 tires.

**What the System Should Do**: Proactively research vehicle specs and standard tire sizes rather than relying solely on user knowledge. Many users don't know their tire size or where to find it, so the system should look up this information when possible.

**Common Challenges**: Users often don't know their trim level or tire size, and may confuse similar model names (e.g., Forte vs. Forte5).

### Stage 2: Driving Preferences & Usage Understanding
**Purpose**: Elicit information about driving habits, typical conditions, and specific preferences (performance, longevity, budget).

**Why This Stage Matters**: This determines tire type selection (all-season, summer, winter, performance) and helps balance competing priorities like cost vs. performance vs. longevity. A highway commuter needs different tires than someone who drives in snow regularly.

**What's Essential**: Understanding driving conditions (highway vs. city, weather patterns, load requirements) is essential for appropriate recommendations. The system should research local weather patterns and driving conditions when relevant.

**Common Trade-offs**: Users often want "the best" but have budget constraints, or want longevity but also performance. The system needs to explain these trade-offs clearly.

### Stage 3: Tire Recommendation Generation
**Purpose**: Utilize gathered data to propose suitable tire options.

**What This Stage Requires**: Synthesizing vehicle compatibility, user preferences, and market availability. The system must ensure recommended tires actually fit the vehicle and are available.

**What the System Should Do**: Present multiple options with clear trade-offs and explain why each recommendation fits the user's specific situation. Research results should inform both the options presented and the explanations given.

**Key Considerations**: Price, performance ratings, warranty, availability, and installation requirements all factor into recommendations.

### Stage 4: Decision Support & Refinement
**Purpose**: Assist the user in finalizing their choice, addressing any further questions or needs.

**What This Stage Involves**: Handling objections, clarifying technical details, and providing additional information that might influence the final decision. Users often have concerns about installation, warranty, or performance characteristics.

**What the System Should Be Prepared For**: Researching specific tire models, comparing alternatives, or addressing concerns about installation, warranty, or performance characteristics. Users might ask about installation costs, warranty terms, or how the tires will perform in specific conditions.

**Common User Concerns**: Installation complexity, warranty coverage, performance in specific weather conditions, and cost comparisons between options.

## Key Features

### Research-Driven Approach
- Uses specialized tools to find information proactively
- Minimizes the burden on users by looking up data when possible
- Tools include: tire size lookup, vehicle specs search, tire reviews, weather conditions, VIN decoder

### Living Form Interface
- Responses are conversational but include embedded form fields
- Form fields are dynamically generated based on what information is needed
- Users can input information naturally within the conversation

### Stage-Aware Processing
- Each step understands what stage the user is in
- Questions and responses are appropriate for the current stage
- System doesn't jump ahead or ask for irrelevant information

### Memory and Context
- Maintains conversation history across interactions
- Remembers previously provided information
- Builds context over multiple interactions

## Data Flow

```
User Input → ANALYSIS → Missing Gaps + Current Stage
Missing Gaps → PLANNING → Research Plan
Research Plan → Tools → Research Results
User Input + Form Data + Research Results + Stage Info → SYNTHESIS → Final Response
```

## Benefits of This Approach

1. **Focused Responsibility**: Each step has a single, clear purpose
2. **Consistency**: Stage information flows through all steps
3. **Efficiency**: Research tools reduce user burden
4. **Flexibility**: Can adapt to user confusion or uncertainty
5. **Maintainability**: Each step can be refined independently
6. **Debugging**: Easy to identify which step needs improvement

## Example Interaction Flow

1. **User**: "I need new tires for my car"
2. **Analysis**: "Stage 1, missing vehicle details"
3. **Planning**: "No research needed yet"
4. **Synthesis**: "I'd be happy to help you find the perfect tires! To get started, I'll need some basic information about your vehicle."

5. **User**: "I have a Kia"
6. **Analysis**: "Stage 1, missing year and model"
7. **Planning**: "Plan to research tire size once I have year/model"
8. **Synthesis**: "Great! I can help you find the perfect tires for your Kia. What year and model is it? Once I know that, I can look up the exact tire size for you."

This workflow ensures that the system is both intelligent and user-friendly, providing a smooth experience while gathering all necessary information for accurate tire recommendations. 