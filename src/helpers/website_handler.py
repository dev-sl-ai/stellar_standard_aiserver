import time
import asyncio
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.helpers.conf_loader import PHONECALL_URL
from src.helpers.logger import logger
from src.helpers.enums import ActionType
from src.helpers import system_flags

edge_driver_path = "msedgedriver.exe"

async def handle_phonecall_action(ws_manager=None, message_manager=None, room_id=None):
    """
    Handle phone call action with room-specific managers.

    Args:
        ws_manager: WebSocketManager instance for the room
        message_manager: MessageManager instance for the room
        room_id: Room ID for the websocket connection
    """
    loop = asyncio.get_running_loop()
    await asyncio.to_thread(open_selenium_browser, loop, ws_manager, message_manager, room_id)

def open_selenium_browser(loop, ws_manager, message_manager, room_id):
    logger.info("Handling phone call action...")
    logger.info(f"Opened phone call URL: {PHONECALL_URL}")
    options = Options()
    prefs = {
    "profile.default_content_setting_values.media_stream_mic": 1,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Edge(service=EdgeService(edge_driver_path, log_path='NUL'), options=options)
    try:
        driver.get(PHONECALL_URL)
        
        wait = WebDriverWait(driver, 20)
        call_button = wait.until(
            EC.element_to_be_clickable((By.ID, "call-button"))
        )
        
        logger.info("Clicking the call button...")
        call_button.click()
        while True:
            time.sleep(1)
            # logger.info(system_flags.get_phone_call_active())
            if not system_flags.get_phone_call_active():
                logger.info("Phone call ended externally. Exiting call start loop.")
                return
            try: 
                call_button = driver.find_element(By.ID, "call-button")
                button_class = call_button.get_attribute("class")
                if "bg-red-500" in button_class:
                    logger.info("Call started (button is red). Monitoring for call end...")
                    break
            except Exception as e:
                logger.error(f"Error checking call button status: {e}")
                break

        while True:
            time.sleep(1)
            # logger.info(system_flags.get_phone_call_active())
            if not system_flags.get_phone_call_active():
                logger.info("Phone call ended externally. Exiting call monitoring loop.")
                return
            try:
                call_button = driver.find_element(By.ID, "call-button")
                button_class = call_button.get_attribute("class")
                if "bg-green-500" in button_class:
                    system_flags.set_phone_call_active(False)
                    if ws_manager and message_manager and room_id:
                        asyncio.run_coroutine_threadsafe(
                            ws_manager.send_to_client(message_manager.action_message(ActionType.PHONEEND_ACTION.value), room_id),
                            loop
                        )

                    logger.info("Call ended (button is green). Exiting browser...")
                    break
            except Exception as e:
                logger.error(f"Error checking call button status: {e}")
                break
        
    except Exception as e:
        logger.error(f"Error during Selenium operation: {e}")
    finally:
        try:
            logger.info("Clicking call button before quitting browser...")
            call_button = driver.find_element(By.ID, "call-button")
            call_button.click()
            logger.info("Call button clicked successfully before quitting.")
        except Exception as e:
            logger.error(f"Error clicking call button before quitting: {e}")
        driver.quit()
        logger.info("Phone Call Browser closed.")
    