import re
import logging
from typing import List, Tuple, Optional, Dict, Any
from agents.form_builder import FormBuilder

logger = logging.getLogger(__name__)

class FunctionCallParser:
    """
    Parser that extracts function calls from AI responses and executes them.
    This replaces the unreliable FORM_FIELDS parsing with direct function execution.
    """
    
    def __init__(self):
        self.form_builder = FormBuilder()
    
    def parse_function_calls(self, ai_response: str) -> Tuple[str, Optional[str]]:
        """
        Parse function calls from AI response and return conversation text and form HTML.
        
        Returns:
            Tuple of (conversation_text, form_html)
        """
        # Reset the form builder for this response
        self.form_builder.reset_field_count()
        
        # Extract function calls using regex
        function_calls = self._extract_function_calls(ai_response)
        
        if not function_calls:
            # No function calls found, return just the conversation text
            return ai_response.strip(), None
        
        # Execute function calls to generate form fields
        form_fields = []
        for func_name, args_str in function_calls:
            try:
                field_html = self.form_builder.call_function(func_name, args_str)
                form_fields.append(field_html)
                logger.info(f"Successfully executed function call: {func_name}({args_str[:100]}...)")
            except Exception as e:
                logger.error(f"Error executing function call {func_name}({args_str}): {str(e)}")
                # Continue with other function calls even if one fails
        
        # Extract conversation text (everything before the first function call)
        conversation_text = self._extract_conversation_text(ai_response, function_calls)
        
        # Generate complete form if we have fields
        if form_fields:
            form_html = self.form_builder.create_complete_form(form_fields, conversation_text)
            return conversation_text, form_html  # Return conversation text AND form HTML
        else:
            # Safety fallback: If no form fields were generated but AI tried to create a form,
            # create a simple form with just the additional thoughts field
            if '[FUNCTION_CALL]' in ai_response:
                logger.warning("AI attempted to create form but no fields were generated. Creating safety fallback form.")
                fallback_field = self.form_builder.create_textarea_field(
                    name="additional_notes",
                    label="Additional Thoughts: (Optional)",
                    required=False,
                    placeholder="Ask a question, add details, or tell me anything..."
                )
                form_html = self.form_builder.create_complete_form([fallback_field], conversation_text)
                return conversation_text, form_html
            else:
                return conversation_text, None
    
    def _extract_function_calls(self, ai_response: str) -> List[Tuple[str, str]]:
        """
        Extract function calls from AI response.
        Handles:
        - [FUNCTION_CALL] function_name(...)
        - function_name(...) in code blocks or plain text
        - function_name param1="value" param2="value" (without parentheses)
        """
        import re
        function_calls = []
        
        # Debug logging
        logger.info(f"Extracting function calls from AI response: {ai_response[:500]}...")
        
        # 1. Extract [FUNCTION_CALL] markers (with parentheses)
        call_markers = list(re.finditer(r'\[FUNCTION_CALL\]', ai_response, re.IGNORECASE))
        for marker in call_markers:
            after_marker = ai_response[marker.end():].strip()
            func_match = re.match(r'(\w+)\s*\((.*)\)', after_marker)
            if func_match:
                func_name = func_match.group(1)
                args_str = func_match.group(2)
                function_calls.append((func_name, args_str))
                logger.info(f"Found [FUNCTION_CALL]: {func_name}({args_str[:100]}...)")
            else:
                logger.warning(f"Found [FUNCTION_CALL] marker but couldn't parse function: {after_marker[:100]}...")
        
        # 2. Extract function calls with parentheses from code blocks and plain text
        valid_functions = self.get_available_functions()
        code_block_pattern = r'(?:```[a-zA-Z]*\n)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)(?:\n```)?'
        for match in re.finditer(code_block_pattern, ai_response):
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Only include if it's a valid function name
            if func_name in valid_functions:
                # Avoid duplicates
                if (func_name, args_str) not in function_calls:
                    function_calls.append((func_name, args_str))
                    logger.info(f"Found function call with parentheses: {func_name}({args_str[:100]}...)")
            else:
                logger.debug(f"Ignoring invalid function call: {func_name}({args_str[:50]}...)")
        
        # 3. Extract function calls WITHOUT parentheses (new flexible format)
        # Look for patterns like: [function_name param1="value" param2="value"]
        # This handles multi-line function calls
        bracket_pattern = r'\[([a-zA-Z_][a-zA-Z0-9_]*)\s*([^\]]*)\]'
        for match in re.finditer(bracket_pattern, ai_response):
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Only include if it's a valid function name
            if func_name in valid_functions:
                # Avoid duplicates
                if (func_name, args_str) not in function_calls:
                    function_calls.append((func_name, args_str))
                    logger.info(f"Found function call without parentheses: {func_name} {args_str[:100]}...")
            else:
                logger.debug(f"Ignoring invalid function call: {func_name} {args_str[:50]}...")
        
        # 4. Extract function calls with incomplete brackets (handle truncated AI output)
        # Look for patterns like: [function_name ...] where the closing bracket might be missing
        incomplete_pattern = r'\[([a-zA-Z_][a-zA-Z0-9_]*)\s*([^\]]*?)(?=\n\s*\[|\n\s*$|$)'
        for match in re.finditer(incomplete_pattern, ai_response):
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Only include if it's a valid function name and we haven't already found it
            if func_name in valid_functions and (func_name, args_str) not in function_calls:
                function_calls.append((func_name, args_str))
                logger.info(f"Found incomplete function call: {func_name} {args_str[:100]}...")
        
        logger.info(f"Total function calls found: {len(function_calls)}")
        return function_calls
    
    def _extract_conversation_text(self, ai_response: str, function_calls: List[Tuple[str, str]]) -> str:
        """
        Extract conversation text from AI response, removing function calls.
        """
        if not function_calls:
            return ai_response.strip()
        
        # Find the position of the first function call (any format)
        # Look for [FUNCTION_CALL], [function_name(...)], or [function_name ...]
        first_call_patterns = [
            r'\[FUNCTION_CALL\]',  # [FUNCTION_CALL] format
            r'\[[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\]',  # [function_name(...)] format
            r'\[[a-zA-Z_][a-zA-Z0-9_]*\s+[^\]]+\]'  # [function_name ...] format
        ]
        
        first_match = None
        for pattern in first_call_patterns:
            match = re.search(pattern, ai_response, re.IGNORECASE)
            if match and (first_match is None or match.start() < first_match.start()):
                first_match = match
        
        if first_match:
            # Extract text before the first function call
            conversation_text = ai_response[:first_match.start()].strip()
            
            # Debug: Log the extracted conversation text
            logger.info(f"Extracted conversation text: '{conversation_text}'")
            
            # Clean up any leading/trailing quotes
            conversation_text = conversation_text.strip('"\'')
            
            return conversation_text
        
        return ai_response.strip()
    
    def get_available_functions(self) -> List[str]:
        """Get list of available form builder functions for the AI prompt"""
        return [
            "create_text_field",
            "create_textarea_field", 
            "create_select_field",
            "create_radio_field",
            "create_checkbox_field",
            "create_number_field",
            "create_year_field",
            "create_budget_range_field",
            "create_mileage_range_field"
        ]
    
    def get_function_documentation(self) -> str:
        """Get documentation for all available functions for the AI prompt"""
        return """
Available form builder functions:

create_text_field(name, label, required=False, placeholder=None, help_text=None)
- Creates a single-line text input field

create_textarea_field(name, label, required=False, placeholder=None, rows=3, help_text=None)
- Creates a multi-line textarea field

create_select_field(name, label, options, required=False, help_text=None)
- Creates a dropdown select field with options

create_radio_field(name, label, options, required=False, help_text=None)
- Creates a radio button group

create_checkbox_field(name, label, options, required=False, help_text=None)
- Creates a checkbox group

create_number_field(name, label, required=False, min_value=None, max_value=None, help_text=None)
- Creates a number input field

create_year_field(name, label, required=False, help_text=None)
- Creates a year input field (1900-2030)

create_budget_range_field(name, label, required=False, help_text=None)
- Creates a budget range field with min/max inputs

create_mileage_range_field(name, label, required=False, help_text=None)
- Creates a mileage range field with min/max inputs

Usage formats:
- [FUNCTION_CALL] function_name(name="value", label="Label", required=True)
- [function_name(name="value", label="Label", required=True)]
- [function_name name="value" label="Label" required=True]

IMPORTANT: For radio fields, checkbox fields, and select fields, you MUST always include the options parameter:
- create_radio_field(name="choice", label="Make a choice", options=["Option 1", "Option 2", "Option 3"], required=True)
- create_checkbox_field(name="selections", label="Select all that apply", options=["Choice A", "Choice B", "Choice C"], required=False)
- create_select_field(name="dropdown", label="Choose an option", options=["First", "Second", "Third"], required=True)
""" 