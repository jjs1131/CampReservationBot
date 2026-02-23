from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod


class CaptchaSolver(ABC):
    @abstractmethod
    async def solve(self, prompt: str) -> str:
        raise NotImplementedError


class ManualCaptchaSolver(CaptchaSolver):
    async def solve(self, prompt: str) -> str:
        return (await asyncio.to_thread(input, prompt)).strip()


class FixedCaptchaSolver(CaptchaSolver):
    """Test helper solver. Reads code from env var CAPTCHA_FIXED_CODE."""

    async def solve(self, prompt: str) -> str:
        _ = prompt
        return os.getenv("CAPTCHA_FIXED_CODE", "").strip()


def get_captcha_solver(mode: str) -> CaptchaSolver:
    selected = (mode or "manual").strip().lower()
    if selected == "fixed":
        return FixedCaptchaSolver()
    return ManualCaptchaSolver()
