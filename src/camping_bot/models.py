from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobConfig:
    name: str
    enabled: bool
    adapter: str
    base_url: str
    interval_seconds: int
    credentials: dict[str, str] = field(default_factory=dict)
    criteria: dict[str, Any] = field(default_factory=dict)


@dataclass
class SlotResult:
    slot_id: str
    zone: str
    site_name: str
    check_in: str
    nights: int
    capacity: int


@dataclass
class RuntimeConfig:
    dry_run: bool
    headless: bool
    timeout_ms: int
    captcha_mode: str
    storage_state_path: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None

