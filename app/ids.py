# app/ids.py
import time
import logging
from app.config import CONFIG

rate_buckets = {}  # addr -> list[timestamps]


def check_rate(addr: tuple) -> bool:
    now = time.time()
    bucket = rate_buckets.setdefault(addr, [])
    bucket.append(now)
    cutoff = now - CONFIG.WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    return len(bucket) <= CONFIG.MAX_MSG_PER_WINDOW


def is_suspicious(msg: str) -> bool:
    msg_lower = msg.lower()
    matched = any(term in msg_lower for term in CONFIG.SUSPICIOUS_TERMS)
    if matched:
        # Fix: previously this was only logged when KICK_ON_SUSPICIOUS was
        # True, so detection was silent by default. Now always logged.
        logging.warning(f"Suspicious content detected: {msg[:200]!r}")
    return matched


def clear_rate_bucket(addr: tuple):
    rate_buckets.pop(addr, None)
