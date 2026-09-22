"""Parser tests against a real HLJ search page saved on 2026-09-21.

The parser is the part that can break silently: HLJ restructures the page, every
selector misses, and the run stays green while reporting nothing. The fixture is the
guard against that.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pokemon_figure_tracker.scraper import (
    PAGES_PER_KEYWORD,
    SEARCH_KEYWORDS,
    SORT_ORDER,
    _parse_listing_page,
    _search_url,
    fetch_current_listings,
)

FIXTURE = Path(__file__).parent / "fixtures" / "hlj_moncolle_search.html"


@pytest.fixture(scope="module")
def parsed() -> dict:
    return _parse_listing_page(FIXTURE.read_text(encoding="utf-8"))


def test_parses_every_item_on_the_page(parsed):
    assert len(parsed) == 24


def test_item_fields(parsed):
    fig = parsed["TKT06886"]
    assert fig.name == "MonColle Mega Delphox"
    assert fig.status == "futurerelease"
    assert fig.url == "https://www.hlj.com/moncolle-mega-delphox-tkt06886"
    assert fig.image_url.startswith("https://")


def test_the_items_that_went_unreported_all_parse(parsed):
    # The five listings that prompted the fix, plus the box set alongside them.
    for code in ("TKT06886", "TKT07530", "TKT05926", "TKT05780", "TKT06528", "TTA11115"):
        assert parsed[code].name
        assert parsed[code].url.startswith("https://www.hlj.com/")


def test_hyphenated_variant_code_resolves():
    # Variant codes contain their own hyphen, so slug matching must take the longest
    # trailing segment rather than splitting on "-".
    html = (
        '<input id="en_name_BANO938160-1P" class="en_name" hidden value="Bath Popping Vol.2">'
        '<input id="item_status_BANO938160-1P" class="en_name" hidden value="futurerelease">'
        '<a class="item-img-wrapper" href="/bath-popping-bano938160-1p">'
        '<img src="//www.hlj.com/productthumbs/ban/x.jpg"/></a>'
    )
    items = _parse_listing_page(html)
    assert set(items) == {"BANO938160-1P"}
    assert items["BANO938160-1P"].image_url == "https://www.hlj.com/productthumbs/ban/x.jpg"


def test_noimage_placeholder_is_dropped():
    html = (
        '<input id="en_name_TKT00001" class="en_name" hidden value="Thing">'
        '<a class="item-img-wrapper" href="/thing-tkt00001">'
        '<img src="//www.hlj.com/static/noimage.png"/></a>'
    )
    assert _parse_listing_page(html)["TKT00001"].image_url == ""


class _FakeSession:
    """Serves the fixture for the pages listed in ``pages``, an empty page otherwise."""

    headers: dict = {}

    def __init__(self, pages=(1,)):
        self.pages = pages
        self.requested: list[str] = []

    def get(self, url, timeout=None):
        self.requested.append(url)
        page = int(url.rsplit("Page=", 1)[1])
        body = FIXTURE.read_text(encoding="utf-8") if page in self.pages else "<html></html>"

        class Response:
            text = body

            def raise_for_status(self) -> None:
                pass

        return Response()


def test_empty_first_page_is_a_hard_failure():
    # A layout change must go red, not quietly report nothing forever.
    with pytest.raises(RuntimeError, match="parsed 0 listings"):
        fetch_current_listings(session=_FakeSession(pages=()))


def test_short_keyword_stops_paging_without_failing(monkeypatch):
    # "dream tomica pokemon" fits on one page; running out of results is not an error,
    # and the remaining pages of that keyword are not requested.
    monkeypatch.setattr("pokemon_figure_tracker.scraper.REQUEST_DELAY_SECONDS", 0)
    session = _FakeSession(pages=(1,))
    items = fetch_current_listings(session=session)
    assert len(items) == 24
    assert [u for u in session.requested if "Page=3" in u] == []
    assert len(session.requested) == 2 * len(SEARCH_KEYWORDS)


def test_search_url_sorts_by_date_added():
    url = _search_url("dream tomica pokemon", 3)
    # "Date Added", not "Release Date" - see SORT_ORDER's comment in scraper.py.
    assert "Sort=rss+desc" in url
    assert "Word=dream+tomica+pokemon" in url
    assert "Page=3" in url
    assert SORT_ORDER == "rss desc"


def test_page_window_covers_the_outage_that_prompted_the_fix():
    # Under "Date Added" sort this is the ~48 most recently listed items per keyword.
    # The 26-day outage left 21 unreported, all inside the top 24 of one keyword.
    assert PAGES_PER_KEYWORD * 24 >= 21 * 2


def test_pages_override_beats_the_default(monkeypatch):
    monkeypatch.setattr("pokemon_figure_tracker.scraper.REQUEST_DELAY_SECONDS", 0)
    session = _FakeSession(pages=(1, 2, 3, 4))
    fetch_current_listings(session=session, pages=1)
    assert len(session.requested) == len(SEARCH_KEYWORDS)
    assert all("Page=1" in url for url in session.requested)
