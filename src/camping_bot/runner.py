from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

from playwright.async_api import async_playwright

from camping_bot.adapters.registry import get_adapter
from camping_bot.models import JobConfig, RuntimeConfig, SlotResult
from camping_bot.notifier import Notifier


class JobRunner:
    def __init__(self, runtime: RuntimeConfig, notifier: Notifier) -> None:
        self.runtime = runtime
        self.notifier = notifier
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def run_once(self, job: JobConfig) -> None:
        if not job.enabled:
            return

        lock = self._locks[job.name]
        if lock.locked():
            await self.notifier.send(f"[{job.name}] 이전 실행이 아직 진행 중이라 스킵")
            return

        async with lock:
            await self._run_guarded(job)

    async def _run_guarded(self, job: JobConfig) -> None:
        try:
            await self._run(job)
        except Exception as exc:
            await self.notifier.send(f"[{job.name}] 오류: {exc}")

    async def _run(self, job: JobConfig) -> None:
        adapter_cls = get_adapter(job.adapter)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.runtime.headless)
            storage_state = self.runtime.storage_state_path
            state_path = Path(storage_state) if storage_state else None
            if state_path and state_path.exists():
                context = await browser.new_context(storage_state=str(state_path))
            else:
                context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(self.runtime.timeout_ms)

            adapter = adapter_cls(
                page,
                job.base_url,
                job.credentials,
                job.criteria,
                self.runtime,
            )
            await adapter.login()
            if state_path:
                state_path.parent.mkdir(parents=True, exist_ok=True)
                await context.storage_state(path=str(state_path))
            slots = await adapter.search_slots()

            selected = self._pick_slot(slots, job)
            if not selected:
                await self.notifier.send(f"[{job.name}] 조건에 맞는 자리 없음")
                await browser.close()
                return

            if self.runtime.dry_run:
                await self.notifier.send(
                    f"[{job.name}] DRY_RUN: 예약 가능 자리 발견 -> {selected.site_name} ({selected.zone})"
                )
                await browser.close()
                return

            ok = await adapter.book_slot(selected)
            if ok:
                await self.notifier.send(
                    f"[{job.name}] 예약 성공: {selected.site_name} / {selected.check_in} / {selected.nights}박"
                )
            else:
                await self.notifier.send(f"[{job.name}] 예약 시도 실패")

            await browser.close()

    def _pick_slot(self, slots: list[SlotResult], job: JobConfig) -> SlotResult | None:
        if not slots:
            return None

        guests = int(job.criteria.get("guests", 1))
        preferred_zones = set(job.criteria.get("preferred_zones", []))

        candidates = [slot for slot in slots if slot.capacity >= guests]
        if preferred_zones:
            preferred = [slot for slot in candidates if slot.zone in preferred_zones]
            if preferred:
                return preferred[0]
        return candidates[0] if candidates else None

