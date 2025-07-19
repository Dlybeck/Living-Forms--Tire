"""
Memory Manager for Living Form Tire Sales Assistant
Handles conversation compression, intelligent summarization, and state management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from agents.ai_client import AIClient
from agents.cost_manager import ModelType

logger = logging.getLogger(__name__)

class DataImportance(Enum):
    """Importance levels for data retention"""
    CRITICAL = "critical"      # Always preserve (vehicle info, tire specs)
    IMPORTANT = "important"    # Preserve if space allows (preferences, budget)
    NORMAL = "normal"          # Preserve in summaries (conversation flow)
    LOW = "low"               # Can be compressed (redundant info)

@dataclass
class ConversationSummary:
    """Represents a compressed conversation summary"""
    summary_id: str
    timestamp: datetime
    summary_text: str
    important_data: Dict[str, Any]
    compressed_events_count: int
    original_events: List[Dict[str, Any]]
    reasoning: str = ""

@dataclass
class MemoryConfig:
    """Configuration for memory management"""
    max_events: int = 200
    max_summary_length: int = 3000
    max_session_duration_hours: int = 2
    compression_threshold: int = 150  # Compress when events exceed this
    important_data_keys: Set[str] = field(default_factory=lambda: {
        'vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_vin',
        'tire_size', 'tire_brand', 'current_tire_condition',
        'budget_min', 'budget_max', 'budget_preference',
        'driving_pattern', 'mileage_per_year', 'climate_considerations',
        'performance_priorities', 'special_considerations'
    })

class MemoryManager:
    """
    Manages conversation memory, compression, and intelligent summarization
    """
    
    def __init__(self, ai_client: AIClient, config: Optional[MemoryConfig] = None):
        self.ai_client = ai_client
        self.config = config or MemoryConfig()
        self._compression_lock = asyncio.Lock()
        
        logger.info(f"MemoryManager initialized with config: {self.config}")
    
    async def compress_conversation_if_needed(self, session) -> bool:
        """
        Compress conversation if it exceeds thresholds
        Returns True if compression occurred
        """
        async with self._compression_lock:
            if len(session['conversation_history']) <= self.config.max_events:
                return False
            
            logger.info(f"Compressing conversation: {len(session['conversation_history'])} events")
            
            # Extract important data before compression
            important_data = self._extract_important_data(session)
            
            # Create intelligent summary of old events
            old_events = session['conversation_history'][:-self.config.compression_threshold]
            summary = await self._create_intelligent_summary(old_events, important_data)
            
            # Replace old events with summary
            session['conversation_history'] = [summary] + session['conversation_history'][-self.config.compression_threshold:]
            
            logger.info(f"Compression complete: {len(session['conversation_history'])} events remaining")
            return True
    
    def _extract_important_data(self, session) -> Dict[str, Any]:
        """Extract all important user-provided data"""
        important_data = {}
        
        # Extract from conversation history
        for event in session['conversation_history']:
            if event.get('type') == 'form_submission':
                form_data = event.get('form_data', {})
                for key, value in form_data.items():
                    if key in self.config.important_data_keys and value not in ['I don\'t know', 'I\'m not sure', '']:
                        important_data[key] = value
        
        # Extract from AI notepad
        if session.get('ai_notepad'):
            # Parse notepad for important information
            notepad_data = self._parse_notepad_for_important_data(session['ai_notepad'])
            important_data.update(notepad_data)
        
        logger.info(f"Extracted important data: {list(important_data.keys())}")
        return important_data
    
    def _parse_notepad_for_important_data(self, notepad_content: str) -> Dict[str, Any]:
        """Parse AI notepad for important user-provided data"""
        important_data = {}
        
        # Look for specific patterns in notepad
        lines = notepad_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Look for key-value patterns
            for key in self.config.important_data_keys:
                if f"{key}:" in line.lower() or f"{key.replace('_', ' ')}:" in line.lower():
                    # Extract value after colon
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        value = parts[1].strip()
                        if value and value not in ['I don\'t know', 'I\'m not sure', '']:
                            important_data[key] = value
        
        return important_data
    
    async def _create_intelligent_summary(self, events: List[Dict], important_data: Dict) -> ConversationSummary:
        """Create intelligent summary using AI with exponential fallback"""
        
        try:
            # Try GPT-4.1 first for best reasoning
            summary = await self._generate_ai_summary(events, important_data, ModelType.GPT_4_1_MINI)
            return summary
        except Exception as e:
            logger.warning(f"GPT-4.1 summary generation failed: {e}")
            
            try:
                # Fallback to GPT-4o-mini
                summary = await self._generate_ai_summary(events, important_data, ModelType.GPT_4O_MINI)
                return summary
            except Exception as e:
                logger.warning(f"GPT-4o-mini summary generation failed: {e}")
                
                try:
                    # Fallback to Claude 3.5 Sonnet
                    summary = await self._generate_ai_summary(events, important_data, ModelType.CLAUDE_3_5_SONNET)
                    return summary
                except Exception as e:
                    logger.error(f"All AI summary generation failed: {e}")
                    
                    # Final fallback: create basic summary
                    return self._create_basic_summary(events, important_data)
    
    async def _generate_ai_summary(self, events: List[Dict], important_data: Dict, model_type: ModelType) -> ConversationSummary:
        """Generate AI-powered summary with reasoning"""
        
        # Build context for AI
        context = {
            'events': events,
            'important_data': important_data,
            'summary_requirements': [
                'Preserve ALL user-provided information (not "I don\'t know" responses)',
                'Include reasoning for why information is important',
                'Maintain conversation flow context',
                'Keep important decisions and preferences',
                'Remove redundant or irrelevant details',
                'Focus on information that will help with tire recommendations'
            ]
        }
        
        # Create detailed prompt for AI
        summary_prompt = self._build_summary_prompt(context)
        
        # Generate summary using AI
        response = await self.ai_client.generate_response(
            user_message=summary_prompt,
            conversation_context=context,
            model_type=model_type
        )
        
        # Parse AI response
        summary_text = response.get('text', '').strip()
        
        # Create summary object
        return ConversationSummary(
            summary_id=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            summary_text=summary_text,
            important_data=important_data,
            compressed_events_count=len(events),
            original_events=events,
            reasoning="AI-generated summary with reasoning"
        )
    
    def _create_basic_summary(self, events: List[Dict], important_data: Dict) -> ConversationSummary:
        """Create basic summary when AI fails"""
        
        # Extract key information manually
        key_points = []
        
        # Add important data
        if important_data:
            key_points.append(f"User provided: {', '.join([f'{k}: {v}' for k, v in important_data.items()])}")
        
        # Add conversation flow
        event_types = [event.get('type', 'unknown') for event in events]
        if event_types:
            key_points.append(f"Conversation flow: {' -> '.join(event_types[-10:])}")  # Last 10 events
        
        summary_text = " | ".join(key_points) if key_points else "Conversation summary unavailable"
        
        return ConversationSummary(
            summary_id=f"basic_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            summary_text=summary_text,
            important_data=important_data,
            compressed_events_count=len(events),
            original_events=events,
            reasoning="Basic summary due to AI generation failure"
        )
    
    def _build_summary_prompt(self, context: Dict) -> str:
        """Build detailed prompt for AI summary generation"""
        
        events = context['events']
        important_data = context['important_data']
        requirements = context['summary_requirements']
        
        # Format events for AI
        formatted_events = []
        for event in events:
            event_type = event.get('type', 'unknown')
            timestamp = event.get('timestamp', 'unknown')
            data = event.get('data', {})
            
            if event_type == 'form_submission':
                form_data = data.get('form_data', {})
                if form_data:
                    answers = []
                    for field, value in form_data.items():
                        if value and value not in ['I don\'t know', 'I\'m not sure', '']:
                            answers.append(f"{field}: {value}")
                    if answers:
                        formatted_events.append(f"{timestamp}: User answered form - {', '.join(answers)}")
            elif event_type == 'data_updated':
                category = data.get('category', 'unknown')
                formatted_events.append(f"{timestamp}: Updated {category} data")
            elif event_type == 'step_advanced':
                from_step = data.get('from_step', 'unknown')
                to_step = data.get('to_step', 'unknown')
                formatted_events.append(f"{timestamp}: Advanced from {from_step} to {to_step}")
        
        # Build the prompt
        prompt = f"""
You are creating an intelligent summary of a tire sales conversation. Your task is to compress {len(events)} conversation events while preserving ALL important information.

IMPORTANT DATA TO PRESERVE:
{important_data}

CONVERSATION EVENTS:
{chr(10).join(formatted_events)}

REQUIREMENTS:
{chr(10).join(f"- {req}" for req in requirements)}

Create a comprehensive summary that:
1. Preserves ALL user-provided information (not "I don't know" responses)
2. Includes reasoning for why information is important for tire recommendations
3. Maintains conversation flow context
4. Focuses on information that will help with tire recommendations
5. Is clear and well-structured

Summary:
"""
        
        return prompt
    
    def is_session_expired(self, session_start_time: datetime) -> bool:
        """Check if session has expired"""
        return datetime.now() - session_start_time > timedelta(hours=self.config.max_session_duration_hours)
    
    def get_memory_stats(self, session) -> Dict[str, Any]:
        """Get memory usage statistics"""
        return {
            'total_events': len(session['conversation_history']),
            'max_events': self.config.max_events,
            'compression_threshold': self.config.compression_threshold,
            'needs_compression': len(session['conversation_history']) > self.config.compression_threshold,
            'important_data_count': len(self._extract_important_data(session)),
            'notepad_length': len(session.get('ai_notepad', ''))
        } 