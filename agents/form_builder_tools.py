from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class FormFieldConfig(BaseModel):
    """Configuration for a form field"""
    name: str = Field(..., description="The name/ID of the form field")
    label: str = Field(..., description="The display label for the field")
    field_type: str = Field(..., description="Type of field: text, textarea, select, radio, checkbox, number, email, phone")
    required: bool = Field(default=False, description="Whether the field is required")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text")
    options: Optional[List[str]] = Field(default=None, description="Options for select/radio fields")
    min_value: Optional[float] = Field(default=None, description="Minimum value for number fields")
    max_value: Optional[float] = Field(default=None, description="Maximum value for number fields")
    rows: Optional[int] = Field(default=3, description="Number of rows for textarea")
    help_text: Optional[str] = Field(default=None, description="Help text to display below the field")

class FormBuilderTools:
    """Tools for building form fields and complete forms"""
    
    def __init__(self):
        self.field_templates = {
            "text": self._create_text_field,
            "textarea": self._create_textarea_field,
            "select": self._create_select_field,
            "radio": self._create_radio_field,
            "checkbox": self._create_checkbox_field,
            "number": self._create_number_field,
            "email": self._create_email_field,
            "phone": self._create_phone_field,
            "year": self._create_year_field,
            "budget_range": self._create_budget_range_field,
            "mileage_range": self._create_mileage_range_field
        }
    
    def create_text_field(self, name: str, label: str, required: bool = False, placeholder: Optional[str] = None, help_text: Optional[str] = None) -> str:
        """Create a single-line text input field"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="text",
            required=required,
            placeholder=placeholder,
            help_text=help_text
        )
        return self._create_text_field(config)
    
    def create_textarea_field(self, name: str, label: str, required: bool = False, placeholder: Optional[str] = None, rows: int = 3, help_text: Optional[str] = None) -> str:
        """Create a multi-line textarea field"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="textarea",
            required=required,
            placeholder=placeholder,
            rows=rows,
            help_text=help_text
        )
        return self._create_textarea_field(config)
    
    def create_select_field(self, name: str, label: str, options: List[str], required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a dropdown select field"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="select",
            required=required,
            options=options,
            help_text=help_text
        )
        return self._create_select_field(config)
    
    def create_radio_field(self, name: str, label: str, options: List[str], required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a radio button group"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="radio",
            required=required,
            options=options,
            help_text=help_text
        )
        return self._create_radio_field(config)
    
    def create_checkbox_field(self, name: str, label: str, options: List[str], required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a checkbox group"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="checkbox",
            required=required,
            options=options,
            help_text=help_text
        )
        return self._create_checkbox_field(config)
    
    def create_number_field(self, name: str, label: str, required: bool = False, min_value: Optional[float] = None, max_value: Optional[float] = None, help_text: Optional[str] = None) -> str:
        """Create a number input field"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="number",
            required=required,
            min_value=min_value,
            max_value=max_value,
            help_text=help_text
        )
        return self._create_number_field(config)
    
    def create_email_field(self, name: str, label: str, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create an email input field"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="email",
            required=required,
            help_text=help_text
        )
        return self._create_email_field(config)
    
    def create_phone_field(self, name: str, label: str, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a phone number input field"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="phone",
            required=required,
            help_text=help_text
        )
        return self._create_phone_field(config)
    
    def create_year_field(self, name: str, label: str, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a year input field with validation"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="year",
            required=required,
            help_text=help_text
        )
        return self._create_year_field(config)
    
    def create_budget_range_field(self, name: str, label: str, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a budget range field with min/max inputs"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="budget_range",
            required=required,
            help_text=help_text
        )
        return self._create_budget_range_field(config)
    
    def create_mileage_range_field(self, name: str, label: str, required: bool = False, help_text: Optional[str] = None) -> str:
        """Create a mileage range field with min/max inputs"""
        config = FormFieldConfig(
            name=name,
            label=label,
            field_type="mileage_range",
            required=required,
            help_text=help_text
        )
        return self._create_mileage_range_field(config)
    
    def create_vehicle_info_form(self, conversation_text: str = "") -> str:
        """Create a complete vehicle information form"""
        form_html = f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {conversation_text}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {self.create_select_field("make", "Vehicle Make", ["Honda", "Toyota", "Ford", "Chevrolet", "Nissan", "Kia", "Hyundai", "Mazda", "Volkswagen", "BMW", "Mercedes", "Audi", "Other"], True, "Select your vehicle's make")}
                {self.create_text_field("model", "Vehicle Model", True, "e.g., Accord, Civic, CR-V", "Enter your vehicle's model name")}
                {self.create_year_field("year", "Vehicle Year", True, "Enter the year your vehicle was manufactured")}
                {self.create_text_field("trim", "Trim Level (Optional)", False, "e.g., EX, LX, Sport", "Optional: Specify the trim level for more accurate recommendations")}
                
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    Continue to Tire Information
                </button>
            </form>
        </div>
        """
        return form_html
    
    def create_tire_specs_form(self, conversation_text: str = "") -> str:
        """Create a complete tire specifications form"""
        form_html = f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {conversation_text}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {self.create_text_field("current_tire_size", "Current Tire Size (Optional)", False, "e.g., 225/60R16", "Found on the sidewall of your current tires")}
                {self.create_select_field("quantity_needed", "Number of Tires Needed", ["1", "2", "4"], True, "How many tires do you need?")}
                {self.create_select_field("tire_type", "Tire Type", ["All-Season", "Summer", "Winter", "All-Terrain", "Performance", "Touring"], False, "What type of tires are you looking for?")}
                
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    Continue to Driving Patterns
                </button>
            </form>
        </div>
        """
        return form_html
    
    def create_driving_patterns_form(self, conversation_text: str = "") -> str:
        """Create a complete driving patterns form"""
        form_html = f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {conversation_text}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {self.create_mileage_range_field("daily_mileage", "Daily Driving Distance", False, "How many miles do you typically drive per day?")}
                {self.create_radio_field("driving_type", "Primary Driving Type", ["Highway", "City", "Mixed"], False, "What type of driving do you do most?")}
                {self.create_checkbox_field("seasonal_needs", "Seasonal Considerations", ["Snow/Ice", "Heavy Rain", "Hot Weather", "Mild Climate"], False, "Select any seasonal conditions that apply")}
                
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    Continue to Budget Preferences
                </button>
            </form>
        </div>
        """
        return form_html
    
    def create_budget_preferences_form(self, conversation_text: str = "") -> str:
        """Create a complete budget preferences form"""
        form_html = f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {conversation_text}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {self.create_budget_range_field("budget", "Budget Range (per tire)", False, "What's your budget range per tire?")}
                {self.create_checkbox_field("preferred_brands", "Preferred Brands", ["Michelin", "Bridgestone", "Goodyear", "Continental", "Pirelli", "Dunlop", "Yokohama", "No Preference"], False, "Select any brands you prefer")}
                {self.create_radio_field("warranty_importance", "Warranty Importance", ["Very Important", "Somewhat Important", "Not Important"], False, "How important is warranty coverage to you?")}
                
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    Continue to Current Tire Status
                </button>
            </form>
        </div>
        """
        return form_html
    
    def create_current_tire_status_form(self, conversation_text: str = "") -> str:
        """Create a complete current tire status form"""
        form_html = f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {conversation_text}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {self.create_select_field("tire_condition", "Current Tire Condition", ["Good", "Fair", "Poor", "Bald", "Damaged"], False, "What's the condition of your current tires?")}
                {self.create_select_field("replacement_reason", "Reason for Replacement", ["Worn Out", "Damaged", "Upgrading", "Seasonal Change", "Safety Concerns"], False, "Why are you replacing your tires?")}
                {self.create_number_field("tire_age", "Tire Age (years)", False, 0, 20, "How old are your current tires?")}
                
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    Continue to Special Considerations
                </button>
            </form>
        </div>
        """
        return form_html
    
    def create_special_considerations_form(self, conversation_text: str = "") -> str:
        """Create a complete special considerations form"""
        form_html = f"""
        <div style="background:white;padding:25px;border-radius:12px;margin-bottom:25px;border:1px solid #e1e5e9;font-size:16px;line-height:1.6;">
            {conversation_text}
            <form class="living-form" style="background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;">
                {self.create_checkbox_field("performance_needs", "Performance Needs", ["High Performance", "Fuel Efficiency", "Comfort", "Handling", "Durability"], False, "Select any performance priorities")}
                {self.create_checkbox_field("special_conditions", "Special Conditions", ["Towing", "Off-Road", "Racing", "Commercial Use", "Heavy Loads"], False, "Any special driving conditions?")}
                {self.create_textarea_field("additional_notes", "Additional Notes", False, "Any other considerations or preferences?", 3, "Tell us anything else that might help with recommendations")}
                
                <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;transition:background-color 0.3s ease;">
                    Get Tire Recommendations
                </button>
            </form>
        </div>
        """
        return form_html
    
    # Private methods for generating individual field HTML
    def _create_text_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        placeholder_attr = f'placeholder="{config.placeholder}"' if config.placeholder else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <input type="text" name="{config.name}" {required_attr} {placeholder_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def _create_textarea_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        placeholder_attr = f'placeholder="{config.placeholder}"' if config.placeholder else ""
        rows_attr = f'rows="{config.rows}"' if config.rows else 'rows="3"'
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <textarea name="{config.name}" {required_attr} {placeholder_attr} {rows_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;resize:vertical;font-family: inherit;"></textarea>
            {help_html}
        </div>
        """
    
    def _create_select_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        options_html = ""
        if config.options:
            for option in config.options:
                options_html += f'<option value="{option}">{option}</option>'
        
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <select name="{config.name}" {required_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                <option value="">Select an option</option>
                {options_html}
            </select>
            {help_html}
        </div>
        """
    
    def _create_radio_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        options_html = ""
        if config.options:
            for option in config.options:
                options_html += f"""
                <label style="display:flex;align-items:center;margin-bottom:10px;cursor:pointer;">
                    <input type="radio" name="{config.name}" value="{option}" {required_attr} style="margin-right:8px;">
                    <span>{option}</span>
                </label>
                """
        
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{config.label}</label>
            <div style="margin-left:10px;">
                {options_html}
            </div>
            {help_html}
        </div>
        """
    
    def _create_checkbox_field(self, config: FormFieldConfig) -> str:
        options_html = ""
        if config.options:
            for option in config.options:
                options_html += f"""
                <label style="display:flex;align-items:center;margin-bottom:10px;cursor:pointer;">
                    <input type="checkbox" name="{config.name}" value="{option}" style="margin-right:8px;">
                    <span>{option}</span>
                </label>
                """
        
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{config.label}</label>
            <div style="margin-left:10px;">
                {options_html}
            </div>
            {help_html}
        </div>
        """
    
    def _create_number_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        min_attr = f'min="{config.min_value}"' if config.min_value is not None else ""
        max_attr = f'max="{config.max_value}"' if config.max_value is not None else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <input type="number" name="{config.name}" {required_attr} {min_attr} {max_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def _create_email_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <input type="email" name="{config.name}" {required_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def _create_phone_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <input type="tel" name="{config.name}" {required_attr} style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def _create_year_field(self, config: FormFieldConfig) -> str:
        required_attr = "required" if config.required else ""
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:5px;font-weight:500;color:#495057;">{config.label}</label>
            <input type="number" name="{config.name}" {required_attr} min="1900" max="2030" style="width:100%;padding:12px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
            {help_html}
        </div>
        """
    
    def _create_budget_range_field(self, config: FormFieldConfig) -> str:
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{config.label}</label>
            <div style="display:flex;gap:10px;align-items:center;">
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Min ($)</label>
                    <input type="number" name="{config.name}_min" min="0" step="10" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Max ($)</label>
                    <input type="number" name="{config.name}_max" min="0" step="10" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
            </div>
            {help_html}
        </div>
        """
    
    def _create_mileage_range_field(self, config: FormFieldConfig) -> str:
        help_html = f'<small style="color:#6c757d;display:block;margin-top:5px;">{config.help_text}</small>' if config.help_text else ""
        
        return f"""
        <div style="margin-bottom:20px;">
            <label style="display:block;margin-bottom:10px;font-weight:500;color:#495057;">{config.label}</label>
            <div style="display:flex;gap:10px;align-items:center;">
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Min (miles)</label>
                    <input type="number" name="{config.name}_min" min="0" step="5" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:5px;font-size:12px;color:#6c757d;">Max (miles)</label>
                    <input type="number" name="{config.name}_max" min="0" step="5" style="width:100%;padding:8px;border:2px solid #e9ecef;border-radius:6px;font-size:14px;font-family: inherit;">
                </div>
            </div>
            {help_html}
        </div>
        """ 