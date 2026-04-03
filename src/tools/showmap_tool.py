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


class ShowMapToolInput(BaseModel):
    pass


class ShowMapTool(BaseTool):
    name: str = "show_map"
    description: str = (
        "展示会の会場マップを表示するツール。"
        "会場の場所・所在地・住所・行き方・アクセス方法を聞かれたとき、または「会場はどこですか」「どこで開催されますか」のような質問に必ず使用してください。"
    )
    args_schema: Type[BaseModel] = ShowMapToolInput
    ws_manager: Optional[WebSocketManager] = None
    message_manager: Optional[WebsocketMessageTemplate] = None
    session_manager: Optional[ChatSessionManager] = None
    return_direct: bool = False

    async def show_map(self):
        action_message = self.message_manager.url_action_message("https://www.google.com/maps/place/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B9%E3%82%B5%E3%83%83%E3%83%9D%E3%83%AD+(%E6%9C%AD%E5%B9%8C%E6%B5%81%E9%80%9A%E7%B7%8F%E5%90%88%E4%BC%9A%E9%A4%A8)/@43.0384178,141.4500115,17z/data=!3m1!4b1!4m6!3m5!1s0x5f0b2b708f0510dd:0x93ef30585119fd05!8m2!3d43.0384178!4d141.4500115!16s%2Fm%2F0k0qzjs?hl=ja&entry=ttu&g_ep=EgoyMDI2MDMyOS4wIKXMDSoASAFQAw%3D%3D",
            ActionType.SHOW_MAP.value
        )
        await self.ws_manager.send_to_client(action_message, self.ws_manager.room_id)
        return "会場はアクセスサッポロです。Googleマップを表示しました。"

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return self.show_map()

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        self.session_manager.context.last_tool_name = self.name
        return await self.show_map()
