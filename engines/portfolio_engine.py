import pandas as pd
import numpy as np
from engines.backtest_engine import BacktestEngine
from engines.capital_manager import CapitalManager
from engines.fill_engine import FillEngine

class PortfolioEngine:
    def __init__(self, strategies, data_dict, config):
        self.strategies = strategies  # list of dicts with name, params, etc.
        self.data = data_dict
        self.config = config
        self.fill_engine = FillEngine(**config['slippage'], latency_ms=config['latency']['mean_ms'])
        self.capital_mgr = CapitalManager(strategies, config['capital_initial'], config)
        self.positions = {}  # per strategy
        self.trades_log = {s['name']: [] for s in strategies}
        self.equity_curves = {s['name']: [config['capital_initial'] / len(strategies)] for s in strategies}
        self.timeline = sorted(set().union(*[df.index for df in data_dict.values()]))

    def run(self):
        # For each timestamp, each strategy receives its allocated capital and can trade
        for ts in self.timeline:
            # Rebalance daily at midnight (UTC) - simplified: every 24h
            if hasattr(self, 'last_rebalance') and ts - self.last_rebalance < pd.Timedelta(hours=24):
                pass
            else:
                # compute metrics for rebalance
                metrics = {}
                for s in self.strategies:
                    name = s['name']
                    # run a quick backtest on existing trades to compute rolling metrics
                    # For simplicity, we'll recompute from trades log
                    # In production, compute incremental metrics.
                self.last_rebalance = ts
                alloc = self.capital_mgr.rebalance(metrics)

            # For each strategy, process signals with its allocated capital
            for s in self.strategies:
                name = s['name']
                cap = alloc.get(name, 0)
                if cap <= 0: continue
                # Run backtest step (simulated by using BacktestEngine but we need incremental)
                # We'll approximate: for now, this is placeholder for multi-strategy integration.
                # In a complete implementation, we maintain state per strategy and execute trades.
                pass
