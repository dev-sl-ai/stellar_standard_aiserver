from datetime import datetime
from src.helpers import logger
from src.helpers.session_logger import write_user_session_log
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

    def end_session(self):
        self.context.session_end_time = datetime.now().replace(microsecond=0)
        logger.info(f"ログ保存してセッション終了: {self.active_session}")

        write_user_session_log(self.context)
        self.clear_history()
        self.context.clear()

    def update_chat_history(self, user_input: str, response: str, history_input: str = None):
        """Append a turn to chat history.

        history_input overrides what gets stored as the "user" side of the
        chat_history tuple fed back to the LLM (e.g. a faq_tool follow-up
        rewritten into a standalone question), so the resolved topic persists
        across turns. The session log always records the raw user_input.
        """
        self.latest_input = user_input
        entry_input = history_input if history_input else user_input
        self.chat_history.append((entry_input, response))
        self.context.add_memory(f"来訪者: {user_input}, アバター: {response}")
        # print(f"Chat history updated: {self.chat_history}")

    def get_chat_data(self):
        return {"chat_history": self.chat_history}
    
    def get_context_memory(self):
        return self.context
