from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from camping_bot.models import JobConfig
from camping_bot.runner import JobRunner


def build_scheduler(runner: JobRunner, jobs: list[JobConfig]) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    for job in jobs:
        if not job.enabled:
            continue
        scheduler.add_job(
            runner.run_once,
            "interval",
            args=[job],
            seconds=job.interval_seconds,
            id=job.name,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=5,
        )

    return scheduler

