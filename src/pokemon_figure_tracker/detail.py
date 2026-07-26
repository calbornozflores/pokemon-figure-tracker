"""Fetch and parse a single HLJ.com product detail page for price/brand/release date."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests

from .scraper import USER_AGENT

_PRODUCT_JSON_RE = re.compile(r"products:\s*\[\s*(\{.*?\})\s*\]", re.DOTALL)
_RELEASE_DATE_RE = re.compile(r"Release Date:\s*(\d{4}/\d{2}/\d{2})")


@dataclass
class ProductDetail:
    brand: str | None = None
    price_jpy: int | None = None
    release_date: str | None = None


def fetch_product_detail(url: str, session: requests.Session | None = None) -> ProductDetail:
    session = session or requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    response = session.get(url, timeout=30)
    response.raise_for_status()
    html = response.text

    detail = ProductDetail()

    match = _PRODUCT_JSON_RE.search(html)
    if match:
        try:
            data = json.loads(match.group(1))
            detail.brand = data.get("brand")
            price = data.get("special_price") or data.get("price")
            if price is not None:
                detail.price_jpy = int(price)
        except (json.JSONDecodeError, ValueError):
            pass

    date_match = _RELEASE_DATE_RE.search(html)
    if date_match:
        detail.release_date = date_match.group(1)

    return detail
