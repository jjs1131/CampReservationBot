from __future__ import annotations

from camping_bot.adapters.base import SiteAdapter
from camping_bot.adapters.interpark_anseong_adapter import InterparkAnseongAdapter
from camping_bot.adapters.mock_adapter import MockAdapter

ADAPTERS: dict[str, type[SiteAdapter]] = {
    "mock": MockAdapter,
    "interpark_anseong": InterparkAnseongAdapter,
}


def get_adapter(name: str) -> type[SiteAdapter]:
    adapter_cls = ADAPTERS.get(name)
    if not adapter_cls:
        available = ", ".join(sorted(ADAPTERS))
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return adapter_cls
