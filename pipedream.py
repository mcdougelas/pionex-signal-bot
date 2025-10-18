import requests
import json
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter, Retry
import os

def handler(pd):
    # ---------------- CONFIG ----------------
    PIONEX_TOKEN = os.environ["PIONEX_TOKEN"] # use pipedream environment to save the value, you can find it in pionex signal log
    SIGNAL_KEY = os.environ["SIGNAL_KEY"] # use pipedream environment to save the value, you can find it in pionex signal log

    BASE = "ETH" # you may change this to any supported Perpetual Pair/USDT that listed in https://api.pionex.com/api/v1/market/indexes
    QUOTE = "USDT"
    SYMBOL_API = f"{BASE}_{QUOTE}_PERP"
    SYMBOL_WEBHOOK = f"{BASE}{QUOTE}.P"
    INTERVAL = "5M" # you can change to 1M，5M，15M，30M，60M，4H，8H，12H，1D
    LIMIT = 50 # we can see this as length at indicator, bigger the number slower the proccess

    API_URL = "https://api.pionex.com/api/v1/market/klines"
    WEBHOOK_URL = f"https://www.pionex.com/signal/api/v1/signal_listener/trading_view?token={PIONEX_TOKEN}"

    # ------------- SESSION REQUEST -------------
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429,500,502,503,504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    # ------------- FETCH KLINES -------------
    try:
        params = {"symbol": SYMBOL_API, "interval": INTERVAL, "limit": LIMIT}
        res = session.get(API_URL, params=params, headers=headers, timeout=15)
        data = res.json()
        klines = data.get("data", {}).get("klines")

        if not klines:
            raise ValueError("❌ Klines invalid!")

        # 🔁 Balik urutan supaya terbaru di belakang
        klines = list(reversed(klines))

        close = [float(k["close"]) for k in klines]
        high = [float(k["high"]) for k in klines]
        low = [float(k["low"]) for k in klines]
        volume = [float(k["volume"]) for k in klines]

    except Exception as e:
        print("❌ Error fetching klines:", e)
        return {"error": str(e)}

    # ------------- INDICATOR FUNCTIONS -------------
    # convert your strategy to python, this example of ta.ema()
    def ema(arr, period):
        k = 2 / (period + 1)
        out = [arr[0]]
        for i in range(1, len(arr)):
            out.append(arr[i] * k + out[i-1] * (1 - k))
        return out

    # ------------- CALCULATE VALUES -------------
    ema50 = ema(close, 50)[-1] # this is the reason, why the limit value is 50
    price = close[-1]

    # ------------- LOAD PREVIOUS SIGNAL -------------
    try:
        prev_signal = pd.steps["create_step_data_store"]["$return_value"].get("prev_signal") # dont forget to create data store or your bot will be failed
    except Exception:
        prev_signal = None

    print(f"📂 Loaded prev_signal: {prev_signal}")

    # ------------- SIGNAL LOGIC -------------
    long_cond = price > ema50 
    short_cond = price < ema50 

    signal = "buy" if long_cond else "sell" if short_cond else None

    if signal is None:
        print("⏳ No signal generated.")
        return

    if signal == prev_signal:
        print(f"🔁 No change | Prev: {prev_signal} | Current: {signal}")
        return {"prev_signal": prev_signal}

    # ------------- SEND WEBHOOK -------------
    iso_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pos_size = round(10 / price, 4) # 10 equal to 10% equity
    pos_signed = pos_size if signal == "buy" else -pos_size

    # === Payload lengkap ===
    payload = {
        "signal_type": SIGNAL_KEY,
        "time": iso_time,                            ### Waktu UTC ISO
        "signal_param": "{}",
        "base": BASE,
        "quote": QUOTE,
        "symbol": SYMBOL_WEBHOOK,
        "price": str(price), # (round(price, 2)), 
        "data": {
            "action": signal,
            "position_size": str(pos_signed),
            "contracts": str(pos_size),
            "direction": "long" if signal == "buy" else "short"
        }
    }

    # Kirim webhook ke Pionex
    try:
        resp = session.post(WEBHOOK_URL, headers=headers, json=payload, timeout=15)
        print(f"📤 Webhook sent | {signal.upper()} | Price {price}")
        print("🪣 Response:", resp.status_code, resp.text)
        # Simpan prev_signal agar tidak kirim ulang
        return {"prev_signal": signal}
    except Exception as e:
        print("❌ Webhook failed:", e)
        return {"error": str(e)}
