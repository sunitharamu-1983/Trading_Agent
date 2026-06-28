# Tech Stack

## Languages & Runtimes

- **Python 3.x** — backend and agent logic
- **TypeScript** — frontend (strict mode via `tsconfig.json`)
- **Node.js** — frontend tooling

## Backend

- **FastAPI** — REST API framework (`/api/analyze`, `/api/watchlist`, `/api/health`)
- **yfinance** — fetches 90-day OHLCV price data for technical indicator computation
- **pandas / numpy** — data processing for RSI, SMA, MACD, and volume indicators
- **pydantic** — request/response schema validation
- **uvicorn** — ASGI server to run FastAPI
- **python-dotenv** — loads `.env` secrets at entry point

## Agent Module

- **openai** — optional LLM call for narrative analysis (falls back gracefully if no key)
- **tavily-python** — MCP-powered web search for market news, macro context, company deep-dives

## Frontend

- **React 19** — UI framework
- **AWS CloudScape** (`@cloudscape-design/components`) — Amazon's open-source design system (same UI as the AWS Console); provides Table, FormField, Button, Badge, Popover, StatusIndicator, etc.
- **Vite** — dev server and build tool (`npm run dev` / `npm run build`)
- **TypeScript ~6.0** — all frontend code is typed
- **oxlint** — fast linter for TypeScript/React code

## Testing

- **pytest** — backend unit and integration tests
- **hypothesis** — property-based testing for indicator correctness (12 formal properties)
- **httpx** — async HTTP client used in API endpoint tests

## Environment & Secrets

- API keys and credentials are stored in `.env` files (never committed)
- Use `python-dotenv` to load them: `load_dotenv()` at entry point
- Frontend env vars are prefixed `VITE_` (e.g. `VITE_API_BASE_URL`)
- Never hardcode secrets in source files

## Common Commands

```bash
# --- Backend ---
# Set up virtual environment
python -m venv .venv
.venv\Scripts\activate           # Windows
source .venv/bin/activate        # macOS/Linux

# Install backend dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Run the FastAPI backend
uvicorn backend.main:app --reload

# Run backend tests
pytest backend/tests/

# --- Agent ---
# Run the original trading agent
python main.py

# --- Frontend ---
cd frontend
npm install
npm run dev        # starts Vite dev server on http://localhost:5173
npm run build      # production build
npm run lint       # run oxlint
```

## Notes

- Jupyter notebooks (`.ipynb`) are used for exploration but excluded from version control
- Data files (`.csv`, `.json`) are excluded from version control
- Backend uses minimum-version bounds (`>=`) in `requirements.txt` for Python 3.14+ compatibility
