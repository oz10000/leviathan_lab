import numpy as np
import pandas as pd
from core.features import compute_features
from core.scoring import MultiTFScorer
from core.exit_manager import HybridExit
from core.risk import KellyRiskManager
from engines.fill_engine import FillEngine
from analytics.metrics import calculate_all_metrics
from reporting.telemetry import log_trade, log_portfolio
import time

class BacktestEngine:
    def __init__(self, strategy, data_dict, config, strategy_name):
        self.strategy = strategy
        self.data = data_dict
        self.config = config
        self.name = strategy_name
        self.initial_capital = config['capital_initial']
        self.capital = self.initial_capital
        self.leverage = strategy.get('leverage', 3)
        self.fees = config['fees']['taker']
        self.fill_engine = FillEngine(**config['slippage'], latency_ms=config['latency']['mean_ms'],
                                      jitter_ms=config['latency']['jitter_ms'])
        self.scorer = MultiTFScorer()
        self.exit_mgr = HybridExit(**strategy.get('exit_params', {}))
        self.risk_mgr = KellyRiskManager()
        self.position = None
        self.trades = []
        self.equity = [self.initial_capital]
        self.timestamps = []

    def run(self):
        # Get global timeline (union of all symbols)
        all_timestamps = set()
        start_dates = []
        end_dates = []
        for df in self.data.values():
            all_timestamps.update(df.index)
            start_dates.append(df.index.min())
            end_dates.append(df.index.max())
        if not all_timestamps: return []
        self.start_date = min(start_dates)
        self.end_date = max(end_dates)
        timeline = sorted(all_timestamps)
        self.timestamps = timeline

        for ts in timeline:
            # Manage open position
            if self.position:
                sym = self.position['symbol']
                df = self.data.get(sym)
                if df is not None and ts in df.index:
                    row = df.loc[ts]
                    price = row['close']
                    atr_hist = df['atr_pct'].dropna().tolist()[-20:]
                    exit_flag, reason, exit_price, updated = self.exit_mgr.should_exit(
                        self.position, price, ts.timestamp(), atr_hist)
                    if updated: self.position = updated
                    if exit_flag:
                        pnl = (exit_price - self.position['entry']) * self.position['dir'] * \
                              self.position['leverage'] * self.position['size'] / self.position['entry']
                        pnl -= self.position['size'] * self.position['entry'] * self.fees * 2
                        self.capital += pnl
                        self.trades.append({
                            'symbol': sym, 'dir': self.position['dir'], 'entry': self.position['entry'],
                            'exit': exit_price, 'pnl': pnl, 'reason': reason,
                            'entry_time': self.position['entry_time'], 'exit_time': ts
                        })
                        self.equity.append(self.capital)
                        self.position = None
                continue

            # Generate signals
            candidates = []
            for sym, df in self.data.items():
                if ts not in df.index: continue
                window = df.loc[:ts].copy()
                if len(window) < 100: continue
                # Features already computed with shift, no lookahead
                row = window.iloc[-1]
                if 'ts' in row.index:  # might be a Series by timestamp
                    row = row.reset_index().iloc[-1]
                score = self.scorer.total_score(window.reset_index().rename(columns={window.index.name: 'ts'}))
                direction = 1 if row['ema20'] > row['ema50'] else -1
                candidates.append((sym, score, direction, row))

            if not candidates: continue

            candidates.sort(key=lambda x: x[1], reverse=True)
            best_sym, best_score, direction, row = candidates[0]

            # Risk sizing
            risk_pct = self.risk_mgr.risk_fraction(self.capital)
            # Fill simulation
            exec_price = self.fill_engine.execution_price(
                row['close'], direction, row['atr_pct'], row.get('volume_ratio', 1.0))
            if not self.fill_engine.simulate_fill(row.get('volume_ratio', 1.0), row['atr_pct']):
                continue
            size = (self.capital * risk_pct * self.leverage) / exec_price

            self.position = {
                'symbol': best_sym,
                'dir': direction,
                'entry': exec_price,
                'atr': row['atr'],
                'size': size,
                'leverage': self.leverage,
                'entry_time': ts.timestamp(),
                'be': False, 'trail': False,
                'trail_sl': exec_price - direction * self.exit_mgr.sl_atr * row['atr'],
                'sl': exec_price - direction * self.exit_mgr.sl_atr * row['atr'],
                'atr_pct_entry': row['atr_pct']
            }

        # Close last position
        if self.position:
            sym = self.position['symbol']
            df = self.data[sym]
            last_price = df.iloc[-1]['close']
            pnl = (last_price - self.position['entry']) * self.position['dir'] * \
                  self.position['leverage'] * self.position['size'] / self.position['entry']
            pnl -= self.position['size'] * self.position['entry'] * self.fees * 2
            self.capital += pnl
            self.trades.append({
                'symbol': sym, 'dir': self.position['dir'], 'entry': self.position['entry'],
                'exit': last_price, 'pnl': pnl, 'reason': 'eod',
                'entry_time': self.position['entry_time'], 'exit_time': self.end_date
            })
            self.equity.append(self.capital)

        return self.trades, self.equity
