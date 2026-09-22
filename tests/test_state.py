from __future__ import annotations

from pokemon_figure_tracker.state import last_find


def test_last_find_picks_newest_and_counts_ties():
    state = {
        "A": {"first_seen": "2026-07-26"},
        "B": {"first_seen": "2026-09-18"},
        "C": {"first_seen": "2026-09-18"},
        "D": {"first_seen": "2026-08-17"},
    }
    assert last_find(state) == ("2026-09-18", 2)


def test_last_find_on_empty_state():
    assert last_find({}) == (None, 0)


def test_last_find_ignores_entries_without_a_date():
    assert last_find({"A": {"name": "x"}, "B": {"first_seen": "2026-01-01"}}) == ("2026-01-01", 1)
