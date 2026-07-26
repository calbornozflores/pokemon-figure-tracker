"""Fetch and parse HLJ.com search-result listing pages."""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "pokemon-figure-tracker/0.1 "
    "(personal, non-commercial daily monitor; contact c.albornoz.flores@gmail.com)"
)

SEARCH_KEYWORDS = ["pokemon monster", "moncolle"]
PAGES_PER_KEYWORD = 2
REQUEST_DELAY_SECONDS = 1.5

BASE_URL = "https://www.hlj.com"
SEARCH_URL = "https://www.hlj.com/search/"


NO_IMAGE_MARKER = "noimage.png"


@dataclass
class ListingItem:
    code: str
    name: str
    status: str
    url: str
    image_url: str = ""


def _search_url(keyword: str, page: int) -> str:
    return f"{SEARCH_URL}?Word={keyword.replace(' ', '+')}&Sort=releaseDate+desc&Page={page}"


def _parse_listing_page(html: str) -> dict[str, ListingItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: dict[str, dict] = {}

    for inp in soup.find_all("input", class_="en_name"):
        field_id = inp.get("id", "")
        value = (inp.get("value") or "").strip()
        if field_id.startswith("en_name_"):
            code = field_id[len("en_name_"):]
            items.setdefault(code, {})["name"] = value
        elif field_id.startswith("item_status_"):
            code = field_id[len("item_status_"):]
            items.setdefault(code, {})["status"] = value

    # Product codes (from en_name_<CODE>) can themselves contain hyphens for variant
    # items (e.g. "BANO938160-1P"), so match by longest trailing slug segment rather
    # than splitting the slug into single tokens.
    codes_by_length = sorted(items, key=len, reverse=True)
    for a in soup.find_all("a", class_="item-img-wrapper"):
        href = a.get("href", "")
        if not href:
            continue
        slug = href.rstrip("/").split("/")[-1].lower()
        for code in codes_by_length:
            code_lower = code.lower()
            if slug == code_lower or slug.endswith("-" + code_lower):
                items[code]["url"] = BASE_URL + href
                img = a.find("img")
                img_src = (img.get("src") or "").strip() if img else ""
                if img_src and NO_IMAGE_MARKER not in img_src.lower():
                    if img_src.startswith("//"):
                        img_src = "https:" + img_src
                    elif img_src.startswith("/"):
                        img_src = BASE_URL + img_src
                    items[code]["image_url"] = img_src
                break

    return {
        code: ListingItem(
            code=code,
            name=fields.get("name", ""),
            status=fields.get("status", ""),
            url=fields.get("url", ""),
            image_url=fields.get("image_url", ""),
        )
        for code, fields in items.items()
        if fields.get("name") and fields.get("url")
    }


def fetch_current_listings(session: requests.Session | None = None) -> dict[str, ListingItem]:
    """Scrape the first PAGES_PER_KEYWORD pages of each SEARCH_KEYWORDS query.

    Returns a dict of product code -> ListingItem, deduped across keywords.
    """
    session = session or requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    all_items: dict[str, ListingItem] = {}
    first_request = True
    for keyword in SEARCH_KEYWORDS:
        for page in range(1, PAGES_PER_KEYWORD + 1):
            if not first_request:
                time.sleep(REQUEST_DELAY_SECONDS)
            first_request = False

            response = session.get(_search_url(keyword, page), timeout=30)
            response.raise_for_status()
            all_items.update(_parse_listing_page(response.text))

    return all_items
