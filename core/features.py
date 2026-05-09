import numpy as np
import pandas as pd

def compute_features(df):
    df = df.copy()
    # Ensure columns exist
    for col in ['open','high','low','close','vol']:
        if col not in df.columns: raise ValueError(f"Missing column {col}")

    df['prev_close'] = df['close'].shift(1)
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['prev_close']),
                                     abs(df['low'] - df['prev_close'])))
    df['atr'] = df['tr'].rolling(14).mean()
    df['atr_pct'] = df['atr'] / df['close']
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['slope_ema20'] = df['ema20'].diff(5) / df['ema20'].shift(5)
    df['volume_avg'] = df['vol'].rolling(20).mean()
    df['volume_ratio'] = df['vol'] / df['volume_avg']
    df['momentum'] = df['close'].pct_change(5)
    df['returns'] = df['close'].pct_change()

    # Sub‑scores
    df['trend_up'] = np.where((df['ema20'] > df['ema50']) & (df['slope_ema20'] > 0), 100,
                              np.where((df['ema20'] > df['ema50']) & (df['slope_ema20'] <= 0), 70,
                                       np.where((df['ema20'] < df['ema50']) & (df['slope_ema20'] < 0), 0, 30)))
    df['volatility_score'] = (100 - np.abs(df['atr_pct'] - 0.01) * 10000).clip(0, 100)
    df['volume_score'] = ((df['volume_ratio'].clip(0.5, 2) - 0.5) / 1.5 * 100)
    df['momentum_score'] = df['momentum'].rolling(50).rank(pct=True) * 100  # <-- will be checked for lookahead
    return df
