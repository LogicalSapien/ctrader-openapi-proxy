"""
skills/example_usage.py

Demonstrates all proxy endpoints. Run the proxy first with `make run`,
then execute this file: python skills/example_usage.py
"""

import requests
import time

BASE = "http://localhost:9009"
ACCOUNT_ID = 0         # Replace with your account ID (or leave 0 to use CTRADER_ACCOUNTID from .env)
SYMBOL_ID  = 1         # Replace with the symbol ID from your broker

def set_account():
    # If ACCOUNT_ID is 0, send empty body — server uses CTRADER_ACCOUNTID from its .env
    body = {"accountId": ACCOUNT_ID} if ACCOUNT_ID else {}
    r = requests.post(f"{BASE}/api/set-account", json=body)
    print("set-account:", r.json())

def get_trendbars():
    now_ms  = int(time.time() * 1000)
    from_ms = now_ms - 3_600_000  # last 1 hour
    r = requests.post(f"{BASE}/api/trendbars", json={
        "fromTimestamp": from_ms,
        "toTimestamp":   now_ms,
        "period":        "M5",
        "symbolId":      SYMBOL_ID,
    })
    print("trendbars:", r.json())

def get_live_quote():
    r = requests.post(f"{BASE}/api/live-quote", json={
        "symbolId":           SYMBOL_ID,
        "quoteType":          "BID",
        "timeDeltaInSeconds": 60,
    })
    print("live-quote:", r.json())

def place_market_buy():
    r = requests.post(f"{BASE}/api/market-order", json={
        "symbolId":           158,    # AUDUSD_SB — replace with your broker's symbolId
        "orderType":          "MARKET",
        "tradeSide":          "BUY",
        "volume":             1000,   # units: 1000 = 0.01 lot, 10000 = 0.1 lot, 100000 = 1 lot
        "comment":            "test buy",
        "relativeStopLoss":   200,    # pips
        "relativeTakeProfit": 350,    # pips
    })
    print("market-order:", r.json())

def list_symbols():
    # No token needed — credentials are read from .env on the server
    r = requests.get(f"{BASE}/get-data", params={"command": "ProtoOASymbolsListReq"})
    print("symbols:", r.json())

def get_open_positions():
    r = requests.get(f"{BASE}/get-data", params={"command": "ProtoOAReconcileReq"})
    print("positions:", r.json())

def close_position(position_id: int, volume_lots: int = 1):
    r = requests.get(f"{BASE}/get-data", params={"command": f"ClosePosition {position_id} {volume_lots}"})
    print("close-position:", r.json())

def cancel_order(order_id: int):
    r = requests.get(f"{BASE}/get-data", params={"command": f"CancelOrder {order_id}"})
    print("cancel-order:", r.json())

if __name__ == "__main__":
    set_account()
    get_open_positions()     # see positions + symbolIds before trading
    get_trendbars()
    get_live_quote()
    # list_symbols()         # Uncomment to list all available symbol IDs
    # place_market_buy()     # Uncomment to actually place a trade
    # close_position(123456) # Uncomment and replace with real positionId
    # cancel_order(789)      # Uncomment and replace with real orderId
