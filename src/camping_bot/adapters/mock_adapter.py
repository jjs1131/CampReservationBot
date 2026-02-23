from __future__ import annotations

from datetime import datetime

from camping_bot.adapters.base import SiteAdapter
from camping_bot.models import SlotResult


class MockAdapter(SiteAdapter):
    async def login(self) -> None:
        # 실제 사이트에서는 로그인 페이지 이동/입력/제출 처리
        await self.page.goto("https://example.com")

    async def search_slots(self) -> list[SlotResult]:
        check_in = self.criteria.get("check_in", "2026-01-01")
        nights = int(self.criteria.get("nights", 1))
        guests = int(self.criteria.get("guests", 2))

        # 분 단위로 가용성 변화를 흉내내는 샘플 데이터
        minute = datetime.utcnow().minute
        available = minute % 2 == 0

        if not available:
            return []

        return [
            SlotResult(
                slot_id=f"mock-{minute}",
                zone="A",
                site_name="Mock Camp A-12",
                check_in=check_in,
                nights=nights,
                capacity=max(guests, 4),
            ),
            SlotResult(
                slot_id=f"mock-{minute}-b",
                zone="RIVER",
                site_name="Mock Camp River-2",
                check_in=check_in,
                nights=nights,
                capacity=max(guests, 2),
            ),
        ]

    async def book_slot(self, slot: SlotResult) -> bool:
        # 실제 사이트에서는 예약 버튼 클릭/확정 페이지 검증
        _ = slot
        return True

