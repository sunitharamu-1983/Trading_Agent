import Table from "@cloudscape-design/components/table";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Alert from "@cloudscape-design/components/alert";
import Spinner from "@cloudscape-design/components/spinner";
import Link from "@cloudscape-design/components/link";
import Box from "@cloudscape-design/components/box";
import Badge from "@cloudscape-design/components/badge";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Popover from "@cloudscape-design/components/popover";
import type { TickerResult } from "../types";

interface ResultsTableProps {
  results: TickerResult[];
  loading: boolean;
  apiError: string | null;
}

type StatusType = "success" | "info" | "stopped" | "error" | "warning" | "pending" | "in-progress";

// Plain-English buy recommendation derived from signal
const BUY_ADVICE: Record<string, { text: string; detail: string; type: StatusType }> = {
  "Strong Buy": {
    text: "✅ Consider Buying",
    detail: "All 4 technical signals are positive. This stock shows strong upward momentum. Review the chart on Kite before buying.",
    type: "success",
  },
  "Bullish": {
    text: "👍 Worth Watching",
    detail: "3 out of 4 signals are positive. Good momentum but not all signals confirmed. Watch for a day or two before buying.",
    type: "info",
  },
  "Neutral": {
    text: "⏳ Wait",
    detail: "Only 1–2 signals are positive. Mixed signals — better to wait until more signals align before buying.",
    type: "stopped",
  },
  "Bearish": {
    text: "🚫 Avoid",
    detail: "No positive signals. The stock does not show buying strength right now. Avoid purchasing.",
    type: "error",
  },
};

/** Strip .NS / .BO suffix and build Zerodha Kite chart URL. */
function toKiteUrl(ticker: string): string {
  const symbol = ticker.replace(/\.(NS|BO)$/i, "");
  return `https://kite.zerodha.com/chart/ext/ciq/NSE:${symbol}/EQ`;
}

/** Friendly company name — strips exchange suffix */
function friendlyTicker(ticker: string): string {
  return ticker.replace(/\.(NS|BO)$/i, "");
}

/** Rule cell with tooltip explaining what the rule means */
function RuleCell({ value, label, explanation }: { value: boolean; label: string; explanation: string }) {
  return (
    <Popover
      content={<Box fontSize="body-s">{explanation}</Box>}
      triggerType="text"
      size="medium"
    >
      <StatusIndicator type={value ? "success" : "error"}>
        {value ? `✓ ${label}` : `✗ ${label}`}
      </StatusIndicator>
    </Popover>
  );
}

const columnDefinitions = [
  {
    id: "recommendation",
    header: "Should I buy?",
    cell: (r: TickerResult) => {
      if (r.error) {
        return <StatusIndicator type="error">Data unavailable</StatusIndicator>;
      }
      const advice = BUY_ADVICE[r.signal] ?? BUY_ADVICE["Neutral"];
      return (
        <Popover
          content={<Box fontSize="body-s">{advice.detail}</Box>}
          triggerType="text"
          size="medium"
        >
          <StatusIndicator type={advice.type}>
            <strong>{advice.text}</strong>
          </StatusIndicator>
        </Popover>
      );
    },
    sortingField: "score",
    width: 200,
  },
  {
    id: "ticker",
    header: "Company (Stock Code)",
    cell: (r: TickerResult) => (
      <SpaceBetween size="xxs" direction="vertical">
        <Box fontWeight="bold" fontSize="body-m">{friendlyTicker(r.ticker)}</Box>
        <Box color="text-body-secondary" fontSize="body-s">{r.ticker}</Box>
      </SpaceBetween>
    ),
    sortingField: "ticker",
    width: 160,
  },
  {
    id: "score",
    header: "Signals Passed",
    cell: (r: TickerResult) =>
      r.error ? (
        <Popover content={<Box fontSize="body-s">{r.error}</Box>} triggerType="text">
          <Badge color="red">Error — hover for details</Badge>
        </Popover>
      ) : (
        <SpaceBetween size="xxs" direction="vertical">
          <Badge color={r.score >= 3 ? "green" : r.score >= 1 ? "blue" : "red"}>
            {r.score} / 4 signals
          </Badge>
          <Box color="text-body-secondary" fontSize="body-s">
            {r.score >= 3 ? "Strong" : r.score >= 1 ? "Moderate" : "Weak"}
          </Box>
        </SpaceBetween>
      ),
    sortingField: "score",
    width: 140,
  },
  {
    id: "rsi",
    header: "Oversold? (RSI)",
    cell: (r: TickerResult) => (
      <RuleCell
        value={r.rsi_rule}
        label={r.rsi_rule ? "Yes" : "No"}
        explanation="RSI ≤ 40 means the stock may be oversold — priced lower than its true value, potentially a good entry point. Like a sale on a quality product."
      />
    ),
    width: 140,
  },
  {
    id: "sma",
    header: "Uptrend? (50-day)",
    cell: (r: TickerResult) => (
      <RuleCell
        value={r.sma_rule}
        label={r.sma_rule ? "Yes" : "No"}
        explanation="Price above its 50-day average means the stock has been rising over the past 2 months — it's in an uptrend. Like a stock climbing a staircase."
      />
    ),
    width: 140,
  },
  {
    id: "macd",
    header: "Momentum? (MACD)",
    cell: (r: TickerResult) => (
      <RuleCell
        value={r.macd_rule}
        label={r.macd_rule ? "Yes" : "No"}
        explanation="MACD crossover means buying momentum just turned positive — like a car switching from reverse to forward. A fresh bullish signal."
      />
    ),
    width: 150,
  },
  {
    id: "volume",
    header: "High Demand? (Volume)",
    cell: (r: TickerResult) => (
      <RuleCell
        value={r.volume_rule}
        label={r.volume_rule ? "Yes" : "No"}
        explanation="Volume 20%+ above average means more people are buying this stock than usual — strong demand, like a crowded sale at a store."
      />
    ),
    width: 165,
  },
  {
    id: "kite",
    header: "View Chart",
    cell: (r: TickerResult) => (
      <Link href={toKiteUrl(r.ticker)} external target="_blank">
        Open on Kite ↗
      </Link>
    ),
    width: 130,
  },
];

export default function ResultsTable({ results, loading, apiError }: ResultsTableProps) {
  if (loading) {
    return (
      <Box textAlign="center" padding="xxl">
        <SpaceBetween size="m" alignItems="center" direction="vertical">
          <Spinner size="large" />
          <Box variant="h3">Analyzing stocks…</Box>
          <Box color="text-body-secondary">
            Fetching 90 days of market data and running technical analysis on each stock.
            This usually takes 10–30 seconds.
          </Box>
        </SpaceBetween>
      </Box>
    );
  }

  if (apiError) {
    return (
      <Alert type="error" header="Something went wrong">
        {apiError}
        <Box padding={{ top: "s" }} fontSize="body-s" color="text-body-secondary">
          Make sure the backend server is running on port 8000 and try again.
        </Box>
      </Alert>
    );
  }

  if (results.length === 0) {
    return null;
  }

  return (
    <SpaceBetween size="l">
      <Table
        columnDefinitions={columnDefinitions}
        items={results}
        variant="full-page"
        stickyHeader
        stripedRows
        header={
          <Box variant="h3">
            {results.length} stock{results.length !== 1 ? "s" : ""} analyzed — sorted by buying strength
          </Box>
        }
        empty={
          <Box textAlign="center" color="inherit" padding="l">
            No results yet. Pick some stocks above and click Analyze.
          </Box>
        }
        footer={
          <SpaceBetween size="s" direction="horizontal">
            <Box color="text-body-secondary" fontSize="body-s">
              💡 <strong>Tip:</strong> Hover over any signal to see a plain-English explanation of what it means.
            </Box>
            <Box color="text-body-secondary" fontSize="body-s">
              Signals: ✅ Strong Buy = 4/4 · 👍 Worth Watching = 3/4 · ⏳ Wait = 1–2/4 · 🚫 Avoid = 0/4
            </Box>
          </SpaceBetween>
        }
      />
    </SpaceBetween>
  );
}
