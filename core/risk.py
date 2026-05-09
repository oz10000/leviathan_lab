class KellyRiskManager:
    def __init__(self, kelly_fraction=0.25, risk_cap=0.04):
        self.kelly = kelly_fraction
        self.cap = risk_cap
        self.pnls = []   # list of pnl percentages
        self.peak = 0.0

    def update(self, pnl_pct, equity):
        self.pnls.append(pnl_pct)
        if equity > self.peak: self.peak = equity

    def drawdown(self, equity):
        if self.peak == 0: return 0.0
        return (self.peak - equity) / self.peak

    def risk_fraction(self, equity):
        if len(self.pnls) < 5: return 0.02
        wins = [x for x in self.pnls[-20:] if x > 0]
        losses = [abs(x) for x in self.pnls[-20:] if x <= 0]
        if not losses: return self.cap
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        b = avg_win / avg_loss if avg_loss > 0 else 1.0
        p = len(wins) / len(self.pnls[-20:])
        f = (b * p - (1 - p)) / b if b > 0 else 0.0
        kelly_risk = self.kelly * f
        dd = self.drawdown(equity)
        if dd > 0.10: kelly_risk *= 0.5
        elif dd > 0.05: kelly_risk *= 0.7
        return min(kelly_risk, self.cap)
