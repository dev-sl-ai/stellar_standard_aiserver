from urllib.parse import quote

from src.helpers.conf_loader import PROXY_URL_BASE


def proxy_url(target_url: str) -> str:
    """Wrap an external URL so it renders through the client-side proxy.

    The proxy expects the target URL percent-encoded after "target=", e.g.
    https://www.google.com/ -> http://127.0.0.1:8989/proxy?target=https%3A%2F%2Fwww.google.com%2F
    """
    if not target_url:
        return target_url
    return f"{PROXY_URL_BASE}{quote(target_url, safe='')}"
