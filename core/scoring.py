import pandas as pd
from core.features import compute_features

class MultiTFScorer:
    def __init__(self, weights=None, sub_weights=None):
        self.weights = weights or {"5m": 0.5, "15m": 0.5}
        self.sub_weights = sub_weights or {"trend": 0.30, "momentum": 0.25,
                                           "volatility": 0.25, "volume": 0.20}
        self.freq_map = {"1m":"1T", "3m":"3T", "5m":"5T", "15m":"15T", "30m":"30T", "1h":"1H", "4h":"4H"}

    def total_score(self, df_1m):
        score = 0.0
        for tf, w in self.weights.items():
            freq = self.freq_map.get(tf)
            if not freq: continue
            try:
                resampled = df_1m.resample(freq, on='ts').agg({
                    'open':'first','high':'max','low':'min','close':'last','vol':'sum'
                }).dropna().reset_index()
                resampled = compute_features(resampled)
                if resampled.empty or len(resampled) < 10: continue
                row = resampled.iloc[-1]
                score += (self.sub_weights['trend'] * row['trend_up'] +
                          self.sub_weights['momentum'] * row['momentum_score'] +
                          self.sub_weights['volatility'] * row['volatility_score'] +
                          self.sub_weights['volume'] * row['volume_score']) * w
            except Exception:
                continue
        return score
