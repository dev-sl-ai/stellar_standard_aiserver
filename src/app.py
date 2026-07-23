import asyncio
import json
import os
import sys
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


class NoCacheStaticFiles(StaticFiles):
    """Serve static assets with no-cache headers so edited files (e.g.
    contact_list.xlsx, list.js, style.css) are always re-fetched by the webview."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

from src.api.unity_log_api import router as unity_log_router
from src.api.log_download_api import router as log_download_router
from src.api.azure_token_api import router as azure_token_router
from src.helpers import logger
from src.helpers.conf_loader import GREET_MSG, server_config_loader
from src.helpers.enums import ActionType, MessageType
from src.helpers.translation_util import localize_from_ja
from src.llm.llm_manager import is_valid_japanese_phone_number
from src.message_templates.websocket_message_template import LanguageData
from src.room_manager import get_or_create_room, remove_room, get_active_rooms

app = FastAPI()

# WebGL build is served from a different origin than this API, so the browser
# requires CORS headers (and OPTIONS preflight) for POST /api/unity-log.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(unity_log_router)
app.include_router(log_download_router)
app.include_router(azure_token_router)

# Serve static files
base_dir = os.path.dirname(__file__)
app.mount("/static", NoCacheStaticFiles(directory=os.path.join(base_dir, "static")), name="static")


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


@app.get("/logs", response_class=HTMLResponse)
def read_logs():
    html_path = Path(base_dir) / "static" / "logs.html"
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
    import signal
    import threading
    logger.info("Server is shutting down from /shutdown route!")
    # Clean up all active rooms on this worker
    active_rooms = get_active_rooms()
    for room_id in active_rooms:
        await remove_room(room_id)

    def delayed_exit():
        time.sleep(0.5)
        if sys.platform == "win32":
            # No process groups / multi-worker mode on Windows (see runner.py) —
            # this process is the only one running, so exiting it is enough.
            os._exit(0)
        else:
            # SIGTERM the whole process group (uvicorn master + every worker), not
            # just this worker's PID via os._exit(0) — otherwise multi-worker mode
            # (WEB_CONCURRENCY > 1) only tears down whichever worker handled this
            # request and the rest keep serving traffic.
            os.killpg(os.getpgid(0), signal.SIGTERM)

    threading.Thread(target=delayed_exit).start()
    return {"status": "shutting down"}


# === WebSocket Endpoint ===
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """Each connected client has its own room_id."""
    # Get or create room-specific managers
    room = await get_or_create_room(room_id)

    await room.ws_manager.connect(websocket, room_id)

    # Send initial language setting
    await room.ws_manager.send_to_client(
        room.message_manager.action_message(
            ActionType.SET_LANGUAGE.value,
            LanguageData(language=server_config_loader.get_language()),
        ),
        room_id,
    )

    idle_timeout_count = 0
    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=120)
                idle_timeout_count = 0
            except asyncio.TimeoutError:
                idle_timeout_count += 1
                logger.info(f"[{room_id}] Connection idle timeout ({idle_timeout_count}).")
                ctx = room.session_manager.get_context_memory()
                if ctx and ctx.session_id:
                    await room.ws_manager.send_to_client(
                        room.message_manager.chat_message(localize_from_ja("セッションがタイムアウトしました。")),
                        room_id,
                    )
                    await end_session(room)

                # No traffic for two consecutive idle periods (~240s) after the
                # session ended means the client is gone without a clean close
                # (network drop, tab killed, laptop slept) — the browser never
                # sent a close frame, so WebSocketDisconnect below would never
                # fire on its own. Close explicitly so `finally: remove_room`
                # reclaims this room's memory instead of it lingering forever.
                if idle_timeout_count >= 2:
                    logger.info(f"[{room_id}] No client activity after idle timeout; closing connection.")
                    break
                continue

            if message == "exit":
                break

            data = room.message_manager.parse_message(json.loads(message))
            if not (data.type == MessageType.ACTION.value and data.action_type == ActionType.TOUCH_ACTION.value):
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
                    if room.session_manager.get_context_memory().last_tool_name == "weather_info" or room.session_manager.get_context_memory().last_tool_name == "contact_person" or room.session_manager.get_context_memory().last_tool_name == "show_map":
                        await room.ws_manager.send_to_client(
                            room.message_manager.action_message(ActionType.HIDE_WEBVIEW.value),
                            room_id
                        )
                        room.session_manager.get_context_memory().last_tool_name = None
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

    except WebSocketDisconnect:
        logger.info(f"[{room_id}] Client disconnected.")
        await end_session(room)
    finally:
        await remove_room(room_id)


# === Logic Handlers ===
async def process_action(action_type: str, params, room):
    """Process action with room-specific managers."""
    room_id = room.room_id
    match action_type:
        case ActionType.START_SESSION.value:
            await start_new_session_and_greet(room)

        case ActionType.END_SESSION.value:
            room.ws_manager.session_end_event.set()
            await end_session_from_client(room)

        case ActionType.SET_LANGUAGE.value:
            if params.language:
                server_config_loader.update_language(params.language)
                logger.debug(f"[{room_id}] Language set to {params.language}")

        case ActionType.SET_LOCATION.value:
            logger.debug(f"[{room_id}] Set Location: {params.city}")
            room.ws_manager.set_location_data(params)

        case ActionType.INPUT_NAME.value:
            if params.name:
                room.user_profile.name = params.name
                ctx = room.session_manager.get_context_memory()
                ctx.name = params.name
                room.session_manager.update_chat_history(params.name, "")

        case ActionType.INPUT_PHONE.value:
            if params.contact:
                room.user_profile.contact = params.contact
                ctx = room.session_manager.get_context_memory()
                ctx.contact = params.contact
                room.session_manager.update_chat_history(params.contact, "")

        case ActionType.SHOW_CONFIRM_INFO.value:
            ctx = room.session_manager.get_context_memory()

            if params.purpose and params.purpose.strip():
                room.user_profile.purpose = params.purpose
                ctx.purpose = params.purpose

            if params.name and params.name.strip():
                room.user_profile.name = params.name
                ctx.name = params.name

            if params.contact and params.contact.strip():
                if await is_valid_japanese_phone_number(params.contact):
                    room.user_profile.contact = params.contact
                    ctx.phone = params.contact
                    ctx.phone_correct = True
                else:
                    ctx.phone_correct = False
                    logger.error(f"[{room_id}] Invalid phone format: {params.contact}")

        case ActionType.END_OF_TTS.value:
            ctx = room.session_manager.get_context_memory()
            if ctx and ctx.session_id:
                if ctx.last_tool_name in ("weather_info", "contact_person", "show_map"):
                    await room.ws_manager.send_to_client(
                        room.message_manager.action_message(ActionType.SHOW_POINT_OUT.value), room_id
                    )


async def process_chat(user_input: str, room):
    """Process chat input and generate response for the given room."""
    room_id = room.room_id
    room.session_manager.update_chat_history(user_input, "")
    lang_instr = _get_language_instruction(server_config_loader.get_language())

    response = await room.agent_executor.run(
        {
            "input": f"{lang_instr}\n{user_input}",
            "chat_history": room.session_manager.get_chat_data()["chat_history"],
        }
    )

    bot_response = ""
    if isinstance(response, dict):
        bot_response = response.get("output", "")
    elif response is not None:
        bot_response = getattr(response, "output", "")
    bot_response = (bot_response or "").strip("「」")

    if not bot_response:
        logger.info(f"[{room_id}] Empty bot response.")
        return

    room.session_manager.update_chat_history(user_input, bot_response)
    await room.ws_manager.send_to_client(room.message_manager.chat_message(bot_response), room_id)


async def process_chat_action(message: str, action_type: str, params, room):
    """Process chat action with room-specific managers."""
    if action_type == ActionType.START_SESSION.value:
        room.ws_manager.set_button_id(message)
    await process_action(action_type, params, room)


async def start_new_session_and_greet(room):
    """Start a new session and send greeting for the given room."""
    room_id = room.room_id
    room.session_manager.start_new_session()
    button_id = room.ws_manager.get_button_id()
    room.session_manager.get_context_memory().button_id = button_id
    room.agent_executor.configure_for_button(button_id)
    room.agent_executor.setup(initial_prompt=True)

    greet_message = GREET_MSG[f"greet_{server_config_loader.get_language()}"]
    room.session_manager.update_chat_history(greet_message, "")
    await room.ws_manager.send_to_client(room.message_manager.chat_message(greet_message), room_id)


async def end_session_from_client(room):
    """End session requested by client."""
    room_id = room.room_id
    end_message = GREET_MSG[f"end_{server_config_loader.get_language()}"]
    room.session_manager.update_chat_history(end_message, "")
    await room.ws_manager.send_to_client(room.message_manager.chat_message(end_message), room_id)

    room.session_manager.end_session()
    room.ws_manager.clear_button_id()
    room.ws_manager.waiting_for_response = False


async def end_session(room):
    """End session and notify client."""
    room_id = room.room_id
    room.session_manager.end_session()
    await room.ws_manager.send_to_client(
        room.message_manager.action_message(ActionType.END_SESSION.value), room_id
    )
    room.ws_manager.clear_button_id()
    room.ws_manager.waiting_for_response = False


def _get_language_instruction(current_language: str) -> str:
    """Add strong language instruction for LLM."""
    return {
        "ja-JP": "【必ず日本語で回答】",
        "en-US": "【YOU MUST RESPOND IN ENGLISH】",
        "zh-CN": "【必须用中文回答】",
        "ko-KR": "【반드시 한국어로 답변】",
        "es-ES": "【DEBES RESPONDER EN ESPAÑOL】",
    }.get(current_language, "【必ず日本語で回答】")
