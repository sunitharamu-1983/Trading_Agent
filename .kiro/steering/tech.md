# Tech Stack

## Language & Runtime

- **Python 3.x** — primary language

## Expected Libraries & Frameworks

Based on the project type, the following are likely in use (confirm against `requirements.txt` or `pyproject.toml` if present):

- **LLM integration**: `openai`, `anthropic`, or similar SDK
- **Trading/market data**: `yfinance`, `alpaca-trade-api`, `ccxt`, or similar
- **Data processing**: `pandas`, `numpy`
- **Agent orchestration**: custom loops or a framework like `langchain`, `langgraph`, or `autogen`
- **Environment config**: `python-dotenv` for loading `.env` files

## Environment & Secrets

- API keys and credentials are stored in `.env` files (never committed)
- Use `python-dotenv` to load them: `load_dotenv()` at entry point
- Never hardcode secrets in source files

## Common Commands

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the agent
python main.py

# Run tests (if pytest is used)
pytest

# Freeze dependencies
pip freeze > requirements.txt
```

## Notes

- Jupyter notebooks (`.ipynb`) are used for exploration but excluded from version control
- Data files (`.csv`, `.json`) are excluded from version control
