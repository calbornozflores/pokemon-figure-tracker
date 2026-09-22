# pokemon-figure-tracker

Daily email digest of new Pokémon **Moncolle** / **Monster Collection** / **Dream Tomica** figure
listings on [HLJ.com](https://www.hlj.com), so you can catch preorders before they sell out.

Runs automatically once a day via GitHub Actions — no server or laptop required — and emails a
digest of newly-listed figures (name, brand, price in JPY, release date, photo, direct link) to
your own Gmail address.

## How it works

1. Scrapes the first 2 pages of HLJ's search results for `pokemon monster`, `moncolle`, and
   `dream tomica pokemon`, sorted by **Date Added** (HLJ's `Sort=rss desc`), e.g.
   `https://www.hlj.com/search/?Word=moncolle&Sort=rss+desc&Page=1`. That is ~48 most-recently-
   listed items per keyword. Sorting by release date instead (as this did until Sept 2026) hides
   any item whose release is near-term or already past behind hundreds of far-future preorders.
2. Compares the product codes found against `data/seen_products.json` (committed to this repo).
3. Anything not seen before gets its own product page fetched once for price/brand/release date,
   then all new items are emailed in one digest. Nothing is sent if there's nothing new —
   except on Mondays, when a short check-in email goes out regardless (see Notes).
4. The updated `data/seen_products.json` is committed back by the workflow.

## Safety / etiquette

- `robots.txt` on hlj.com has no `Disallow` on `/search/` or product pages, and no crawl-delay —
  verified before building this. The scraper still adds a 1.5s delay between requests, sends an
  identifying `User-Agent`, and only runs once a day (6 listing pages + a handful of product
  pages, only for genuinely new items).
- No login, no purchasing, no automation beyond reading public pages.
- You should still skim HLJ's Terms of Service yourself if you have concerns — this project only
  reflects a robots.txt check, not a legal review.

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

### Local test run (no email sent, no state written)

```bash
uv run python -m pokemon_figure_tracker --dry-run
```

### Local real run

Copy `.env.example` to `.env`, fill in `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` (a
[Google App Password](https://myaccount.google.com/apppasswords), requires 2FA on the account),
then:

```bash
export $(cat .env | xargs)
uv run python -m pokemon_figure_tracker
```

### Automated daily runs (GitHub Actions)

1. Push this repo to GitHub (public repo works fine — nothing sensitive is stored).
2. Add two repository secrets (Settings → Secrets and variables → Actions):
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
   ```bash
   gh secret set GMAIL_ADDRESS
   gh secret set GMAIL_APP_PASSWORD
   ```
3. The `.github/workflows/daily-check.yml` workflow runs daily on a single `0 11 * * *` cron —
   07:00 or 08:00 Chile time depending on DST, plus however late GitHub dispatches it. It can also
   be triggered manually from the Actions tab or with `gh workflow run daily-check.yml`.

   There is deliberately **no** step that checks the local time before scraping. There used to be
   one, pinned to exactly 08:00 Chile; because GitHub dispatches scheduled runs hours late, it
   skipped every run from 2026-08-27 to 2026-09-21 while still reporting success, and 21 new
   listings were never emailed.

## Notes

- First run ever records the current listings as a silent baseline and sends a short
  "tracker initialized" email — it does not dump ~1,400 existing listings on you.
- **Mondays send a check-in email** even with nothing new (items tracked, date of the last new
  find). A quiet day and a day the workflow never ran look identical from the inbox, which is how
  a month of skipped runs went unnoticed; now a silent week is itself the alarm.
- **After adding a search keyword or raising `PAGES_PER_KEYWORD`,** run
  `uv run python -m pokemon_figure_tracker --absorb` once. The wider window exposes back
  catalogue that is new to the tracker but not newly listed; `--absorb` records it as seen
  without emailing, so the next digest is real listings only.
- `--pages N` overrides the pages-per-keyword depth for one run — useful for a deliberate
  deeper catch-up after a known long outage.
- A first search page that parses to zero items raises and fails the run, rather than quietly
  reporting "nothing new" forever if HLJ restructures its HTML.
- `data/seen_products.json` only ever contains public product codes/names/URLs — safe for a
  public repo.
