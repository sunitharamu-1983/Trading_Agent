from pydantic import BaseModel, field_validator
from typing import Optional


class AnalyzeRequest(BaseModel):
    tickers: list[str]

    @field_validator("tickers")
    @classmethod
    def tickers_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("tickers array must not be empty")
        return v


class TickerResult(BaseModel):
    ticker: str
    score: int                    # 0–4
    signal: str                   # "Strong Buy" | "Bullish" | "Neutral" | "Bearish"
    rsi_rule: bool
    sma_rule: bool
    macd_rule: bool
    volume_rule: bool
    error: Optional[str] = None   # set when data fetch/compute fails


class AnalyzeResponse(BaseModel):
    results: list[TickerResult]


class WatchlistResponse(BaseModel):
    tickers: list[str]
    label: str
