from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class BeadCount:
    code: str
    count: int


@dataclass(slots=True)
class ReviewDiff:
    code: str
    grid_count: int | None = None
    summary_count: int | None = None


@dataclass(slots=True)
class ParseResult:
    id: str
    name: str
    image: str
    template: str
    grid_rows: int
    grid_cols: int
    beads: list[BeadCount] = field(default_factory=list)
    total: int = 0
    confidence: float = 0.0
    status: str = "error"
    warnings: list[str] = field(default_factory=list)
    reviewed: bool = False
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    diffs: list[ReviewDiff] = field(default_factory=list)
    source_version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["beads"] = [asdict(item) for item in self.beads]
        payload["diffs"] = [asdict(item) for item in self.diffs]
        return payload

    @classmethod
    def now_reviewed(cls, **kwargs: Any) -> str:
        return datetime.now(timezone.utc).isoformat()
