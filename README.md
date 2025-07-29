# Living Form Tire Sales Agent

An AI-powered conversational system that guides users through tire recommendations using dynamically generated forms and intelligent research capabilities.

## Project Structure Overview

### Root Level Files
- **`main.py`** - FastAPI application entry point with RESTful endpoints for chat processing, session management, and health monitoring
- **`requirements.txt`** - Python dependencies including FastAPI, LangChain, and AI model libraries
- **`Dockerfile`** - Container configuration for easy deployment
- **`.dockerignore`** - Files to exclude from Docker builds
- **`.gitignore`** - Git ignore patterns for Python projects
- **`WORKFLOW_AND_FRAMEWORK.md`** - Comprehensive documentation of the system architecture and workflow

### Core Components (`core/`)
- **`tire_graph.py`** - LangGraph workflow implementation with 4-stage tire recommendation process
- **`graph_coordinator.py`** - Main coordinator that manages the LangGraph workflow and AI interactions
- **`form_builder.py`** - Dynamic HTML form generator that creates forms with embedded fields
- **`ai_client.py`** - Multi-model AI client supporting OpenAI and Anthropic with fallback logic
- **`tire_tools.py`** - Web search tools for vehicle specs, tire sizes, reviews, and weather conditions
- **`memory_manager.py`** - Conversation history and session management using LangChain memory
- **`output_parser.py`** - Parsing utilities for AI responses and form data extraction

### Configuration (`config/`)
- **`graph_prompts.py`** - Centralized prompts for the LangGraph workflow stages
- **`prompt.py`** - General system prompts and AI agent configurations

### Web Interface (`web/`)
- **`chat.html`** - Main chat interface with real-time form generation
- **`app.js`** - Frontend JavaScript for form handling and UI updates
- **`styles.css`** - Modern, responsive styling for the chat interface

### Examples (`examples/`)
- Currently empty directory for example usage and demonstrations

### Virtual Environment (`.venv/`)
- Isolated Python environment for dependency management

## Quick Start

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Set Environment Variables**: Add your OpenAI and/or Anthropic API keys
3. **Run the Application**: `uvicorn main:app --host localhost --port 8000 --reload`
4. **Access the Interface**: Open `http://localhost:8000` in your browser

## Key Features

- **Living Form Concept**: Dynamic form generation with embedded fields in conversational text
- **Intelligent Research**: Proactive web search for vehicle specs and tire information
- **Multi-Model AI**: Support for both Claude Sonnet 3.5 and O4-mini with automatic fallback
- **LangGraph Workflow**: 4-stage process for comprehensive tire recommendations
- **Session Management**: Conversation continuity and context preservation
- **Responsive Design**: Mobile-friendly interface with modern styling

## Architecture

The system uses a LangGraph workflow with the following stages:
1. **Information Analysis** - Determine what information is needed
2. **Research Planning** - Create strategic research plan
3. **Research Execution** - Gather information using web search tools
4. **Response Synthesis** - Generate conversational response with forms

For detailed architecture and workflow information, see `WORKFLOW_AND_FRAMEWORK.md`.