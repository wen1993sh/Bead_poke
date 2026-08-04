from __future__ import annotations

from collections import Counter

from pixel_counter.models import BeadCount, ReviewDiff


def count_from_beads(items: list[BeadCount]) -> dict[str, int]:
    counts = Counter()
    for item in items:
        counts[item.code] += int(item.count)
    return dict(counts)


def reconcile_counts(grid_counts: dict[str, int], summary_counts: dict[str, int]) -> tuple[str, list[ReviewDiff]]:
    if grid_counts == summary_counts:
        return "ok", []

    diffs: list[ReviewDiff] = []
    all_codes = sorted(set(grid_counts) | set(summary_counts))
    for code in all_codes:
        grid_value = grid_counts.get(code)
        summary_value = summary_counts.get(code)
        if grid_value != summary_value:
            diffs.append(ReviewDiff(code=code, grid_count=grid_value, summary_count=summary_value))
    return "review", diffs
