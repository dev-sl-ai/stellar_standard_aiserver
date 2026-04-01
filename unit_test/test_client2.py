import asyncio
import websockets
import json

# Global variable to store websocket connection
websocket_connection = None


async def websocket_client():
    """Function to receive messages from the server."""
    global websocket_connection
    uri = "ws://localhost:8080/ws/user002"  # Your WebSocket server URL

    try:
        async with websockets.connect(uri) as websocket:
            websocket_connection = websocket  # Store connection
            print("✅ Connected to WebSocket server.")

            await send_action("set_location", params={"city": "Tokyo", "region": "Tokyo", "lat":35.6762, "lon":139.6503,
                             "prefecture":'東京都'})

            await send_chat_action("button_1","start_session")
            # Start message listener in background
            asyncio.create_task(listen_to_server(websocket))

            # Start sending user input in parallel
            await send_user_input(websocket)

    except Exception as e:
        print(f"❌ Connection error: {e}")


async def listen_to_server(websocket):
    """Continuously listen for messages from the WebSocket server."""
    try:
        while True:
            response = await websocket.recv()  # Receive message
            data = json.loads(response)
            if "message" in data:
                print(f"\n💬 Server: {data['message']}\nYou: ", end="")
            else:
                print(f"\n⚠️ Unknown message: {data}\nYou: ", end="")
    except websockets.exceptions.ConnectionClosed:
        print("❌ WebSocket connection closed. Reconnecting...")
    except Exception as e:
        print(f"⚠️ Error receiving message: {e}")


async def send_user_input(websocket):
    """Continuously send user input to the WebSocket server."""
    while True:
        user_input = await asyncio.to_thread(input, "You: ")  # Non-blocking input
        if user_input != "":
            if user_input.lower() == "exit":
                print("👋 Goodbye! Closing connection.")
                await websocket.close()
                break
            else:
                await send_message(user_input)

async def send_action(action_type: str, params: dict = None):
    """Send an action to the WebSocket server."""
    global websocket_connection
    if websocket_connection:
        try:
            payload = {
                "type": "action",
                "action_type": action_type,
                "params": params or {}
            }
            await websocket_connection.send(json.dumps(payload))
        except Exception as e:
            print(f"⚠️ Error sending action: {e}")
    else:
        print("⚠️ WebSocket connection is not established. Cannot send action.")

async def send_chat_action(message: str, action_type: str, params: dict = None):
    """Send a chat action to the WebSocket server."""
    global websocket_connection
    if websocket_connection:
        try:
            payload = {
                "type": "chat_action",
                "message": message,
                "action": {
                    "action_type": action_type,
                    "params": params or {}
                }
            }
            await websocket_connection.send(json.dumps(payload))
        except Exception as e:
            print(f"⚠️ Error sending chat action: {e}")
    else:
        print("⚠️ WebSocket connection is not established. Cannot send chat action.")

async def send_message(message: str):
    """Send a message to the WebSocket server."""
    global websocket_connection
    if websocket_connection:
        try:
            await websocket_connection.send(json.dumps({"type": "chat", "message": message}))
        except Exception as e:
            print(f"⚠️ Error sending message: {e}")
    else:
        print("⚠️ WebSocket connection is not established. Cannot send message.")


async def run_client():
    """Run the WebSocket client."""
    await websocket_client()


if __name__ == "__main__":
    asyncio.run(run_client())
