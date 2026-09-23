import pandas as pd
import yfinance as yf
from datetime import datetime

def evaluate_doji_breakouts(df_dojis, setup_date):
    """
    Checks today's price action against yesterday's saved Doji setups 
    for an engulfing breakout on increasing volume.
    """   
    if df_dojis.empty:
        return pd.DataFrame()
        
    tickers = df_dojis['ticker'].tolist()
    print(f"Evaluating breakouts for {len(tickers)} Doji setups from {setup_date}...")
    
    # Download today's price action for the watchlist tickers
    data = yf.download(tickers, period="2d", group_by="ticker", threads=True, progress=False)
    
    breakouts = []
    
    for index, row in df_dojis.iterrows():
        ticker = row['ticker']
        doji_high = row['high']
        doji_vol = row['volume']
        
        try:
            hist = data if len(tickers) == 1 else data[ticker]
            hist = hist.dropna()
            
            if len(hist) < 2:
                continue
                
            # Get today's candle (last row)
            today_candle = hist.iloc[-1]
            t_close = float(today_candle['Close'])
            t_vol = int(today_candle['Volume'])
            
            # Breakout Conditions:
            # 1. Closes above yesterday's Doji high (Engulfing / Breakout)
            is_breakout = t_close > doji_high
            
            # 2. Volume is higher than yesterday's Doji volume
            is_increasing_vol = t_vol > doji_vol
            
            if is_breakout and is_increasing_vol:
                breakouts.append({
                    'ticker': ticker,
                    'setup_date': setup_date,
                    'doji_high': doji_high,
                    'breakout_close': t_close,
                    'volume_ratio': round(t_vol / doji_vol, 2) if doji_vol > 0 else 0
                })
                
        except Exception as e:
            print(f"Error checking breakout for {ticker}: {e}")
            continue
            
    df_breakouts = pd.DataFrame(breakouts)
    return df_breakouts