import time
import urllib.request
import urllib.parse
import logging

logger = logging.getLogger(__name__)


# In-memory dedup state for send_alert_rate_limited.
# Key shape: (endpoint_path: str, status_code: int) or any caller-defined tuple.
# Value: epoch seconds of last successful firing.
_last_fmp_alert_at: dict = {}


def send_alert(message: str) -> bool:
    from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")
        return False


def send_alert_rate_limited(
    key: tuple, message: str, min_interval_s: int = 86400
) -> bool:
    """
    Fire send_alert(message) only if (key, now) is more than
    min_interval_s past the last firing for the same key.

    NOTE: dedup state is process-local. A scheduler restart resets
    the dict and the next matching alert fires fresh. This is
    acceptable for the entitlement-failure case — restart-fresh
    alerts are rare and self-explanatory. Do not persist this state
    to DB without an explicit product decision.

    Returns True if alert was sent, False if suppressed by dedup.
    """
    now = time.time()
    last = _last_fmp_alert_at.get(key)
    if last is not None and (now - last) < min_interval_s:
        logger.info(f"Telegram alert suppressed by dedup (key={key})")
        return False
    sent = send_alert(message)
    if sent:
        _last_fmp_alert_at[key] = now
    return sent
