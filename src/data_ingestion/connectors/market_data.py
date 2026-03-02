from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import httpx


@dataclass
class PriceBar:
    ticker: str
    ts_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str = "1d"
    source: str = "unknown"


class MarketDataProvider(Protocol):
    def fetch_daily_bars(self, tickers: list[str], lookback_days: int = 5) -> list[PriceBar]:
        ...


class StubMarketDataProvider:
    def fetch_daily_bars(self, tickers: list[str], lookback_days: int = 5) -> list[PriceBar]:
        now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        bars: list[PriceBar] = []
        for idx, ticker in enumerate(tickers):
            for day in range(max(1, lookback_days)):
                ts_utc = now - timedelta(days=day)
                base = 100.0 + (idx * 20.0) + day
                bars.append(
                    PriceBar(
                        ticker=ticker,
                        ts_utc=ts_utc,
                        open=base,
                        high=base + 1.5,
                        low=base - 1.25,
                        close=base + 0.8,
                        volume=1_000_000 + (idx * 100_000),
                        source="stub",
                    )
                )
        return bars


class YahooFinanceProvider:
    base_url = "https://query1.finance.yahoo.com"

    def fetch_daily_bars(self, tickers: list[str], lookback_days: int = 5) -> list[PriceBar]:
        bars: list[PriceBar] = []
        period_days = max(5, lookback_days + 2)
        for ticker in tickers:
            url = f"{self.base_url}/v8/finance/chart/{ticker}"
            params = {"range": f"{period_days}d", "interval": "1d"}
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                payload = resp.json()
            bars.extend(self._parse_chart_payload(ticker, payload, lookback_days))
        return bars

    @staticmethod
    def _parse_chart_payload(ticker: str, payload: dict, lookback_days: int) -> list[PriceBar]:
        chart = payload.get("chart", {})
        results = chart.get("result") or []
        if not results:
            return []
        row = results[0]
        timestamps = row.get("timestamp") or []
        indicators = row.get("indicators", {}).get("quote", [])
        quote = indicators[0] if indicators else {}
        opens = quote.get("open") or []
        highs = quote.get("high") or []
        lows = quote.get("low") or []
        closes = quote.get("close") or []
        volumes = quote.get("volume") or []

        bars: list[PriceBar] = []
        for ts, o, h, low, c, v in zip(
            timestamps, opens, highs, lows, closes, volumes, strict=False
        ):
            if None in (o, h, low, c, v):
                continue
            bars.append(
                PriceBar(
                    ticker=ticker,
                    ts_utc=datetime.fromtimestamp(ts, tz=UTC),
                    open=float(o),
                    high=float(h),
                    low=float(low),
                    close=float(c),
                    volume=float(v),
                    source="yahoo",
                )
            )

        bars.sort(key=lambda b: b.ts_utc, reverse=True)
        return bars[: max(1, lookback_days)]


class YFinanceProvider:
    def fetch_daily_bars(self, tickers: list[str], lookback_days: int = 5) -> list[PriceBar]:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError(
                "yfinance is not installed. Run `make setup` to install dependencies."
            ) from exc

        bars: list[PriceBar] = []
        period_days = max(5, lookback_days + 2)
        for ticker in tickers:
            history = yf.Ticker(ticker).history(
                period=f"{period_days}d",
                interval="1d",
                auto_adjust=False,
                actions=False,
            )
            if history.empty:
                continue
            history = history.reset_index().tail(max(1, lookback_days))
            for _, row in history.iterrows():
                ts = row["Date"].to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                else:
                    ts = ts.astimezone(UTC)
                bars.append(
                    PriceBar(
                        ticker=ticker,
                        ts_utc=ts,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row["Volume"]),
                        source="yfinance",
                    )
                )
        return bars


def get_market_data_provider(provider_name: str) -> MarketDataProvider:
    normalized = provider_name.strip().lower()
    if normalized in {"yfinance", "yahoo"}:
        return YFinanceProvider()
    if normalized == "yahoo-chart":
        return YahooFinanceProvider()
    return StubMarketDataProvider()
