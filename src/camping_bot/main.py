from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Allow direct execution: `python src/camping_bot/main.py`
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from camping_bot.config import load_jobs
from camping_bot.notifier import Notifier
from camping_bot.runner import JobRunner
from camping_bot.scheduler import build_scheduler
from camping_bot.settings import load_runtime_config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def _serve(config_path: str) -> None:
    runtime = load_runtime_config()
    notifier = Notifier(runtime)
    jobs = load_jobs(config_path)

    runner = JobRunner(runtime, notifier)
    scheduler = build_scheduler(runner, jobs)
    scheduler.start()

    await notifier.send(f"캠핑 예약 봇 시작: jobs={len(jobs)}, dry_run={runtime.dry_run}")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        scheduler.shutdown(wait=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Camping reservation bot")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    args = parser.parse_args()

    asyncio.run(_serve(args.config))


if __name__ == "__main__":
    main()
