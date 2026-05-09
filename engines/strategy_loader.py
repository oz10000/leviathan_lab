import json
import importlib
import sys
from typing import Dict

class StrategyLoader:
    def __init__(self, contract_path: str):
        with open(contract_path) as f:
            self.contract = json.load(f)
        self.name = self.contract["name"]
        self.params = self.contract.get("params", {})

    def load_scoring(self):
        # If contract contains code for scoring, evaluate it safely
        code = self.contract.get("code", "")
        scoring_class = None
        if code:
            # execute in isolated namespace
            namespace = {}
            exec(code, namespace)
            for item in namespace.values():
                if hasattr(item, 'total_score'):
                    scoring_class = item
                    break
        return scoring_class
