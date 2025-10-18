from flask import Flask, render_template, jsonify, request
from bot import PionexBot
import os

app = Flask(__name__)

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
        
        bot = PionexBot()
        result = bot.run(send_webhook=send_webhook)
        
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
    app.run(host='0.0.0.0', port=5000, debug=True)
