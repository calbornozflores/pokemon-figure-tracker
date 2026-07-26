"""Daily entrypoint: scrape HLJ.com, diff against seen state, email new listings."""

from __future__ import annotations

import argparse
import os
import sys
import time

import requests

from . import notifier, state
from .detail import fetch_product_detail
from .notifier import NewFigure
from .scraper import REQUEST_DELAY_SECONDS, USER_AGENT, fetch_current_listings


def run(dry_run: bool) -> int:
    current = fetch_current_listings()
    print(f"Scraped {len(current)} unique listings across all keywords/pages.")

    seen = state.load_state()

    if not seen:
        for code, item in current.items():
            state.record_seen(seen, code, item.name, item.url)
        subject, text_body, message = notifier.build_baseline_email(len(current))
        print(text_body)
        if not dry_run:
            gmail_address, app_password = _require_credentials()
            notifier.send_email(message, gmail_address, app_password)
            state.save_state(seen)
        else:
            print("[dry-run] Not saving state or sending email.")
        return 0

    new_codes = sorted(code for code in current if code not in seen)
    if not new_codes:
        print("No new listings today.")
        if not dry_run:
            state.save_state(seen)
        return 0

    print(f"Found {len(new_codes)} new listing(s): {', '.join(new_codes)}")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    new_figures: list[NewFigure] = []
    for i, code in enumerate(new_codes):
        item = current[code]
        if i > 0:
            time.sleep(REQUEST_DELAY_SECONDS)
        try:
            detail = fetch_product_detail(item.url, session=session)
        except Exception as exc:  # noqa: BLE001 - keep the run going even if one detail fetch fails
            print(f"  warning: could not fetch detail for {code}: {exc}", file=sys.stderr)
            detail = None

        image_bytes = None
        if item.image_url and not dry_run:
            time.sleep(REQUEST_DELAY_SECONDS)
            try:
                response = session.get(item.image_url, timeout=30)
                response.raise_for_status()
                image_bytes = response.content
            except Exception as exc:  # noqa: BLE001 - a failed image fetch shouldn't drop the item
                print(f"  warning: could not fetch image for {code}: {exc}", file=sys.stderr)
        elif item.image_url:
            print(f"  [dry-run] image available for {code}: {item.image_url}")

        new_figures.append(
            NewFigure(
                code=code,
                name=item.name,
                url=item.url,
                status=item.status,
                brand=detail.brand if detail else None,
                price_jpy=detail.price_jpy if detail else None,
                release_date=detail.release_date if detail else None,
                image_bytes=image_bytes,
            )
        )
        state.record_seen(seen, code, item.name, item.url)

    subject, text_body, message = notifier.build_new_items_email(new_figures)
    print(text_body)

    if dry_run:
        print("[dry-run] Not saving state or sending email.")
        return 0

    gmail_address, app_password = _require_credentials()
    notifier.send_email(message, gmail_address, app_password)
    state.save_state(seen)
    return 0


def _require_credentials() -> tuple[str, str]:
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not gmail_address or not app_password:
        print(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD env vars are required "
            "(unless running with --dry-run).",
            file=sys.stderr,
        )
        sys.exit(1)
    return gmail_address, app_password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and print what would be emailed, without sending mail or writing state.",
    )
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
