# ctrader-openapi-proxy

A lightweight HTTP proxy that wraps the cTrader OpenAPI Protobuf TCP connection and exposes it as a REST API on `localhost:9009`. Designed to be called as an **OpenAI / OpenClaw skill** or from any HTTP client.

## Setup

```bash
make install
cp .env.example .env
```

Fill in your credentials in `.env`:

```dotenv
CTRADER_CLIENT_ID=********
CTRADER_CLIENT_SECRET=********
CTRADER_TOKEN=********
CTRADER_ACCOUNTID=YOUR_ACCOUNT_ID   # your cTrader account ID
CTRADER_HOST=live            # "demo" or "live"
CONSOLE_LOG_LEVEL=INFO
```

## Run

**Foreground (for development/testing):**
```bash
make run
```

**Background (for production / keeping it running after closing the terminal):**
```bash
# Using nohup
nohup make run > logs/proxy.log 2>&1 &
echo "PID: $!"

# Check it started
tail -f logs/proxy.log

# Stop it
pkill -f "python main.py"
```

Or with tmux (lets you reattach later):
```bash
tmux new-session -d -s proxy 'make run'
tmux attach -t proxy   # reattach anytime
```

The proxy starts at `http://localhost:9009`.

> **Account auth is automatic.** On startup the proxy reads `CTRADER_ACCOUNTID` from `.env` and authorises that account immediately — no manual `/api/set-account` call required.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/set-account` | (Optional) Switch active account — reads `CTRADER_ACCOUNTID` from `.env` if no body sent |
| `POST` | `/api/trendbars` | Fetch OHLC candle data |
| `POST` | `/api/live-quote` | Fetch recent tick/quote data |
| `POST` | `/api/market-order` | Place a market, limit, or stop order (`volume` in units: 1000 = 0.01 lot) |
| `GET` | `/get-data?command=` | Generic command passthrough (no token needed) |

See [skills/README.md](skills/README.md) for full request/response examples, curl commands, and a Python usage guide.

> **Symbol IDs are broker-specific.** Before placing orders or fetching candle data, run `GET /get-data?command=ProtoOASymbolsListReq` to retrieve the list of symbols and their IDs for your broker. See [Finding your Symbol IDs](skills/README.md#finding-your-symbol-ids) in the skills guide.

## Deploy on Ubuntu Server

### Prerequisites
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### Install
```bash
git clone https://github.com/LogicalSapien/ctrader-openapi-proxy.git
cd ctrader-openapi-proxy
make install
cp .env.example .env
nano .env   # fill in your credentials
```

> **Important:** `.env` must exist before starting the service. The service will fail if this file is missing.

### Run as a systemd service (auto-start on boot)
```bash
# Automatically fills in the correct user and path — run from inside the repo directory
make install-service
sudo systemctl start ctrader-proxy
```

Check status and logs:
```bash
sudo systemctl status ctrader-proxy
sudo journalctl -u ctrader-proxy -f
```

> The proxy binds to `localhost:9009` only — it is **not exposed externally** by default. If you want to reach it from another machine or Docker container, proxy through nginx or open the port via `ufw allow 9009` (only on a trusted network).