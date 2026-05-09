import numpy as np
import pandas as pd
from copy import deepcopy
from engines.backtest_engine import BacktestEngine
from analytics.metrics import calculate_all_metrics

def run_walkforward(strategy, data, config, train_ratio=0.7, min_train_bars=1000):
    # Sort timeline
    timeline = sorted(set().union(*[d.index for d in data.values()]))
    split_idx = int(len(timeline) * train_ratio)
    train_ts = timeline[:split_idx]
    test_ts = timeline[split_idx:]
    if len(train_ts) < min_train_bars or len(test_ts) < min_train_bars:
        return None

    # Train
    train_data = {sym: df[df.index <= train_ts[-1]] for sym, df in data.items()}
    test_data = {sym: df[df.index > train_ts[-1]] for sym, df in data.items()}

    engine_train = BacktestEngine(strategy, train_data, config, strategy_name=strategy.get('name', 'strategy'))
    train_trades, train_equity = engine_train.run()
    train_metrics = calculate_all_metrics(train_trades, train_equity, config['capital_initial'],
                                          start_date=train_ts[0], end_date=train_ts[-1])

    engine_test = BacktestEngine(strategy, test_data, config, strategy_name=strategy.get('name', 'strategy'))
    test_trades, test_equity = engine_test.run()
    test_metrics = calculate_all_metrics(test_trades, test_equity, config['capital_initial'],
                                         start_date=test_ts[0], end_date=test_ts[-1])

    degradation = {key: test_metrics.get(key, 0) / (train_metrics.get(key, 1) or 1)
                   for key in ['sharpe', 'pf', 'roi']}
    return {
        'train': train_metrics,
        'test': test_metrics,
        'degradation': degradation,
        'train_period': [str(train_ts[0]), str(train_ts[-1])],
        'test_period': [str(test_ts[0]), str(test_ts[-1])]
    }
