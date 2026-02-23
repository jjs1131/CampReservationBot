from __future__ import annotations

from pathlib import Path

import yaml

from camping_bot.models import JobConfig


def load_jobs(config_path: str) -> list[JobConfig]:
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    jobs = []
    for item in raw.get("jobs", []):
        jobs.append(
            JobConfig(
                name=item["name"],
                enabled=bool(item.get("enabled", True)),
                adapter=item["adapter"],
                base_url=item["base_url"],
                interval_seconds=int(item.get("interval_seconds", 30)),
                credentials=item.get("credentials", {}),
                criteria=item.get("criteria", {}),
            )
        )
    return jobs

