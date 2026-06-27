import { useState } from "react";
import AppLayout from "@cloudscape-design/components/app-layout";
import ContentLayout from "@cloudscape-design/components/content-layout";
import Header from "@cloudscape-design/components/header";
import Container from "@cloudscape-design/components/container";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Alert from "@cloudscape-design/components/alert";
import ExpandableSection from "@cloudscape-design/components/expandable-section";

import TickerInput from "./components/TickerInput";
import ResultsTable from "./components/ResultsTable";
import { analyzeTickers } from "./api";
import type { TickerResult } from "./types";

// Beginner explainer cards
function HowItWorksCard({ icon, title, body }: { icon: string; title: string; body: string }) {
  return (
    <Box padding="l" variant="div">
      <SpaceBetween size="xs">
        <Box fontSize="heading-xl">{icon}</Box>
        <Box variant="h3" fontSize="heading-s" fontWeight="bold">{title}</Box>
        <Box color="text-body-secondary" fontSize="body-s">{body}</Box>
      </SpaceBetween>
    </Box>
  );
}

export default function App() {
  const [results, setResults]   = useState<TickerResult[]>([]);
  const [loading, setLoading]   = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const strongBuys = results.filter((r) => r.signal === "Strong Buy");
  const bullishCount = results.filter((r) => r.signal === "Bullish" || r.signal === "Strong Buy").length;

  const handleAnalyze = async (tickers: string[]) => {
    setLoading(true);
    setApiError(null);
    setResults([]);
    try {
      const data = await analyzeTickers(tickers);
      setResults(data.results);
    } catch (err: unknown) {
      setApiError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout
      navigationHide
      toolsHide
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="Find the most promising stocks to buy from India's Nifty 50 index — powered by technical analysis. No finance knowledge needed."
              actions={
                <Box color="text-body-secondary" fontSize="body-s">
                  Data from Yahoo Finance · Updated daily · Not financial advice
                </Box>
              }
            >
              📈 Stock Bullishness Analyzer
            </Header>
          }
        >
          <SpaceBetween size="xl">

            {/* How it works — beginner explainer */}
            <Container
              header={<Header variant="h2">How does this work?</Header>}
            >
              <ColumnLayout columns={4} variant="text-grid">
                <HowItWorksCard
                  icon="🔢"
                  title="Step 1 — Pick stocks"
                  body='Click "Load Nifty 50" to auto-fill India\'s top 50 stocks, or type the names of stocks you\'re interested in.'
                />
                <HowItWorksCard
                  icon="🔍"
                  title="Step 2 — We analyze"
                  body="We check 4 technical signals on each stock: price momentum, trend direction, buying pressure, and trading volume."
                />
                <HowItWorksCard
                  icon="🏆"
                  title="Step 3 — See the winners"
                  body='Stocks are scored 0–4 and ranked. "Strong Buy" means all 4 signals point upward — the most promising to consider buying.'
                />
                <HowItWorksCard
                  icon="🔗"
                  title="Step 4 — Act on it"
                  body='Click "View on Kite" next to any stock to open its live chart on Zerodha Kite and place a trade if you choose.'
                />
              </ColumnLayout>
            </Container>

            {/* What is a "stock symbol" explainer */}
            <ExpandableSection
              headerText="🤔 What is a stock symbol / ticker?"
              variant="container"
            >
              <SpaceBetween size="s">
                <Box>
                  A <strong>stock symbol</strong> (also called a ticker) is a short code that identifies a company on the stock exchange — like a nickname.
                  For example:
                </Box>
                <ColumnLayout columns={3} variant="text-grid">
                  <Box><strong>RELIANCE.NS</strong> = Reliance Industries on NSE</Box>
                  <Box><strong>TCS.NS</strong> = Tata Consultancy Services on NSE</Box>
                  <Box><strong>HDFCBANK.NS</strong> = HDFC Bank on NSE</Box>
                </ColumnLayout>
                <Box color="text-body-secondary" fontSize="body-s">
                  The <strong>.NS</strong> at the end means the stock trades on the <strong>National Stock Exchange (NSE)</strong> of India.
                  You don't need to know these — just click <strong>Load Nifty 50</strong> and we'll fill them in for you.
                </Box>
              </SpaceBetween>
            </ExpandableSection>

            {/* Main input */}
            <Container
              header={
                <Header
                  variant="h2"
                  description='Don\'t know which stocks to check? Click "Load Nifty 50" to instantly analyze India\'s top 50 stocks.'
                >
                  Which stocks do you want to check?
                </Header>
              }
            >
              <TickerInput onSubmit={handleAnalyze} loading={loading} />
            </Container>

            {/* Summary banner shown after results */}
            {results.length > 0 && !loading && (
              <Alert
                type={strongBuys.length > 0 ? "success" : bullishCount > 0 ? "info" : "warning"}
                header={
                  strongBuys.length > 0
                    ? `✅ ${strongBuys.length} stock${strongBuys.length > 1 ? "s" : ""} look like strong buying opportunities right now`
                    : bullishCount > 0
                    ? `👍 ${bullishCount} stock${bullishCount > 1 ? "s" : ""} show bullish signals worth watching`
                    : "⚠️ No strong buying signals found in this batch right now"
                }
              >
                {strongBuys.length > 0 && (
                  <Box>
                    <strong>Strong Buy candidates:</strong> {strongBuys.map((r) => r.ticker.replace(".NS","").replace(".BO","")).join(", ")}
                    <Box color="text-body-secondary" fontSize="body-s" padding={{ top: "xs" }}>
                      These stocks passed all 4 technical checks. Use "View on Kite" to review the chart before buying. Always do your own research.
                    </Box>
                  </Box>
                )}
                {strongBuys.length === 0 && bullishCount > 0 && (
                  <Box color="text-body-secondary" fontSize="body-s">
                    No stocks passed all 4 checks today, but some passed 3. Check the table below for details.
                  </Box>
                )}
                {bullishCount === 0 && (
                  <Box color="text-body-secondary" fontSize="body-s">
                    Technical signals don't favor buying any of these stocks right now. Consider waiting or checking again tomorrow.
                  </Box>
                )}
              </Alert>
            )}

            {/* Results table */}
            {(loading || apiError || results.length > 0) && (
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Ranked by buying strength (strongest first). Green = good signal, Red = not favorable. Click 'View on Kite' to see the live chart."
                  >
                    Results — Should I buy these stocks?
                  </Header>
                }
              >
                <ResultsTable
                  results={results}
                  loading={loading}
                  apiError={apiError}
                />
              </Container>
            )}

            {/* Footer disclaimer */}
            <Box color="text-body-secondary" fontSize="body-s" textAlign="center" padding={{ bottom: "xl" }}>
              ⚠️ <strong>Disclaimer:</strong> This tool is for educational purposes only. Technical analysis is not a guarantee of future performance.
              Always consult a SEBI-registered financial advisor before investing. Past signals do not guarantee future returns.
            </Box>

          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
