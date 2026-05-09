import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.features import compute_features
from core.exit_manager import HybridExit
from core.risk import KellyRiskManager

class LeviathanBacktest:
    def __init__(self, contract, capital=1000, start_date=None, end_date=None):
        self.contract = contract
        self.capital = capital
        self.start_date = start_date or (datetime.utcnow() - timedelta(days=90))
        self.end_date = end_date or datetime.utcnow()
        self.fees = 0.0005  # taker fee OKX
        self.slippage_bps = 1.0
        self.latency_ms = 150
        self.universe = self._fetch_universe()
        self.data = self._download_data()

    def _fetch_universe(self):
        # Descarga top 40 USDT perpetuals por volumen
        url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
        resp = requests.get(url).json()
        tickers = []
        for item in resp["data"]:
            instId = item["instId"]
            if instId.endswith("-USDT-SWAP"):
                tickers.append({
                    "symbol": instId.replace("-USDT-SWAP", ""),
                    "vol24h": float(item["vol24h"])
                })
        df = pd.DataFrame(tickers).sort_values("vol24h", ascending=False)
        return df.head(40)["symbol"].tolist()

    def _download_candles(self, symbol, bar="5m", limit=1000):
        instId = f"{symbol}-USDT-SWAP"
        url = f"https://www.okx.com/api/v5/market/candles?instId={instId}&bar={bar}&limit={limit}"
        resp = requests.get(url).json()
        if resp.get("code") != "0": return None
        cols = ["ts","open","high","low","close","vol"]
        data = resp["data"]
        df = pd.DataFrame(data, columns=cols)
        for c in ["open","high","low","close","vol"]:
            df[c] = pd.to_numeric(df[c])
        df["ts"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
        return df.sort_values("ts")

    def _download_data(self):
        all_data = {}
        for sym in self.universe:
            df = self._download_candles(sym)
            if df is not None:
                all_data[sym] = compute_features(df)
        return all_data

    def run(self):
        # Implementación del bucle de backtest con rotación multi‑activo
        # usando los parámetros del contrato (umbrales, pesos, etc.).
        pass  # Detalles completos en el paquete final
