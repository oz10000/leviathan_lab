import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time, os

class OKXFetcher:
    def __init__(self, testnet=False):
        self.exchange = ccxt.okx({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        if testnet:
            self.exchange.set_sandbox_mode(True)

    def fetch_top_symbols(self, n=40, min_vol=2_000_000):
        self.exchange.load_markets()
        tickers = self.exchange.fetch_tickers()
        candidates = []
        for sym, ticker in tickers.items():
            if sym.endswith('/USDT:USDT') and ticker.get('quoteVolume', 0) >= min_vol:
                candidates.append({'symbol': sym.split('/')[0], 'volume': ticker['quoteVolume']})
        df = pd.DataFrame(candidates).sort_values('volume', ascending=False)
        return df.head(n)['symbol'].tolist()

    def fetch_ohlcv(self, symbol, timeframe='5m', since=None, limit=1000):
        inst = f"{symbol}/USDT:USDT"
        all_candles = []
        while True:
            try:
                candles = self.exchange.fetch_ohlcv(inst, timeframe, since=since, limit=limit)
                if not candles: break
                all_candles.extend(candles)
                since = candles[-1][0] + 1
                time.sleep(self.exchange.rateLimit / 1000 * 2)
                if len(candles) < limit: break
            except Exception as e:
                print(f"Error {symbol} {timeframe}: {e}")
                time.sleep(10)
                continue
        if not all_candles: return None
        df = pd.DataFrame(all_candles, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        df.set_index('ts', inplace=True)
        return df

    def download_all(self, symbols, timeframes, days=90, save_dir='data/parquet'):
        os.makedirs(save_dir, exist_ok=True)
        since = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
        for sym in symbols:
            for tf in timeframes:
                fname = f"{save_dir}/{sym}_{tf}.parquet"
                if os.path.exists(fname): continue
                df = self.fetch_ohlcv(sym, tf, since=since)
                if df is not None and not df.empty:
                    df.to_parquet(fname)
                    print(f"Saved {sym} {tf}: {len(df)} rows")
                time.sleep(0.5)
