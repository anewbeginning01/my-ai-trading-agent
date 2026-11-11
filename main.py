import os
from datetime import datetime, timedelta, timezone

from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

WATCHLIST = ["KO", "PG", "JNJ", "PEP", "WMT", "MCD", "VZ", "CL", "MMM", "XOM", "SPY"]

SMA_DAYS = 50
VOL_DAYS = 20
MAX_DAILY_VOL = 0.015
DOLLARS_PER_TRADE = 500
MAX_POSITIONS = 5

KEY = os.environ["ALPACA_API_KEY"]
SECRET = os.environ["ALPACA_SECRET_KEY"]

trading = TradingClient(KEY, SECRET, paper=True)  # paper=True = fake money
data = StockHistoricalDataClient(KEY, SECRET)


def main():
    if not trading.get_clock().is_open:
        print("Market closed. Nothing to do.")
        return

    start = datetime.now(timezone.utc) - timedelta(days=140)
    bars = data.get_stock_bars(
        StockBarsRequest(
            symbol_or_symbols=WATCHLIST,
            timeframe=TimeFrame.Day,
            start=start,
            feed=DataFeed.IEX,
        )
    ).df

    held = {p.symbol for p in trading.get_all_positions()}
    pending = {o.symbol for o in trading.get_orders()}
    buys = []

    for sym in WATCHLIST:
        if sym not in bars.index.get_level_values(0):
            continue
        closes = bars.loc[sym]["close"]
        if len(closes) < SMA_DAYS:
            continue
        last = closes.iloc[-1]
        sma = closes.tail(SMA_DAYS).mean()
        vol = closes.pct_change().tail(VOL_DAYS).std()
        print(f"{sym}: price={last:.2f} sma50={sma:.2f} vol={vol:.4f}")

        if sym in pending:
            continue
        if sym in held and last < sma:
            print(f"  SELL {sym}")
            trading.close_position(sym)
        elif sym not in held and last > sma and vol < MAX_DAILY_VOL:
            buys.append((vol, sym))

    open_slots = MAX_POSITIONS - len(held)
    for vol, sym in sorted(buys)[: max(open_slots, 0)]:
        print(f"  BUY ${DOLLARS_PER_TRADE} of {sym}")
        trading.submit_order(
            MarketOrderRequest(
                symbol=sym,
                notional=DOLLARS_PER_TRADE,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
        )


if __name__ == "__main__":
    main()

