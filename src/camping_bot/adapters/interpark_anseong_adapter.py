from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from camping_bot.adapters.base import SiteAdapter
from camping_bot.captcha import get_captcha_solver
from camping_bot.models import SlotResult


class InterparkAnseongAdapter(SiteAdapter):
    """Interpark ticket flow adapter for Anseong맞춤캠핑장.

    Selectors vary over time; pass site-specific selectors via criteria.selectors.
    """

    async def login(self) -> None:
        await self.page.goto(self.base_url, wait_until="domcontentloaded")
        await self._close_optional_popups()

        selectors = self._selectors()
        login_buttons = self._as_list(selectors.get("login_button"))
        if login_buttons:
            await self._click_first_existing(self.page, login_buttons)
            await self.page.wait_for_timeout(600)

        username = self.credentials.get("username")
        password = self.credentials.get("password")
        if not username or not password:
            raise ValueError("Missing credentials.username or credentials.password")

        user_selectors = self._as_list(selectors.get("username_input"))
        pass_selectors = self._as_list(selectors.get("password_input"))
        submit_selectors = self._as_list(selectors.get("submit_login_button"))
        if not (user_selectors and pass_selectors and submit_selectors):
            await self._manual_login_if_enabled("Missing login selectors in criteria.selectors")
            return

        login_ctx = await self._find_context_with_any_selector(user_selectors, timeout_ms=15000)
        if login_ctx is None:
            login_url = str(self.criteria.get("login_url", "")).strip()
            if login_url:
                await self.page.goto(login_url, wait_until="domcontentloaded")
                login_ctx = await self._find_context_with_any_selector(
                    user_selectors, timeout_ms=10000
                )

        if login_ctx is None:
            await self._dump_debug("login_not_found")
            await self._manual_login_if_enabled(
                "Login username input not found: " + " | ".join(user_selectors)
            )
            return

        if not await self._fill_first_existing(login_ctx, user_selectors, username):
            await self._dump_debug("login_user_fill_failed")
            await self._manual_login_if_enabled("Failed to fill username input")
            return

        if not await self._fill_first_existing(login_ctx, pass_selectors, password):
            await self._dump_debug("login_pass_fill_failed")
            await self._manual_login_if_enabled("Failed to fill password input")
            return

        if not await self._click_first_existing(login_ctx, submit_selectors):
            await self._dump_debug("login_submit_failed")
            await self._manual_login_if_enabled("Failed to click submit login button")
            return

        await self.page.wait_for_timeout(1000)

    async def search_slots(self) -> list[SlotResult]:
        await self._close_optional_popups()
        await self._apply_schedule_filters()
        await self._move_to_booking_page()
        await self._handle_anti_bot_text()
        await self._close_optional_popups()

        chosen_site_name = await self._select_deck_site()
        if not chosen_site_name:
            return []

        nights = int(self.criteria.get("nights", 1))
        guests = int(self.criteria.get("guests", 1))
        check_in = self.criteria.get("check_in", datetime.now().strftime("%Y-%m-%d"))

        return [
            SlotResult(
                slot_id=f"interpark-{check_in}-{chosen_site_name}",
                zone=self.criteria.get("preferred_zone", "DECK"),
                site_name=chosen_site_name,
                check_in=check_in,
                nights=nights,
                capacity=max(guests, 1),
            )
        ]

    async def book_slot(self, slot: SlotResult) -> bool:
        _ = slot
        await self._select_discount()
        await self._fill_personal_info()
        await self._select_payment_bank_transfer()
        await self._agree_and_submit()
        return True

    async def _close_optional_popups(self) -> None:
        selectors = self._selectors()
        close_buttons = self._as_list(selectors.get("popup_close_buttons"))
        for close_selector in close_buttons:
            try:
                loc = self.page.locator(close_selector)
                if await loc.count() > 0:
                    await loc.first.click(timeout=1000)
                    await self.page.wait_for_timeout(150)
            except Exception:
                continue

    async def _apply_schedule_filters(self) -> None:
        selectors = self._selectors()
        check_in = self.criteria.get("check_in")
        nights = self.criteria.get("nights")
        guests = self.criteria.get("guests")

        check_in_input = selectors.get("check_in_input")
        nights_select = selectors.get("nights_select")
        guests_select = selectors.get("guests_select")
        search_button = selectors.get("search_button")

        if check_in and check_in_input:
            await self.page.locator(check_in_input).fill(str(check_in))
        if nights and nights_select:
            await self.page.locator(nights_select).select_option(str(nights))
        if guests and guests_select:
            await self.page.locator(guests_select).select_option(str(guests))
        if search_button:
            await self.page.locator(search_button).click()

    async def _move_to_booking_page(self) -> None:
        selectors = self._selectors()
        booking_button = selectors.get("booking_page_button")
        if not booking_button:
            return
        await self.page.locator(booking_button).click()
        await self.page.wait_for_timeout(500)

    async def _handle_anti_bot_text(self) -> None:
        selectors = self._selectors()
        anti_bot_input = selectors.get("anti_bot_input")
        anti_bot_submit = selectors.get("anti_bot_submit")

        if not anti_bot_input:
            return

        solver_mode = str(self.criteria.get("captcha_mode", self.runtime.captcha_mode))
        solver = get_captcha_solver(solver_mode)
        code = await solver.solve("[ANTI-BOT] 화면의 문자를 입력하세요: ")
        if not code:
            raise ValueError("Captcha code is empty")

        await self.page.locator(anti_bot_input).fill(code)
        if anti_bot_submit:
            await self.page.locator(anti_bot_submit).click()

    async def _select_deck_site(self) -> str | None:
        selectors = self._selectors()
        preferred = self.criteria.get("preferred_sites", [])
        item_selector = selectors.get("site_item")
        name_selector = selectors.get("site_name")
        click_selector = selectors.get("site_select_button")

        if not (item_selector and click_selector):
            raise ValueError("Missing site selectors in criteria.selectors")

        items = self.page.locator(item_selector)
        count = await items.count()
        for idx in range(count):
            row = items.nth(idx)
            name = ""
            if name_selector:
                child = row.locator(name_selector)
                if await child.count() > 0:
                    name = (await child.first.inner_text()).strip()
            if preferred and name and name not in preferred:
                continue
            await row.locator(click_selector).first.click()
            return name or f"site-{idx + 1}"

        return None

    async def _select_discount(self) -> None:
        selectors = self._selectors()
        discount = self.criteria.get("discount_value")
        discount_select = selectors.get("discount_select")
        if discount and discount_select:
            await self.page.locator(discount_select).select_option(str(discount))

    async def _fill_personal_info(self) -> None:
        selectors = self._selectors()
        personal = self.criteria.get("personal_info", {})

        birth_input = selectors.get("birth_input")
        car_input = selectors.get("car_number_input")

        if birth_input and personal.get("birth"):
            await self.page.locator(birth_input).fill(str(personal["birth"]))
        if car_input and personal.get("car_number"):
            await self.page.locator(car_input).fill(str(personal["car_number"]))

    async def _select_payment_bank_transfer(self) -> None:
        selectors = self._selectors()
        bank_transfer_radio = selectors.get("bank_transfer_radio")
        bank_select = selectors.get("bank_select")
        bank_value = self.criteria.get("bank_code")

        if bank_transfer_radio:
            await self.page.locator(bank_transfer_radio).click()
        if bank_select and bank_value:
            await self.page.locator(bank_select).select_option(str(bank_value))

    async def _agree_and_submit(self) -> None:
        selectors = self._selectors()
        for agree_selector in self._as_list(selectors.get("agree_checkboxes")):
            box = self.page.locator(agree_selector)
            if await box.count() > 0:
                await box.first.check()

        submit_selector = selectors.get("submit_reservation_button")
        if not submit_selector:
            raise ValueError("Missing submit_reservation_button selector")
        await self.page.locator(submit_selector).click()

    async def _find_context_with_any_selector(
        self,
        selector_candidates: list[str],
        timeout_ms: int,
    ) -> Any | None:
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while asyncio.get_running_loop().time() < deadline:
            pages = list(self.page.context.pages)
            for page in pages:
                for ctx in [page, *page.frames]:
                    for selector in selector_candidates:
                        try:
                            if await ctx.locator(selector).count() > 0:
                                return ctx
                        except Exception:
                            continue
            await asyncio.sleep(0.2)
        return None

    async def _fill_first_existing(self, ctx: Any, selectors: list[str], value: str) -> bool:
        for selector in selectors:
            try:
                loc = ctx.locator(selector)
                if await loc.count() > 0:
                    await loc.first.fill(value)
                    return True
            except Exception:
                continue
        return False

    async def _click_first_existing(self, ctx: Any, selectors: list[str]) -> bool:
        for selector in selectors:
            try:
                loc = ctx.locator(selector)
                if await loc.count() > 0:
                    await loc.first.click()
                    return True
            except Exception:
                continue
        return False

    async def _dump_debug(self, tag: str) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root = Path("logs")
        root.mkdir(parents=True, exist_ok=True)
        screenshot = root / f"{tag}_{stamp}.png"
        html = root / f"{tag}_{stamp}.html"

        try:
            await self.page.screenshot(path=str(screenshot), full_page=True)
        except Exception:
            pass

        try:
            html.write_text(await self.page.content(), encoding="utf-8")
        except Exception:
            pass

    async def _manual_login_if_enabled(self, message: str) -> None:
        if not bool(self.criteria.get("manual_login_fallback", False)):
            raise ValueError(message)
        if self.runtime.headless:
            raise ValueError(
                f"{message} / manual_login_fallback requires HEADLESS=false for bootstrap login"
            )
        print(f"[LOGIN] {message}")
        print("[LOGIN] 브라우저에서 로그인 완료 후 터미널에서 Enter를 누르세요.")
        await asyncio.to_thread(input, "")
        await self.page.wait_for_timeout(500)

    def _as_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]

    def _selectors(self) -> dict:
        selectors = self.criteria.get("selectors", {})
        if not isinstance(selectors, dict):
            return {}
        return selectors
