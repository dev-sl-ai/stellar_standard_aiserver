from enum import Enum


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
    SHOW_CONFIRM_INFO = "show_confirm_info"
    SHOW_NAME = "show_name"
    INPUT_NAME = "input_name"
    SHOW_PHONE = "show_phone"
    INPUT_PHONE = "input_phone"
    SHOW_KEYBOARD = "show_keyboard"
    SHOW_NUM_KEYBOARD = "show_num_keyboard"
    SHOW_CONFRIM_YESNO = "show_confirm_yesno"
    SHOW_TRAIN = "show_train"
    SHOW_WEATHER = "show_weather"
    SHOW_TOP = "show_top"
    SHOW_SORRY = "show_sorry"
    SHOW_WAIT = "show_wait"
    TOUCH_ACTION = "touch_action"
    PHONECALL_ACTION = "phonecall_action"
    PHONEEND_ACTION = "phoneend_action"
    CHOOSE_CONTACT = "choose_contact"
    SHOW_BOCHI = "show_bochi"
    SHOW_PET = "show_pet"
    SHOW_CONFIRM_FOR_DENGON = "show_confirm_for_dengon"
    SHOW_PHONE_PAGE = "show_phone_page"
    END_OF_TTS = "end_of_TTS"
    SHOW_POINT_OUT = "show_pointout"
    SET_LANGUAGE = "set_language"
    HIDE_WEBVIEW = "hide_webview"
    SHOW_MAP = "show_map"
    SET_LOCATION = "set_location"

