from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FormBuilder:
    """
    Form builder that generates HTML form fields through function calls.
    This replaces the unreliable parsing approach with direct function execution.
    """
    
    def __init__(self):
        self.field_count = 0
    
    def create_text_field(self, name: str, label: Optional[str] = None, required: bool = False, placeholder: Optional[str] = None, help_text: Optional[str] = None) -> str:
        """Create a single-line text input field"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        
        # Provide default placeholders if none given
        if not placeholder:
            field_name = name.lower()
            if 'make' in field_name:
                placeholder = "e.g., Honda, Toyota, Ford, Kia, Hyundai"
            elif 'model' in field_name:
                placeholder = "e.g., Accord, Camry, F-150, Forte, Sonata"
            elif 'year' in field_name:
                placeholder = "e.g., 2015, 2020, 2023"
            elif 'size' in field_name or 'tire' in field_name:
                placeholder = "e.g., 205/55R16, 225/45R17"
            elif 'mileage' in field_name:
                placeholder = "e.g., 15,000, 50,000"
            else:
                placeholder = "Enter your answer here"
        
        required_attr = "required" if required else ""
        placeholder_attr = f'placeholder="{placeholder}"' if placeholder else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{label}</label>
            <input type="text" name="{name}" {required_attr} {placeholder_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def create_textarea_field(self, name: str, label: Optional[str] = None, required: bool = False, placeholder: Optional[str] = None, rows: int = 3, help_text: Optional[str] = None) -> str:
        """Create a multi-line textarea field"""
        # Safety check: Prevent AI from manually creating the additional_notes field
        if name == "additional_notes":
            logger.warning("AI attempted to manually create additional_notes field - this is automatically added. Skipping.")
            return ""
        
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        required_attr = "required" if required else ""
        placeholder_attr = f'placeholder="{placeholder}"' if placeholder else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{label}</label>
            <textarea name="{name}" {required_attr} {placeholder_attr} rows="{rows}" style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;resize:vertical;font-family: inherit;"></textarea>
            {help_html}
        </div>
        """
    
    def create_select_field(self, name: str, label: Optional[str] = None, options: Optional[List[str]] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a dropdown select field"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        if options is None:
            options = []
        
        # Always add "I don't know" option to help users who are unsure
        if "I don't know" not in options and "I'm not sure" not in options:
            options.append("I don't know")
        
        required_attr = "required" if required else ""
        options_html = ""
        for option in options:
            options_html += f'<option value="{option}">{option}</option>'
        
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{label}</label>
            <select name="{name}" {required_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                <option value="">Select an option</option>
                {options_html}
            </select>
            {help_html}
        </div>
        """
    
    def create_radio_field(self, name: str, label: Optional[str] = None, options: Optional[List[str]] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a radio button group"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        if options is None:
            options = []
        
        # Always add "I don't know" option to help users who are unsure
        if "I don't know" not in options and "I'm not sure" not in options:
            options.append("I don't know")
        
        required_attr = "required" if required else ""
        options_html = ""
        for option in options:
            options_html += f"""
            <label style="display:flex;align-items:center;margin-bottom:10px;cursor:pointer;">
                <input type="radio" name="{name}" value="{option}" {required_attr} style="margin-right:8px;">
                <span>{option}</span>
            </label>
            """
        
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{label}</label>
            <div style="margin-left:10px;">
                {options_html}
            </div>
            {help_html}
        </div>
        """
    
    def create_checkbox_field(self, name: str, label: Optional[str] = None, options: Optional[List[str]] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a checkbox group"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        if options is None:
            options = []
        
        options_html = ""
        has_other_option = False
        
        for option in options:
            # Check if this is an "Other" option
            if "other" in option.lower() or "please specify" in option.lower():
                has_other_option = True
                options_html += f"""
                <label style="display:flex;align-items:center;margin-bottom:10px;cursor:pointer;">
                    <input type="checkbox" name="{name}" value="{option}" style="margin-right:8px;" onchange="toggleOtherField(this, '{name}_other')">
                    <span>{option}</span>
                </label>
                <div id="{name}_other" style="margin-left:20px;margin-bottom:10px;display:none;">
                    <input type="text" name="{name}_other_text" placeholder="Please describe..." style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
                """
            else:
                options_html += f"""
                <label style="display:flex;align-items:center;margin-bottom:10px;cursor:pointer;">
                    <input type="checkbox" name="{name}" value="{option}" style="margin-right:8px;">
                    <span>{option}</span>
                </label>
                """
        
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        # Add JavaScript for "Other" field toggle if needed
        js_code = ""
        if has_other_option:
            js_code = """
            <script>
            function toggleOtherField(checkbox, otherFieldId) {
                const otherField = document.getElementById(otherFieldId);
                if (checkbox.checked) {
                    otherField.style.display = 'block';
                } else {
                    otherField.style.display = 'none';
                    otherField.querySelector('input').value = '';
                }
            }
            </script>
            """
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{label}</label>
            <div style="margin-left:10px;">
                {options_html}
            </div>
            {help_html}
            {js_code}
        </div>
        """
    
    def create_number_field(self, name: str, label: Optional[str] = None, required: bool = False, min_value: Optional[float] = None, max_value: Optional[float] = None, help_text: Optional[str] = None) -> str:
        """Create a number input field"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        required_attr = "required" if required else ""
        min_attr = f'min="{min_value}"' if min_value is not None else ""
        max_attr = f'max="{max_value}"' if max_value is not None else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{label}</label>
            <input type="number" name="{name}" {required_attr} {min_attr} {max_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def create_year_field(self, name: str, label: Optional[str] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a year input field with validation"""
        if not label:
            label = name.replace('_', ' ').capitalize()
        return self.create_number_field(name, label, required, 1900, 2030, help_text)
    
    def create_budget_range_field(self, name: str, label: Optional[str] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a budget range field with min/max inputs"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{label}</label>
            <div style="display:flex;gap:10px;align-items:center;">
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Min ($)</label>
                    <input type="number" name="{name}_min" min="0" step="10" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Max ($)</label>
                    <input type="number" name="{name}_max" min="0" step="10" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
            </div>
            {help_html}
        </div>
        """
    
    def create_mileage_range_field(self, name: str, label: Optional[str] = None, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a mileage range field with min/max inputs"""
        self.field_count += 1
        if not label:
            label = name.replace('_', ' ').capitalize()
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{help_text}</small>' if help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{label}</label>
            <div style="display:flex;gap:10px;align-items:center;">
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Min (miles)</label>
                    <input type="number" name="{name}_min" min="0" step="5" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Max (miles)</label>
                    <input type="number" name="{name}_max" min="0" step="5" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
            </div>
            {help_html}
        </div>
        """
    
    def create_complete_form(self, fields_html: List[str], conversation_text: str = "", submit_text: str = "Continue") -> str:
        """Create a complete form with conversation text and submit button. Always append an 'Additional Thoughts' free-text field at the end."""
        # Safety check: Ensure fields_html is a list
        if not isinstance(fields_html, list):
            fields_html = [str(fields_html)] if fields_html else []
        
        # Always add the free-text field at the end (create directly to avoid safety check)
        additional_notes_field = f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">Confused? Need help?</label>
            <textarea name="additional_notes" placeholder="Ask a question, add details, or tell me anything..." rows="3" style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;resize:vertical;font-family: inherit;"></textarea>
        </div>
        """
        
        # Ensure we don't duplicate the additional_notes field if it already exists
        existing_additional_notes = any('name="additional_notes"' in field for field in fields_html)
        if existing_additional_notes:
            fields_combined = "\n".join(fields_html)
        else:
            fields_combined = "\n".join(fields_html + [additional_notes_field])
        
        # Format conversation text with proper paragraphs and text formatting
        formatted_conversation = ""
        if conversation_text and conversation_text.strip():
            formatted_conversation = f'<div style="margin-bottom:20px;">{self._format_conversation_text(conversation_text)}</div>'
        
        return f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {formatted_conversation}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {fields_combined}
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    {submit_text}
                </button>
            </form>
        </div>
        """

    def _format_conversation_text(self, text: str) -> str:
        """Format conversation text with simple text formatting (same as frontend)"""
        import html
        import re
        
        # Escape HTML first
        formatted = html.escape(text)
        
        # Process formatting BEFORE converting line breaks to <br> tags
        # Convert ### headers to <h3>
        formatted = re.sub(r'^### (.*?)$', r'__HEADER_START__\1__HEADER_END__', formatted, flags=re.MULTILINE)
        
        # Convert numbered lists (1. item)
        formatted = re.sub(r'^(\d+)\. (.*?)$', r'__LIST_START__\1__LIST_MID__\2__LIST_END__', formatted, flags=re.MULTILINE)
        
        # Convert bullet points (- item)
        formatted = re.sub(r'^- (.*?)$', r'__BULLET_START__\1__BULLET_END__', formatted, flags=re.MULTILINE)
        
        # Convert **bold** to <strong>
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
        
        # Convert code blocks (`code`)
        formatted = re.sub(r'`(.*?)`', r'<code style="background:#f8f9fa;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:0.9em;">\1</code>', formatted)
        
        # Now convert line breaks to <br> tags
        formatted = formatted.replace('\n', '<br>')
        
        # Replace placeholders with actual HTML
        formatted = re.sub(r'__HEADER_START__(.*?)__HEADER_END__', r'</p><h3 style="color:#667eea;margin:15px 0 10px 0;font-size:18px;">\1</h3><p style="margin-bottom:12px;">', formatted)
        formatted = re.sub(r'__LIST_START__(.*?)__LIST_MID__(.*?)__LIST_END__', r'</p><div style="margin:8px 0;"><strong>\1.</strong> \2</div><p style="margin-bottom:12px;">', formatted)
        formatted = re.sub(r'__BULLET_START__(.*?)__BULLET_END__', r'</p><div style="margin:8px 0;margin-left:15px;">• \1</div><p style="margin-bottom:12px;">', formatted)
        
        # Add paragraph breaks for double line breaks
        formatted = re.sub(r'(<br>){2,}', r'</p><p style="margin-bottom:12px;">', formatted)
        
        # Wrap in paragraph tags
        formatted = f'<p style="margin-bottom:12px;">{formatted}</p>'
        
        # Clean up any empty paragraphs or malformed HTML
        formatted = re.sub(r'<p[^>]*>\s*</p>', '', formatted)  # Remove empty paragraphs
        formatted = re.sub(r'</p>\s*<p[^>]*>', '</p><p style="margin-bottom:12px;">', formatted)  # Normalize paragraph tags
        
        return formatted
    
    def call_function(self, func_name: str, args_str: str) -> str:
        """Call a form builder function by name with arguments"""
        try:
            # Parse the arguments string
            args = self._parse_function_args(args_str)
            
            # Get the function
            if hasattr(self, func_name):
                func = getattr(self, func_name)
                
                # Special handling for select fields without options
                if func_name == "create_select_field" and (not args.get("options") or len(args.get("options", [])) == 0):
                    field_name = args.get('name', 'unknown').lower()
                    logger.warning(f"Select field '{field_name}' created without options, using context-aware defaults")
                    
                    # Provide context-aware default options based on field name
                    if 'driving' in field_name or 'pattern' in field_name:
                        args["options"] = ["Daily commute", "Highway driving", "Weekend trips", "Long road trips", "Sporty driving"]
                    elif 'budget' in field_name:
                        args["options"] = ["Budget ($50-100 per tire)", "Mid-range ($100-200 per tire)", "Premium ($200+ per tire)"]
                    elif 'weather' in field_name or 'climate' in field_name:
                        args["options"] = ["Mostly dry", "Rainy", "Snowy winters", "Mixed conditions"]
                    elif 'usage' in field_name or 'purpose' in field_name:
                        args["options"] = ["Personal use", "Family car", "Work vehicle", "Recreational"]
                    elif 'priority' in field_name:
                        args["options"] = ["Performance", "Comfort", "Longevity", "Price", "Safety"]
                    else:
                        args["options"] = ["Option A", "Option B", "Option C", "Other"]
                
                return func(**args)
            else:
                logger.error(f"Unknown function: {func_name}")
                return f"<p>Error: Unknown function {func_name}</p>"
                
        except Exception as e:
            logger.error(f"Error calling function {func_name}: {str(e)}")
            return f"<p>Error: {str(e)}</p>"
    
    def _parse_function_args(self, args_str: str) -> Dict[str, Any]:
        """Parse function arguments from string format"""
        import ast
        import re
        
        try:
            # Handle different argument formats
            if args_str.strip().startswith('{') and args_str.strip().endswith('}'):
                # JSON-like format
                args_str = args_str.replace("'", '"')
                import json
                return json.loads(args_str)
            else:
                # Parse keyword arguments in format: name="value", label="value", required=True
                args = {}
                
                # Special handling for arrays - look for options=["item1", "item2", "item3"]
                # Also handle incomplete arrays that might be missing the closing bracket
                options_match = re.search(r'options\s*=\s*\[(.*?)\]', args_str, re.DOTALL)
                if not options_match:
                    # Try to find incomplete options array
                    options_match = re.search(r'options\s*=\s*\[(.*?)(?=\n\s*\w+\s*=|$)', args_str, re.DOTALL)
                
                if options_match:
                    options_content = options_match.group(1)
                    # Parse the options array - handle multi-line and quoted strings
                    options = []
                    
                    # Split by commas, but be careful about commas inside quotes
                    import shlex
                    try:
                        # Use shlex to properly handle quoted strings
                        lexer = shlex.shlex(options_content, posix=True)
                        lexer.quotes = '"'  # Only handle double quotes
                        lexer.whitespace = ',\n\r\t '  # Split on commas and whitespace
                        lexer.whitespace_split = True
                        
                        for token in lexer:
                            token = token.strip().strip('"\'')
                            if token and token not in ['[', ']', ',']:
                                options.append(token)
                    except:
                        # Fallback: simple parsing
                        current_option = ""
                        in_quotes = False
                        quote_char = None
                        
                        for char in options_content:
                            if char in ['"', "'"] and not in_quotes:
                                in_quotes = True
                                quote_char = char
                            elif char == quote_char and in_quotes:
                                in_quotes = False
                                quote_char = None
                            elif char == ',' and not in_quotes:
                                if current_option.strip():
                                    options.append(current_option.strip().strip('"\''))
                                    current_option = ""
                            else:
                                current_option += char
                        
                        # Add the last option
                        if current_option.strip():
                            options.append(current_option.strip().strip('"\''))
                    
                    args["options"] = options
                    
                    # Remove the options part from args_str for further parsing
                    args_str = re.sub(r'options\s*=\s*\[.*?\],?\s*', '', args_str, flags=re.DOTALL)
                
                # Pattern to match remaining keyword arguments
                # This handles: name="value", label="value", required=True
                pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\w+))'
                matches = re.findall(pattern, args_str)
                
                for match in matches:
                    key = match[0]
                    # Check which group has the value
                    if match[1]:  # Double quoted string
                        value = match[1]
                    elif match[2]:  # Single quoted string
                        value = match[2]
                    elif match[3]:  # Boolean or number
                        if match[3].lower() == 'true':
                            value = True
                        elif match[3].lower() == 'false':
                            value = False
                        else:
                            try:
                                value = int(match[3])
                            except ValueError:
                                value = match[3]
                    else:
                        continue
                    
                    args[key] = value
                
                if args:
                    return args
                
                # Fallback: try ast.literal_eval
                try:
                    return ast.literal_eval(f"{{{args_str}}}")
                except:
                    # Final fallback: treat as a single string argument
                    return {"name": "field", "label": args_str.strip()}
                        
        except Exception as e:
            logger.error(f"Error parsing function args '{args_str}': {str(e)}")
            return {"name": "field", "label": args_str.strip()}
    
    def reset_field_count(self):
        """Reset the field counter"""
        self.field_count = 0 