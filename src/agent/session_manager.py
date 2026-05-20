from pathlib import Path
from datetime import datetime
from src.helpers import logger
from src.helpers.session_logger import (
    write_user_session_log,
)
from src.agent.context_variables import ContextMemory

class ChatSessionManager:
    """Manages chat sessions and history with contextual memory."""

    def __init__(self):
        self.active_session = None
        self.chat_history = []
        self.session_counter = {}
        self.context = ContextMemory()
        self.latest_input = None

    def _generate_session_id(self):
        now = datetime.now().replace(microsecond=0)
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")

        if date_str not in self.session_counter:
            self.session_counter[date_str] = 1
        else:
            self.session_counter[date_str] += 1

        count = self.session_counter[date_str]
        return f"session_{date_str}_{time_str}_{count}"

    def clear_history(self):
        self.chat_history = []

    def start_new_session(self):

        if self.context.session_id:
            self.context.session_end_time = datetime.now().replace(microsecond=0)
            write_user_session_log(self.context)
            logger.info(f"前回のセッションログを保存しました: {self.context.session_id}")
        
        self.active_session = self._generate_session_id()
        self.clear_history()
        self.context.clear()
        self.context.session_id = self.active_session
        self.context.session_start_time = datetime.now().replace(microsecond=0)
        logger.info(f"セッション開始: {self.active_session}")
        # capture_image(self.active_session)
        # logger.info(f"画像キャプチャ完了")

    def end_session(self):
        self.context.session_end_time = datetime.now().replace(microsecond=0)
        logger.info(f"ログ保存してセッション終了: {self.active_session}")
 
        write_user_session_log(self.context)
        self.clear_history()
        self.context.clear()

    def update_chat_history(self, user_input: str, response: str):
        self.latest_input = user_input
        self.chat_history.append((user_input, response))
        self.context.add_memory(f"来訪者: {user_input}, アバター: {response}")
        # print(f"Chat history updated: {self.chat_history}")

    def get_chat_data(self):
        return {"chat_history": self.chat_history}
    
    def get_context_memory(self):
        return self.context
    
    def line_images_delete(self):
        # 画像削除処理
        try:
            line_images_dir = Path(__file__).resolve().parent.parent / "line_images"
            if line_images_dir.exists():
                deleted = 0
                for file in line_images_dir.glob("*.*"):
                    if file.is_file():
                        file.unlink()
                        deleted += 1
                logger.info(f"line_images フォルダの画像を {deleted} 件削除しました。")
            else:
                logger.warning("line_images フォルダが見つかりませんでした。")
        except Exception as e:
            logger.error(f"画像削除中にエラー発生: {e}")
