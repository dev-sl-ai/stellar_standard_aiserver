from enum import Enum


class Mode(Enum):
    ZAITAKU = "在宅モード"
    HANZAITAKU = "半在宅モード"
    FUZAI = "不在モード"


class MessageType(Enum):
    CHAT = "chat"
    ACTION = "action"
    CHAT_ACTION = "chat_action"
    CONFIRM_ACTION = "confirm_action"
    URL_ACTION = "url_action"


class ActionType(Enum):
    START_SESSION = "start_session"
    END_SESSION = "end_session"
    SHOW_CONVERSATION = "show_conversation"
    SHOW_TOP = "show_top"
    TOUCH_ACTION = "touch_action"
    END_OF_TTS = "end_of_TTS"
    SHOW_POINT_OUT = "show_pointout"
    SET_LANGUAGE = "set_language"
    SHOW_MAP = "show_map"
    SET_LOCATION = "set_location"

