from datetime import datetime
from typing import Optional

class ContextMemory:
    def __init__(self):
        self.button_id: None
        self.session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.session_end_time: Optional[datetime] = None

        self.memory_log: list = []
        self.workflow_active: bool = True
        self.last_tool_name: Optional[str] = None
    
    def set_button_id(self, button_id: str):
        self.button_id = button_id

    def add_memory(self, memory: str):
        self.memory_log.append(memory)

    def get_memory(self) -> list:
        return self.memory_log

    def clear(self):
        self.__init__()
