#!/usr/bin/env python

from klein import Klein
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.endpoints import EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
import json
from twisted.internet import endpoints, reactor
from twisted.web.server import Site
import sys
from twisted.web.static import File
import datetime
from google.protobuf.json_format import MessageToJson
import calendar
from dotenv import load_dotenv
from twisted.web.server import NOT_DONE_YET
from libs.config import CTRADER_TOKEN, CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_HOST, CTRADER_ACCOUNTID
from libs.logging_config import logger


load_dotenv(".env")

token = CTRADER_TOKEN

host = "localhost"
port = 9009

if not token:
    logger.error("Error: No token found in environment variables")
    sys.exit(1)
currentAccountId = None

auth = Auth(CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, f"http://{host}:{port}/redirect")
authUri = auth.getAuthUri()
app = Klein()

client = None

def onError(failure):
    logger.error("Error: \n", failure)

def connected(client):
    logger.info("Client Connected")
    request = ProtoOAApplicationAuthReq()
    request.clientId = CTRADER_CLIENT_ID
    request.clientSecret = CTRADER_CLIENT_SECRET
    deferred = client.send(request)
    deferred.addErrback(onError)

def disconnected(client, reason):
    logger.info("Client Disconnected, reason: \n", reason)

def onMessageReceived(client, message):
    if message.payloadType == ProtoHeartbeatEvent().payloadType:
        return
    logger.debug(f"Received Message: \n {message}")
    if message.payloadType == ProtoOAApplicationAuthRes().payloadType:
        logger.info("App auth successful.")
        if CTRADER_ACCOUNTID:
            logger.info(f"Auto-setting account {CTRADER_ACCOUNTID} from .env")
            setAccount(CTRADER_ACCOUNTID)
        else:
            logger.warning("CTRADER_ACCOUNTID not set in .env — call /api/set-account manually")
    elif message.payloadType == ProtoOAAccountAuthRes().payloadType:
        pb = Protobuf.extract(message)
        acct_id = str(pb.ctidTraderAccountId)
        authorizedAccounts.append(acct_id)
        logger.info(f"Account {acct_id} authorized successfully.")
    elif message.payloadType == ProtoOAErrorRes().payloadType:
        pb = Protobuf.extract(message)
        logger.error(f"API error: {pb.errorCode} — {pb.description}")
    else:
        logger.info(f"Message received: payloadType={message.payloadType}")

authorizedAccounts = []

def setAccount(accountId):
    global currentAccountId
    currentAccountId = int(accountId)
    if accountId not in authorizedAccounts:
        return sendProtoOAAccountAuthReq(accountId)
    logger.info("Account already authorized")
    return "Account changed successfully"

def sendProtoOAVersionReq(clientMsgId=None):
    request = ProtoOAVersionReq()
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAGetAccountListByAccessTokenReq(clientMsgId=None):
    request = ProtoOAGetAccountListByAccessTokenReq()
    request.accessToken = token
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAccountLogoutReq(clientMsgId=None):
    request = ProtoOAAccountLogoutReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAccountAuthReq(clientMsgId=None):
    request = ProtoOAAccountAuthReq()
    request.ctidTraderAccountId = currentAccountId
    request.accessToken = token
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAssetListReq(clientMsgId=None):
    request = ProtoOAAssetListReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAssetClassListReq(clientMsgId=None):
    request = ProtoOAAssetClassListReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOASymbolCategoryListReq(clientMsgId=None):
    request = ProtoOASymbolCategoryListReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOASymbolsListReq(includeArchivedSymbols=False, clientMsgId=None):
    request = ProtoOASymbolsListReq()
    request.ctidTraderAccountId = currentAccountId
    request.includeArchivedSymbols = includeArchivedSymbols if type(includeArchivedSymbols) is bool else bool(includeArchivedSymbols)
    deferred = client.send(request)
    deferred.addErrback(onError)
    return deferred

def sendProtoOATraderReq(clientMsgId=None):
    request = ProtoOATraderReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAUnsubscribeSpotsReq(symbolId, clientMsgId=None):
    request = ProtoOAUnsubscribeSpotsReq()
    request.ctidTraderAccountId = currentAccountId
    request.symbolId.append(int(symbolId))
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAReconcileReq(clientMsgId=None):
    request = ProtoOAReconcileReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAGetTrendbarsReq(fromTimestamp, toTimestamp, period, symbolId, clientMsgId=None):
    request = ProtoOAGetTrendbarsReq()
    request.ctidTraderAccountId = currentAccountId
    request.period = ProtoOATrendbarPeriod.Value(period)
    request.fromTimestamp = int(fromTimestamp)
    request.toTimestamp = int(toTimestamp)
    request.symbolId = int(symbolId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAGetTickDataReq(seconds, quoteType, symbolId, clientMsgId=None):
    request = ProtoOAGetTickDataReq()
    request.ctidTraderAccountId = currentAccountId
    request.type = ProtoOAQuoteType.Value(quoteType.upper())
    request.fromTimestamp = int(calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(seconds=int(seconds))).utctimetuple())) * 1000
    request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000
    request.symbolId = int(symbolId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOANewOrderReq(symbolId, orderType, tradeSide, volume, price=None, comment=None, relativeStopLoss=None, relativeTakeProfit=None, clientMsgId=None):
    request = ProtoOANewOrderReq()
    request.ctidTraderAccountId = currentAccountId
    request.symbolId = int(symbolId)
    request.orderType = ProtoOAOrderType.Value(orderType.upper())
    request.tradeSide = ProtoOATradeSide.Value(tradeSide.upper())
    request.volume = int(float(volume))  # volume in units: 1000 = 0.01 lot, 10000 = 0.1 lot, 100000 = 1 lot
    request.comment = comment
    if request.orderType == ProtoOAOrderType.LIMIT:
        request.limitPrice = float(price)
    elif request.orderType == ProtoOAOrderType.STOP:
        request.stopPrice = float(price)
    if request.orderType == ProtoOAOrderType.MARKET:
        if relativeStopLoss not in (None, ""):
            request.relativeStopLoss = int(relativeStopLoss)
        if relativeTakeProfit not in (None, ""):
            request.relativeTakeProfit = int(relativeTakeProfit)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendNewMarketOrder(symbolId, tradeSide, volume, comment, relativeStopLoss=None, relativeTakeProfit=None, clientMsgId=None):
    return sendProtoOANewOrderReq(symbolId, "MARKET", tradeSide, volume, None, comment, relativeStopLoss, relativeTakeProfit, clientMsgId)

def sendNewLimitOrder(symbolId, tradeSide, volume, price, clientMsgId=None):
    return sendProtoOANewOrderReq(symbolId, "LIMIT", tradeSide, volume, price, None, None, None, clientMsgId)

def sendNewStopOrder(symbolId, tradeSide, volume, price, clientMsgId=None):
    return sendProtoOANewOrderReq(symbolId, "STOP", tradeSide, volume, price, None, None, None, clientMsgId)

def sendProtoOAClosePositionReq(positionId, volume, clientMsgId=None):
    request = ProtoOAClosePositionReq()
    request.ctidTraderAccountId = currentAccountId
    request.positionId = int(positionId)
    request.volume = int(float(volume))  # volume in units
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOACancelOrderReq(orderId, clientMsgId=None):
    request = ProtoOACancelOrderReq()
    request.ctidTraderAccountId = currentAccountId
    request.orderId = int(orderId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOADealOffsetListReq(dealId, clientMsgId=None):
    request = ProtoOADealOffsetListReq()
    request.ctidTraderAccountId = currentAccountId
    request.dealId = int(dealId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

def sendProtoOAGetPositionUnrealizedPnLReq(clientMsgId=None):
    request = ProtoOAGetPositionUnrealizedPnLReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAOrderDetailsReq(orderId, clientMsgId=None):
    request = ProtoOAOrderDetailsReq()
    request.ctidTraderAccountId = currentAccountId
    request.orderId = int(orderId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

def sendProtoOAOrderListByPositionIdReq(positionId, fromTimestamp=None, toTimestamp=None, clientMsgId=None):
    request = ProtoOAOrderListByPositionIdReq()
    request.ctidTraderAccountId = currentAccountId
    request.positionId = int(positionId)
    deferred = client.send(request, fromTimestamp=fromTimestamp, toTimestamp=toTimestamp, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

def sendProtoOAExpectedMarginReq(symbolId, volume, clientMsgId=None):
    request = ProtoOAExpectedMarginReq()
    request.ctidTraderAccountId = currentAccountId
    request.symbolId = int(symbolId)
    request.volume.append(int(volume))
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)
    return deferred

commands = {
    "setAccount": setAccount,
    "ProtoOAVersionReq": sendProtoOAVersionReq,
    "ProtoOAGetAccountListByAccessTokenReq": sendProtoOAGetAccountListByAccessTokenReq,
    "ProtoOAAssetListReq": sendProtoOAAssetListReq,
    "ProtoOAAssetClassListReq": sendProtoOAAssetClassListReq,
    "ProtoOASymbolCategoryListReq": sendProtoOASymbolCategoryListReq,
    "ProtoOASymbolsListReq": sendProtoOASymbolsListReq,
    "ProtoOATraderReq": sendProtoOATraderReq,
    "ProtoOAReconcileReq": sendProtoOAReconcileReq,
    "ProtoOAGetTrendbarsReq": sendProtoOAGetTrendbarsReq,
    "ProtoOAGetTickDataReq": sendProtoOAGetTickDataReq,
    "NewMarketOrder": sendNewMarketOrder,
    "NewLimitOrder": sendNewLimitOrder,
    "NewStopOrder": sendNewStopOrder,
    "ClosePosition": sendProtoOAClosePositionReq,
    "CancelOrder": sendProtoOACancelOrderReq,
    "DealOffsetList": sendProtoOADealOffsetListReq,
    "GetPositionUnrealizedPnL": sendProtoOAGetPositionUnrealizedPnLReq,
    "OrderDetails": sendProtoOAOrderDetailsReq,
    "OrderListByPositionId": sendProtoOAOrderListByPositionIdReq,
    "ProtoOAExpectedMarginReq": sendProtoOAExpectedMarginReq,
}

def encodeResult(result):
    if type(result) is str:
        return f'{{"result": "{result}"}}'.encode(encoding='UTF-8')
    else:
        return MessageToJson(Protobuf.extract(result)).encode(encoding='UTF-8')

@app.route('/get-data')
def getData(request):
    request.responseHeaders.addRawHeader(b"content-type", b"application/json")
    command = request.args.get(b"command", [None])[0]
    if (command is None or command == b""):
        return encodeResult(f"Invalid Command: {command}")
    commandSplit = command.decode('UTF-8').split(" ")
    logger.info(f"Command: {commandSplit}")
    if (commandSplit[0] not in commands):
        return encodeResult(f"Invalid Command: {commandSplit[0]}")
    parameters = commandSplit[1:]
    result = commands[commandSplit[0]](*parameters)
    result.addCallback(encodeResult)
    return result

def respond(request, deferred, wrap_key=None):
    request.setHeader('Content-Type', 'application/json')
    if hasattr(deferred, 'addCallback'):
        def on_success(msg):
            if isinstance(msg, str):
                payload = {'result': msg}
            else:
                pb = Protobuf.extract(msg)
                obj = json.loads(MessageToJson(pb))
                payload = {wrap_key: obj} if wrap_key else obj
            request.write(json.dumps(payload).encode('utf-8'))
            request.finish()

        def on_error(failure):
            request.setResponseCode(500)
            request.write(json.dumps({'error': str(failure)}).encode('utf-8'))
            request.finish()

        deferred.addCallback(on_success)
        deferred.addErrback(on_error)
        return NOT_DONE_YET
    return json.dumps({'result': deferred}).encode('utf-8')

@app.route('/api/set-account', methods=['POST'])
def http_set_account(request):
    body = request.content.read().decode('utf-8')
    request.responseHeaders.addRawHeader(b"content-type", b"application/json")
    try:
        data = json.loads(body) if body.strip() else {}
    except ValueError:
        data = {}
    acct = str(data.get('accountId') or CTRADER_ACCOUNTID or '')
    if not acct:
        request.setResponseCode(400)
        return json.dumps({'error': 'No accountId in request body and CTRADER_ACCOUNTID not set in .env'}).encode('utf-8')
    result = setAccount(acct)
    if type(result) is str:
        return encodeResult(result)
    result.addCallback(encodeResult)
    return result

@app.route('/api/trendbars', methods=['POST'])
def http_trendbars(request):
    body = request.content.read().decode('utf-8')
    try:
        data = json.loads(body)
        fromTimestamp = str(data['fromTimestamp'])
        toTimestamp = str(data['toTimestamp'])
        period = str(data['period'])
        symbolId = str(data['symbolId'])
        result = sendProtoOAGetTrendbarsReq(fromTimestamp, toTimestamp, period, symbolId)
        result.addCallback(encodeResult)
        if type(result) is str:
            result = encodeResult(result)
        return result
    except (ValueError, KeyError):
        request.setResponseCode(400)
        return json.dumps({'error': 'expected { fromTimestamp, toTimestamp, period, symbolId }'}).encode('utf-8')

@app.route('/api/live-quote', methods=['POST'])
def http_live_quote(request):
    body = request.content.read().decode('utf-8')
    try:
        data = json.loads(body)
        quoteType = str(data['quoteType'])
        symbolId = str(data['symbolId'])
        timeDeltaInSeconds = int(data['timeDeltaInSeconds'])
        result = sendProtoOAGetTickDataReq(timeDeltaInSeconds, quoteType, symbolId)
        result.addCallback(encodeResult)
        if type(result) is str:
            result = encodeResult(result)
        return result
    except (ValueError, KeyError):
        request.setResponseCode(400)
        return json.dumps({'error': 'unexpected input/output'}).encode('utf-8')

@app.route('/api/market-order', methods=['POST'])
def http_market_order(request):
    body = request.content.read().decode('utf-8')
    try:
        data = json.loads(body)
        symbolId = int(data['symbolId'])
        orderType = data['orderType'].upper()
        tradeSide = data['tradeSide'].upper()
        volume = float(data['volume'])
        comment = data.get('comment', '')
        relativeStopLoss = data.get('relativeStopLoss')
        relativeTakeProfit = data.get('relativeTakeProfit')
        result = sendProtoOANewOrderReq(symbolId, orderType, tradeSide, volume, None, comment, relativeStopLoss, relativeTakeProfit)
        result.addCallback(encodeResult)
        if type(result) is str:
            result = encodeResult(result)
        return result
    except (ValueError, KeyError):
        request.setResponseCode(400)
        return json.dumps({'error': 'unexpected input/output'}).encode('utf-8')

def main():
    global client
    logger.info("Starting cTrader OpenAPI Proxy...")

    client = Client(
        EndPoints.PROTOBUF_LIVE_HOST if CTRADER_HOST.lower() == "live"
        else EndPoints.PROTOBUF_DEMO_HOST,
        EndPoints.PROTOBUF_PORT,
        TcpProtocol
    )
    client.setConnectedCallback(connected)
    client.setDisconnectedCallback(disconnected)
    client.setMessageReceivedCallback(onMessageReceived)
    client.startService()

    endpoint_description = f"tcp6:port={port}:interface={host}"
    endpoint = endpoints.serverFromString(reactor, endpoint_description)
    site = Site(app.resource())
    site.displayTracebacks = True

    endpoint.listen(site)
    logger.info(f"HTTP proxy listening on http://{host}:{port}")
    reactor.run()

if __name__ == '__main__':
    main()
