"""
Test script to verify room separation functionality.

This test verifies that:
1. Each room has its own separate managers
2. Sessions don't interfere with each other
3. Chat histories are isolated per room
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.room_manager import get_or_create_room, remove_room, get_active_rooms, get_room_count


async def test_room_separation():
    """Test that rooms are properly separated."""
    print("\n=== Testing Room Separation ===\n")

    # Test 1: Create multiple rooms
    print("Test 1: Creating separate rooms for user001 and user002...")
    room1 = await get_or_create_room("user001")
    room2 = await get_or_create_room("user002")

    assert room1.room_id == "user001", "Room1 should have correct room_id"
    assert room2.room_id == "user002", "Room2 should have correct room_id"
    assert room1 != room2, "Rooms should be different instances"
    print("✓ Rooms created with correct IDs")

    # Test 2: Verify managers are separate instances
    print("\nTest 2: Verifying managers are separate instances...")
    assert room1.ws_manager != room2.ws_manager, "WebSocket managers should be different"
    assert room1.session_manager != room2.session_manager, "Session managers should be different"
    assert room1.agent_executor != room2.agent_executor, "Agent executors should be different"
    print("✓ Each room has separate manager instances")

    # Test 3: Verify room_id is stored in ws_manager
    print("\nTest 3: Verifying room_id is stored in WebSocketManager...")
    assert room1.ws_manager.room_id == "user001", "WS manager should have correct room_id"
    assert room2.ws_manager.room_id == "user002", "WS manager should have correct room_id"
    print("✓ WebSocketManager stores room_id correctly")

    # Test 4: Start sessions in both rooms
    print("\nTest 4: Starting sessions in both rooms...")
    room1.session_manager.start_new_session()
    room2.session_manager.start_new_session()

    session1_id = room1.session_manager.active_session
    session2_id = room2.session_manager.active_session

    assert session1_id != session2_id, "Sessions should have different IDs"
    print(f"✓ Room 1 session: {session1_id}")
    print(f"✓ Room 2 session: {session2_id}")

    # Test 5: Update chat history in both rooms
    print("\nTest 5: Testing chat history isolation...")
    room1.session_manager.update_chat_history("Hello from user001", "Response to user001")
    room2.session_manager.update_chat_history("Hello from user002", "Response to user002")

    history1 = room1.session_manager.get_chat_data()["chat_history"]
    history2 = room2.session_manager.get_chat_data()["chat_history"]

    assert len(history1) == 1, "Room 1 should have 1 chat entry"
    assert len(history2) == 1, "Room 2 should have 1 chat entry"
    assert history1[0][0] == "Hello from user001", "Room 1 should have correct message"
    assert history2[0][0] == "Hello from user002", "Room 2 should have correct message"
    print("✓ Chat histories are properly isolated")

    # Test 6: Update user profiles separately
    print("\nTest 6: Testing user profile isolation...")
    room1.user_profile.name = "Alice"
    room2.user_profile.name = "Bob"

    assert room1.user_profile.name == "Alice", "Room 1 should have Alice"
    assert room2.user_profile.name == "Bob", "Room 2 should have Bob"
    print("✓ User profiles are properly isolated")

    # Test 7: Get active rooms
    print("\nTest 7: Testing room registry...")
    active_rooms = get_active_rooms()
    room_count = get_room_count()

    assert "user001" in active_rooms, "user001 should be in active rooms"
    assert "user002" in active_rooms, "user002 should be in active rooms"
    assert room_count == 2, f"Should have 2 active rooms, got {room_count}"
    print(f"✓ Active rooms: {active_rooms}")
    print(f"✓ Room count: {room_count}")

    # Test 8: Remove rooms
    print("\nTest 8: Testing room cleanup...")
    await remove_room("user001")

    remaining_rooms = get_active_rooms()
    assert "user001" not in remaining_rooms, "user001 should be removed"
    assert "user002" in remaining_rooms, "user002 should still exist"
    print("✓ Room removal works correctly")

    # Cleanup
    await remove_room("user002")
    final_count = get_room_count()
    assert final_count == 0, "All rooms should be removed"
    print("✓ All rooms cleaned up")

    print("\n=== All Tests Passed! ===\n")
    print("Summary:")
    print("- Each room has isolated managers (ws_manager, session_manager, agent_executor)")
    print("- Sessions don't interfere with each other")
    print("- Chat histories are kept separate per room")
    print("- User profiles are isolated per room")
    print("- Room registry and cleanup work correctly")
    print("\nThe system is ready for multi-user concurrent access!")


async def test_concurrent_operations():
    """Test concurrent operations on different rooms."""
    print("\n=== Testing Concurrent Operations ===\n")

    async def simulate_user_session(room_id: str, message: str):
        """Simulate a user session."""
        room = await get_or_create_room(room_id)
        room.session_manager.start_new_session()
        room.session_manager.update_chat_history(message, f"Response to {room_id}")
        await asyncio.sleep(0.1)  # Simulate processing time
        history = room.session_manager.get_chat_data()["chat_history"]
        return room_id, len(history), history[0][0]

    # Simulate 3 concurrent users
    tasks = [
        simulate_user_session("user001", "Message from user001"),
        simulate_user_session("user002", "Message from user002"),
        simulate_user_session("user003", "Message from user003"),
    ]

    results = await asyncio.gather(*tasks)

    print("Concurrent session results:")
    for room_id, history_len, first_message in results:
        print(f"  {room_id}: {history_len} messages, first message: '{first_message}'")
        assert history_len == 1, f"{room_id} should have 1 message"

    print("✓ Concurrent operations work correctly")

    # Cleanup
    for room_id in ["user001", "user002", "user003"]:
        await remove_room(room_id)

    print("\n=== Concurrent Test Passed! ===\n")


async def main():
    """Run all tests."""
    try:
        await test_room_separation()
        await test_concurrent_operations()
        print("\n✅ All tests completed successfully!")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
