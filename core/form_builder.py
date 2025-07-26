"""
Simplified Form Builder
Generates HTML form fields with clean, maintainable code
"""

from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FormBuilder:
    """
    Simplified form builder that generates HTML form fields
    """
    
    def __init__(self):
        self.field_count = 0
    
    def create_text_field(self, name: str, label: Optional[str] = None, required: bool = False, 
                         placeholder: Optional[str] = None, help_text: Optional[str] = None) -> str:
        """Create a single-line text input field"""
        self.field_count += 1
        label = label or name.replace('_', ' ').capitalize()
        placeholder = placeholder or self._get_default_placeholder(name)
        
        return self._create_field_html(
            field_type="text",
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            help_text=help_text
        )
    
    def create_textarea_field(self, name: str, label: Optional[str] = None, required: bool = False,
                             placeholder: Optional[str] = None, rows: int = 3, help_text: Optional[str] = None, 
                             skip_additional_notes_check: bool = False) -> str:
        """Create a multi-line textarea field"""
        if name == "additional_notes" and not skip_additional_notes_check:
            logger.debug("AI attempted to manually create additional_notes field - this is automatically added. Skipping.")
            return ""
        
        self.field_count += 1
        label = label or name.replace('_', ' ').capitalize()
        
        return self._create_field_html(
            field_type="textarea",
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            help_text=help_text,
            rows=rows
        )
    
    def create_select_field(self, name: str, label: Optional[str] = None, options: Optional[List[str]] = None,
                           required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a dropdown select field"""
        self.field_count += 1
        label = label or name.replace('_', ' ').capitalize()
        # Ensure options is a list
        if isinstance(options, str):
            import ast
            try:
                options = ast.literal_eval(options)
            except Exception:
                options = [options]
        options = options or []
        
        # Add "I don't know" option if not present
        if "I don't know" not in options and "I'm not sure" not in options:
            options.append("I don't know")
        
        options_html = "".join([f'<option value="{option}">{option}</option>' for option in options])
        
        return self._create_field_html(
            field_type="select",
            name=name,
            label=label,
            required=required,
            help_text=help_text,
            options_html=options_html
        )
    
    def create_checkbox_field(self, name: str, label: Optional[str] = None, options: Optional[List[str]] = None,
                             required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a checkbox field"""
        self.field_count += 1
        label = label or name.replace('_', ' ').capitalize()
        # Ensure options is a list
        if isinstance(options, str):
            import ast
            try:
                options = ast.literal_eval(options)
            except Exception:
                options = [options]
        options = options or []
        
        checkboxes_html = ""
        for option in options:
            checkboxes_html += f"""
            <label style="display:flex;align-items:center;cursor:pointer;font-size:14px;margin-bottom:1px;">
                <input type="checkbox" name="{name}" value="{option}" style="margin-right:4px;">
                <span>{option}</span>
            </label>
            """
        
        return self._create_field_html(
            field_type="checkbox",
            name=name,
            label=label,
            required=required,
            help_text=help_text,
            checkboxes_html=checkboxes_html
        )
    
    def create_year_field(self, name: str, label: Optional[str] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a year input field"""
        return self.create_text_field(
            name=name,
            label=label or "Year",
            required=required,
            placeholder="e.g., 2020",
            help_text=help_text or "Enter the year of your vehicle"
        )
    
    def create_complete_form(self, fields_html: List[str], conversation_text: str = "", submit_text: str = "Continue") -> str:
        """Create a complete form with all fields"""
        fields_content = "".join(fields_html)
        
        # Add additional notes field automatically
        additional_notes = self.create_textarea_field(
            name="additional_notes",
            label="Additional Thoughts (Optional)",
            required=False,
            placeholder="Ask a question, add details, or tell me anything...",
            skip_additional_notes_check=True
        )
        
        conversation_html = f'<div style="color:#495057;">{self._format_conversation_text(conversation_text)}</div>' if conversation_text else ""
        
        return f"""
        <form id="tire-form" style="max-width:600px;">
            {conversation_html}
            {fields_content}
            {additional_notes}
            <button type="submit" style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;">
                {submit_text}
            </button>
        </form>
        """
    
    def create_embedded_form(self, conversation_with_fields: str, submit_text: str = "Continue") -> str:
        """Create a form with conversation text and form fields embedded within it"""
        import re
        
        # Add additional notes field automatically
        additional_notes = self.create_textarea_field(
            name="additional_notes",
            label="Additional Thoughts (Optional)",
            required=False,
            placeholder="Ask a question, add details, or tell me anything...",
            skip_additional_notes_check=True
        )
        

        
        # Replace all function calls in the conversation text (handling nested braces)
        def find_function_calls(text):
            """Find function calls with proper brace matching"""
            import re
            # Find all {create_...} patterns
            pattern = r'\{create_\w+\([^}]*\)\}'
            matches = re.finditer(pattern, text, re.DOTALL)
            return matches
        
        # Process each function call
        processed_content = conversation_with_fields
        for match in find_function_calls(conversation_with_fields):
            function_call = match.group(0)
            # Remove the outer braces
            function_content = function_call[1:-1]
            try:
                # Extract function name and arguments
                func_match = re.match(r'(\w+)\((.*)\)', function_content, re.DOTALL)
                if func_match:
                    func_name = func_match.group(1)
                    args_str = func_match.group(2)
                    # Call the function to generate the field HTML
                    field_html = self.call_function(func_name, args_str)
                    processed_content = processed_content.replace(function_call, field_html)
            except Exception as e:
                logger.error(f"Error processing function call {function_call}: {str(e)}")
                processed_content = processed_content.replace(function_call, f"<span style='color:red;'>Error: {function_call}</span>")
        
        # Clean up the text formatting - preserve line breaks and bullet points
        processed_content = processed_content.replace('\n', '<br>')
        processed_content = processed_content.replace('•', '• ')
        
        return f"""
        <form id="tire-form" style="max-width:600px;">
            <div style="color:#495057;">{processed_content}</div>
            {additional_notes}
            <button type="submit" style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;">
                {submit_text}
            </button>
        </form>
        """
    
    def _create_field_html(self, field_type: str, name: str, label: str, required: bool = False,
                          placeholder: Optional[str] = None, help_text: Optional[str] = None,
                          **kwargs) -> str:
        """Create clean, minimal HTML for any field type"""
        required_attr = "required" if required else ""
        placeholder_attr = f'placeholder="{placeholder}"' if placeholder else ""
        help_html = f'<div style="color:#6c757d;font-size:13px;">{help_text}</div>' if help_text else ""
        
        # Common input styling for consistency - proper spacing
        input_style = "width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;font-family:inherit;transition:border-color 0.2s;"
        
        if field_type == "text":
            input_html = f'<input type="text" name="{name}" {required_attr} {placeholder_attr} style="{input_style}">'
        elif field_type == "textarea":
            rows = kwargs.get('rows', 3)
            input_html = f'<textarea name="{name}" {required_attr} {placeholder_attr} rows="{rows}" style="{input_style}resize:vertical;"></textarea>'
        elif field_type == "select":
            options_html = kwargs.get('options_html', '')
            input_html = f'<select name="{name}" {required_attr} style="{input_style}"><option value="">Select an option</option>{options_html}</select>'
        elif field_type == "checkbox":
            checkboxes_html = kwargs.get('checkboxes_html', '')
            # Very tight checkbox spacing
            input_html = f'<div style="margin-top:1px;">{checkboxes_html}</div>'
        else:
            input_html = ""
        
        # Clean field container with very tight spacing between fields
        return f"""
        <div style="margin-bottom:3px;">
            <label style="display:block;font-weight:500;color:#333;font-size:14px;margin-bottom:1px;">{label}</label>
            {input_html}
            {help_html}
        </div>
        """
    
    def _get_default_placeholder(self, name: str) -> str:
        """Get default placeholder based on field name"""
        field_name = name.lower()
        placeholders = {
            'make': "e.g., Honda, Toyota, Ford, Kia, Hyundai",
            'model': "e.g., Accord, Camry, F-150, Forte, Sonata",
            'year': "e.g., 2015, 2020, 2023",
            'size': "e.g., 205/55R16, 225/45R17",
            'tire': "e.g., 205/55R16, 225/45R17",
            'mileage': "e.g., 15,000, 50,000",
            'vin': "17-character VIN from dashboard or registration"
        }
        
        for key, placeholder in placeholders.items():
            if key in field_name:
                return placeholder
        
        return "Enter your answer here"
    
    def _format_conversation_text(self, text: str) -> str:
        """Format conversation text for display"""
        if not text:
            return ""
        
        # Preserve line breaks by converting them to <br> tags
        formatted_text = text.replace('\n', '<br>')
        
        return formatted_text
    
    def call_function(self, func_name: str, args_str: str) -> str:
        """Call a form builder function with parsed arguments"""
        try:
            args = self._parse_function_args(args_str)
            
            # Validate the function call
            validation_errors = self.validate_function_call(func_name, args)
            
            # Log validation results
            if validation_errors:
                logger.warning(f"Validation errors for {func_name}: {validation_errors}")
                # Try to fix common issues
                args = self._fix_common_issues(func_name, args)
            
            # Call the appropriate function
            if func_name == "create_text_field":
                return self.create_text_field(**args)
            elif func_name == "create_textarea_field":
                return self.create_textarea_field(**args)
            elif func_name == "create_select_field":
                return self.create_select_field(**args)
            elif func_name == "create_checkbox_field":
                return self.create_checkbox_field(**args)
            elif func_name == "create_year_field":
                return self.create_year_field(**args)
            else:
                logger.warning(f"Unknown function: {func_name}")
                return ""
                
        except Exception as e:
            logger.error(f"Error calling function {func_name}: {str(e)}")
            # Return a fallback form field
            return self._create_fallback_field(func_name, args_str)
    
    def _fix_common_issues(self, func_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues with function arguments"""
        fixed_args = args.copy()
        
        # Fix missing options for select/checkbox fields
        if func_name in ['create_select_field', 'create_checkbox_field']:
            if 'options' not in fixed_args or not fixed_args['options']:
                logger.info(f"Adding default options for {func_name}")
                fixed_args['options'] = ["Option 1", "Option 2", "I don't know"]
        
        # Fix missing name
        if 'name' not in fixed_args:
            logger.info(f"Adding default name for {func_name}")
            fixed_args['name'] = f"field_{self.field_count}"
        
        # Fix missing label
        if 'label' not in fixed_args:
            logger.info(f"Adding default label for {func_name}")
            fixed_args['label'] = fixed_args.get('name', 'Field').replace('_', ' ').capitalize()
        
        # Fix boolean values
        if 'required' in fixed_args and not isinstance(fixed_args['required'], bool):
            try:
                fixed_args['required'] = bool(fixed_args['required'])
            except:
                fixed_args['required'] = False
        
        # Fix integer values
        if 'rows' in fixed_args and not isinstance(fixed_args['rows'], int):
            try:
                fixed_args['rows'] = int(fixed_args['rows'])
            except:
                fixed_args['rows'] = 3
        
        return fixed_args
    
    def _create_fallback_field(self, func_name: str, args_str: str) -> str:
        """Create a fallback form field when function call fails"""
        logger.warning(f"Creating fallback field for failed {func_name}")
        
        # Extract basic info from args_str if possible
        import re
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', args_str)
        label_match = re.search(r'label\s*=\s*["\']([^"\']+)["\']', args_str)
        
        name = name_match.group(1) if name_match else f"fallback_{self.field_count}"
        label = label_match.group(1) if label_match else "Please provide information"
        
        # Create a simple text field as fallback
        return self.create_text_field(
            name=name,
            label=label,
            required=False,
            placeholder="Please enter your information here",
            help_text="This field was created due to a processing error. Please provide your information."
        )
    
    def _parse_function_args(self, args_str: str) -> Dict[str, Any]:
        """Parse function arguments from string, robustly handling lists, dicts, numbers, booleans, and quoted strings for any argument."""
        args = {}
        import re
        import ast
        
        # Debug logging
        logger.debug(f"Parsing function args: {args_str[:200]}...")
        
        # First, handle options list specially since it's the most complex
        options_match = re.search(r'options\s*=\s*(\[[^\]]*\])', args_str, re.DOTALL)
        if options_match:
            options_raw = options_match.group(1)
            logger.debug(f"Found options raw: {options_raw}")
            try:
                options = ast.literal_eval(options_raw)
                args['options'] = options
                logger.debug(f"Successfully parsed options: {options}")
                # Remove options from args_str so it doesn't get double-parsed
                args_str = re.sub(r'options\s*=\s*\[[^\]]*\]', '', args_str, flags=re.DOTALL)
            except Exception as e:
                logger.warning(f"Error parsing options list with ast.literal_eval: {e}")
                # Fallback: try manual parsing
                options = self._safe_parse_options(options_raw)
                args['options'] = options
                logger.debug(f"Fallback parsed options: {options}")
        
        # Now parse remaining arguments
        # Find all key=value pairs (including lists, dicts, numbers, booleans, quoted strings)
        matches = re.findall(r'(\w+)\s*=\s*("[^"]*"|\'[^\']*\'|\[[^\]]*\]|\{[^\}]*\}|[^\s,]+)', args_str)
        for key, value in matches:
            if key == 'options':  # Skip options as we already handled it
                continue
            value = value.strip()
            # Try to parse as a Python literal
            try:
                parsed_value = ast.literal_eval(value)
                args[key] = parsed_value
                logger.debug(f"Parsed {key}: {parsed_value}")
            except Exception:
                # Fallback: treat as string, strip quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    args[key] = value[1:-1]
                else:
                    args[key] = value
                logger.debug(f"Fallback parsed {key}: {args[key]}")
        
        logger.debug(f"Final parsed args: {args}")
        return args
    
    def _safe_parse_options(self, options_str: str) -> List[str]:
        """Safely parse options with multiple fallback strategies"""
        import re
        
        # Remove outer brackets
        options_str = options_str.strip()
        if options_str.startswith('[') and options_str.endswith(']'):
            options_str = options_str[1:-1]
        
        # Strategy 1: Split by comma, but be smart about quoted strings
        try:
            # This regex splits by comma but respects quoted strings
            pattern = r'"[^"]*"|\'[^\']*\'|[^,]+'
            matches = re.findall(pattern, options_str)
            options = []
            for match in matches:
                match = match.strip()
                # Remove quotes if present
                if (match.startswith('"') and match.endswith('"')) or (match.startswith("'") and match.endswith("'")):
                    match = match[1:-1]
                if match:
                    options.append(match)
            
            if options:
                logger.debug(f"Manual parsing successful: {options}")
                return options
        except Exception as e:
            logger.warning(f"Manual parsing failed: {e}")
        
        # Strategy 2: Simple comma split (fallback)
        try:
            options = [opt.strip().strip('"').strip("'") for opt in options_str.split(',') if opt.strip()]
            if options:
                logger.debug(f"Simple comma split successful: {options}")
                return options
        except Exception as e:
            logger.warning(f"Simple comma split failed: {e}")
        
        # Strategy 3: Treat entire string as single option
        logger.warning(f"All parsing strategies failed, treating as single option: {options_str}")
        return [options_str.strip().strip('"').strip("'")]
    
    def validate_function_call(self, func_name: str, args: Dict[str, Any]) -> List[str]:
        """Validate function call and return error messages"""
        errors = []
        
        # Check for required parameters
        if 'name' not in args:
            errors.append(f"{func_name} requires 'name' parameter")
        
        # Check for options in select/checkbox fields
        if func_name in ['create_select_field', 'create_checkbox_field']:
            if 'options' not in args:
                errors.append(f"{func_name} requires 'options' parameter")
            elif not args['options'] or (isinstance(args['options'], list) and len(args['options']) == 0):
                errors.append(f"{func_name} requires non-empty 'options' parameter")
        
        # Check for valid boolean values
        if 'required' in args and not isinstance(args['required'], bool):
            try:
                args['required'] = bool(args['required'])
            except:
                errors.append(f"{func_name} 'required' parameter must be boolean")
        
        # Check for valid integer values
        if 'rows' in args and not isinstance(args['rows'], int):
            try:
                args['rows'] = int(args['rows'])
            except:
                errors.append(f"{func_name} 'rows' parameter must be integer")
        
        if errors:
            logger.warning(f"Validation errors for {func_name}: {errors}")
        
        return errors
    
    def reset_field_count(self):
        """Reset field counter"""
        self.field_count = 0 