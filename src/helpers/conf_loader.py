import yaml
import threading
from . import logger
from src.resource_path import src_path

class ConfigLoader:
    _lock = threading.Lock()

    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_yaml()
        self.current_language = self.config.get("language", "ja")  # Default to Japanese

    def load_yaml(self):
        """Load YAML configuration."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_file}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {self.config_file}: {e}")
            return {}

    def update_language(self, new_language: str):
        """Thread-safe update of language in YAML and server state."""
        with self._lock:
            self.config["language"] = new_language
            self.save_config(self.config)  # Save updated config

            # Update the current language in server state
            self.current_language = new_language

            logger.info(f"言語が変更されました: {new_language}")

    def save_config(self, config_data):
        """Save the given configuration to the YAML file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                yaml.safe_dump(config_data, file, allow_unicode=True)
            logger.info(f"Configuration saved: {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config to {self.config_file}: {e}")

    def get_language(self):
        """Get the current language from memory."""
        return self.current_language


# Initialize Config Loaders
ai_config_loader = ConfigLoader(config_file=src_path("configs/AI_conf.yaml"))
server_config_loader = ConfigLoader(config_file=src_path("configs/server_conf.yaml"))

# Load configurations
ai_config = ai_config_loader.load_yaml()
server_config = server_config_loader.load_yaml()

# Access configurations
AGENT_TOOLS = ai_config.get("tools", {})
MODELS_CONF = ai_config.get("model", {})
DAILOGUE = ai_config.get("dailogue", {})
GREET_MSG = ai_config.get("greeting", {})
DISPLAY_TXT = ai_config.get("display_text", {})
RAG_CONF = ai_config.get("rag", {})

# Public HTTPS origin that serves the WebGL build (nginx TLS host). Used to build
# absolute URLs pushed to the client so they stay same-origin HTTPS (no mixed content).
PUBLIC_BASE_URL = server_config.get("public_base_url", "").rstrip("/")
# Client-side proxy used to render external sites (JMA, Google Maps) in the WebGL webview.
# The target URL is percent-encoded and appended after "target=".
PROXY_URL_BASE = server_config.get("proxy_url_base", "http://127.0.0.1:8989/proxy?target=")
PHONECALL_URL = server_config.get("phonecall_url", "https://153.126.190.186:8000/phone")
