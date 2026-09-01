# Peblo TV

A miniature of the Peblo TV pipeline: an internal CMS for content editors,
a FastAPI + Postgres backend, a publish job that builds a catalogue file,
and a colorful, playful browse UI for kids.

```
CMS (React) ──► API (FastAPI + Postgres) ──► publish job ──► catalogue.json
                                                                     │
                                              Viewer UI (React) ◄────┘
```

## Quick start

```bash
cp .env.example .env   # defaults work as-is for local dev
docker-compose up --build
```

- **Viewer** (kids' browse UI): http://localhost:5173
- **CMS** (internal editor tool): http://localhost:5174
  - editor: `editor@peblo.tv` / `editor123`
  - admin (can publish): `admin@peblo.tv` / `admin123`
- **API**: http://localhost:8000 (docs at `/docs`, health at `/health`)

## Running Components Individually

If you prefer to run the components individually without Docker:

### 1. Run the API (Backend)

```bash
cd backend

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Run the CMS (Frontend)

```bash
cd cms
npm install
npm run dev
```

### 3. Run the Viewer (Frontend)

```bash
cd viewer
npm install
npm run dev
```

### 🔑 CMS Login Credentials

If you are testing the CMS, use these accounts:
- **Editor**: `editor@peblo.tv` / `editor123`
- **Admin** (can publish): `admin@peblo.tv` / `admin123`

---

On first boot, the API container runs migrations, seeds ~95 episodes across
8 shows from `data/seed_shows.json`, and runs an initial publish attempt.
This uses the **real** `reference.json` / `seed_shows.json` / test artwork
provided with the assignment (`data/assets/`) — not a synthetic stand-in.

**The initial publish is expected to fail.** The real seed data has a
genuine defect: one published episode ("The Midnight Market", part of
*Discover India with Moti*) has no thumbnail artwork. The seed log prints
exactly this via the validation report, e.g.:

```
[seed] initial publish blocked — this is expected: the seed data has
a deliberately broken published episode. Log in to the CMS as admin@peblo.tv,
open Publish, fix what's listed (e.g. upload the missing thumbnail), and
publish again.
  - published_episode_missing_required_artwork: 1
      · Discover India with Moti S1E4 (en) — The Midnight Market: Missing thumbnail artwork.
```

To fix it and publish: log into the CMS as `admin@peblo.tv`, open **Shows**,
find *Discover India with Moti*, open the affected episode's row, upload any
640×360 image as its thumbnail (the assignment's own `assets/thumb_good.jpg`
works, or use the CMS's live artwork validation to try a bad one first —
`assets/thumb_tiny.jpg`, `poster_wrong_ratio.jpg`, and `banner_too_big.png`
are all included specifically to fail validation with a readable message).
Then go to **Publish** and click publish — it now succeeds (7 shows, 84
episode-language rows). I verified this exact flow end-to-end against the
real fixture files before packaging this.

The seed data also has one duplicate `(content_group, language)` pair,
which the seed loader rejects on import (logged, not silently dropped) —
that's the other deliberate imperfection the brief mentions.

## Repo layout

```
backend/    FastAPI + SQLAlchemy + Alembic + pytest
cms/        React + TS + TanStack Query — internal editor tool
viewer/     React + TS — public kids' browse UI
data/       reference.json, seed_shows.json, assets/ — the real assignment files
.github/    CI workflow
```

## Decisions & trade-offs

**Categories are a list, not one.** The real seed data has shows with
several categories each (e.g. *Discover India with Moti* is
`india, learning, travel`). `Show.categories` is a JSON array column;
`ShowCreate`/`ShowUpdate` take a list; the CMS renders it as a checkbox
group instead of a single select; search's `category` filter still takes
one value at a time and matches shows where it's present anywhere in the
list.

**Artwork requirement.** The brief says an episode can't publish "without
artwork," without saying which of the three kinds. I required `thumbnail`
on episodes (used in episode lists) and `poster` + `banner` on shows (rows
and hero). This is enforced in one place — `validation_service.py` — used
by both the report endpoint and the publish gate, so they can never drift.

**IDs.** Postgres in production, but tests run against in-memory SQLite for
speed, so primary keys are plain `String(36)` UUIDs rather than Postgres's
native UUID type — portable, and the type is a wash at this scale.

**State/data-fetching.** CMS uses TanStack Query — mutations need cache
invalidation (save a show, see the list update) and several screens want
background refetch (the validation report polls every 15s), both of which
plain `fetch` + `useState` would mean reimplementing. The viewer skipped it
deliberately: it only ever does one un-mutated GET per page, so a query
library would be pure overhead — plain `useEffect` + `fetch` is enough.

**Seed idempotency.** Duplicate-key inserts during seeding use a SQLAlchemy
`SAVEPOINT` (`db.begin_nested()`) per episode rather than a full session
rollback, so one bad row doesn't wipe out every other row staged earlier in
the same transaction — a real bug I hit and fixed while building this.

**What I left out**, given the scope: a real audit log of field-level
changes; versioned catalogues with rollback (the run history and immutable
`catalogue/runs/{id}.json` objects are already there — rollback is "point
the pointer at an older run," a couple hours of work, not done here);
tracked-changes/comments-style review flow; rate limiting; refresh tokens
(access tokens just expire after 8h); and real Cloudflare R2 credentials
wired into CI (the class is written and unit-testable in isolation, but I
didn't want to fake a live bucket for a take-home).

**AI tools.** I used Claude (this conversation) to write the implementation
directly — models, endpoints, services, both frontends, and this README —
then ran the actual test suite, a live seed/publish/search smoke test, and
`tsc`/`vite build` for both frontends myself and fixed what failed (a
SQLite `StaticPool` issue, an artwork-validation ordering bug, an `Artwork`
model missing a `url` property, a seed-loader savepoint bug, and a
deprecated raw-SQL health-check call). The first pass was built against a
synthetic seed set because the assignment's real `seed_shows.json` /
`reference.json` / test images weren't attached to the initial prompt; once
they were provided, I diffed the real files against my assumptions (they
differed in several real ways — shows have *multiple* categories not one,
different section/category/language vocab, different artwork-spec JSON
keys, seed rows are a flat list not a wrapped object) and refactored the
schema, both frontends, and the seed loader to match, then re-ran the full
test suite and a live end-to-end pass against the real fixture images and
data before packaging. I did not hand-verify every line the way I would on
a production PR — in a real review I'd want a second pass on the search
implementation's edge cases and the R2 class against a live bucket before
merging.

## Part E — written answers

**Atomicity.** Publish writes the full catalogue to a brand-new,
uniquely-named object (`catalogue/runs/{run_id}.json`) that nothing points
at yet, then flips a separate pointer object (`catalogue/current.json`) to
it in one storage operation — `os.replace()` on local disk, a copy-object
call on R2. Readers only ever read the pointer, so they see either the
fully-old or the fully-new catalogue, never a partial one. If the process
dies before the pointer flip, the live catalogue is untouched and the
half-built run file is just orphaned garbage; if it dies after, the flip
already succeeded and the new catalogue is live. The `PublishRun` row is
only marked `success` after the flip succeeds, so a crash mid-run leaves an
honest `outcome="failed"` (or `"running"` forever, which is itself a signal
worth alerting on) rather than a false success.

**Storage abstraction.** Everything above `Storage` calls `write_bytes` /
`read_bytes` / `exists` / `url_for` / `atomic_publish` and never touches
disk or S3 directly. Moving to R2 means implementing those five methods
against R2's S3-compatible API (sketched in `R2Storage`) and flipping
`STORAGE_BACKEND=r2` — no caller changes. The interesting part is
`atomic_publish`: local disk gets a real atomic rename; R2/S3 has no
rename, so the R2 implementation uses a copy-object call, which is the
closest equivalent (each resulting object version is immutable, so readers
never see a partial write, but there's no way to make the *swap* itself
transactional the way a rename is).

**Search.** `GET /catalog/search` loads the already-published (and
therefore already small and pre-filtered-to-published-only) catalogue file
and filters it in memory per request. That's fine at this catalogue's
size — tens of shows, low hundreds of episodes — and it's genuinely
simple. It stops being fine somewhere in the low thousands of shows,
where re-scanning and re-parsing JSON on every request starts costing
real latency and CPU, and it never had relevance ranking or typo
tolerance to begin with. The next step isn't "add more filters," it's a
real search index (Postgres full-text search to start, since the data's
already there — Meilisearch/Typesense/Elasticsearch if ranking quality or
query volume outgrow that), built from the same publish step so it stays
in lockstep with the catalogue rather than the DB.

**Why a pre-published file instead of querying the DB per request?**
Because the viewer is read-heavy, public, and doesn't need read-your-writes
consistency — an editor's change should NOT be visible until it's
deliberately published, so "always fresh" is actually the wrong property
here, not a shortcut. Publish, not "editor hits save," is the CDN-cacheable
event, and it means the browse experience survives a database blip. It
bites you in exactly the ways above: search that outgrows a full-file scan,
and the fact that "freshness" is now measured in publish runs instead of
requests — if an editor expects an instant preview of an unpublished
change, this design doesn't give them one (a documented, deliberate
trade-off, not an oversight).

**Health & alerting.** `GET /health` checks the DB and storage backend are
reachable. The one thing I'd alert on: **a `PublishRun` whose `outcome`
stays `"running"` for longer than a normal publish takes** (e.g. >5
minutes) — that's a stuck or crashed publish, which is the one failure mode
that silently freezes the *live* catalogue at its last good state while
looking, from the outside, like nothing is wrong. Latency/error-rate
alerts on the API are standard and worth having too, but a stuck publish is
the failure specific to this system's design that generic uptime
monitoring wouldn't catch.

## Roughly how long I spent

This was built directly in an AI coding session rather than tracked as
person-hours, so "time spent" doesn't map cleanly — as a rough proxy for
where the effort went: backend (schema, storage abstraction, validation,
publish job, tests) was the largest share; the two frontends were roughly
equal to each other and smaller than the backend; pipeline/docs were the
smallest share.

## Stretch goals

Not attempted — time went to the required scope above (see "what I left
out"). Of the three listed, versioned-catalogue-with-rollback is closest to
already existing (see above) and would be the cheapest to finish.
