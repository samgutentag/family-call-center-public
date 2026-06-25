import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def send_notification(title, message, url=None, url_title=None, timeout=10):
    """POST a Pushover message. Returns True on send, False if unconfigured.

    Raises on HTTP error — callers must wrap in try/except so a notification
    failure never breaks the calling request.
    """
    if not (Config.PUSHOVER_TOKEN and Config.PUSHOVER_USER):
        logger.info("Pushover not configured; skipping: %s", title)
        return False

    payload = {
        "token": Config.PUSHOVER_TOKEN,
        "user": Config.PUSHOVER_USER,
        "title": title,
        "message": message,
    }
    if url:
        payload["url"] = url
    if url_title:
        payload["url_title"] = url_title

    resp = requests.post(PUSHOVER_URL, data=payload, timeout=timeout)
    resp.raise_for_status()
    logger.info("Pushover sent: %s", title)
    return True
