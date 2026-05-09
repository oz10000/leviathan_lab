import websocket
import json
import threading
from datetime import datetime

class PaperTrader:
    def __init__(self, strategies, capital_manager):
        self.strategies = strategies
        self.cm = capital_manager
        self.ws = None
        self.running = False

    def on_message(self, ws, msg):
        data = json.loads(msg)
        if "data" in data:
            # Procesar tick de mercado y ejecutar señales de todas las estrategias
            for strat in self.strategies:
                signal = strat.generate_signal(data)   # Cada estrategia tiene su lógica
                if signal:
                    # Simular ejecución realista (slippage, comisión)
                    fill = self.simulate_fill(signal, data)
                    if fill:
                        self.log_trade(strat.name, fill)
                        strat.update_position(fill)

    def simulate_fill(self, signal, market_data):
        # Usar orderbook simulado para obtener slippage realista
        slippage = 0.001  # dummy
        return {
            "price": signal["price"] * (1 + signal["direction"] * slippage),
            "qty": signal["qty"],
            "fee": 0.0005
        }

    def start(self):
        self.running = True
        ws_url = "wss://wspap.okx.com/ws/v5/public?brokerId=9999"  # Testnet
        self.ws = websocket.WebSocketApp(ws_url,
            on_open=lambda ws: ws.send(json.dumps({
                "op": "subscribe",
                "args": [{"channel":"tickers","instType":"SWAP"}]
            })),
            on_message=self.on_message,
            on_close=lambda ws: print("WebSocket closed"))
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
