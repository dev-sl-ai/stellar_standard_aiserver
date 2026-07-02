from typing import Optional, Type, Union

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from pydantic.v1 import BaseModel

from src.api.websocket_manager import WebSocketManager
from src.agent.session_manager import ChatSessionManager
from src.helpers.enums import ActionType
from src.message_templates.websocket_message_template import WebsocketMessageTemplate


class ContactPersonToolInput(BaseModel):
    pass


class ContactPersonTool(BaseTool):
    name: str = "contact_person"
    description: str = (
        "担当者に直接繋ぐツール"
    )
    args_schema: Type[BaseModel] = ContactPersonToolInput
    ws_manager: Optional[WebSocketManager] = None
    message_manager: Optional[WebsocketMessageTemplate] = None
    session_manager: Optional[ChatSessionManager] = None
    return_direct: bool = True

    async def contact_person(self):
        action_message = self.message_manager.url_action_message("http://153.126.190.186:8080/contactlist",
            ActionType.SHOW_PHONE_PAGE.value
        )
        await self.ws_manager.send_to_client(action_message, self.ws_manager.room_id)
        return "担当者にお繋ぎしますので、担当者をお選びください。" 

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return self.contact_person()

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        self.session_manager.context.last_tool_name = self.name
        return await self.contact_person()
