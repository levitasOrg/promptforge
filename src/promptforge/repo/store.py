"""Registry of indexed repos — stored at ~/.config/promptforge/repos.json."""

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

STORE_PATH = Path.home() / ".config" / "promptforge" / "repos.json"


@dataclass
class RepoEntry:
    name: str           # alias (e.g. "my-api")
    path: str           # absolute path to the repo root
    graph_dir: str      # absolute path to graphify-out/
    indexed_at: str     # ISO 8601


class RepoStore:
    def __init__(self, store_path: Path = STORE_PATH) -> None:
        self.store_path = store_path

    def load(self) -> list[RepoEntry]:
        if not self.store_path.exists():
            return []
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            return [RepoEntry(**r) for r in data]
        except Exception:
            return []

    def save(self, entries: list[RepoEntry]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps([asdict(e) for e in entries], indent=2),
            encoding="utf-8",
        )

    def add(self, entry: RepoEntry) -> None:
        entries = [e for e in self.load() if e.name != entry.name]
        entries.append(entry)
        self.save(entries)

    def remove(self, name: str) -> None:
        self.save([e for e in self.load() if e.name != name])

    def get(self, name: str) -> RepoEntry | None:
        return next((e for e in self.load() if e.name == name), None)

    def detect_current(self) -> RepoEntry | None:
        """Auto-detect the repo from the current git directory."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                repo_root = result.stdout.strip()
                for e in self.load():
                    if e.path == repo_root:
                        return e
        except Exception:
            pass
        return None

    def resolve(self, name: str | None) -> RepoEntry | None:
        """
        Resolve which repo to use:
          1. If name given → look up by name
          2. Auto-detect from current git dir
          3. If exactly one repo indexed → use it
        """
        if name:
            return self.get(name)
        detected = self.detect_current()
        if detected:
            return detected
        entries = self.load()
        if len(entries) == 1:
            return entries[0]
        return None
