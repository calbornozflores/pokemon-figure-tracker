"""--absorb: fold newly-visible back catalogue into state without mailing it."""

from __future__ import annotations

import pytest

from pokemon_figure_tracker import __main__ as entry
from pokemon_figure_tracker import notifier, state
from pokemon_figure_tracker.scraper import ListingItem


@pytest.fixture
def absorb_run(monkeypatch):
    saved: list[dict] = []
    sent: list[str] = []

    def fake_listings(pages=None):
        return {
            code: ListingItem(code, f"Item {code}", "futurerelease", f"https://x/{code}", "")
            for code in ("OLD1", "OLD2", "NEW1")
        }

    monkeypatch.setattr(entry, "fetch_current_listings", fake_listings)
    monkeypatch.setattr(state, "load_state", lambda: {"OLD1": {"first_seen": "2026-07-26"}})
    monkeypatch.setattr(state, "save_state", lambda s: saved.append(s))
    monkeypatch.setattr(entry, "_require_credentials", lambda: ("a@b.c", "pw"))
    monkeypatch.setattr(notifier, "send_email", lambda m, a, p: sent.append(m["Subject"]))
    return saved, sent


def test_absorb_records_everything_and_mails_nothing(absorb_run):
    saved, sent = absorb_run
    assert entry.run(dry_run=False, absorb=True) == 0
    assert sent == []
    assert set(saved[0]) == {"OLD1", "OLD2", "NEW1"}
    assert saved[0]["OLD1"]["first_seen"] == "2026-07-26"  # existing entries untouched


def test_absorb_dry_run_writes_nothing(absorb_run):
    saved, sent = absorb_run
    assert entry.run(dry_run=True, absorb=True) == 0
    assert (saved, sent) == ([], [])


def test_without_absorb_the_same_state_produces_a_digest(absorb_run, monkeypatch):
    saved, sent = absorb_run
    monkeypatch.setattr(entry, "REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(entry, "fetch_product_detail", lambda url, session=None: None)
    assert entry.run(dry_run=False, absorb=False) == 0
    assert sent == ["HLJ Pokemon figures: 2 new listing(s)"]
    assert set(saved[0]) == {"OLD1", "OLD2", "NEW1"}
