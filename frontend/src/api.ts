import type { AnalyzeResponse } from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function analyzeTickers(tickers: string[]): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tickers }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Server error: HTTP ${res.status}`);
  }

  return res.json() as Promise<AnalyzeResponse>;
}

export async function getWatchlist(): Promise<{ tickers: string[]; label: string }> {
  const res = await fetch(`${BASE_URL}/api/watchlist`);
  if (!res.ok) {
    throw new Error(`Failed to load watchlist: HTTP ${res.status}`);
  }
  return res.json();
}
