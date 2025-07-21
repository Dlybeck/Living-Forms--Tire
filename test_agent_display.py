#!/usr/bin/env python3
"""
Test script to verify agent display functionality
"""

import asyncio
import json
from agents.improved_agent_coordinator import ImprovedAgentCoordinator
from agents.ai_client import AIClient
from agents.cost_manager import CostManager
from agents.form_builder import FormBuilder
from database.tire_database import TireDatabase

async def test_agent_display():
    """Test that agent display information is included in responses"""
    
    print("🧪 Testing Agent Display Functionality")
    print("=" * 50)
    
    # Initialize components
    ai_client = AIClient()
    cost_manager = CostManager(config={"conversation_budget": 0.20})
    form_builder = FormBuilder()
    tire_db = TireDatabase()
    coordinator = ImprovedAgentCoordinator(ai_client, cost_manager, form_builder, tire_db)
    
    # Test session ID
    session_id = "test_agent_display_123"
    
    # Test message
    test_message = "I need help finding tires for my car"
    
    print(f"📝 Testing with message: '{test_message}'")
    print(f"🆔 Session ID: {session_id}")
    print()
    
    try:
        # Process message
        response = await coordinator.process_message(
            user_message=test_message,
            session_id=session_id
        )
        
        print("✅ Response received successfully!")
        print()
        
        # Check for agent information
        print("🔍 Checking for agent information:")
        print(f"   - current_agent: {response.get('current_agent', 'NOT FOUND')}")
        print(f"   - agent_display_name: {response.get('agent_display_name', 'NOT FOUND')}")
        print()
        
        # Check coordinator info
        coordinator_info = response.get('coordinator_info', {})
        print("🔍 Checking coordinator_info:")
        print(f"   - current_agent_name: {coordinator_info.get('current_agent_name', 'NOT FOUND')}")
        print(f"   - agent_display_name: {coordinator_info.get('agent_display_name', 'NOT FOUND')}")
        print()
        
        # Check response structure
        print("📋 Full response keys:")
        for key in sorted(response.keys()):
            print(f"   - {key}")
        print()
        
        # Test if agent display would show in frontend
        if response.get('agent_display_name'):
            print("🎉 SUCCESS: Agent display name found - should show in frontend!")
        else:
            print("❌ FAILURE: Agent display name not found")
            
        if response.get('current_agent'):
            print("🎉 SUCCESS: Current agent found - should show in frontend!")
        else:
            print("❌ FAILURE: Current agent not found")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_display()) 