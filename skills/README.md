# cTrader OpenAPI Proxy — Skills / Usage Guide

This proxy wraps the cTrader OpenAPI Protobuf TCP connection and exposes it as a simple HTTP REST API on `localhost:9009`. It is designed to be used as an **OpenAI / OpenClaw skill** or called from any HTTP client or automation.

---

## Getting Started

### 1. Install
```bash
make install
```

### 2. Configure
```bash
cp .env.example .env
```

Fill in `.env`:
```dotenv
CTRADER_CLIENT_ID=********
CTRADER_CLIENT_SECRET=********
CTRADER_TOKEN=********
CTRADER_ACCOUNTID=YOUR_ACCOUNT_ID   # your cTrader account ID — auto-used on startup
CTRADER_HOST=live            # "demo" or "live"
CONSOLE_LOG_LEVEL=INFO
```

### 3. Run
```bash
make run
```

The proxy is now running at `http://localhost:9009`.

> **Account auth is automatic.** The proxy reads `CTRADER_ACCOUNTID` from `.env` at startup and authorises that account straight away. Callers (including OpenAI / OpenClaw skills) do **not** need to know or pass the account ID.

---

## Endpoints

### Set Active Account _(optional)_
> The account from `.env` is authorised automatically on startup. Only call this if you want to switch to a different account at runtime.

```
POST /api/set-account
Content-Type: application/json

{}
```

Sending an empty body (or no body) uses `CTRADER_ACCOUNTID` from `.env`.  
To switch accounts, pass `{ "accountId": 12345678 }`.

**Expected response when already authorised (normal — not an error):**
```json
{
  "ctidTraderAccountId": "42425848",
  "errorCode": "ALREADY_LOGGED_IN",
  "description": "Trading account is already authorized in this channel"
}
```

---

### Get Trendbars (OHLC Candles)
```
POST /api/trendbars
Content-Type: application/json

{
  "fromTimestamp": 1700000000000,
  "toTimestamp":   1700086400000,
  "period":        "M5",
  "symbolId":      1
}
```

**Supported periods:** `M1`, `M2`, `M3`, `M4`, `M5`, `M10`, `M15`, `M30`, `H1`, `H4`, `H12`, `D1`, `W1`, `MN1`

> `symbolId` values are broker-specific. See [Finding your Symbol IDs](#finding-your-symbol-ids) below.

---

### Get Live Quote (Tick Data)
```
POST /api/live-quote
Content-Type: application/json

{
  "symbolId":           1,
  "quoteType":          "BID",
  "timeDeltaInSeconds": 60
}
```

`quoteType` is `"BID"` or `"ASK"`.

> `symbolId` values are broker-specific. See [Finding your Symbol IDs](#finding-your-symbol-ids) below.

---

### Place a Market / Limit / Stop Order
```
POST /api/market-order
Content-Type: application/json

{
  "symbolId":           158,
  "orderType":          "MARKET",
  "tradeSide":          "BUY",
  "volume":             1000,
  "comment":            "my trade",
  "relativeStopLoss":   200,
  "relativeTakeProfit": 350
}
```

- `orderType`: `"MARKET"`, `"LIMIT"`, or `"STOP"`
- `volume` is in **units** (not lots). Minimum is broker-dependent (typically 1000):

| `volume` | Lots | Size |
|---|---|---|
| `1000` | 0.01 | Micro lot (typical minimum) |
| `10000` | 0.1 | Mini lot |
| `100000` | 1 | Standard lot |

- `price`: required for `LIMIT` and `STOP` orders (e.g. `0.62500`)
- `relativeStopLoss` / `relativeTakeProfit`: distance in **pips** from entry, `MARKET` orders only (optional)

---

### Get Open Positions and Pending Orders

```
GET /get-data?command=ProtoOAReconcileReq
```

Returns all open positions (`position` array) and pending orders (`order` array) for the active account. Each position includes `positionId`, `symbolId`, `tradeSide`, `volume`, and `price`.

---

### Close an Open Position

```
GET /get-data?command=ClosePosition <positionId> <volumeInLots>
```

**Example** — close 1 lot of position 123456:
```
GET /get-data?command=ClosePosition 123456 1
```

> Get `positionId` from `ProtoOAReconcileReq` above.

---

### Cancel a Pending Order

```
GET /get-data?command=CancelOrder <orderId>
```

**Example:**
```
GET /get-data?command=CancelOrder 789
```

---

### Get Deal History (Closed Trades)

```
GET /get-data?command=ProtoOAGetDealListReq <fromTimestamp> <toTimestamp>
```

Timestamps are in **milliseconds** since Unix epoch. Returns all executed deals (closed/partially-closed trades) in the given range. Each deal includes `dealId`, `orderId`, `positionId`, `symbolId`, `tradeSide`, `volume`, `executionPrice`, `commission`, `dealStatus`, and `closePositionDetail` for closing deals.

**Example** — deals from the last 7 days:
```bash
NOW_MS=$(python3 -c "import time; print(int(time.time()*1000))")
FROM_MS=$(python3 -c "import time; print(int(time.time()*1000) - 604800000)")
curl -s "http://localhost:9009/get-data?command=ProtoOAGetDealListReq%20${FROM_MS}%20${NOW_MS}"
```

On Linux:
```bash
NOW_MS=$(date +%s%3N)
FROM_MS=$(( NOW_MS - 604800000 ))
curl -s "http://localhost:9009/get-data?command=ProtoOAGetDealListReq%20${FROM_MS}%20${NOW_MS}"
```

---

### Generic Command Endpoint
For any command not covered by the dedicated routes above:

```
GET /get-data?command=COMMAND_NAME arg1 arg2
```

No token required — credentials are read from `.env` on the server.

**All available commands:**
| Command | Args | Description |
|---|---|---|
| `setAccount` | `accountId` | Switch active account |
| `ProtoOAVersionReq` | — | Get API version |
| `ProtoOAGetAccountListByAccessTokenReq` | — | List all accounts accessible by the token |
| `ProtoOASymbolsListReq` | — | List all tradeable symbols with their IDs |
| `ProtoOAAssetListReq` | — | List all assets (currencies, etc.) |
| `ProtoOAAssetClassListReq` | — | List asset classes |
| `ProtoOASymbolCategoryListReq` | — | List symbol categories |
| `ProtoOATraderReq` | — | Get account details (balance, equity, leverage) |
| `ProtoOAReconcileReq` | — | Get open positions and pending orders |
| `ProtoOAGetTrendbarsReq` | `fromTs toTs period symbolId` | OHLC candle data |
| `ProtoOAGetTickDataReq` | `seconds quoteType symbolId` | Tick/quote data |
| `NewMarketOrder` | `symbolId tradeSide volume comment [sl] [tp]` | Place market order |
| `NewLimitOrder` | `symbolId tradeSide volume price` | Place limit order |
| `NewStopOrder` | `symbolId tradeSide volume price` | Place stop order |
| `ClosePosition` | `positionId volume` | Close an open position |
| `CancelOrder` | `orderId` | Cancel a pending order |
| `OrderDetails` | `orderId` | Get details of a specific order |
| `OrderListByPositionId` | `positionId` | Get order history for a position |
| `DealOffsetList` | `dealId` | Get offset deals for a deal |
| `GetPositionUnrealizedPnL` | — | Get unrealised P&L for all open positions |
| `ProtoOAGetDealListReq` | `fromTimestamp toTimestamp` | **Deal/trade history (closed trades)** |
| `ProtoOAExpectedMarginReq` | `symbolId volume` | Calculate expected margin for a trade |

---

## Calling from curl (macOS)

> macOS does not support `date +%s%3N`. Use `python3` for millisecond timestamps.

```bash
# (Optional) Switch account — reads CTRADER_ACCOUNTID from .env
curl -s -X POST http://localhost:9009/api/set-account

# Get 5-min candles for the last hour
NOW_MS=$(python3 -c "import time; print(int(time.time()*1000))")
FROM_MS=$(python3 -c "import time; print(int(time.time()*1000) - 3600000)")

curl -s -X POST http://localhost:9009/api/trendbars \
  -H "Content-Type: application/json" \
  -d "{\"fromTimestamp\": $FROM_MS, \"toTimestamp\": $NOW_MS, \"period\": \"M5\", \"symbolId\": 1}"

# Get last 60 seconds of BID ticks
curl -s -X POST http://localhost:9009/api/live-quote \
  -H "Content-Type: application/json" \
  -d '{"symbolId": 1, "quoteType": "BID", "timeDeltaInSeconds": 60}'

# List all symbols (find your broker's symbolIds)
curl -s "http://localhost:9009/get-data?command=ProtoOASymbolsListReq"
```

## Calling from curl (Linux / Ubuntu)

On Linux `date +%s%3N` gives milliseconds directly:

```bash
NOW_MS=$(date +%s%3N)
FROM_MS=$(( NOW_MS - 3600000 ))

curl -s -X POST http://localhost:9009/api/trendbars \
  -H "Content-Type: application/json" \
  -d "{\"fromTimestamp\": $FROM_MS, \"toTimestamp\": $NOW_MS, \"period\": \"M5\", \"symbolId\": 1}"

curl -s -X POST http://localhost:9009/api/live-quote \
  -H "Content-Type: application/json" \
  -d '{"symbolId": 1, "quoteType": "BID", "timeDeltaInSeconds": 60}'
```

---

## Calling from Python (OpenAI / OpenClaw Skill)

```python
import requests
import time

BASE = "http://localhost:9009"

# No set-account call needed — auto-authorised from .env on startup.
# Only call if switching accounts at runtime:
# requests.post(f"{BASE}/api/set-account")

# Get 5-minute candles for the last hour
now_ms  = int(time.time() * 1000)
from_ms = now_ms - 3_600_000

resp = requests.post(f"{BASE}/api/trendbars", json={
    "fromTimestamp": from_ms,
    "toTimestamp":   now_ms,
    "period":        "M5",
    "symbolId":      1,
})
print(resp.json())

# Get live BID quotes (last 60 seconds)
resp = requests.post(f"{BASE}/api/live-quote", json={
    "symbolId":           1,
    "quoteType":          "BID",
    "timeDeltaInSeconds": 60,
})
print(resp.json())

# Place a market buy (1000 units = 0.01 lot minimum, 20 pip SL, 35 pip TP)
resp = requests.post(f"{BASE}/api/market-order", json={
    "symbolId":           158,
    "orderType":          "MARKET",
    "tradeSide":          "BUY",
    "volume":             1000,
    "comment":            "AUDUSD long",
    "relativeStopLoss":   200,
    "relativeTakeProfit": 350,
})
print(resp.json())

# Place a limit buy at a specific price (0.01 lot)
resp = requests.post(f"{BASE}/api/market-order", json={
    "symbolId":  158,
    "orderType": "LIMIT",
    "tradeSide": "BUY",
    "volume":    1000,
    "price":     0.62500,
})
print(resp.json())

# Place a stop sell at a specific price
resp = requests.post(f"{BASE}/api/market-order", json={
    "symbolId":  158,
    "orderType": "STOP",
    "tradeSide": "SELL",
    "volume":    1000,
    "price":     0.61900,
})
print(resp.json())

# Get open positions and pending orders
resp = requests.get(f"{BASE}/get-data", params={"command": "ProtoOAReconcileReq"})
print(resp.json())

# Close an open position (use positionId from ProtoOAReconcileReq above)
resp = requests.get(f"{BASE}/get-data", params={"command": "ClosePosition 123456 1"})
print(resp.json())

# Cancel a pending order
resp = requests.get(f"{BASE}/get-data", params={"command": "CancelOrder 789"})
print(resp.json())

# Deal / trade history — last 7 days (closed trades)
now_ms  = int(time.time() * 1000)
from_ms = now_ms - 7 * 24 * 3_600_000
resp = requests.get(f"{BASE}/get-data", params={
    "command": f"ProtoOAGetDealListReq {from_ms} {now_ms}"
})
print(resp.json())
```

---

## Finding your Symbol IDs

Symbol IDs are **broker-specific** — they differ between brokers and even between demo and live accounts. You must look them up before placing orders or fetching candle/tick data.

### Fetch all available symbols

```bash
curl -s "http://localhost:9009/get-data?command=ProtoOASymbolsListReq"
```

Truncated example response:
```json
{
  "symbol": [
    { "symbolId": 1,   "symbolName": "EURUSD" },
    { "symbolId": 2,   "symbolName": "GBPUSD" },
    { "symbolId": 158, "symbolName": "AUDUSD_SB" },
    ...
  ]
}
```

Note the `symbolId` for the instrument you want to trade and use it in all subsequent requests.

### Search for a specific symbol (Python)

```python
import requests

resp = requests.get("http://localhost:9009/get-data", params={"command": "ProtoOASymbolsListReq"})
symbols = resp.json().get("symbol", [])

# Find by name (case-insensitive, partial match)
search = "AUDUSD"
matches = [s for s in symbols if search.lower() in s["symbolName"].lower()]
for m in matches:
    print(m["symbolId"], m["symbolName"])
# Example output:
# 158 AUDUSD_SB
# 159 AUDUSD
```

### Use the ID in an order

Once you have the `symbolId`, pass it directly:

```python
requests.post("http://localhost:9009/api/market-order", json={
    "symbolId":  158,   # AUDUSD_SB on this broker
    "orderType": "MARKET",
    "tradeSide": "BUY",
    "volume":    1000,  # 0.01 lot minimum
})
```

Or with curl:

```bash
curl -s -X POST http://localhost:9009/api/market-order \
  -H "Content-Type: application/json" \
  -d '{"symbolId": 158, "orderType": "MARKET", "tradeSide": "BUY", "volume": 1000}'
```
