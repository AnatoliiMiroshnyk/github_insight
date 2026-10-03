# GitHub Insight

A production-structured FastAPI web service that converts a public GitHub profile into an interactive engineering portfolio report: repository traction, language distribution, recent public activity, automated observations, snapshots and CSV export.

> Portfolio project by Anatolii Miroshnyk. It demonstrates async API integration, layered architecture, data aggregation, caching, persistence, responsive UI, automated tests and CI.

## Highlights

- Public GitHub profile and repository analysis
- Language distribution from repository language-byte endpoints
- Ranked original repositories with stars, forks and update dates
- Recent public event distribution (not a contribution-calendar replacement)
- SQLite snapshot history and 30-minute configurable cache
- CSV export, OpenAPI docs, light/dark mode and responsive layout
- Graceful handling of missing users, timeouts and API rate limits
- FastAPI, HTTPX, SQLAlchemy 2, Pydantic 2, Jinja2 and vanilla JavaScript
- pytest test suite, Ruff checks and GitHub Actions

## Architecture

```text
Browser UI (HTML/CSS/JS)
          |
          | JSON / HTTP
          v
FastAPI routes -> AnalysisService -> GitHubClient -> GitHub REST API
                      |
                      v
               SQLAlchemy -> SQLite
```

The browser never receives the GitHub token. `GitHubClient` owns remote HTTP concerns, `AnalysisService` coordinates caching and persistence, while `analyzer.py` contains pure testable transformations.

## Quick start

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn github_insight.main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is available at <http://127.0.0.1:8000/docs>.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
uvicorn github_insight.main:app --reload
```

## GitHub token

Public analysis works without a token, but a fine-grained personal access token is recommended to increase the GitHub API quota. Put it only in the local `.env` file:

```dotenv
GITHUB_TOKEN=github_pat_your_token
```

Never commit `.env`; it is already excluded by `.gitignore`. Public read-only analysis does not require broad repository write permissions.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/analyses` | Analyze a username or return a cached snapshot |
| `GET` | `/api/v1/analyses/{id}` | Read a saved snapshot |
| `GET` | `/api/v1/analyses/{id}/export.csv` | Download metrics as CSV |
| `GET` | `/api/v1/history` | List recent snapshots |
| `DELETE` | `/api/v1/history/{id}` | Delete one snapshot |
| `GET` | `/health` | Service health probe |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyses \
  -H "Content-Type: application/json" \
  -d '{"username":"octocat","force_refresh":false}'
```

## Tests and quality

```bash
ruff check src tests
pytest --cov=github_insight --cov-report=term-missing
```

Tests use an in-memory SQLite database and a fake GitHub client, so the suite is deterministic and does not consume API quota.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The `data` directory is mounted as a volume, preserving SQLite snapshots between container restarts.

## Project structure

```text
src/github_insight/
├── api/                 # API routes and dependency composition
├── core/                # Typed environment configuration
├── db/                  # SQLAlchemy database and model
├── services/            # GitHub gateway, orchestration and analytics
├── static/              # Responsive CSS and browser JavaScript
├── templates/           # Jinja2 application shell
├── cli.py               # Installed console command
├── main.py              # FastAPI factory
└── schemas.py           # Pydantic contracts
tests/                   # Unit and integration tests
```

## Data interpretation

- Language percentages are calculated from byte totals returned for up to the configured number of original repositories.
- Recent activity uses GitHub's public events feed and is therefore not a full contribution history.
- Repository totals cover only repositories retrieved within `MAX_REPOSITORY_PAGES`.
- Snapshot storage is local; this version has no user accounts or multi-tenant authorization.

## Roadmap

- GitHub OAuth and private profile mode
- PostgreSQL plus Alembic migrations
- Background jobs for large profiles
- Profile-to-profile comparison
- OpenTelemetry metrics and structured logs
- Deployable frontend/backend split

## Security

Report vulnerabilities privately instead of opening a public issue. Rotate a token immediately if it is accidentally exposed. The UI escapes third-party text before inserting it into HTML and only allows HTTP(S) links.

## License

MIT — see [LICENSE](LICENSE).
