from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic.v1 import BaseModel
from src.api.websocket_manager import WebSocketManager
from src.message_templates.websocket_message_template import WebsocketMessageTemplate, UserProfile
from src.agent.session_manager import ChatSessionManager
from src.agent.context_variables import ContextMemory
from src.llm.intent_classifier import intent_chain, correction_chain
from src.helpers.logger import logger
from src.helpers.enums import ActionType, Mode
from src.helpers.maps import BUTTON_TITLE_MAP
from src.helpers.conf_loader import DAILOGUE, LINE_USER1, LINE_USER2

class ContactToolInput(BaseModel):
    tool_input: str

class BaseContactTool(BaseTool):
    args_schema: Type[BaseModel] = ContactToolInput
    ws_manager: Optional[WebSocketManager] = None
    message_manager: Optional[WebsocketMessageTemplate] = None
    session_manager: Optional[ChatSessionManager] = None
    user_profile: Optional[UserProfile] = None
    context_memory: Optional[ContextMemory] = None
    return_direct: bool = True

    async def handle_timeout(self, *, end_message: str = DAILOGUE["timeout_message"]) -> str:
        await self.send_action_msg(ActionType.SHOW_TOP.value)
        await self.send_action_msg(ActionType.END_SESSION.value)
        self.session_manager.end_session()
        self.context_memory.workflow_active = False
        return end_message

    async def send_chat_action_msg(self, message: str, action: ActionType, param: object = None):
        self.session_manager.update_chat_history("", message)
        await self.ws_manager.send_to_client(
            self.message_manager.chat_action_message(message, action, param),
            self.ws_manager.room_id
        )

    async def send_action_msg(self, action: ActionType):
        await self.ws_manager.send_to_client(self.message_manager.action_message(action), self.ws_manager.room_id)

    async def send_action_msg_with_param(self, action: ActionType, param: object = None):
        await self.ws_manager.send_to_client(self.message_manager.action_message(action, param), self.ws_manager.room_id)

    async def send_chat_msg(self, message: str):
        self.session_manager.update_chat_history("", message)
        await self.ws_manager.send_to_client(self.message_manager.chat_message(message), self.ws_manager.room_id)

    async def send_confirm_action_msg(self, message: str, action: ActionType, param: object = None):
        await self.ws_manager.send_to_client(
            self.message_manager.confirm_action_message(message, action, param),
            self.ws_manager.room_id
        )

    async def is_confirmed_yesno(self, response: str) -> bool:
        result = await intent_chain.ainvoke({"response": response})
        if result.content.strip().lower() == "confirmation":
            return "confirmation"
        elif result.content.strip().lower() == "decline":
            return "decline"
        else:
            return "unknown"
        
    async def is_confirmed_correction(self, response: str) -> bool:
        result = await correction_chain.ainvoke({"response": response})
        if result.content.strip().lower() == "confirmation":
            return "confirmation"
        elif result.content.strip().lower() == "correction":
            return "correction"
        else:
            return "unknown"

    def reload_memory(self):
        self.context_memory = self.session_manager.get_context_memory()
        self.user_profile.name = self.context_memory.name
        self.user_profile.purpose = self.context_memory.purpose
        self.user_profile.contact = self.context_memory.phone
        logger.info(f"ユーザープロフィール再読み込み: {self.context_memory.name}, {self.context_memory.phone}, {self.context_memory.purpose}")

    def get_title_text(self):
        return BUTTON_TITLE_MAP.get(self.context_memory.button_id, "")

    def set_purpose(self):
        if self.context_memory.button_id == "button_4":
            self.context_memory.purpose = BUTTON_TITLE_MAP.get(self.context_memory.button_id, "")
        elif self.context_memory.button_id == "button_2":
            self.context_memory.purpose = "付届けを持ってきた"
        elif self.context_memory.button_id == "button_3":
            self.context_memory.purpose = "設備について"
        self.context_memory.name_retry += 1
            
    def decide_person2contact(self, mode: str, person2contact: list):
        line_ids = []
        if "user2" in person2contact and mode == Mode.HANZAITAKU.value:
            line_ids = LINE_USER1 + LINE_USER2
            logger.info(f"住職・奥様 LINE ID : {line_ids}にメッセージ通信します。")
        else:
            line_ids = LINE_USER1
            logger.info(f"住職 LINE ID : {line_ids[0]}にメッセージ通信します。")
        return line_ids