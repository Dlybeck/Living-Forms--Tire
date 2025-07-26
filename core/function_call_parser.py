import re
import logging
from typing import List, Tuple, Optional, Dict, Any
from .form_builder import FormBuilder

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
            logger.info("No function calls found in AI response")
            return ai_response.strip(), None
        
        # Execute function calls to generate form fields
        form_fields = []
        successful_calls = 0
        failed_calls = 0
        
        for func_name, args_str in function_calls:
            try:
                field_html = self.form_builder.call_function(func_name, args_str)
                if field_html:
                    form_fields.append(field_html)
                    successful_calls += 1
                    logger.info(f"Successfully executed function call: {func_name}({args_str[:100]}...)")
                else:
                    failed_calls += 1
                    logger.warning(f"Function call returned empty result: {func_name}({args_str[:100]}...)")
            except Exception as e:
                failed_calls += 1
                logger.error(f"Error executing function call {func_name}({args_str}): {str(e)}")
                # Continue with other function calls even if one fails
        
        # Log execution summary
        logger.info(f"Function call execution summary: {successful_calls} successful, {failed_calls} failed")
        
        # Extract conversation text (everything before the first function call)
        conversation_text = self._extract_conversation_text(ai_response, function_calls)
        
        # Generate complete form if we have fields
        if form_fields:
            logger.info(f"Generated {len(form_fields)} form fields")
            
            # Check if conversation text contains embedded function calls
            if re.search(r'\{[^}]+\}', conversation_text):
                # Use embedded form method
                form_html = self.form_builder.create_embedded_form(conversation_text)
                logger.debug("Using embedded form method")
            else:
                # Use traditional form method
                form_html = self.form_builder.create_complete_form(form_fields, conversation_text)
                logger.debug("Using traditional form method")
            
            return conversation_text, form_html
        else:
            logger.info("No form fields generated")
            # Safety fallback: If no form fields were generated but AI tried to create a form,
            # create a simple form with just the additional thoughts field
            if '[FUNCTION_CALL]' in ai_response or any(func in ai_response for func in ['create_text_field', 'create_select_field', 'create_checkbox_field']):
                logger.warning("AI attempted to create form but no fields were generated. Creating safety fallback form.")
                fallback_field = self.form_builder.create_textarea_field(
                    name="additional_notes",
                    label="Additional Thoughts: (Optional)",
                    required=False,
                    placeholder="Ask a question, add details, or tell me anything..."
                )
                form_html = self.form_builder.create_complete_form([fallback_field], conversation_text)
                print(f"Safety fallback form created")
                print(f"=== END NO FORM FIELDS ===\n")
                return conversation_text, form_html
            else:
                print(f"No fallback needed - AI didn't attempt to create a form")
                print(f"=== END NO FORM FIELDS ===\n")
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
        
        logger.debug(f"Extracting function calls from AI response: {len(ai_response)} characters")
        
        # 1. Extract [FUNCTION_CALL] markers (with parentheses)
        call_markers = list(re.finditer(r'\[FUNCTION_CALL\]', ai_response, re.IGNORECASE))
        for marker in call_markers:
            after_marker = ai_response[marker.end():].strip()
            func_match = re.match(r'(\w+)\s*\((.*)\)', after_marker)
            if func_match:
                func_name = func_match.group(1)
                args_str = func_match.group(2)
                function_calls.append((func_name, args_str))
                logger.debug(f"Found [FUNCTION_CALL]: {func_name}")
            else:
                logger.warning(f"Found [FUNCTION_CALL] marker but couldn't parse function")
        
        # 2. Extract function calls with parentheses from code blocks and plain text
        valid_functions = self.get_available_functions()
        
        # Improved regex to handle multi-line and complex function calls
        # This regex captures the entire function call including nested parentheses
        function_pattern = r'(\w+)\s*\(((?:[^()]*|\([^()]*\))*)\)'
        
        for match in re.finditer(function_pattern, ai_response, re.DOTALL):
            func_name = match.group(1)
            args_str = match.group(2).strip()
            
            # Only include if it's a valid function name
            if func_name in valid_functions:
                # Avoid duplicates
                if (func_name, args_str) not in function_calls:
                    function_calls.append((func_name, args_str))
                    logger.debug(f"Found function call: {func_name}")
        
        # 3. Extract function calls without parentheses (fallback)
        # This handles cases where the AI forgets parentheses
        for func_name in valid_functions:
            # Look for function calls without parentheses
            pattern = rf'{func_name}\s+([^)]+?)(?=\n|$|create_)'
            for match in re.finditer(pattern, ai_response):
                args_str = match.group(1).strip()
                # Only add if it looks like valid arguments
                if '=' in args_str and (func_name, args_str) not in function_calls:
                    function_calls.append((func_name, args_str))
                    logger.info(f"Found function call without parentheses: {func_name} {args_str[:100]}...")
        
        # Log results
        print(f"\n=== FUNCTION CALL PARSING RESULTS ===")
        print(f"Total function calls found: {len(function_calls)}")
        for i, (func_name, args_str) in enumerate(function_calls, 1):
            print(f"Function call {i}: {func_name}({args_str[:50]}...)")
        print(f"=== END FUNCTION CALL PARSING ===\n")
        
        return function_calls
    
    def _extract_conversation_text(self, ai_response: str, function_calls: List[Tuple[str, str]]) -> str:
        """
        Extract conversation text from AI response, removing function calls.
        """
        if not function_calls:
            return ai_response.strip()
        
        # Find the position of the first function call (any format)
        # Look for [FUNCTION_CALL], [function_name(...)], [function_name ...], or code blocks with function calls
        first_call_patterns = [
            r'\[FUNCTION_CALL\]',  # [FUNCTION_CALL] format
            r'\[[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\]',  # [function_name(...)] format
            r'\[[a-zA-Z_][a-zA-Z0-9_]*\s+[^\]]+\]',  # [function_name ...] format
            r'```[a-zA-Z]*\s*\n\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)',  # Code blocks with function calls
            r'```[a-zA-Z]*\s*\n\s*[a-zA-Z_][a-zA-Z0-9_]*\s+[^\n]*'  # Code blocks with function calls (no parentheses)
        ]
        
        first_match = None
        for pattern in first_call_patterns:
            match = re.search(pattern, ai_response, re.IGNORECASE | re.MULTILINE)
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
            "create_checkbox_field",
            "create_year_field"
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

create_checkbox_field(name, label, options, required=False, help_text=None)
- Creates a checkbox group

create_year_field(name, label, required=False, help_text=None)
- Creates a year input field with appropriate placeholder

Usage formats:
- function_name(name="value", label="Label", required=True)
- [function_name(name="value", label="Label", required=True)]

IMPORTANT: For checkbox fields and select fields, you MUST always include the options parameter:
- create_checkbox_field(name="selections", label="Select all that apply", options=["Choice A", "Choice B", "Choice C"], required=False)
- create_select_field(name="dropdown", label="Choose an option", options=["First", "Second", "Third"], required=True)
""" 