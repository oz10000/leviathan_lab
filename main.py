import argparse
import yaml
from engines.parser import generate_all_contracts
from engines.backtest_engine import BacktestEngine
from engines.capital_manager import CapitalManager
from engines.paper_trader import PaperTrader
from analytics.bias_detector import detect_lookahead
import os
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['parse','backtest','paper','validate'], default='backtest')
    parser.add_argument('--all', action='store_true', help='Run all strategies')
    args = parser.parse_args()

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    if args.mode == 'parse':
        generate_all_contracts()
        return

    # Load contracts
    contracts = []
    for fn in os.listdir('contracts'):
        if fn.endswith('.json'):
            with open(os.path.join('contracts', fn)) as f:
                contracts.append(json.load(f))

    if args.mode == 'backtest':
        cap_mgr = CapitalManager([c['name'] for c in contracts], config['capital_initial'])
        for c in contracts:
            strat = load_strategy_from_contract(c)   # need to implement
            # run walk‑forward
            engine = BacktestEngine(c['name'])
            results = engine.run_walk_forward()
            # update metrics
            # ...
        # generate artifacts
    elif args.mode == 'paper':
        # connect to testnet and run live simulation
        # use PaperTrader
        pass
    # ...

if __name__ == '__main__':
    main()
