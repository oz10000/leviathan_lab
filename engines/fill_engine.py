import numpy as np

class FillEngine:
    def __init__(self, base_slippage_bps=1.0, atr_factor=0.02, vol_factor=0.01,
                 liquidity_factor=0.5, latency_ms=150, jitter_ms=50,
                 partial_fill_base=0.99, high_vol_fill=0.95):
        self.base_bps = base_slippage_bps
        self.atr_factor = atr_factor
        self.vol_factor = vol_factor
        self.liquidity_factor = liquidity_factor
        self.latency_ms = latency_ms / 1000
        self.jitter_ms = jitter_ms / 1000
        self.partial_fill_base = partial_fill_base
        self.high_vol_fill = high_vol_fill
        self.rng = np.random.default_rng(42)

    def calculate_slippage(self, direction, atr_pct, volume_ratio=1.0):
        base = self.base_bps / 10000
        vol_slip = self.atr_factor * atr_pct
        liq_slip = self.liquidity_factor * (1/max(volume_ratio, 0.5)) * atr_pct
        total = base + vol_slip + liq_slip
        return direction * total

    def execution_price(self, current_price, direction, atr_pct, volume_ratio=1.0):
        slip = self.calculate_slippage(direction, atr_pct, volume_ratio)
        # Simulate latency move
        latency_move = self.rng.normal(0, atr_pct * 0.2)
        exec_price = current_price * (1 + slip + latency_move)
        return exec_price

    def fill_probability(self, volume_ratio, atr_pct):
        if atr_pct > 0.02:
            return self.high_vol_fill
        return min(self.partial_fill_base, 0.85 + 0.14 * volume_ratio)

    def simulate_fill(self, volume_ratio, atr_pct):
        prob = self.fill_probability(volume_ratio, atr_pct)
        return self.rng.random() < prob
