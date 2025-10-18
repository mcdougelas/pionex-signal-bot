# Pionex Signal Bot

## Overview
An automated trading signal generator for Pionex that uses EMA (Exponential Moving Average) strategy to generate buy/sell signals and send them via webhook to Pionex trading platform.

**Current Status**: Converted from Pipedream/Cloudflare Worker setup to standalone Flask web application for easy testing and development.

<img width="620" height="540" alt="replit-bot" src="https://github.com/user-attachments/assets/acbe5808-b27c-418b-ba15-eea967305ae8" />
<img width="630" height="393" alt="replit-bot" src="https://github.com/user-attachments/assets/178464e4-c029-4533-9858-5bd5759798e7" />

## Recent Changes
- **2025-10-18**: Migrated from Pipedream/Cloudflare Worker to standalone Flask application
  - Created `bot.py` module with refactored bot logic
  - Created `app.py` Flask web server with API endpoints
  - Built web interface for manual testing and monitoring
  - Added support for test mode (without sending webhook)

## Project Architecture

### Files Structure
- `app.py` - Flask web server (runs on port 5000)
- `bot.py` - Core bot logic and trading signal generation
- `templates/index.html` - Web interface for monitoring and testing
- `pipedream.py` - Original Pipedream implementation (reference)
- `worker.js` - Original Cloudflare Worker implementation (reference)

### Trading Strategy
The bot uses a simple EMA crossover strategy:
- **Buy Signal**: Current price > EMA(50)
- **Sell Signal**: Current price < EMA(50)
- Only sends webhook when signal changes (not on every run)

### Configuration
Required environment variables (set in Replit Secrets):
- `PIONEX_TOKEN` - Your Pionex API token (found in Pionex signal log)
- `SIGNAL_KEY` - Your signal key (found in Pionex signal log)

Default settings (configurable in `bot.py`):
- Trading pair: ETH/USDT Perpetual
- Timeframe: 5M (5 minutes)
- Position size: 10% of equity per trade

## Features
- Web interface for manual testing
- Test mode to check signals without sending webhooks
- Real-time price and EMA display
- Signal history tracking
- Error handling and detailed logging

## Usage
1. Set `PIONEX_TOKEN` and `SIGNAL_KEY` in Replit Secrets
2. Run the application (workflow starts automatically)
3. Open the web interface
4. Click "Test Signal" to see current market conditions
5. Click "Run & Send Webhook" to execute and send signal to Pionex

## API Endpoints
- `GET /` - Web interface
- `POST /api/run` - Run bot logic (params: `send_webhook: boolean`)
- `GET /api/status` - Check configuration status

## How To :
### (old version)
- Cloudflare - create worker - worker.js - setting cron trigger - post webhook to pipedream -
- Pipeream step - get webhook - get data store - pipedream.py - update data store
