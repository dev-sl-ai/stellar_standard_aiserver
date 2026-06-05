import asyncio
from src.helpers.enums import ActionType
from src.helpers import logger
from src.helpers.conf_loader import server_config_loader, SHOW_MAP_TIMEOUT, SESSION_TIMEOUT, RAG_TTS_TIMEOUT
from src.helpers.maps import BUTTON_TITLE_MAP
from src.message_templates.websocket_message_template import LanguageData

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

        case ActionType.END_OF_TTS.value:
            ctx = room.session_manager.get_context_memory()
            if ctx and ctx.session_id:
                ctx.is_waiting_rag_tts = False
                if ctx.last_tool_name in {"faq_tool"}:
                    ctx.set_is_show_map_page(True)

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
    await room.ws_manager.send_to_client(room.message_manager.chat_message(bot_response, server_config_loader.get_language()), room_id)

    ctx = room.session_manager.get_context_memory()
    if ctx and ctx.last_tool_name == "faq_tool":
        ctx.is_waiting_rag_tts = True
        await room.ws_manager.send_to_client(
            room.message_manager.action_message(ActionType.SHOW_MAP.value), room_id
        )


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
    room.session_manager.get_context_memory().set_button_id(button_id)
    room.agent_executor.configure_for_button(button_id)
    room.agent_executor.setup(initial_prompt=True)

    greet_message = f"{BUTTON_TITLE_MAP[button_id]} についてですね。\nどのような展示品が目的でしょうか？"
    room.session_manager.update_chat_history(greet_message, "")

    await room.ws_manager.send_to_client(room.message_manager.action_message(ActionType.SHOW_CONVERSATION.value), room_id)
    await room.ws_manager.send_to_client(room.message_manager.chat_message(greet_message, server_config_loader.get_language()), room_id)


async def end_session_from_client(room):
    """End session requested by client."""
    await room.ws_manager.send_to_client(
        room.message_manager.action_message(ActionType.SHOW_ADS_PAGE.value, LanguageData("ja"),),
        room.room_id,
    )
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
    server_config_loader.reset_current_language()  # Reset language to default on session end

def _get_language_instruction(current_language: str) -> str:
    """Add strong language instruction for LLM."""
    return {
        "ja-JP": "【必ず日本語で回答】",
        "en-US": "【YOU MUST RESPOND IN ENGLISH】",
        "zh-CN": "【必须用中文回答】",
        "ko-KR": "【반드시 한국어로 답변】",
        "es-ES": "【DEBES RESPONDER EN ESPAÑOL】",
    }.get(current_language, "【必ず日本語で回答】")

async def receive_with_dynamic_timeout(websocket, room):
    """Receive message with timeout that adapts to room state."""
    start_time = asyncio.get_event_loop().time()
    poll_interval = 1.0  # Check state every second
    
    while True:
        # Get current timeout based on state
        ctx = room.session_manager.context
        if ctx.session_id is not None and ctx.get_is_show_map_page():
            max_timeout = SHOW_MAP_TIMEOUT
        elif ctx.session_id is not None and ctx.is_waiting_rag_tts:
            max_timeout = RAG_TTS_TIMEOUT
        else:
            max_timeout = SESSION_TIMEOUT
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Check if we've exceeded the timeout
        if elapsed >= max_timeout:
            raise asyncio.TimeoutError()
        
        # Wait for message with short polling interval
        remaining = min(poll_interval, max_timeout - elapsed)
        
        try:
            message = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=remaining
            )
            return message
        except asyncio.TimeoutError:
            # Continue polling if not exceeded max timeout
            continue