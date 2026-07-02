from datetime import datetime
from typing import Optional
from src.agent.conversation_state import ConversationState

class ContextMemory:
    def __init__(self):
        self.button_id: None
        self.session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.session_end_time: Optional[datetime] = None
        self.conversation_state: str = ConversationState.GATHER_USER_INFO

        self.name: Optional[str] = None
        self.purpose: Optional[str] = None
        self.phone: Optional[str] = None

        self.name_retry: int = 0
        self.purpose_retry: int = 0
        self.phone_retry: int = 0
        self.phone_correct: bool = False

        self.memory_log: list = []
        self.workflow_active: bool = True
        self.last_tool_name: Optional[str] = None
        self.last_faq_query: Optional[str] = None

    def add_memory(self, memory: str):
        self.memory_log.append(memory)

    def get_memory(self) -> list:
        return self.memory_log

    def clear(self):
        self.__init__()
