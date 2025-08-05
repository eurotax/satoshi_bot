from bybit.signals import extract_change_pct, format_alert


def test_extract_change_pct():
    ticker = {"price24hPcnt": "0.05"}
    assert extract_change_pct(ticker) == 5.0


def test_format_alert_contains_values():
    msg = format_alert("BTCUSDT", 10000.0, 5.1234)
    assert "BTCUSDT" in msg
    assert "5.12%" in msg
