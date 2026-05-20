import asyncio
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.helpers import logger
from src.helpers.logic_handler import *
from src.helpers.enums import ActionType, MessageType

from src.message_templates.websocket_message_template import LanguageData
from src.room_manager import get_or_create_room, remove_room, get_active_rooms

app = FastAPI()

# Serve static files
base_dir = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = Path(base_dir) / "static" / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/contactlist", response_class=HTMLResponse)
def contact_list():
    html_path = Path(base_dir) / "static" / "namelist.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/phone", response_class=HTMLResponse)
def read_phone():
    html_path = Path(base_dir) / "static" / "phone.html"
    return html_path.read_text(encoding="utf-8")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server is shutting down!")
    # Clean up all active rooms
    active_rooms = get_active_rooms()
    for room_id in active_rooms:
        await remove_room(room_id)


@app.post("/shutdown")
async def shutdown():
    import threading
    logger.info("Server is shutting down from /shutdown route!")
    # Clean up all active rooms
    active_rooms = get_active_rooms()
    for room_id in active_rooms:
        await remove_room(room_id)

    def delayed_exit():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=delayed_exit).start()
    return {"status": "shutting down"}


# === WebSocket Endpoint ===
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """Each connected client has its own room_id."""
    # Get or create room-specific managers
    room = await get_or_create_room(room_id)

    await room.ws_manager.connect(websocket, room_id)

    try:
        while True:
            try:
                message = await receive_with_dynamic_timeout(websocket, room)
            
                if message == "exit":
                    break

                data = room.message_manager.parse_message(json.loads(message))
                is_action = data.type == MessageType.ACTION.value
                is_touch = data.action_type == ActionType.TOUCH_ACTION.value
                is_end_tts = data.action_type == ActionType.END_OF_TTS.value

                if not (is_action and (is_touch or is_end_tts)):
                    logger.info(f"[{room_id}] WebSocket message: {data.__dict__}")

                # Handle waiting-for-response state
                if room.ws_manager.waiting_for_response:
                    ctx = room.session_manager.get_context_memory()
                    if ctx and ctx.session_id:
                        if data.type == MessageType.CHAT.value:
                            await room.ws_manager.receive_message(data.message)
                            continue
                        if data.type == MessageType.ACTION.value and data.action_type == ActionType.TOUCH_ACTION.value:
                            room.ws_manager.notify_touch()
                            continue

                # === Handle Message Types ===
                if data.type == MessageType.CHAT.value:
                    if room.session_manager.get_context_memory().session_id is not None:
                        asyncio.create_task(process_chat(data.message, room))

                elif data.type == MessageType.ACTION.value:
                    if room.session_manager.get_context_memory().session_id is not None or data.action_type == ActionType.START_SESSION.value or data.action_type == ActionType.SET_LANGUAGE.value or data.action_type == ActionType.SET_LOCATION.value:
                        asyncio.create_task(process_action(data.action_type, data.params, room)) 

                elif data.type == MessageType.CHAT_ACTION.value:
                    if room.session_manager.get_context_memory().session_id is not None or data.action.action_type == ActionType.START_SESSION.value:
                        asyncio.create_task(
                            process_chat_action(
                                data.message, data.action.action_type, data.action.params, room
                            )
                        )
            
            except asyncio.TimeoutError:
                logger.info(f"[{room_id}] Connection idle timeout.")

    except WebSocketDisconnect:
        logger.info(f"[{room_id}] Client disconnected.")
        await end_session(room)
    finally:
        await remove_room(room_id)

