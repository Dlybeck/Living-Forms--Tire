from typing import Dict, List, Optional, Any
from utils.state_manager import ConversationState, UserKnowledgeLevel
import logging

logger = logging.getLogger(__name__)

class LivingFormGenerator:
    """
    Generates dynamic HTML forms that adapt to user knowledge level and conversation state
    This is the core of the "living form" concept - forms that explain themselves and adapt
    """
    
    def __init__(self):
        # Remove all old form generator methods and templates
        # Only keep: generate_living_form, _generate_field_block, _get_adaptive_help_texts, _get_input_type, _generate_additional_notes_section, _generate_ask_anything_section, _generate_summary_with_final_input
        # Remove generate_vehicle_info_form, generate_preferences_form, generate_recommendation_form, and all _generate_*_form methods except the new ones
        # Fix any incomplete lines or syntax issues in the new code
        # (No code to add here, just remove the old methods and ensure the new ones are correct)
        pass
    
    def generate_living_form(self, conversation_state: ConversationState) -> str:
        """
        Generate a living form that's flexible and conversational.
        Shows relevant questions based on what we know, but doesn't hide things when user skips.
        Always helpful and reassuring.
        """
        from utils.state_manager import DataCategory
        
        # Get what we know so far
        vehicle_info = conversation_state.vehicle_info
        tire_specs = conversation_state.tire_specs
        
        # Determine what to show based on current progress
        level = conversation_state.user_knowledge_level
        
        # Start with a conversational header
        form_html = f'<form class="living-form {level.value}-level">'
        
        # Determine current stage and create appropriate header
        if not vehicle_info or not any(vehicle_info.values()):
            # Very beginning - vehicle info
            form_html += '<div class="form-header">'
            form_html += '<h3>🚗 Let\'s find your perfect tires!</h3>'
            form_html += '<p class="help-text">Tell me about your vehicle. Don\'t worry if you\'re not sure about everything - just fill in what you know and I\'ll help you with the rest! 😊</p>'
            form_html += '</div>'
            form_html += '<div class="form-body">'
            
            # Always show basic vehicle info
            form_html += self._generate_field_block('year', None, level, conversation_state)
            form_html += self._generate_field_block('make', None, level, conversation_state)
            form_html += self._generate_field_block('model', None, level, conversation_state)
            form_html += self._generate_field_block('quantity_needed', None, level, conversation_state)
            
        elif vehicle_info and not tire_specs.get('current_tire_size'):
            # We have basic vehicle info, let's get more details
            form_html += '<div class="form-header">'
            form_html += f'<h3>Great! I see you have a {vehicle_info.get("year", "")} {vehicle_info.get("make", "")} {vehicle_info.get("model", "")} 👍</h3>'
            form_html += '<p class="help-text">Now let\'s get some more details to find the perfect tires for you. Everything is optional - just share what you know!</p>'
            form_html += '</div>'
            form_html += '<div class="form-body">'
            
            # Show tire size and other details
            form_html += self._generate_field_block('current_tire_size', None, level, conversation_state)
            if not vehicle_info.get('trim'):
                form_html += self._generate_field_block('trim', None, level, conversation_state)
            
        else:
            # We have good vehicle info, let's get preferences
            form_html += '<div class="form-header">'
            form_html += f'<h3>Perfect! Now let\'s talk about your tire needs 🎯</h3>'
            form_html += '<p class="help-text">Help me understand how you use your vehicle so I can recommend the best tires for you. All questions are optional!</p>'
            form_html += '</div>'
            form_html += '<div class="form-body">'
            
            # Show usage and preference questions
            missing_driving = conversation_state.get_missing_driving_patterns()
            missing_budget = conversation_state.get_missing_budget_preferences()
            missing_current = conversation_state.get_missing_current_tire_status()
            
            # Show a few key questions from each category
            if missing_driving:
                for field in missing_driving[:2]:  # Show first 2 driving questions
                    form_html += self._generate_field_block(field, None, level, conversation_state)
            
            if missing_budget:
                for field in missing_budget[:2]:  # Show first 2 budget questions
                    form_html += self._generate_field_block(field, None, level, conversation_state)
            
            if missing_current:
                for field in missing_current[:1]:  # Show first current tire question
                    form_html += self._generate_field_block(field, None, level, conversation_state)
        
        # Always include the additional notes section with proper formatting
        form_html += self._generate_additional_notes_section(conversation_state)
        
        form_html += '</div>'
        form_html += '<div class="form-actions">'
        form_html += '<button type="submit" class="btn-primary">Continue</button>'
        form_html += '<p class="flexibility-note">💡 Don\'t know something? No problem! Just leave it blank or ask in the notes above. I\'m here to help!</p>'
        form_html += '</div></form>'
        
        return form_html

    def _generate_field_block(self, field: str, category, level, conversation_state) -> str:
        """Generate a form field block with help tooltips. No extra buttons."""
        help_texts = self._get_adaptive_help_texts(field, level)
        label = field.replace('_', ' ').title()
        input_type = self._get_input_type(field)
        html = f'<div class="form-group">'
        html += f'<label for="{field}">{label} <span class="help-tooltip" title="{help_texts["tooltip"]}">?</span></label>'
        if level.value == "novice" and help_texts.get('explanation'):
            html += f'<small class="field-help">{help_texts["explanation"]}</small>'
        html += f'<input type="{input_type}" id="{field}" name="{field}" placeholder="{help_texts["placeholder"]}">'  # Properly closed input tag
        html += '</div>'
        return html

    def _get_adaptive_help_texts(self, field: str, level) -> dict:
        """Get help texts that adapt to user knowledge level"""
        base_texts = {
            'make': {
                'tooltip': 'Brand of your vehicle, e.g., Honda, Toyota, Ford, Chevrolet',
                'placeholder': 'e.g., Honda, Toyota, Ford, Chevrolet',
                'explanation': 'Look on your registration, insurance card, or the front/back of your car'
            },
            'model': {
                'tooltip': 'Model of your vehicle, e.g., Accord, Camry, F-150',
                'placeholder': 'e.g., Accord, Camry, Civic, Corolla, F-150, Silverado',
                'explanation': 'The specific name of your car (not the brand)'
            },
            'year': {
                'tooltip': 'Year your vehicle was made',
                'placeholder': 'e.g., 2019',
                'explanation': 'Check your registration, insurance card, or look for a sticker on your driver\'s side door'
            },
            'trim': {
                'tooltip': 'Trim level (optional)',
                'placeholder': 'e.g., Sport, LX, Limited',
                'explanation': 'This is usually on your registration or can be found online using your VIN'
            },
            'current_tire_size': {
                'tooltip': 'Size printed on your tire sidewall, e.g., 225/60R16',
                'placeholder': 'e.g., 225/60R16',
                'explanation': 'Look on the side of your tire for numbers like 2256- it\'s usually in large letters'
            },
            'quantity_needed': {
                'tooltip': 'How many tires do you want?',
                'placeholder': '1, 2, or 4',
                'explanation': 'Most people replace all 4 tires, but you can replace just 2 if needed'
            },
            'daily_mileage': {
                'tooltip': 'Average miles you drive per day',
                'placeholder': 'e.g., 25',
                'explanation': 'This helps determine how long your tires need to last'
            },
            'budget': {
                'tooltip': 'How much you want to spend per tire',
                'placeholder': 'e.g., $100-150',
                'explanation': 'Tire prices range from $75 for budget to $300 for premium'
            },
            'tire_condition': {
                'tooltip': 'Current condition of your tires',
                'placeholder': 'e.g., worn, damaged, old',
                'explanation': 'Are they worn out, damaged, or just old?'
            },
            'replacement_reason': {
                'tooltip': 'Why are you replacing tires?',
                'placeholder': 'e.g., worn out, flat, upgrade',
                'explanation': 'This helps me recommend the right type of tire'
            }
        }
        
        texts = base_texts.get(field, {
            'tooltip': f'Information about {field.replace("_", " ")}',
            'placeholder': f'Enter {field.replace("_", " ")}',
            'explanation': ''
        })
        
        # Simplify for expert users
        if level.value == "expert":
            texts['explanation'] = ""
        return texts

    def _get_input_type(self, field: str) -> str:
        """Determine the appropriate input type for a field"""
        if 'year' in field:
            return 'number'
        if any(word in field for word in ['quantity', 'mileage', 'age', 'budget']):
            return 'number'
        if 'condition' in field or 'reason' in field or 'needs' in field:
            return 'text'
        return 'text'

    def _generate_additional_notes_section(self, conversation_state: ConversationState) -> str:
        """Generate the additional notes section with proper formatting"""
        return '''
        <div class="form-group">
            <label for="additional_notes">Questions or Additional Info</label>
            <textarea id="additional_notes" name="additional_notes" 
                      class="form-control" 
                      placeholder="Ask me anything! Like: 'What tire size should I get?' or 'I drive mostly on highways' or 'I need quiet tires'..." 
                      rows="4"
                      style="width: 100%; padding: 12px; border: 2px solid #e9ecef; border-radius: 8px; font-family: inherit; font-size: 14px; resize: vertical; min-height: 80px;"></textarea>
            <small class="help-text" style="display: block; margin-top: 8px; color: #666; font-size: 12px;">💬 This is your space to ask questions, share concerns, or tell me anything else that might help me recommend the perfect tires for you!</small>
        </div>
        '''

    def _generate_ask_anything_section(self, conversation_state: ConversationState) -> str:
        """Generate the 'Ask me anything' section for later categories"""
        return '''
        <div class="form-group">
            <label for="ask_anything">Tell me what you want (optional)</label>
            <textarea id="ask_anything" name="ask_anything" 
                      placeholder="Describe your ideal tires, ask about specific features, or tell me what's most important to you..." 
                      rows="3"></textarea>
            <small class="help-text">This is your chance to tell me exactly what you're looking for. Be as specific as you want!</small>
        </div>
        '''

    def _generate_summary_with_final_input(self, conversation_state: ConversationState) -> str:
        """Generate a summary of all collected info with final input options."""
        
        html = '<div class="living-form-summary">'
        html += '<h3>All Information Collected!</h3>'
        html += '<div class="summary-content">'
        # Show summary of collected data
        for cat, values in [
            ("Vehicle Info", conversation_state.vehicle_info),
            ("Tire Specs", conversation_state.tire_specs),
            ("Driving Patterns", conversation_state.driving_patterns),
            ("Budget Preferences", conversation_state.budget_preferences),
            ("Current Tire Status", conversation_state.current_tire_status),
            ("Special Considerations", conversation_state.special_considerations),
        ]:
            if isinstance(values, dict) and values:
                html += f'<div class="summary-section"><strong>{cat}:</strong> '
                html += ', '.join(f'{k}: {v}' for k, v in values.items() if v)
                html += '</div>'
        html += '</div>'
        html += '<p class="summary-note">Ready to get your personalized tire recommendations!</p>'
        # Final input form for any last questions or preferences
        html += '''
        <form class="final-input-form">
            <div class="form-group">
                <label for="final_questions">Any last questions or preferences?</label>
                <textarea id="final_questions" name="final_questions" 
                          placeholder="Ask about specific brands, features, or anything else before I make recommendations..." 
                          rows="3"></textarea>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn-primary">Get My Recommendations</button>
            </div>
        </form>
        '''
        html += '</div>'
        return html 