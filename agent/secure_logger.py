import logging
import re
import os

SENSITIVE_PATTERNS = [
    r"(secret[_-]?key|password|token|secret)\s*[:=]\s*\S+",
    r"(AZURE_CLIENT_SECRET|AWS_SECRET_ACCESS_KEY)\s*[:=]\s*\S+",
    r"github_pat_[A-Za-z0-9_]+",
    r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
]

class SecureFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        for pattern in SENSITIVE_PATTERNS:
            msg = re.sub(pattern, "[MASKED]", msg, flags=re.IGNORECASE)
        return msg

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = SecureFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    return logger

def mask_cost_data(data: dict) -> dict:
    safe = {}
    for key, value in data.items():
        if key in ("source", "period", "total_usd"):
            safe[key] = value
        elif key == "services":
            safe[key] = f"[{len(value)} services]"
        elif key == "daily":
            safe[key] = f"[{len(value)} days]"
        elif key == "recommendations":
            safe[key] = f"[{len(value)} recommendations]"
        else:
            safe[key] = value
    return safe
