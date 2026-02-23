from __future__ import annotations

import logging

import httpx

from camping_bot.models import RuntimeConfig

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self._token = runtime.telegram_bot_token
        self._chat_id = runtime.telegram_chat_id

    async def send(self, message: str) -> None:
        logger.info(message)
        if not self._token or not self._chat_id:
            return

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": message}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

