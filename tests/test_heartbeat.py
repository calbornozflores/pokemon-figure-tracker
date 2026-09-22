"""The quiet path: no new listings, so no digest - but a check-in mail on Mondays."""

from __future__ import annotations

import datetime

import pytest

from pokemon_figure_tracker import __main__ as entry
from pokemon_figure_tracker import notifier, state
from pokemon_figure_tracker.scraper import ListingItem

SEEN = {"TKT00001": {"name": "Thing", "url": "https://www.hlj.com/x", "first_seen": "2026-09-18"}}


@pytest.fixture
def quiet_run(monkeypatch):
    """A run where the scrape finds only what state already has. Returns sent subjects."""
    sent: list[str] = []

    def fake_listings(pages=None):
        return {"TKT00001": ListingItem("TKT00001", "Thing", "futurerelease", "https://x", "")}

    monkeypatch.setattr(entry, "fetch_current_listings", fake_listings)
    monkeypatch.setattr(state, "load_state", lambda: dict(SEEN))
    monkeypatch.setattr(state, "save_state", lambda s: None)
    monkeypatch.setattr(entry, "_require_credentials", lambda: ("a@b.c", "pw"))
    monkeypatch.setattr(
        notifier, "send_email", lambda msg, addr, pw: sent.append(msg["Subject"])
    )
    return sent


def _freeze_weekday(monkeypatch, iso: str) -> None:
    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return datetime.date.fromisoformat(iso)

    monkeypatch.setattr(entry, "date", FakeDate)


def test_monday_sends_the_check_in(quiet_run, monkeypatch, capsys):
    _freeze_weekday(monkeypatch, "2026-09-21")  # a Monday
    assert entry.run(dry_run=False) == 0
    assert quiet_run == ["HLJ tracker weekly check-in"]
    out = capsys.readouterr().out
    assert "1 products tracked" in out
    assert "Last new find: 2026-09-18" in out


def test_other_days_send_nothing(quiet_run, monkeypatch):
    _freeze_weekday(monkeypatch, "2026-09-22")  # a Tuesday
    assert entry.run(dry_run=False) == 0
    assert quiet_run == []


def test_dry_run_on_monday_sends_nothing(quiet_run, monkeypatch):
    _freeze_weekday(monkeypatch, "2026-09-21")
    assert entry.run(dry_run=True) == 0
    assert quiet_run == []


def test_heartbeat_body_without_any_recorded_find():
    _, text, message = notifier.build_heartbeat_email(0, 96, None, 0)
    assert "No new find recorded yet." in text
    assert message["Subject"] == "HLJ tracker weekly check-in"
