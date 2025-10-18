from flask import Flask, render_template, jsonify, request
from bot import PionexBot
import os
import json

app = Flask(__name__)

bot_instance = PionexBot()

STATE_FILE = 'bot_state.json'

def load_state():
    """Load previous signal state from file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('prev_signal')
    except Exception:
        pass
    return None

def save_state(signal):
    """Save signal state to file"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({'prev_signal': signal}, f)
    except Exception:
        pass

bot_instance.prev_signal = load_state()

@app.route('/')
def index():
    pionex_token_set = bool(os.environ.get("PIONEX_TOKEN"))
    signal_key_set = bool(os.environ.get("SIGNAL_KEY"))
    
    return render_template('index.html', 
                         pionex_token_set=pionex_token_set,
                         signal_key_set=signal_key_set)

@app.route('/api/run', methods=['POST'])
def run_bot():
    try:
        data = request.get_json() or {}
        send_webhook = data.get('send_webhook', False)
        
        result = bot_instance.run(send_webhook=send_webhook)
        
        if result.get('status') == 'error':
            return jsonify(result), 500
        
        if send_webhook and bot_instance.prev_signal:
            save_state(bot_instance.prev_signal)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    pionex_token = os.environ.get("PIONEX_TOKEN", "")
    signal_key = os.environ.get("SIGNAL_KEY", "")
    
    return jsonify({
        "pionex_token_set": bool(pionex_token),
        "signal_key_set": bool(signal_key),
        "ready": bool(pionex_token and signal_key)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
