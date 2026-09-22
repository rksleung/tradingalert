import pandas as pd
import yfinance as yf

def filter_candlestick_patterns(df_finviz):
    """
    Takes the Finviz DataFrame, fetches recent daily history for each ticker,
    and filters for:
    1. Yesterday was a Doji.
    2. Today has expanding volume.
    3. Today is a bullish engulfing / closes above yesterday's range.
    """
    if df_finviz.empty or 'ticker' not in df_finviz.columns:
        return pd.DataFrame()

    tickers = df_finviz['ticker'].tolist()
    qualified_stocks = []

    print(f"Analyzing daily price action for {len(tickers)} tickers...")

    # Download last 5 days of history for all tickers in batch to optimize speed
    data = yf.download(tickers, period="5d", group_by="ticker", threads=True, progress=False)

    for ticker in tickers:
        try:
            # Extract historical dataframe for the individual ticker
            if len(tickers) == 1:
                hist = data
            else:
                hist = data[ticker]

            # Drop missing rows
            hist = hist.dropna()
            
            if len(hist) < 2:
                continue

            # Get Today (-1) and Yesterday (-2) data
            yesterday = hist.iloc[-2]
            today = hist.iloc[-1]

            # --- CONDITION 1: Yesterday was a Doji ---
            # Body size is less than 10% of the total high-low range
            y_open, y_close, y_high, y_low = yesterday['Open'], yesterday['Close'], yesterday['High'], yesterday['Low']
            y_range = y_high - y_low
            y_body = abs(y_close - y_open)
            
            # Prevent division by zero if range is 0
            is_doji = y_range > 0 and (y_body <= y_range * 0.1)

            # --- CONDITION 2: Expanding Volume Today ---
            t_volume, y_volume = today['Volume'], yesterday['Volume']
            is_expanding_volume = t_volume > y_volume

            # --- CONDITION 3: Engulfing / Closes above yesterday's range ---
            t_close = today['Close']
            # Closes above yesterday's high (strong breakout engulfing)
            is_engulfing = t_close > y_high

            # Combine conditions
            if is_doji and is_expanding_volume and is_engulfing:
                qualified_stocks.append({
                    'ticker': ticker,
                    'y_close': y_close,
                    't_close': t_close,
                    'volume_ratio': round(t_volume / y_volume, 2) if y_volume > 0 else 0
                })

        except Exception as e:
            # Skip tickers that fail download or have bad data
            continue

    return pd.DataFrame(qualified_stocks)