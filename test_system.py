"""
Simple test to verify the cleaned up system works
"""

import asyncio
import logging
from agents.improved_agent_coordinator import ImprovedAgentCoordinator
from agents.ai_client import AIClient
from agents.cost_manager import CostManager
from agents.form_builder import FormBuilder
from database.tire_database import TireDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system():
    """Test the cleaned up system"""
    
    print("🧹 Testing Cleaned Up System")
    print("=" * 40)
    
    # Initialize components
    tire_db = TireDatabase()
    cost_manager = CostManager(config={"conversation_budget": 0.20})
    ai_client = AIClient()
    form_builder = FormBuilder()
    
    # Initialize improved coordinator
    coordinator = ImprovedAgentCoordinator(ai_client, cost_manager, form_builder, tire_db)
    
    # Test session ID
    session_id = "test_session_001"
    
    print(f"📝 Testing session: {session_id}")
    
    # Test 1: Initial greeting
    print("\n1️⃣ Testing initial greeting...")
    response1 = await coordinator.process_message(
        user_message="Hello, I need help finding tires for my car",
        session_id=session_id
    )
    
    print(f"✅ Response received: {len(response1.get('response', ''))} characters")
    print(f"📊 Coordinator info: {response1.get('coordinator_info', {})}")
    
    # Test 2: Form submission with vehicle info
    print("\n2️⃣ Testing form submission with vehicle info...")
    form_data = {
        "info_method": "make_model_year",
        "vehicle_make": "Honda",
        "vehicle_model": "Civic",
        "vehicle_year": "2018"
    }
    
    response2 = await coordinator.process_message(
        user_message="I have a 2018 Honda Civic",
        session_id=session_id,
        form_data=form_data
    )
    
    print(f"✅ Response received: {len(response2.get('response', ''))} characters")
    print(f"📊 Coordinator info: {response2.get('coordinator_info', {})}")
    
    # Test 3: Get session info
    print("\n3️⃣ Testing session info retrieval...")
    session_info = await coordinator.get_session_info(session_id)
    
    print(f"✅ Session info retrieved:")
    print(f"   - Created: {session_info.get('created_at', 'unknown')}")
    print(f"   - Last activity: {session_info.get('last_activity', 'unknown')}")
    print(f"   - Conversation length: {session_info.get('conversation_length', 0)}")
    print(f"   - Memory stats: {session_info.get('memory_stats', {})}")
    
    # Test 4: Get system status
    print("\n4️⃣ Testing system status...")
    system_status = await coordinator.get_system_status()
    
    print(f"✅ System status:")
    print(f"   - Active sessions: {system_status.get('active_sessions', 0)}")
    print(f"   - Available agents: {system_status.get('available_agents', [])}")
    print(f"   - System health: {system_status.get('system_health', 'unknown')}")
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(test_system()) 