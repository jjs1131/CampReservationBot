from __future__ import annotations

import os

from dotenv import load_dotenv

from camping_bot.models import RuntimeConfig


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_runtime_config() -> RuntimeConfig:
    load_dotenv()
    return RuntimeConfig(
        dry_run=_to_bool(os.getenv("DRY_RUN"), True),
        headless=_to_bool(os.getenv("HEADLESS"), True),
        timeout_ms=int(os.getenv("TIMEOUT_MS", "15000")),
        captcha_mode=os.getenv("CAPTCHA_MODE", "manual").strip().lower(),
        storage_state_path=(os.getenv("STORAGE_STATE_PATH") or "cfg/storage_state.json"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
    )

