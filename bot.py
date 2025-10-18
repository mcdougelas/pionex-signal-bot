import requests
import json
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter, Retry
import os

class PionexBot:
    def __init__(self):
        self.pionex_token = os.environ.get("PIONEX_TOKEN", "")
        self.signal_key = os.environ.get("SIGNAL_KEY", "")
        
        self.base = "ETH"
        self.quote = "USDT"
        self.symbol_api = f"{self.base}_{self.quote}_PERP"
        self.symbol_webhook = f"{self.base}{self.quote}.P"
        self.interval = "5M"
        self.limit = 50
        
        self.api_url = "https://api.pionex.com/api/v1/market/klines"
        self.webhook_url = f"https://www.pionex.com/signal/api/v1/signal_listener/trading_view?token={self.pionex_token}"
        
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        
        self.prev_signal = None
    
    def ema(self, arr, period):
        """Calculate Exponential Moving Average"""
        k = 2 / (period + 1)
        out = [arr[0]]
        for i in range(1, len(arr)):
            out.append(arr[i] * k + out[i-1] * (1 - k))
        return out
    
    def fetch_klines(self):
        """Fetch klines data from Pionex API"""
        try:
            params = {"symbol": self.symbol_api, "interval": self.interval, "limit": self.limit}
            res = self.session.get(self.api_url, params=params, headers=self.headers, timeout=15)
            data = res.json()
            klines = data.get("data", {}).get("klines")
            
            if not klines:
                raise ValueError("Klines invalid!")
            
            klines = list(reversed(klines))
            
            close = [float(k["close"]) for k in klines]
            high = [float(k["high"]) for k in klines]
            low = [float(k["low"]) for k in klines]
            volume = [float(k["volume"]) for k in klines]
            
            return {
                "close": close,
                "high": high,
                "low": low,
                "volume": volume
            }
        except Exception as e:
            raise Exception(f"Error fetching klines: {e}")
    
    def calculate_signal(self, close):
        """Calculate trading signal based on EMA strategy"""
        ema50 = self.ema(close, 50)[-1]
        price = close[-1]
        
        long_cond = price > ema50
        short_cond = price < ema50
        
        signal = "buy" if long_cond else "sell" if short_cond else None
        
        return signal, price, ema50
    
    def send_webhook(self, signal, price):
        """Send webhook to Pionex"""
        if not self.pionex_token or not self.signal_key:
            raise Exception("PIONEX_TOKEN and SIGNAL_KEY must be set")
        
        iso_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pos_size = round(10 / price, 4)
        pos_signed = pos_size if signal == "buy" else -pos_size
        
        payload = {
            "signal_type": self.signal_key,
            "time": iso_time,
            "signal_param": "{}",
            "base": self.base,
            "quote": self.quote,
            "symbol": self.symbol_webhook,
            "price": str(price),
            "data": {
                "action": signal,
                "position_size": str(pos_signed),
                "contracts": str(pos_size),
                "direction": "long" if signal == "buy" else "short"
            }
        }
        
        resp = self.session.post(self.webhook_url, headers=self.headers, json=payload, timeout=15)
        return {
            "status_code": resp.status_code,
            "response": resp.text
        }
    
    def run(self, send_webhook=True):
        """Run the bot logic"""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "message": ""
        }
        
        try:
            kline_data = self.fetch_klines()
            close = kline_data["close"]
            
            signal, price, ema50 = self.calculate_signal(close)
            
            result["price"] = price
            result["ema50"] = ema50
            result["signal"] = signal
            result["prev_signal"] = self.prev_signal
            
            if signal is None:
                result["message"] = "No signal generated"
                return result
            
            if signal == self.prev_signal:
                result["message"] = f"No change | Prev: {self.prev_signal} | Current: {signal}"
                return result
            
            if send_webhook:
                webhook_result = self.send_webhook(signal, price)
                result["webhook"] = webhook_result
                result["message"] = f"Webhook sent | {signal.upper()} | Price {price}"
                self.prev_signal = signal
            else:
                result["message"] = f"Signal generated: {signal.upper()} | Price {price} (webhook not sent)"
            
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)
            return result
