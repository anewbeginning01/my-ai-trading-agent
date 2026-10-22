import pandas as pd

from my_ai_trading_agent.rules import passes_trade_rules, build_decision


def make_valid_df() -> pd.DataFrame:
    closes = [95.0 + i * 1.3 for i in range(60)]
    volumes = [700_000] * len(closes)
    index = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=index)


def test_valid_candidate_passes_rules() -> None:
    df = make_valid_df()
    assert passes_trade_rules(df) is True


def test_low_price_is_rejected() -> None:
    df = make_valid_df()
    df["Close"] = [8.0 + i * 0.05 for i in range(len(df))]
    assert passes_trade_rules(df) is False


def test_low_volume_is_rejected() -> None:
    df = make_valid_df()
    df["Volume"] = 200_000
    assert passes_trade_rules(df) is False


def test_price_below_20_day_average_is_rejected() -> None:
    df = make_valid_df()
    df["Close"] = [100.0 + (i * 0.3) for i in range(len(df))]
    df.loc[df.index[-1], "Close"] = 98.0
    assert passes_trade_rules(df) is False


def test_build_decision_has_reason_and_risk_note() -> None:
    df = make_valid_df()
    decision = build_decision("AAPL", df)

    assert decision["ticker"] == "AAPL"
    assert decision["action"] == "BUY"
    assert "reason" in decision
    assert "risk_note" in decision
