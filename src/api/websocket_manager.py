import asyncio
from typing import Optional
from fastapi import WebSocket

from src.helpers import logger
from src.helpers.enums import ActionType
from src.message_templates.websocket_message_template import ActionMessage, ChatActionMessage

unity_clients: dict[str, WebSocket] = {}


class WebSocketManager:
    """WebSocket接続とメッセージ管理を行うクラス（1ルーム1ユーザー、多ルーム対応）"""

    def __init__(self, room_id: Optional[str] = None):
        self.room_id = room_id
        self.response_queue = asyncio.Queue()
        self.waiting_for_response = False
        self.button_id: Optional[str] = None
        self.session_end_event = asyncio.Event()
        self.touch_event = None
        self.location_data = None

    # ====== 基本設定 ======
    def set_button_id(self, button_id: str):
        self.button_id = button_id

    def get_button_id(self) -> Optional[str]:
        return self.button_id

    def clear_button_id(self):
        self.button_id = None

    def set_location_data(self, location_data: dict):
        self.location_data = location_data

    def get_location_data(self) -> Optional[dict]:
        return self.location_data

    # ====== 接続管理 ======
    async def connect(self, websocket: WebSocket, room_id: str):
        """ユーザーごとのroom_idでWebSocket接続を管理。"""
        # 既存の同一room_id接続があれば切断
        if room_id in unity_clients:
            try:
                await unity_clients[room_id].close()
                logger.info(f"既存接続を閉じました: room_id={room_id}")
            except Exception:
                logger.warning(f"room_id={room_id} の既存接続を閉じる際にエラー発生。")

        await websocket.accept()
        unity_clients[room_id] = websocket
        logger.info(f"新規クライアント接続: room_id={room_id}, total_rooms={len(unity_clients)}")

    async def disconnect(self, room_id: str):
        """指定したroom_idの接続を切断し削除。"""
        if room_id in unity_clients:
            try:
                await unity_clients[room_id].close()
            except Exception:
                pass
            del unity_clients[room_id]
            logger.info(f"クライアント切断: room_id={room_id}, 残りルーム数={len(unity_clients)}")

    # ====== メッセージ送信 ======
    async def send_to_client(self, message: object, room_id: str):
        """指定したroom_idにメッセージを送信。"""
        allow_send = (
            self.button_id is not None
            or (isinstance(message, ActionMessage) and message.action_type == ActionType.SHOW_TOP.value)
            or (isinstance(message, ChatActionMessage) and message.action.action_type == ActionType.SHOW_TOP.value)
            or (isinstance(message, ChatActionMessage) and message.action.action_type == ActionType.SHOW_PHONE_PAGE.value)
            or (isinstance(message, ActionMessage) and message.action_type == ActionType.SET_LANGUAGE.value)
        )

        if not allow_send:
            logger.warning(f"[{room_id}] ボタンIDが設定されていません。メッセージ送信をスキップ。")
            return

        ws = unity_clients.get(room_id)
        if not ws:
            logger.warning(f"[{room_id}] アクティブなWebSocketが存在しません。")
            return

        try:
            logger.info(f"[{room_id}] メッセージ送信: {message.__dict__}")
            await ws.send_text(message.to_json())
        except Exception as e:
            logger.error(f"[{room_id}] クライアントへの送信中にエラー: {e}")
            await self.disconnect(room_id)

    # ====== ユーザー応答処理 ======
    def notify_touch(self):
        if self.touch_event and not self.touch_event.is_set():
            self.touch_event.set()

    async def wait_for_user_response(self, timeout: int = 30) -> Optional[str]:
        """ユーザーの応答を指定時間まで待機。"""
        self.waiting_for_response = True
        self.session_end_event = asyncio.Event()
        self.touch_event = asyncio.Event()

        response_task = asyncio.create_task(self.response_queue.get())
        end_session_task = asyncio.create_task(self.session_end_event.wait())
        timeout_task = asyncio.create_task(asyncio.sleep(timeout))
        touch_task = asyncio.create_task(self.touch_event.wait())

        try:
            while True:
                done, _ = await asyncio.wait(
                    [response_task, end_session_task, timeout_task, touch_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if end_session_task in done:
                    logger.info("セッション終了を検出。応答待機を中断。")
                    return None

                if response_task in done:
                    return (await response_task).strip()

                if touch_task in done:
                    self.touch_event.clear()
                    timeout_task.cancel()
                    timeout_task = asyncio.create_task(asyncio.sleep(timeout))
                    touch_task = asyncio.create_task(self.touch_event.wait())

                if timeout_task in done:
                    logger.info("ユーザー応答待機がタイムアウトしました。")
                    return "timeout"

        finally:
            self.waiting_for_response = False
            for t in [response_task, end_session_task, timeout_task, touch_task]:
                if t and not t.done():
                    t.cancel()
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass

    async def receive_message(self, message: str):
        """ユーザーからのメッセージを受信。"""
        if self.waiting_for_response:
            await self.response_queue.put(message)
        else:
            logger.info(f"通常メッセージを処理中: {message}")
