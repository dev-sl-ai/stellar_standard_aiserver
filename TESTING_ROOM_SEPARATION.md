# Testing Room Separation

## Overview
This guide shows how to test that user001 and user002 have completely separate rooms with isolated managers.

## What Was Changed

### Room-Specific Architecture
Each room (user001, user002, etc.) now has:
- **Separate WebSocketManager** - own connection state
- **Separate SessionManager** - own chat history
- **Separate AgentExecutor** - own AI agent instance
- **Separate UserProfile** - own user data

### Files Modified
1. **src/room_manager.py** (NEW) - Manages per-room instances
2. **src/app.py** - Updated to use room-specific managers
3. **src/api/websocket_manager.py** - Added room_id tracking
4. **src/tools/** - Updated to pass room_id parameter
5. **src/main.py** - Deprecated (managers moved to room-specific)

## Testing Steps

### Prerequisites
1. Make sure your server is running on port 8080
2. You have two test clients ready:
   - `unit_test/test_client1.py` (connects as user001)
   - `unit_test/test_client2.py` (connects as user002)

### Test Procedure

#### Step 1: Start the Server
```bash
# In Terminal 1
cd c:\Myat\Avatar\standard_aiserver
python -m uvicorn src.app:app --host 0.0.0.0 --port 8080 --reload
```

#### Step 2: Connect Client 1 (user001)
```bash
# In Terminal 2
cd c:\Myat\Avatar\standard_aiserver
python unit_test/test_client1.py
```

You should see:
- "Connected to WebSocket server."
- Session started for user001

#### Step 3: Connect Client 2 (user002)
```bash
# In Terminal 3
cd c:\Myat\Avatar\standard_aiserver
python unit_test/test_client2.py
```

You should see:
- "Connected to WebSocket server."
- Session started for user002

#### Step 4: Send Different Messages from Each Client

**In Terminal 2 (user001):**
```
You: Hello, I am user001
```

**In Terminal 3 (user002):**
```
You: Hello, I am user002
```

#### Step 5: Verify Isolation

**Expected Behavior:**
- Each client receives responses only to their own messages
- user001's chat history does NOT include user002's messages
- user002's chat history does NOT include user001's messages
- Sessions remain separate even when both are active simultaneously

**What to Check:**
1. Both clients can chat independently at the same time
2. Messages sent by user001 are NOT seen by user002
3. Messages sent by user002 are NOT seen by user001
4. Each user has their own session state

### Test Scenarios

#### Scenario 1: Concurrent Sessions
1. Start session on both clients
2. Send messages simultaneously from both
3. Verify each gets their own responses

#### Scenario 2: Session Isolation
1. user001: "My name is Alice"
2. user002: "My name is Bob"
3. Ask each agent "What is my name?"
4. user001 should get "Alice", user002 should get "Bob"

#### Scenario 3: Tool Usage
1. user001: "Show me the weather"
2. user002: "Show me the map"
3. Verify tools send messages to the correct client

#### Scenario 4: Disconnect and Reconnect
1. Disconnect user001 (type "exit")
2. Verify user002 continues working normally
3. Reconnect user001
4. Verify it starts a fresh session

## Server Logs to Monitor

Check server logs for:
```
Initializing RoomManager for room: user001
Initializing RoomManager for room: user002
[user001] WebSocket message: ...
[user002] WebSocket message: ...
```

Each room should have separate log prefixes showing isolation.

## Success Criteria

✅ Both clients connect without conflicts
✅ Each client has isolated chat history
✅ Sessions don't interfere with each other
✅ Tools send messages to correct client only
✅ Room cleanup works when client disconnects
✅ No cross-contamination of user data

## Troubleshooting

### Issue: "Connection refused"
- Make sure server is running on port 8080
- Check firewall settings

### Issue: "Messages getting mixed up"
- Check server logs for room_id tracking
- Verify each tool call includes room_id parameter

### Issue: "Session state shared between users"
- Check that RoomManager creates separate instances
- Verify get_or_create_room returns different objects

## Architecture Verification

You can verify the architecture in code:

```python
# In Python REPL while server is running
import sys
sys.path.append('c:\\Myat\\Avatar\\standard_aiserver')

from src.room_manager import get_active_rooms, get_room_count

# After clients connect
print(get_active_rooms())  # Should show ['user001', 'user002']
print(get_room_count())    # Should show 2
```

## Next Steps

After successful testing:
1. Test with more than 2 concurrent users
2. Load test with 10+ simultaneous connections
3. Monitor memory usage for potential leaks
4. Test session persistence across reconnections

## Notes

- Each room loads its own FAISS index (you'll see duplicate loading in logs)
- This is expected and ensures complete isolation
- Memory usage will scale with number of concurrent users
- Consider implementing connection limits if needed
