from __future__ import annotations

from collections import Counter
from typing import Iterable

from pixel_counter.models import BeadCount


def merge_beads(items: Iterable[BeadCount]) -> list[BeadCount]:
    counts = Counter()
    for item in items:
        counts[item.code] += int(item.count)
    return [BeadCount(code=code, count=counts[code]) for code in sorted(counts)]


def total_beads(items: Iterable[BeadCount]) -> int:
    return sum(int(item.count) for item in items)
