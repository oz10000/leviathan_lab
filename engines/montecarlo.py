import numpy as np
from analytics.metrics import calculate_all_metrics

def monte_carlo_simulation(trades, initial_capital, num_runs=200, random_seed=42):
    rng = np.random.default_rng(random_seed)
    pnls = [t['pnl'] for t in trades]
    results = []
    for _ in range(num_runs):
        shuffled = rng.permutation(pnls)
        equity = [initial_capital]
        for pnl in shuffled:
            equity.append(equity[-1] + pnl)
        m = calculate_all_metrics(trades, equity, initial_capital, start_date=None, end_date=None)
        results.append(m)
    # Aggregate
    sharpe_list = [m['sharpe'] for m in results]
    pf_list = [m['pf'] for m in results if m['pf'] != np.inf]
    dd_list = [m['max_dd'] for m in results]
    return {
        'sharpe_mean': np.mean(sharpe_list),
        'sharpe_std': np.std(sharpe_list),
        'pf_mean': np.mean(pf_list),
        'dd_mean': np.mean(dd_list),
        'dd_95pct': np.percentile(dd_list, 95)
    }
