"""
Scribe AI Agent
Automatically extracts and records important information from conversations
"""

import re
import logging
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from agents.ai_client import AIClient
from agents.cost_manager import CostManager, ModelType
from agents.form_builder import FormBuilder
from utils.conversation_roadmap import ConversationRoadmap
from prompts.scribe_agent_prompt import SCRIBE_AGENT_PROMPT

logger = logging.getLogger(__name__)

class ScribeAgent(BaseAgent):
    """
    Scribe AI Agent - Automatically extracts and records important information
    """
    
    def __init__(self, ai_client: AIClient, cost_manager: CostManager, form_builder: FormBuilder):
        super().__init__(ai_client, cost_manager, form_builder, "ScribeAgent")
    
    def get_system_prompt(self) -> str:
        return SCRIBE_AGENT_PROMPT
    
    def get_agent_prompt(self) -> str:
        return "Extract and record any important information from this conversation."
    
    async def extract_and_record(self, user_message: str, roadmap: ConversationRoadmap, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract important information from the conversation and record it in the notepad
        """
        try:
            extracted_info = {}
            
            # Extract vehicle information
            vehicle_info = self._extract_vehicle_info(user_message)
            if vehicle_info:
                extracted_info["vehicle_info"] = vehicle_info
                # Write to notepad in a natural way
                vehicle_notes = []
                for key, value in vehicle_info.items():
                    vehicle_notes.append(f"{key}: {value}")
                roadmap.write_to_notepad("Vehicle information: " + ", ".join(vehicle_notes), "Vehicle Details")
            
            # Extract tire information
            tire_info = self._extract_tire_info(user_message)
            if tire_info:
                extracted_info["tire_info"] = tire_info
                # Write to notepad in a natural way
                tire_notes = []
                for key, value in tire_info.items():
                    tire_notes.append(f"{key}: {value}")
                roadmap.write_to_notepad("Tire information: " + ", ".join(tire_notes), "Tire Details")
            
            # Extract user preferences
            preferences = self._extract_preferences(user_message)
            if preferences:
                extracted_info["preferences"] = preferences
                # Write to notepad in a natural way
                pref_notes = []
                for key, value in preferences.items():
                    pref_notes.append(f"{key}: {value}")
                roadmap.write_to_notepad("User preferences: " + ", ".join(pref_notes), "User Preferences")
            
            # Extract user situation
            situation = self._extract_situation(user_message)
            if situation:
                extracted_info["situation"] = situation
                # Write to notepad in a natural way
                sit_notes = []
                for key, value in situation.items():
                    sit_notes.append(f"{key}: {value}")
                roadmap.write_to_notepad("User situation: " + ", ".join(sit_notes), "User Situation")
            
            # Extract conversation context and form data
            conversation_insights = self._extract_conversation_insights(user_message, conversation_context)
            if conversation_insights:
                for insight in conversation_insights:
                    roadmap.write_to_notepad(insight, "Conversation Progress")
            
            return {
                "extracted_info": extracted_info,
                "notepad_updated": bool(extracted_info or conversation_insights),
                "notepad_content": roadmap.get_notepad_content()
            }
            
        except Exception as e:
            logger.error(f"Error in ScribeAgent extraction: {str(e)}")
            return {"extracted_info": {}, "notepad_updated": False}
    
    def _extract_vehicle_info(self, text: str) -> Dict[str, str]:
        """Extract vehicle information from text"""
        info = {}
        
        # Extract make and model
        make_model_patterns = [
            r'(\w+)\s+(\w+)',  # "Honda Civic"
            r'(\w+)\s+(\w+)\s+(\w+)',  # "Toyota Camry LE"
        ]
        
        for pattern in make_model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    # Check if it looks like a make/model
                    if self._is_likely_vehicle_make(match[0]):
                        info['make'] = match[0].title()
                        info['model'] = match[1].title()
                        if len(match) > 2:
                            info['submodel'] = match[2].title()
                        break
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            info['year'] = year_match.group()
        
        # Extract VIN
        vin_match = re.search(r'\b[A-Z0-9]{17}\b', text.upper())
        if vin_match:
            info['vin'] = vin_match.group()
        
        return info
    
    def _extract_tire_info(self, text: str) -> Dict[str, str]:
        """Extract tire information from text"""
        info = {}
        
        # Extract tire size
        tire_size_patterns = [
            r'\b(\d{3}/\d{2}R\d{2})\b',  # "225/60R16"
            r'\b(\d{3}-\d{2}-\d{2})\b',  # "225-60-16"
        ]
        
        for pattern in tire_size_patterns:
            match = re.search(pattern, text)
            if match:
                info['size'] = match.group(1)
                break
        
        # Extract tire brand
        tire_brands = ['michelin', 'bridgestone', 'goodyear', 'continental', 'pirelli', 'dunlop', 'yokohama', 'toyo', 'falken', 'hankook']
        for brand in tire_brands:
            if brand in text.lower():
                info['brand'] = brand.title()
                break
        
        return info
    
    def _extract_preferences(self, text: str) -> Dict[str, str]:
        """Extract user preferences from text"""
        info = {}
        
        # Extract budget information
        budget_patterns = [
            r'\$(\d+)',  # "$200"
            r'(\d+)\s*dollars?',  # "200 dollars"
            r'budget.*?(\d+)',  # "budget around 200"
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['budget'] = match.group(1)
                break
        
        # Extract driving patterns
        driving_patterns = ['daily commute', 'highway', 'city', 'sporty', 'off-road', 'winter', 'summer']
        for pattern in driving_patterns:
            if pattern in text.lower():
                info['driving_pattern'] = pattern
                break
        
        return info
    
    def _extract_situation(self, text: str) -> Dict[str, str]:
        """Extract user situation information"""
        info = {}
        
        # Extract location/proximity
        if 'near' in text.lower() or 'close' in text.lower():
            if 'vehicle' in text.lower() or 'car' in text.lower():
                info['near_vehicle'] = 'yes'
        
        # Extract document access
        documents = ['registration', 'manual', 'receipt', 'insurance']
        for doc in documents:
            if doc in text.lower():
                info['has_documents'] = 'yes'
                break
        
        return info
    
    def _is_likely_vehicle_make(self, word: str) -> bool:
        """Check if a word is likely a vehicle make"""
        common_makes = [
            'honda', 'toyota', 'ford', 'chevrolet', 'nissan', 'hyundai', 'kia', 'mazda', 'subaru',
            'volkswagen', 'bmw', 'mercedes', 'audi', 'lexus', 'acura', 'infiniti', 'buick', 'cadillac',
            'chrysler', 'dodge', 'jeep', 'ram', 'gmc', 'volvo', 'saab', 'mitsubishi', 'suzuki'
        ]
        return word.lower() in common_makes 

    def _extract_conversation_insights(self, user_message: str, conversation_context: Dict[str, Any]) -> List[str]:
        """Extract meaningful conversation insights and progress"""
        insights = []
        
        # Check for form data and extract meaningful information
        if 'form_data' in conversation_context:
            form_data = conversation_context['form_data']
            
            # Extract method choice - only note if it's important
            if 'info_method' in form_data:
                method = form_data['info_method']
                if method == 'not_sure':
                    insights.append("User needs help - doesn't know how to find tire info")
                elif method == 'tire_size':
                    insights.append("User has tire size ready")
                elif method == 'make_model_year':
                    insights.append("User will provide vehicle details")
                elif method == 'vin':
                    insights.append("User has VIN number")
            
            # Extract proximity information - important for guidance
            if 'proximity' in form_data:
                proximity = form_data['proximity']
                if proximity == 'no':
                    insights.append("User not near car - need to use documents")
                elif proximity == 'yes':
                    insights.append("User near car - can check tire sidewall")
            
            # Extract document access - very important for next steps
            if 'document_access' in form_data:
                documents = form_data['document_access']
                if isinstance(documents, list) and documents:
                    doc_list = ", ".join(documents)
                    insights.append(f"User has: {doc_list}")
                elif documents:
                    insights.append(f"User has: {documents}")
        
        # Extract meaningful user statements - the real important stuff
        meaningful_phrases = [
            "I have", "I know", "I need", "I want", "I'm looking for",
            "My car", "My vehicle", "My tires", "My budget",
            "I drive", "I use", "I prefer", "I need help",
            "I don't", "I can't", "I'm not sure"
        ]
        
        for phrase in meaningful_phrases:
            if phrase.lower() in user_message.lower():
                # Extract the meaningful part of the message
                start_idx = user_message.lower().find(phrase.lower())
                if start_idx >= 0:
                    meaningful_part = user_message[start_idx:start_idx + 100].strip()
                    if len(meaningful_part) > len(phrase):
                        # Make it more natural
                        insights.append(f"User: {meaningful_part}")
                    break
        
        # Extract specific important information
        if any(word in user_message.lower() for word in ['budget', 'money', 'cost', 'price', 'cheap', 'expensive']):
            insights.append("User mentioned budget/cost concerns")
        
        if any(word in user_message.lower() for word in ['snow', 'winter', 'summer', 'all-season', 'performance']):
            insights.append("User mentioned tire type preferences")
        
        if any(word in user_message.lower() for word in ['highway', 'city', 'commute', 'long distance']):
            insights.append("User mentioned driving patterns")
        
        return insights 