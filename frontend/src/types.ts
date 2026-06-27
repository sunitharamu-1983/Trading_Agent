export interface TickerResult {
  ticker: string;
  score: number;                // 0–4
  signal: string;               // "Strong Buy" | "Bullish" | "Neutral" | "Bearish"
  rsi_rule: boolean;
  sma_rule: boolean;
  macd_rule: boolean;
  volume_rule: boolean;
  error?: string;
}

export interface AnalyzeResponse {
  results: TickerResult[];
}
