# Bullish Ticker Analyzer — Frontend

React + TypeScript + Vite UI for the Bullish Ticker Analyzer. Built with [AWS CloudScape](https://cloudscape.design/) design system.

## Setup

```bash
npm install
cp .env.example .env   # optional — override VITE_API_BASE_URL if needed
npm run dev
```

Dev server runs at `http://localhost:5173`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

Copy `.env.example` to `.env` and edit as needed. The file is gitignored — never commit `.env`.

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start development server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npx vitest run` | Run unit tests |

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx              # Root component — state management and layout
│   ├── api.ts               # analyzeTickers() — POST /api/analyze
│   ├── types.ts             # TickerResult and AnalyzeResponse interfaces
│   └── components/
│       ├── TickerInput.tsx  # Textarea input + submit button
│       └── ResultsTable.tsx # CloudScape Table with scored results
├── .env.example             # Environment variable template
└── vite.config.ts
```

## Dependencies

| Package | Purpose |
|---|---|
| `@cloudscape-design/components` | AWS CloudScape UI components |
| `@cloudscape-design/global-styles` | CloudScape CSS reset and theming |
| `vitest` | Unit test runner |
