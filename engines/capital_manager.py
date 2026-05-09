import numpy as np

class CapitalManager:
    def __init__(self, strategies, initial_equity, config):
        self.strategies = {s['name']: s for s in strategies}
        self.equity = initial_equity
        self.peak = initial_equity
        self.config = config
        self.allocations = {name: initial_equity / len(strategies) for name in self.strategies}
        self.max_alloc = config['portfolio']['max_concentration']

    def rebalance(self, metrics):
        """
        metrics: dict {strategy_name: {'sharpe':..., 'pf':..., 'dd':..., 'degradation':...}}
        Returns new allocations dict.
        """
        # Calculate raw scores
        scores = {}
        for name in self.strategies:
            m = metrics.get(name, {})
            sharpe = max(0, m.get('sharpe', 0))
            dd = m.get('max_dd', 0)
            pf = m.get('pf', 1)
            # Score: balance of Sharpe and drawdown
            score = sharpe * max(0.1, 1 - dd)
            if pf < 0.8 or dd > self.config['risk']['max_strategy_dd']:
                score = 0  # kill
            scores[name] = score
        total_score = sum(scores.values())
        if total_score == 0:
            # All dead, keep cash
            return {name: 0 for name in self.strategies}
        new_alloc = {}
        for name, sc in scores.items():
            frac = sc / total_score
            new_alloc[name] = min(frac, self.max_alloc) * self.equity
        # Normalize to sum to equity
        total_alloc = sum(new_alloc.values())
        if total_alloc > 0:
            new_alloc = {k: v * self.equity / total_alloc for k, v in new_alloc.items()}
        else:
            new_alloc = {k: 0 for k in self.strategies}
        self.allocations = new_alloc
        return new_alloc
