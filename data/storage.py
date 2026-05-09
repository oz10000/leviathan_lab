import duckdb
from pathlib import Path

DB_PATH = "storage/leviathan.duckdb"

def get_connection():
    Path("storage").mkdir(exist_ok=True)
    return duckdb.connect(DB_PATH)

def init_db():
    con = get_connection()
    con.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY,
        strategy TEXT,
        symbol TEXT,
        direction INTEGER,
        entry_price DOUBLE,
        exit_price DOUBLE,
        pnl DOUBLE,
        reason TEXT,
        entry_time TIMESTAMP,
        exit_time TIMESTAMP,
        run_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    con.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
        timestamp TIMESTAMP,
        equity DOUBLE,
        run_id TEXT
    )""")
    con.execute("""
    CREATE TABLE IF NOT EXISTS metrics_history (
        run_id TEXT,
        strategy TEXT,
        sharpe DOUBLE,
        pf DOUBLE,
        max_dd DOUBLE,
        win_rate DOUBLE,
        roi DOUBLE,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    con.close()

def save_trades(trades, strategy_name, run_id):
    con = get_connection()
    for t in trades:
        con.execute("""
        INSERT INTO trades (strategy, symbol, direction, entry_price, exit_price, pnl, reason,
                            entry_time, exit_time, run_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [strategy_name, t['symbol'], t['dir'], t['entry'], t['exit'],
              t['pnl'], t['reason'], pd.Timestamp(t['entry_time'], unit='s'),
              pd.Timestamp(t['exit_time'], unit='s'), run_id])
    con.close()

def save_metrics(run_id, strategy, metrics):
    con = get_connection()
    con.execute("""
    INSERT INTO metrics_history (run_id, strategy, sharpe, pf, max_dd, win_rate, roi)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [run_id, strategy, metrics.get('sharpe',0), metrics.get('pf',0),
          metrics.get('max_dd',0), metrics.get('win_rate',0), metrics.get('roi',0)])
    con.close()
