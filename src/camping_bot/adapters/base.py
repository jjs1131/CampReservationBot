from __future__ import annotations

from abc import ABC, abstractmethod

from playwright.async_api import Page

from camping_bot.models import RuntimeConfig, SlotResult


class SiteAdapter(ABC):
    def __init__(
        self,
        page: Page,
        base_url: str,
        credentials: dict[str, str],
        criteria: dict,
        runtime: RuntimeConfig,
    ) -> None:
        self.page = page
        self.base_url = base_url
        self.credentials = credentials
        self.criteria = criteria
        self.runtime = runtime

    @abstractmethod
    async def login(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search_slots(self) -> list[SlotResult]:
        raise NotImplementedError

    @abstractmethod
    async def book_slot(self, slot: SlotResult) -> bool:
        raise NotImplementedError

