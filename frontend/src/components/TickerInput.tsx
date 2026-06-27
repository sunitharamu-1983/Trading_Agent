import { useState } from "react";
import FormField from "@cloudscape-design/components/form-field";
import Textarea from "@cloudscape-design/components/textarea";
import Button from "@cloudscape-design/components/button";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Box from "@cloudscape-design/components/box";
import Alert from "@cloudscape-design/components/alert";
import { getWatchlist } from "../api";

interface TickerInputProps {
  onSubmit: (tickers: string[]) => void;
  loading: boolean;
}

/** Parse raw textarea input into clean, uppercased ticker tokens. */
export function parseTickers(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map((t) => t.trim().toUpperCase())
    .filter((t) => t.length > 0);
}

export default function TickerInput({ onSubmit, loading }: TickerInputProps) {
  const [raw, setRaw] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);

  const handleSubmit = () => {
    const tickers = parseTickers(raw);
    if (tickers.length === 0) {
      setError("Please enter at least one ticker symbol.");
      return;
    }
    if (tickers.length > 50) {
      setError("Maximum 50 tickers allowed per request.");
      return;
    }
    setError(null);
    onSubmit(tickers);
  };

  const handleLoadNifty50 = async () => {
    setLoadingWatchlist(true);
    setWatchlistError(null);
    try {
      const data = await getWatchlist();
      setRaw(data.tickers.join(", "));
      setError(null);
    } catch (err: unknown) {
      setWatchlistError(
        err instanceof Error ? err.message : "Failed to load watchlist."
      );
    } finally {
      setLoadingWatchlist(false);
    }
  };

  const tickerCount = parseTickers(raw).length;

  return (
    <SpaceBetween size="m">
      {watchlistError && (
        <Alert type="error" dismissible onDismiss={() => setWatchlistError(null)}>
          {watchlistError}
        </Alert>
      )}

      <FormField
        label="Stock Tickers"
        description={
          tickerCount > 0
            ? `${tickerCount} ticker${tickerCount !== 1 ? "s" : ""} entered. Use .NS for NSE (e.g. RELIANCE.NS) or .BO for BSE.`
            : "Enter up to 50 tickers, or click 'Load Nifty 50' to auto-fill the index."
        }
        errorText={error ?? undefined}
      >
        <Textarea
          value={raw}
          onChange={({ detail }) => {
            setRaw(detail.value);
            if (error) setError(null);
          }}
          placeholder={"RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS\n— or click 'Load Nifty 50' below —"}
          rows={5}
          disabled={loading}
        />
      </FormField>

      <SpaceBetween size="s" direction="horizontal">
        <Button
          variant="primary"
          onClick={handleSubmit}
          loading={loading}
          disabled={loading || loadingWatchlist}
          iconName="search"
        >
          Analyze Tickers
        </Button>

        <Button
          variant="normal"
          onClick={handleLoadNifty50}
          loading={loadingWatchlist}
          disabled={loading || loadingWatchlist}
          iconName="download"
        >
          Load Nifty 50
        </Button>

        {raw.length > 0 && (
          <Button
            variant="link"
            onClick={() => { setRaw(""); setError(null); }}
            disabled={loading}
          >
            Clear
          </Button>
        )}
      </SpaceBetween>

      <Box color="text-body-secondary" fontSize="body-s">
        💡 Click <strong>Load Nifty 50</strong> to instantly populate all 50 index stocks, then hit <strong>Analyze Tickers</strong>.
      </Box>
    </SpaceBetween>
  );
}
