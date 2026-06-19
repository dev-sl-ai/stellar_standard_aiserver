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
from src.helpers.url_proxy import proxy_url
from src.message_templates.websocket_message_template import WebsocketMessageTemplate


class ShowMapToolInput(BaseModel):
    pass


class ShowMapTool(BaseTool):
    name: str = "show_map"
    description: str = (
        "ステラリン会社のマップを表示するツール。"
    )
    args_schema: Type[BaseModel] = ShowMapToolInput
    ws_manager: Optional[WebSocketManager] = None
    message_manager: Optional[WebsocketMessageTemplate] = None
    session_manager: Optional[ChatSessionManager] = None
    return_direct: bool = True

    async def show_map(self):
        maps_url = "https://www.google.com/maps/place/%E5%AF%8C%E5%A3%AB%E5%B7%9D%E3%83%93%E3%83%AB/@35.6911746,139.7379521,16z/data=!4m6!3m5!1s0x60188d0b8cf39fb7:0xb09b2be9c9dae438!8m2!3d35.6914891!4d139.7397957!16s%2Fg%2F11fj3tclmz?hl=ja&entry=ttu&g_ep=EgoyMDI1MTAxMy4wIKXMDSoASAFQAw%3D%3D"
        action_message = self.message_manager.url_action_message(
            proxy_url(maps_url),
            ActionType.SHOW_MAP.value
        )
        await self.ws_manager.send_to_client(action_message, self.ws_manager.room_id)
        return "本社は、〒102-0074 東京都千代田区九段南4丁目3-4 九段富士川ビル3階にあります。JR中央線「市ヶ谷駅」から徒歩6分、または地下鉄有楽町線・南北線・都営新宿線「市ヶ谷駅」A3出口から徒歩3分の場所です。ステラリンク東京本社の地図を表示しました。"

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
