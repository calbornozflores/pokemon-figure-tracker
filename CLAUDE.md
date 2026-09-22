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
  already-seen product codes (committed back to the repo by the GitHub Actions workflow), plus
  `last_find()` for the heartbeat email.
- `src/pokemon_figure_tracker/notifier.py` — builds and sends the digest, baseline and weekly
  heartbeat emails via Gmail SMTP.
- `src/pokemon_figure_tracker/__main__.py` — orchestrates: scrape → diff against state → email
  new items → save state. Flags: `--dry-run` (no email, no state write), `--absorb` (record
  everything scraped as seen without emailing), `--pages N` (override scrape depth).
- `.github/workflows/daily-check.yml` — a single unguarded `0 11 * * *` cron, runs the tracker
  with `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` secrets, commits the state file.

## Design decisions worth not re-litigating

- **Nothing clock-dependent gates the scrape.** The workflow used to fire two crons and let only
  the one landing on exactly 08:00 Chile proceed. GitHub dispatches scheduled runs hours late, so
  from 2026-08-27 to 2026-09-21 the guard skipped *every* run — ~50 green six-second runs that
  never scraped — and 21 new listings were never emailed. One cron, no guard, imprecise arrival
  time. Do not reintroduce a time check to make the email land at a nicer hour.
- **Search sorts by `rss desc` ("Date Added"), not `releaseDate desc`.** Release-date order buries
  any item whose release is near-term or already past below hundreds of far-future preorders,
  outside the scraped pages; since seen state is never revisited, such an item is missed
  *permanently*, not just late. Found this way: ML-28 Mega Zygarde (release 2026/08/31).
- **`PAGES_PER_KEYWORD = 2` is deliberate, not conservative.** Under Date Added sort it means the
  ~48 most recently listed items per keyword. Going deeper reaches the 2024 back catalogue —
  items new to the tracker but not new listings (4 pages turned a 21-item digest into 87). Use
  `--pages` for a one-off deeper catch-up, and `--absorb` if a config change widens the window
  for good.
- **Monday always sends mail.** Otherwise "nothing new" and "never ran" are indistinguishable
  from the inbox, which is exactly why the outage above went unnoticed for a month.
- **An empty *first* search page raises.** An empty page 2+ just means the keyword ran out of
  results (`dream tomica pokemon` fits on one page) and stops paging.
- There is no Moncolle/Pokémon name filter — whatever the three keywords return is tracked, so
  bath salts and plushes turn up in digests. Left loose on purpose: for a don't-miss-a-preorder
  tracker, a false positive costs a glance and a false negative costs a preorder.

## Conventions

Follows the root `CLAUDE.md`: Python 3.12, `uv` for all dependency management, never `pip`.

## Testing

`uv run pytest` — offline unit tests. The parser ones run against
`tests/fixtures/hlj_moncolle_search.html`, a real search page saved 2026-09-21; refresh it if
HLJ's markup changes, and keep the item-count assertion in step with it.

`uv run python -m pokemon_figure_tracker --dry-run` scrapes live HLJ.com and prints what would be
emailed, without sending mail or writing `data/seen_products.json`. Per the root `CLAUDE.md`, this
live run — not the unit suite — is what confirms a scraper change works.

Email can only be sent from CI: the Gmail secrets live in GitHub Actions and there is no local
`.env` (and no dotenv loading). Verify a mail-path change with `gh workflow run daily-check.yml`.
