# Peblo TV Assignment

This document describes the implemented part of the Peblo TV assignment and
the steps needed to run it manually without Docker.

## 1. Implemented Solution

Peblo TV is split into three applications:

```text
CMS (React) -> FastAPI API + PostgreSQL -> publish job -> catalogue JSON
                                                        ^
Viewer (React) -----------------------------------------+
```

### Backend

- FastAPI application with interactive OpenAPI documentation at `/docs`.
- PostgreSQL persistence through SQLAlchemy and Alembic migrations.
- JWT authentication with separate `editor` and `admin` roles.
- Show CRUD, season creation, and episode CRUD under `/admin`.
- Reference-data validation for categories, sections, and languages.
- Artwork upload and replacement for show posters/banners and episode
  thumbnails.
- Image validation using Pillow for file type, file size, aspect ratio, and
  dimensions.
- A shared validation report used by both the CMS and the publish gate.
- Publish history with run status, counts, checksum, and error information.
- Local-disk storage for development and an R2/S3-compatible storage
  abstraction for deployment.
- Health endpoint at `/health` that checks database and storage availability.

### CMS

The internal React editor is available on port `5174` and provides:

- Login using the backend JWT authentication.
- Show listing with search, section, status, language, and pagination filters.
- Create, edit, publish, and delete shows.
- Edit show synopsis, categories, section, and status.
- Create seasons and manage episodes, including language variants.
- Upload show and episode artwork with immediate validation feedback.
- Validation report showing the exact issues that would block publishing.
- Publish page showing recent publish runs.
- Admin-only publishing; editors can manage content but cannot publish.

### Viewer

The public React viewer is available on port `5173` and provides:

- Firebase login and signup flow.
- Protected home/browse experience.
- Published-show detail pages with seasons, episodes, languages, and artwork.
- Search across show titles, categories, and episode titles.
- Search filters for category, language, and section; filters compose with AND
  behavior.
- Profile and settings screens, including theme support.

The viewer reads `/catalog`, not the operational database. Unpublished edits
therefore remain invisible until an administrator publishes a new catalogue.

## 2. Publish and Catalogue Behavior

Publishing is intentionally a separate workflow from saving editor changes.

1. The validation report checks every published show and published episode.
2. The complete catalogue is built in memory from published database content.
3. It is written to a new immutable object at
   `catalogue/runs/{run_id}.json`.
4. `catalogue/current.json` is atomically replaced to point at the new run.
5. The publish run is marked successful only after the pointer update succeeds.

This prevents viewers from reading a partially written catalogue. Repeating a
publish with unchanged content is safe and produces the same content checksum.

Published content must satisfy these rules:

- A published show has a valid section.
- A published show has poster and banner artwork.
- A published show has at least one published episode.
- A published episode has a positive duration.
- A published episode has a thumbnail.
- A published episode uses an allowed language.
- `(content_group, language)` is unique for episode language variants.

Language variants with the same content group are collapsed into one catalogue
episode with a `languages[]` list. Trailer seasons use season number `0` and
are marked with `is_trailer` in the catalogue.

## 3. Seed Data and Expected Initial State

On first startup, the seed process:

- Creates the demo editor and admin accounts.
- Loads the supplied `data/seed_shows.json` and reference data.
- Creates placeholder artwork only where the seed says artwork is available.
- Rejects duplicate or invalid seed rows without discarding valid rows.
- Attempts an initial publish.

The initial publish is expected to be blocked. The supplied seed deliberately
contains a published episode without a thumbnail: **The Midnight Market** from
*Discover India with Moti*. The duplicate `(content_group, language)` row is
also reported during import.

To complete the happy-path demonstration:

1. Sign into the CMS as `admin@peblo.tv` / `admin123`.
2. Open **Shows** and select *Discover India with Moti*.
3. Upload a valid `thumbnail` for the affected episode. The supplied
   `data/assets/thumb_good.jpg` can be used.
4. Open **Publish** and publish again.
5. Confirm that the run succeeds and the viewer shows the published content.

The supplied invalid assets can be used to exercise validation errors:
`thumb_tiny.jpg`, `poster_wrong_ratio.jpg`, and `banner_too_big.png`.

## 4. Run With Docker Compose

Prerequisites: Docker Desktop with Compose enabled.

From the repository root:

```bash
cp .env.example .env
docker-compose up --build
```

On Windows PowerShell, the copy command is:

```powershell
Copy-Item .env.example .env
docker-compose up --build
```

Open:

- Viewer: http://localhost:5173
- CMS: http://localhost:5174
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The database is exposed on host port `5433`; the API reaches it through the
Compose service name `db`. Stop the stack with `Ctrl+C`, or run
`docker-compose down`. Add `-v` only when intentionally removing the seeded
database and storage volumes.

## 5. Manual Run Without Docker

### Prerequisites

- Python 3.12 or compatible Python 3.x.
- Node.js and npm.
- A running PostgreSQL instance.
- Git Bash, WSL, or PowerShell on Windows.

Create a PostgreSQL database and user matching the values below, or use an
existing database and adjust `DATABASE_URL` accordingly:

```sql
CREATE USER peblo WITH PASSWORD 'peblo';
CREATE DATABASE peblo OWNER peblo;
```

Copy the environment template, then change the database host from the Docker
service name to `localhost`:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env` for a local machine run:

```dotenv
DATABASE_URL=postgresql://peblo:peblo@localhost:5432/peblo
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./storage
STORAGE_PUBLIC_BASE_URL=http://localhost:8000/static
REFERENCE_JSON_PATH=../data/reference.json
VITE_API_BASE_URL=http://localhost:8000
```

If PostgreSQL is listening on another port, update `DATABASE_URL`. The
`STORAGE_LOCAL_PATH` and `REFERENCE_JSON_PATH` values may also be replaced by
absolute paths when required by the local environment.

### 5.1 Backend

From the repository root, create and activate a virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks script activation, use the interpreter directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run migrations and seed data. Execute these from `backend` so Python can
import the `app` package:

```powershell
alembic upgrade head
python -m app.seed
```

Start the API in a separate terminal:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The local storage directory is served through `/static`. The API should now
respond at http://localhost:8000/health.

### 5.2 CMS

In a new terminal:

```powershell
cd cms
npm install
npm run dev
```

Open http://localhost:5174 and use:

- Editor: `editor@peblo.tv` / `editor123`
- Admin: `admin@peblo.tv` / `admin123`

### 5.3 Viewer

The viewer requires Firebase client configuration for its authentication
screens. Add the Firebase `VITE_...` values from `.env` to the viewer's local
Vite environment before starting it. These are build-time frontend variables;
do not put private Firebase server credentials in the frontend.

In a new terminal:

```powershell
cd viewer
npm install
npm run dev
```

Open http://localhost:5173. A Firebase user must exist in the configured
Firebase project before viewer login will succeed. The viewer's catalogue API
base URL defaults to `http://localhost:8000`.

## 6. Verification Commands

Backend tests use an in-memory SQLite database and temporary local storage, so
they do not require PostgreSQL to be running:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

Build both frontends:

```powershell
cd cms
npm run build

cd ..\viewer
npm run build
```

Useful manual checks:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/docs`
- Sign in to CMS as editor and confirm show CRUD works.
- Confirm an editor receives `403` when attempting to publish.
- Sign in as admin, fix the seeded missing thumbnail, and publish.
- Confirm `GET http://localhost:8000/catalog` returns the current catalogue.
- Confirm viewer search combines `q`, `category`, `language`, and `section`.

## 7. Repository Layout

```text
backend/    FastAPI API, models, migrations, seed, storage, and tests
cms/        React + TypeScript internal CMS
viewer/     React + TypeScript public viewer
data/       reference.json, seed_shows.json, and supplied artwork assets
```

## 8. Deliberate Scope Decisions

- The published catalogue is a pre-built file so the public viewer is read
  optimized, cacheable, and isolated from editor database changes.
- Search currently scans the small published catalogue in memory. A dedicated
  search index would be the next step if catalogue size or query volume grows.
- Local disk is the default for development; the storage interface leaves room
  for Cloudflare R2/S3 deployment.
- Access tokens expire after eight hours. Refresh tokens, field-level audit
  history, tracked-change review, and catalogue rollback UI are outside the
  implemented assignment scope.