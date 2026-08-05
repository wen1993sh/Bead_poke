from __future__ import annotations

from collections import Counter

from pixel_counter.models import BeadCount, ReviewDiff


def count_from_beads(items: list[BeadCount]) -> dict[str, int]:
    counts = Counter()
    for item in items:
        counts[item.code] += int(item.count)
    return dict(counts)


def reconcile_counts(
    grid_counts: dict[str, int],
    summary_counts: dict[str, int],
) -> tuple[str, list[ReviewDiff]]:
    """Reconcile grid-OCR counts against summary-OCR counts.

    Strategy:
      - Summary OCR provides the verified CODE LIST (more reliable)
      - Grid OCR provides per-cell COUNTS (each cell counted once)
      - Status is "ok" when all summary codes are found in grid
      - Count differences are flagged in diffs but do not block "ok"
    """
    grid_codes = set(grid_counts)
    summary_codes = set(summary_counts)

    # Build diffs for transparency
    diffs: list[ReviewDiff] = []
    all_codes = sorted(grid_codes | summary_codes)
    for code in all_codes:
        gv = grid_counts.get(code)
        sv = summary_counts.get(code)
        if gv != sv:
            diffs.append(ReviewDiff(code=code, grid_count=gv, summary_count=sv))

    if not grid_codes:
        return "error", diffs

    if not summary_codes:
        return "review", diffs

    # All summary-verified codes are present in grid → OK
    missing_from_grid = summary_codes - grid_codes
    if not missing_from_grid:
        return "ok", diffs

    return "review", diffs
