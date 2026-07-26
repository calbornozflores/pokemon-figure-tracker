# CLAUDE.md — pokemon-figure-tracker

Daily-scheduled scraper + emailer that watches HLJ.com for newly listed Pokémon Moncolle /
Monster Collection figures. See `README.md` for setup, safety notes, and secrets.

## Layout

- `src/pokemon_figure_tracker/scraper.py` — fetches + parses HLJ search-result listing pages
  (product code, name, status, URL) from hidden `en_name_<CODE>` / `item_status_<CODE>` inputs
  and `item-img-wrapper` links.
- `src/pokemon_figure_tracker/detail.py` — fetches a single product page, extracts the inline
  `products: [ {...} ]` JS object (brand/price) and the `Release Date: YYYY/MM/DD` line via regex.
- `src/pokemon_figure_tracker/state.py` — loads/saves `data/seen_products.json`, the record of
  already-seen product codes (committed back to the repo by the GitHub Actions workflow).
- `src/pokemon_figure_tracker/notifier.py` — builds and sends the digest email via Gmail SMTP.
- `src/pokemon_figure_tracker/__main__.py` — orchestrates: scrape → diff against state → email
  new items → save state. Supports `--dry-run` (no email sent, no state written).
- `.github/workflows/daily-check.yml` — cron trigger (guarded to ~8am Chile time across DST),
  runs the tracker with `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` secrets, commits the state file.

## Conventions

Follows the root `CLAUDE.md`: Python 3.12, `uv` for all dependency management, never `pip`.

## Testing

`uv run python -m pokemon_figure_tracker --dry-run` scrapes live HLJ.com and prints what would be
emailed, without sending mail or writing `data/seen_products.json`.
