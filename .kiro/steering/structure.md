# Project Structure

## Current Layout

```
Trading_Agent/
├── .gitignore          # Python, secrets, data files excluded
├── README.md           # Project description
└── .kiro/              # Kiro AI assistant configuration
    ├── settings/       # MCP and tool settings
    └── steering/       # AI steering documents (this folder)
```

## Recommended Structure (as project grows)

```
Trading_Agent/
├── main.py             # Entry point — starts the trading agent
├── agent/              # Core agent logic
│   ├── agent.py        # Main agent loop and decision-making
│   ├── tools.py        # Tool definitions the agent can call
│   └── prompts.py      # System and user prompt templates
├── data/               # Market data (gitignored)
├── config/             # Non-secret configuration (thresholds, symbols, etc.)
│   └── settings.py
├── tests/              # Unit and integration tests
│   └── test_agent.py
├── .env                # API keys and secrets (gitignored)
├── requirements.txt    # Pinned Python dependencies
└── README.md
```

## Conventions

- Keep agent logic in `agent/` and entry point in `main.py`
- Configuration that is NOT a secret goes in `config/` and can be committed
- Secrets always go in `.env` — never in committed files
- Data files belong in `data/` (gitignored)
- One responsibility per module — separate data fetching, decision logic, and execution
