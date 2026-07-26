# pokemon-figure-tracker

Daily email digest of new Pokémon **Moncolle** / **Monster Collection** / **Dream Tomica** figure
listings on [HLJ.com](https://www.hlj.com), so you can catch preorders before they sell out.

Runs automatically once a day via GitHub Actions — no server or laptop required — and emails a
digest of newly-listed figures (name, brand, price in JPY, release date, photo, direct link) to
your own Gmail address.

## How it works

1. Scrapes the first 2 pages of HLJ's search results for `pokemon monster`, `moncolle`, and
   `dream tomica pokemon` (sorted newest-first), e.g.
   `https://www.hlj.com/search/?Word=moncolle&Sort=releaseDate+desc&Page=1`.
2. Compares the product codes found against `data/seen_products.json` (committed to this repo).
3. Anything not seen before gets its own product page fetched once for price/brand/release date,
   then all new items are emailed in one digest. Nothing is sent if there's nothing new.
4. The updated `data/seen_products.json` is committed back by the workflow.

## Safety / etiquette

- `robots.txt` on hlj.com has no `Disallow` on `/search/` or product pages, and no crawl-delay —
  verified before building this. The scraper still adds a 1.5s delay between requests, sends an
  identifying `User-Agent`, and only runs once a day (~4 listing pages + a handful of product
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
3. The `.github/workflows/daily-check.yml` workflow runs daily around 8:00 AM Chile time
   (handles both DST states automatically) and can also be triggered manually from the Actions tab
   or with `gh workflow run daily-check.yml`.

## Notes

- First run ever records the current listings as a silent baseline and sends a short
  "tracker initialized" email — it does not dump ~1,400 existing listings on you.
- `data/seen_products.json` only ever contains public product codes/names/URLs — safe for a
  public repo.
