"""
Form Builder
Generates HTML form fields with clean, maintainable code
"""

from typing import List, Optional, Dict, Any
import logging
import re
import ast

logger = logging.getLogger(__name__)

class FormBuilder:
    """
    Form builder that generates HTML form fields
    """
    
    def __init__(self):
        self.field_count = 0
    
    def create_embedded_form(self, conversation_with_fields: str, submit_text: str = "Continue") -> str:
        """
        Create a form with conversation text and form fields embedded within it
        
        Args:
            conversation_with_fields: Text containing embedded function calls like {create_text_field(...)}
            submit_text: Text for the submit button
            
        Returns:
            Complete HTML form with embedded fields
        """
        # Add the additional notes field that's always included
        additional_notes = self._create_additional_notes_field()
        
        # Process the conversation text, replacing function calls with HTML fields
        processed_content = self._process_function_calls(conversation_with_fields)
        
        # Format the final HTML form
        return self._build_form_html(processed_content, additional_notes, submit_text)
    
    def _create_additional_notes_field(self) -> str:
        """Create the standard additional notes field"""
        return self._create_field_html(
            field_type="textarea_field",
            name="additional_notes",
            label="Additional Thoughts (Optional)",
            required=False,
            placeholder="Ask a question, add details, or tell me anything...",
            rows=3
        )
    
    def _process_function_calls(self, text: str) -> str:
        """
        Process conversation text and replace function calls with HTML fields
        
        Args:
            text: Conversation text containing function calls
            
        Returns:
            Text with function calls replaced by HTML fields
        """
        processed_text = text
        
        # Find all function calls in the text
        for match in re.finditer(r'\{create_\w+\([^}]*\)\}', text, re.DOTALL):
            function_call = match.group(0)
            try:
                field_html = self._parse_and_create_field(function_call)
                processed_text = processed_text.replace(function_call, field_html)
            except Exception as e:
                logger.error(f"Error processing function call {function_call}: {str(e)}")
                error_html = f'<span style="color:red;">Error: {function_call}</span>'
                processed_text = processed_text.replace(function_call, error_html)
        
        # Clean up text formatting
        return processed_text.replace('\n', '<br>')
    
    def _parse_and_create_field(self, function_call: str) -> str:
        """
        Parse a function call and create the corresponding HTML field
        
        Args:
            function_call: Function call string like {create_text_field(...)}
            
        Returns:
            HTML for the form field
        """
        # Extract function name and arguments
        match = re.match(r'create_(\w+)\((.*)\)', function_call[1:-1], re.DOTALL)
        if not match:
            raise ValueError(f"Invalid function call format: {function_call}")
        
        field_type = match.group(1)
        args_str = match.group(2)
        
        # Parse the arguments
        args = self._parse_arguments(args_str)
        
        # Map function names to field types
        field_type_mapping = {
            'text_field': 'text_field',
            'textarea_field': 'textarea_field', 
            'select_field': 'select_field',
            'checkbox_field': 'checkbox_field',
            'year_field': 'year_field'
        }
        
        # Use mapped field type or fallback to original
        mapped_type = field_type_mapping.get(field_type, field_type)
        
        # Create the field HTML
        return self._create_field_html(field_type=mapped_type, **args)
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """
        Parse function arguments from string
        
        Args:
            args_str: Arguments string like 'name="field", label="Field Label"'
            
        Returns:
            Dictionary of parsed arguments
        """
        args = {}
        
        # Handle options list specially (most complex to parse)
        options_match = re.search(r'options\s*=\s*(\[[^\]]*\])', args_str, re.DOTALL)
        if options_match:
            try:
                args['options'] = ast.literal_eval(options_match.group(1))
                # Remove options from args_str to avoid double parsing
                args_str = re.sub(r'options\s*=\s*\[[^\]]*\]', '', args_str, flags=re.DOTALL)
            except:
                pass
        
        # Parse remaining arguments
        for key, value in re.findall(r'(\w+)\s*=\s*("[^"]*"|\'[^\']*\'|\[[^\]]*\]|\{[^\}]*\}|[^\s,]+)', args_str):
            try:
                args[key] = ast.literal_eval(value)
            except:
                # Strip quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    args[key] = value[1:-1]
                else:
                    args[key] = value
        
        return args
    
    def _create_field_html(self, field_type: str, name: str, label: str = None, 
                          required: bool = False, placeholder: str = None, 
                          help_text: str = None, **kwargs) -> str:
        """
        Create HTML for any field type
        
        Args:
            field_type: Type of field (text_field, textarea_field, select_field, etc.)
            name: Field name
            label: Field label
            required: Whether field is required
            placeholder: Placeholder text
            help_text: Help text to display
            **kwargs: Additional field-specific arguments
            
        Returns:
            HTML string for the form field
        """
        self.field_count += 1
        
        # Set defaults
        label = label or name.replace('_', ' ').capitalize()
        placeholder = placeholder or self._get_placeholder(name)
        
        # Create the input HTML based on field type
        input_html = self._create_input_html(field_type, name, required, placeholder, **kwargs)
        
        # Create help text HTML
        help_html = self._create_help_html(help_text)
        
        # Return the complete field HTML
        return self._wrap_field_html(label, input_html, help_html)
    
    def _create_input_html(self, field_type: str, name: str, required: bool, 
                          placeholder: str, **kwargs) -> str:
        """Create the input HTML for a specific field type"""
        required_attr = "required" if required else ""
        placeholder_attr = f'placeholder="{placeholder}"' if placeholder else ""
        base_style = "width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;font-family:inherit;transition:border-color 0.2s;"
        
        if field_type == "text_field":
            return f'<input type="text" name="{name}" {required_attr} {placeholder_attr} style="{base_style}">'
        
        elif field_type == "textarea_field":
            rows = kwargs.get('rows', 3)
            return f'<textarea name="{name}" {required_attr} {placeholder_attr} rows="{rows}" style="{base_style}resize:vertical;"></textarea>'
        
        elif field_type == "select_field":
            options = self._process_options(kwargs.get('options', []))
            options_html = "".join([f'<option value="{opt}">{opt}</option>' for opt in options])
            return f'<select name="{name}" {required_attr} style="{base_style}"><option value="">Select an option</option>{options_html}</select>'
        
        elif field_type == "checkbox_field":
            options = self._process_options(kwargs.get('options', []))
            checkboxes_html = "".join([
                f'<label style="display:flex;align-items:center;cursor:pointer;font-size:14px;margin-bottom:1px;"><input type="checkbox" name="{name}" value="{opt}" style="margin-right:4px;"><span>{opt}</span></label>'
                for opt in options
            ])
            return f'<div style="margin-top:1px;">{checkboxes_html}</div>'
        
        elif field_type == "year_field":
            return f'<input type="text" name="{name}" {required_attr} placeholder="e.g., 2020" style="{base_style}">'
        
        else:
            # Default to text field for unknown types
            return f'<input type="text" name="{name}" {required_attr} {placeholder_attr} style="{base_style}">'
    
    def _process_options(self, options) -> List[str]:
        """Process and validate options for select/checkbox fields"""
        if isinstance(options, str):
            try:
                options = ast.literal_eval(options)
            except:
                options = [options]
        
        options = options or ["Option 1", "Option 2", "I don't know"]
        return options
    
    def _create_help_html(self, help_text: str) -> str:
        """Create help text HTML if provided"""
        if not help_text:
            return ""
        return f'<div style="color:#6c757d;font-size:13px;">{help_text}</div>'
    
    def _wrap_field_html(self, label: str, input_html: str, help_html: str) -> str:
        """Wrap field elements in a container div"""
        return f"""
        <div style="margin-bottom:3px;">
            <label style="display:block;font-weight:500;color:#333;font-size:14px;margin-bottom:1px;">{label}</label>
            {input_html}
            {help_html}
        </div>
        """
    
    def _get_placeholder(self, name: str) -> str:
        """Get default placeholder based on field name"""
        # Simple fallback placeholder - AI should provide specific ones
        return "Enter your answer here"
    
    def _build_form_html(self, content: str, additional_notes: str, submit_text: str) -> str:
        """Build the complete form HTML"""
        return f"""
        <form id="tire-form" style="max-width:600px;">
            <div style="color:#495057;">{content}</div>
            {additional_notes}
            <button type="submit" style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;">
                {submit_text}
            </button>
        </form>
        """
    
    def get_function_documentation(self) -> str:
        """Get documentation for available form builder functions"""
        return """
Available form builder functions:

create_text_field - Creates a single-line text input field
Parameters: name, label, required=False, placeholder=None, help_text=None

create_textarea_field - Creates a multi-line textarea field  
Parameters: name, label, required=False, placeholder=None, rows=3, help_text=None

create_select_field - Creates a dropdown select field with options
Parameters: name, label, options=[], required=False, help_text=None

create_checkbox_field - Creates a checkbox field with multiple options
Parameters: name, label, options=[], required=False, help_text=None

create_year_field - Creates a year input field with appropriate placeholder
Parameters: name, label, required=False, help_text=None
""" 