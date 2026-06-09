import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from promptforge.stats.models import RatingRecord, UsageRecord

logger = logging.getLogger(__name__)

LOG_PATH = Path.home() / ".config" / "promptforge" / "usage_log.jsonl"


class UsageLogger:
    def __init__(self, log_path: Path = LOG_PATH) -> None:
        self.log_path = log_path

    def record(self, usage_record: UsageRecord) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(asdict(usage_record), default=str)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def record_rating(self, session_id: str, rating: int) -> None:
        rated_at = datetime.now(tz=timezone.utc).isoformat()
        rec = RatingRecord(session_id=session_id, rating=rating, rated_at=rated_at)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(asdict(rec), default=str)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def load_all(self) -> list[UsageRecord]:
        if not self.log_path.exists():
            return []

        session_records: dict[str, UsageRecord] = {}
        rating_records: list[RatingRecord] = []

        with open(self.log_path, encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    rtype = data.get("record_type", "session")
                    if rtype == "rating":
                        rating_records.append(
                            RatingRecord(
                                session_id=data["session_id"],
                                rating=data["rating"],
                                rated_at=data["rated_at"],
                            )
                        )
                    else:
                        rec = UsageRecord(**{k: v for k, v in data.items() if k != "record_type"})
                        session_records[rec.session_id] = rec
                except Exception as e:
                    logger.warning("Skipping malformed usage log line %d: %s", lineno, e)

        for rr in rating_records:
            if rr.session_id in session_records:
                sr = session_records[rr.session_id]
                sr.rating = rr.rating
                sr.rated_at = rr.rated_at

        return sorted(session_records.values(), key=lambda r: r.timestamp)

    def reset(self, skip_confirmation: bool = False) -> None:
        if not skip_confirmation:
            if not sys.stdin.isatty():
                raise SystemExit("Refusing to reset without --yes in non-interactive mode.")
            records = self.load_all()
            confirm = input(f"This will delete {len(records)} sessions. Type 'yes' to confirm: ")
            if confirm.strip().lower() != "yes":
                return
        if self.log_path.exists():
            self.log_path.unlink()

    def export(self, output_path: Path) -> None:
        records = self.load_all()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in records], f, indent=2, default=str)
