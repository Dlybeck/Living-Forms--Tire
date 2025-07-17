# Agent Implementation Plan for Living Form Tire Sales Assistant

## Current Problem
- AI generates malformed FORM_FIELDS format
- Parsing is unreliable and error-prone
- System is working "backwards" - trying to parse AI output instead of using structured tools

## Goal
Create a reliable, agent-based system where:
1. AI focuses on conversation and reasoning
2. Tools handle form generation consistently
3. No more parsing errors or malformed output

## Implementation Options

### Option 1: Simple Function-Based Approach (RECOMMENDED)
**Pros:**
- No external dependencies beyond what we already have
- Simple, reliable, and fast
- Easy to debug and maintain
- No version conflicts

**Implementation:**
```python
# Define form builder functions
def create_text_field(name, label, required=False, placeholder=None):
    return f'<input type="text" name="{name}" placeholder="{placeholder}">'

def create_select_field(name, label, options, required=False):
    # Generate select HTML
    pass

# In the AI prompt, tell it to use these functions
# AI calls: create_text_field("make", "Vehicle Make", True, "e.g., Honda")
```

**How it works:**
1. AI generates conversation + function calls
2. We execute the function calls to generate forms
3. No parsing needed - just function execution

### Option 2: OpenAI Function Calling (LIGHTWEIGHT)
**Pros:**
- Uses OpenAI's built-in function calling
- No additional dependencies
- Reliable and well-tested

**Implementation:**
```python
# Define functions for OpenAI
functions = [
    {
        "name": "create_text_field",
        "description": "Create a text input field",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "label": {"type": "string"},
                "required": {"type": "boolean"},
                "placeholder": {"type": "string"}
            }
        }
    }
]
```

### Option 3: LangChain Agent (HEAVY)
**Pros:**
- Full agent framework
- Many built-in tools
- Good for complex workflows

**Cons:**
- Heavy dependencies
- Version conflicts
- Overkill for our needs
- Slower startup

## Recommended Approach: Option 1 (Simple Function-Based)

### Step 1: Create Form Builder Functions
```python
class FormBuilder:
    def create_text_field(self, name, label, required=False, placeholder=None):
        # Generate HTML for text field
        
    def create_select_field(self, name, label, options, required=False):
        # Generate HTML for select field
        
    def create_radio_field(self, name, label, options, required=False):
        # Generate HTML for radio buttons
        
    def create_checkbox_field(self, name, label, options, required=False):
        # Generate HTML for checkboxes
        
    def create_number_field(self, name, label, min_value=None, max_value=None):
        # Generate HTML for number field
        
    def create_textarea_field(self, name, label, rows=3):
        # Generate HTML for textarea
```

### Step 2: Update AI Prompt
```
You are a tire sales assistant. When you need to collect information, use these functions:

create_text_field(name, label, required=False, placeholder=None)
create_select_field(name, label, options, required=False)
create_radio_field(name, label, options, required=False)
create_checkbox_field(name, label, options, required=False)
create_number_field(name, label, min_value=None, max_value=None)
create_textarea_field(name, label, rows=3)

Example:
User: "I need tires for my Honda"
You: "Great! I can help you find the perfect tires for your Honda. Let me get some information about your vehicle.

[FUNCTION_CALL] create_text_field("model", "Vehicle Model", True, "e.g., Accord, Civic, CR-V")
[FUNCTION_CALL] create_number_field("year", "Vehicle Year", 1900, 2030)
[FUNCTION_CALL] create_select_field("quantity", "Number of Tires", ["1", "2", "4"], True)

Please fill out this information so I can recommend the best tires for you."
```

### Step 3: Parse Function Calls
```python
def parse_function_calls(ai_response):
    """Extract function calls from AI response"""
    import re
    pattern = r'\[FUNCTION_CALL\] (\w+)\((.*?)\)'
    matches = re.findall(pattern, ai_response)
    
    forms = []
    for func_name, args in matches:
        # Parse arguments and call the function
        form_html = form_builder.call_function(func_name, args)
        forms.append(form_html)
    
    return forms
```

### Step 4: Integration
```python
async def process_message(user_message, conversation_state):
    # 1. Generate AI response with function calls
    ai_response = await ai_client.generate_response(
        user_message, 
        conversation_state,
        include_function_calls=True
    )
    
    # 2. Extract conversation text
    conversation_text = extract_conversation_text(ai_response)
    
    # 3. Parse and execute function calls
    form_html = parse_function_calls(ai_response)
    
    # 4. Return integrated response
    return {
        "response": conversation_text,
        "form_html": form_html
    }
```

## Benefits of This Approach

1. **No Dependencies**: Uses only what we already have
2. **Reliable**: No parsing of malformed text
3. **Fast**: Direct function calls
4. **Debuggable**: Easy to see what's happening
5. **Maintainable**: Simple code structure
6. **Flexible**: Easy to add new field types

## Migration Steps

1. **Create FormBuilder class** with all field types
2. **Update AI prompt** to use function calls
3. **Add function call parsing** to orchestrator
4. **Test with simple scenarios**
5. **Add more complex field types** as needed
6. **Remove old FORM_FIELDS parsing code**

## Success Criteria

- [ ] No more malformed form errors
- [ ] Consistent form generation
- [ ] AI remembers conversation context
- [ ] Fast response times
- [ ] Easy to add new field types
- [ ] No dependency conflicts

## Next Steps

1. Implement the FormBuilder class
2. Update the AI prompt
3. Add function call parsing
4. Test the approach
5. Migrate away from old system

This approach gives us all the benefits of an agent-based system without the complexity and dependency issues. 