import numpy as np
import pandas as pd

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all technical indicators WITHOUT LOOKAHEAD.
    All rolling operations are shifted by 1 to avoid using current candle's information.
    """
    df = df.copy()
    df['prev_close'] = df['close'].shift(1)

    # True Range
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(abs(df['high'] - df['prev_close']),
                   abs(df['low'] - df['prev_close']))
    )
    df['atr'] = df['tr'].rolling(14).mean().shift(1)          # <-- shift
    df['atr_pct'] = df['atr'] / df['close']

    # EMAs (use shift to avoid lookahead? EMAs are already causal if using ewm with adjust=False)
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    # Slope of EMA20: diff over 5 periods, then shift
    df['slope_ema20'] = (df['ema20'].diff(5) / df['ema20'].shift(5)).shift(1)

    # Volume
    df['volume_avg'] = df['vol'].rolling(20).mean().shift(1)
    df['volume_ratio'] = df['vol'] / df['volume_avg']

    # Momentum: 5-period return, shift to avoid lookahead
    df['momentum'] = df['close'].pct_change(5).shift(1)

    # Sub-scores (0-100)
    df['trend_up'] = np.where((df['ema20'] > df['ema50']) & (df['slope_ema20'] > 0), 100,
                              np.where((df['ema20'] > df['ema50']) & (df['slope_ema20'] <= 0), 70,
                                       np.where((df['ema20'] < df['ema50']) & (df['slope_ema20'] < 0), 0, 30)))
    df['volatility_score'] = (100 - np.abs(df['atr_pct'] - 0.01) * 10000).clip(0, 100)
    df['volume_score'] = ((df['volume_ratio'].clip(0.5, 2) - 0.5) / 1.5 * 100)
    # Momentum percentile: rolling rank of momentum over last 50, shifted
    df['momentum_score'] = df['momentum'].rolling(50).rank(pct=True).shift(1) * 100

    return df
