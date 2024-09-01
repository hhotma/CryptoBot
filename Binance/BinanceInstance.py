from binance import Client, enums, ThreadedWebsocketManager
from binance.helpers import round_step_size
from Utils.Logger import Logger
from threading import Thread

class BinanceInstance:
    def __init__(self, id, user_id, name, api_key, api_secret, risk, fixed_balance):
        # CLIENT
        self.id = id
        self.user_id = user_id
        self.name = name
        self.__client = Client(api_key, api_secret)
        self.risk = risk
        self.fixedBalance = fixed_balance
        # self.maxleverage = 20

        # DATABASE
        self.__positionDatabase = {}

        # LOGGER
        self.logPre = "Binance Bot | " + self.name + " | "
        self.logger = Logger(self.logPre)

        # WEBSOCKET
        self.threadedListener(api_key, api_secret)


    # ------------------------- WEBSOCKET STUFF ------------------------------------------------------------------------

    def threadedListener(self, api_key, api_secret):
        th = Thread(target=self.__websocketListener, kwargs={"api_key": api_key, "api_secret": api_secret})
        th.daemon = True
        th.start()

    def __websocketListener(self, api_key, api_secret):
        self.twm = ThreadedWebsocketManager(api_key, api_secret)
        self.twm.setDaemon(True)
        self.twm.start()
        self.twm.start_futures_user_socket(callback=self.__handle_socket_message)
        # self.twm.join()

    def __handle_socket_message(self, msg):
        if msg["e"] != "ORDER_TRADE_UPDATE" or msg["o"]["s"] not in self.__positionDatabase or msg["o"]["X"] != "FILLED":
            return
        
        self.logger.Log(self.logPre+"Websocket MSG detected")

        if msg["o"]["i"] in self.__positionDatabase[msg["o"]["s"]]["orderIds"]:
            args = self.__positionDatabase[msg["o"]["s"]]["orderIds"][msg["o"]["i"]]

            if args["type"] == "SL":
                self.logger.Log(self.logPre+"TP reached.. updating SL")

                newSlId = self.__updateStopLoss(msg["o"]["s"], args["slId"], args["side"], args["price"])
                # update SL id in database
                self.__positionDatabase[msg["o"]["s"]]["orderIds"][newSlId] = self.__positionDatabase[msg["o"]["s"]]["orderIds"].pop(args["slId"])

            elif args["type"] == "TP":
                self.logger.Log(self.logPre+"LIMIT order reached.. updating TPs")

                self.__positionDatabase[msg["o"]["s"]]["qty"] += args["qty"]
                newTpIds = self.__updateTakeProfits(msg["o"]["s"], args["tpIds"], args["side"], args["percentage"], args["prices"], self.__positionDatabase[msg["o"]["s"]]["qty"], args["qtyPrecision"])
                # update TP ids in database
                for x in range(len(newTpIds)):
                    self.__positionDatabase[msg["o"]["s"]]["orderIds"][newTpIds[x]] = self.__positionDatabase[msg["o"]["s"]]["orderIds"].pop(args["tpIds"][x])
                
            elif args["type"] == "CLOSE":
                self.logger.Log(self.logPre+"Closing position")

                for x in self.__positionDatabase[msg["o"]["s"]]["orderIds"]:
                    self.__cancelOrder(msg["o"]["s"], x)
                
                # DELETE POSITION FROM DATABASE
                del self.__positionDatabase[msg["o"]["s"]]

    #    ------------------------- CLIENT STUFF ------------------------------------------------------------------------

    def handleArgs(self, args):
        self.logger.Log(self.logPre+"Starting to handle request")
        
        if self.__getAccountBalance() < 10:
            self.logger.Log(self.logPre+"Skipped request.. Reason: Account balance lower than 10 BNFCR")
            return
        
        symbol = args[0]
        if symbol in self.__positionDatabase:
            self.logger.Log(self.logPre+"Skipped request.. Reason: Position already opened in: #"+symbol)
            return
        
        p_args = args[1]
        cp = self.__getPrice(symbol)
        tp_args = args[2]
        sl_args = args[3][0]
        lv = self.__getMaxLeverage(symbol)
        # lv = 20
        # if self.maxleverage <= lv:
        #     lv = self.maxleverage

        self.__handleRequest(symbol, cp, p_args, tp_args, sl_args, lv)

    def __handleRequest(self, symbol, cp, p_args, tp_args, sl_args, lv):

        if not self.__checkVolatility(cp, p_args[0][0], tp_args[0][0], sl_args[0]): return

        symbolEchangeInfo = self.__getSymbolExchangeInfo(symbol)

        moneyIn = self.__calculateMoneyIn(cp, p_args, sl_args, lv)
        qty = self.__calculateQty(moneyIn, cp, lv, symbolEchangeInfo["quantityPrecision"])
        
        if not self.__validateEchangeInfo(symbolEchangeInfo, moneyIn, qty, lv, cp): return

        self.__setMarginTypeCross(symbol)
        self.__setLeverage(symbol, lv)

        side = self.__getOrderSide(cp, p_args[0][0], tp_args[0][0])

        # creates all of the orders
        self.__handleOrders(symbol, side, qty, p_args, tp_args, sl_args, symbolEchangeInfo)

    def __handleOrders(self, symbol, side, qty, p_args, tp_args, sl_args, exchangeInfo):
        orderIds = []
        orderQtys = []
        tpIds = []
        tpPercentage = []
        tpPrices = []
        slIds = []
        error = False
        firstOrderPrice = 0
        firstOrderQty = 0
        positionSide = side
        closeIds = []

        # create orders
        for i, p in enumerate(p_args):
            orderQty = self.__calculateOrderQty(qty, p[1], exchangeInfo["quantityPrecision"])
            if i == 0:
                orderId = self.__createMarketOrder(symbol, side, orderQty)
                firstOrderPrice = self.__getPrice(symbol)
                firstOrderQty = orderQty
            else:
                price = round_step_size(p[0], self.__getTickSize(exchangeInfo))
                orderId = self.__createLimitOrder(symbol, side, price, orderQty)
            
            if not orderId: 
                if i == 0: return
                error = True
            else:
                if i > 0: 
                    orderIds.append(orderId)
                    orderQtys.append(orderQty)


        # flip order side
        if side == enums.SIDE_BUY:
            side = enums.SIDE_SELL
        else:
            side = enums.SIDE_BUY

        # create take profits
        for tp in tp_args:
            if tp[1] != 100:
                tpId = self.__setTakeProfitMarket(symbol, side, tp[0], self.__calculateOrderQty(firstOrderQty, tp[1], exchangeInfo["quantityPrecision"]))
            else:
                tpId = self.__setTakeProfitMarket(symbol, side, tp[0])
        
            if not tpId: 
                error = True
            else:
                if tp[1] != 100: 
                    tpIds.append(tpId)
                    tpPrices.append(tp[0])
                    tpPercentage.append(tp[1])
                else:
                    closeIds.append(tpId)
                    break


        # create stop loss
        slId = self.__setStopLossMarket(symbol, side, sl_args[0])
        if not slId: 
            error = True
        else:
            slIds.append(slId)
            closeIds.append(slId)

        if error:
            sellAll = self.__createMarketOrder(symbol, side, firstOrderQty)
            if sellAll: self.logger.Log(self.logPre+"Sold everything.. Reason: error setting orders")

            self.logger.Log(self.logPre+"Trying to cancel created orders..")
            ids = [orderIds, tpIds, slIds]
            for id_type in ids:
                for id in id_type:
                    self.__cancelOrder(symbol, id)
            return
        
        # DATABASE CREATE NEW
        data = {}
        data["side"] = positionSide
        data["qty"] = firstOrderQty
        data["orderIds"] = {}

        # limit order events for take profit update
        for l in range(len(orderIds)):
            data["orderIds"][orderIds[l]] = {
                "type": "TP",
                "tpIds": tpIds,
                "side": side,
                "prices": tpPrices,
                "percentage": tpPercentage,
                "qty": orderQtys[l],
                "qtyPrecision": exchangeInfo["quantityPrecision"]
            }

        # take profit events for stop loss update
        for i in range(len(tpIds)):
            if i == 0:
                data["orderIds"][tpIds[i]] = {
                    "type": "SL",
                    "slId": slId,
                    "side": side,
                    "price": firstOrderPrice
                }
            else:
                data["orderIds"][tpIds[i]] = {
                    "type": "SL",
                    "slId": slId,
                    "side": side,
                    "price": tp_args[i-1][0]
                }

        # position closing events for order closing
        for j in range(len(closeIds)):
            data["orderIds"][closeIds[j]] = {
                "type": "CLOSE",
            }

        self.__positionDatabase[symbol] = data
        # print(self.__positionDatabase[symbol])

    # ---------------------------------------------------------------------------------------------------------------

    def __getTickSize(self, exchangeInfo):
        for type in exchangeInfo["filters"]:
            if type["filterType"] == "PRICE_FILTER":
                return type["tickSize"]

    def __updateStopLoss(self, symbol, slId, side, price):
        self.__cancelOrder(symbol, slId)
        orderId = self.__setStopLossMarket(symbol, side, price)
        if not orderId:
            return False
        return orderId

    def __updateTakeProfits(self, symbol, tpIds, side, percentage, prices, qty, qtyPrecision):
        newIds = []

        for x in range(len(tpIds)):
            self.__cancelOrder(symbol, tpIds[x])
            tpId = self.__setTakeProfitMarket(symbol, side, prices[x], self.__calculateOrderQty(qty, percentage[x], qtyPrecision))
            newIds.append(tpId)

        if len(tpIds) != len(newIds):
            return False
        return newIds

    def __calculateQty(self, moneyIn, cp, lv, quantityPrecision):
        qty = moneyIn / cp * lv
        return round(qty, quantityPrecision)

    def __getOrderSide(self, cp, p, tp):
        if cp < tp and p < tp:
            return enums.SIDE_BUY
        else:
            return enums.SIDE_SELL

    def __checkVolatility(self, cp, p, tp, sl):
        if (cp > tp and p < tp) or (cp < tp and p > tp):
            self.logger.Log(self.logPre+"Skipped request.. Reason: (CP > TP and P < TP) or (CP < TP and P > TP)")
            return False
        elif (cp < sl and p > sl) or (cp > sl and p < sl):
            self.logger.Log(self.logPre+"Skipped request.. Reason: (CP < SL and P > SL) or (CP > SL and P < SL)")
            return False
        return True

    def __validateEchangeInfo(self, info, moneyIn, qty, lv, cp):
        if info["contractType"] != "PERPETUAL":
            self.logger.Log(self.logPre+"Skipped request.. Reason: Contract NOT perpetual")
            return False

        for filter in info["filters"]:
            if filter["filterType"] == "MIN_NOTIONAL":
                notionalValue = qty*moneyIn*lv
                if float(filter["notional"]) > notionalValue: 
                    self.logger.Log(self.logPre+"Skipped request.. Reason: Min NOTIONAL of "+ filter["notional"]+" not met")
                    return False
        return True

    def __getSymbolExchangeInfo(self, symbol):
        response = self.__client.futures_exchange_info()["symbols"]
        for x in response:
            if x["symbol"] == symbol:
                return x

    def __calculateMoneyIn(self, cp, p_args, sl_args, lv):
        realBalance = self.__getAccountBalance()
        if realBalance > self.fixedBalance:
            balance = realBalance
        else:
            balance = self.fixedBalance

        if self.risk == 0:
            moneyIn = balance / 100

        else:
            p_args[0][0] = cp
            
            # calculate weighted average
            total = 0
            for x in p_args:
                total += x[1]
            
            calc = 0
            for p in p_args:
                calc += p[1] * p[0]
            avg = calc / total

            percent = (100 - sl_args[0]/avg*100)
            moneyIn = balance * self.risk / percent
            moneyIn = moneyIn / lv
            moneyIn = abs(moneyIn)

        if realBalance < moneyIn:
            return realBalance
        return moneyIn
    
    def __calculateOrderQty(self, qty, percent, quantityPrecision):
        return round(qty/100*percent, quantityPrecision)

    def __createMarketOrder(self, _symbol, _side, _quantity):
        try:
            order = self.__client.futures_create_order(
                symbol = _symbol,
                side = _side,
                type = enums.FUTURE_ORDER_TYPE_MARKET,
                quantity = _quantity
            )
        except Exception as e:
            self.logger.Error(self.logPre+"Error creating market order")
            self.logger.Error(self.logPre+"Error: "+str(e))
            return False
        else:
            self.logger.Log(self.logPre+"Created new market order | Id: "+str(order["orderId"])+" Side: "+_side+" Quantity: "+str(_quantity))
            return order["orderId"]
        
    def __createLimitOrder(self, _symbol, _side, _limit, _quantity):
        try:
            order = self.__client.futures_create_order(
                symbol = _symbol,
                side = _side,
                type = enums.FUTURE_ORDER_TYPE_LIMIT,
                timeInForce = enums.TIME_IN_FORCE_GTC,
                quantity = _quantity,
                price = _limit
            )
        except Exception as e:
            self.logger.Error(self.logPre+"Error creating limit order")
            self.logger.Error(self.logPre+"Error: "+str(e))
            return False
        else:
            self.logger.Log(self.logPre+"Created new limit order | Id: "+str(order["orderId"])+" Side: "+_side+" Quantity: "+str(_quantity))
            return order["orderId"]

    def __setTakeProfitMarket(self, _symbol, _side, _stopPrice, _qty = 0):
        try:
            if _qty == 0:
                order = self.__client.futures_create_order(
                    symbol = _symbol,
                    side = _side,
                    type = enums.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                    stopPrice = _stopPrice,
                    timeInForce = "GTE_GTC",
                    closePosition = True
                )
            else:
                order = self.__client.futures_create_order(
                    symbol = _symbol,
                    side = _side,
                    type = enums.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                    stopPrice = _stopPrice,
                    timeInForce = "GTE_GTC",
                    quantity = _qty
                )
        except Exception as e:
            self.logger.Error(self.logPre+"Error creating take profit")
            self.logger.Error(self.logPre+"Error: "+str(e))
            return False
        else:
            self.logger.Log(self.logPre+"Created new TP | Id: "+str(order["orderId"])+" Side: "+_side+" Stop price: "+str(_stopPrice))
            return order["orderId"]

    def __setStopLossMarket(self, _symbol, _side, _stopPrice):
        try:
            order = self.__client.futures_create_order(
                symbol = _symbol,
                side = _side,
                type = enums.FUTURE_ORDER_TYPE_STOP_MARKET,
                stopPrice = _stopPrice,
                # timeInForce = enums.TIME_IN_FORCE_GTC,
                timeInForce = "GTE_GTC",
                closePosition = True
            )
        except Exception as e:
            self.logger.Error(self.logPre+"Error creating stop loss")
            self.logger.Error(self.logPre+"Error: "+str(e))
            return False
        else:
            self.logger.Log(self.logPre+"Created new SL | Id: "+str(order["orderId"])+" Side: "+_side+" Stop price: "+str(_stopPrice))
            return order["orderId"]

    def __cancelOrder(self, _symbol, _orderId):
        try:
            order = self.__client.futures_cancel_order(
                symbol = _symbol,
                orderId = _orderId
            )
        except Exception as e:
            self.logger.Error(self.logPre+"Error canceling order")
            self.logger.Error(self.logPre+"Error: "+str(e))
            return False
        else:
            self.logger.Log(self.logPre+"Canceled order: "+str(order["orderId"]))
            return order["orderId"]

    def __getMaxLeverage(self, _symbol):
        return self.__client.futures_leverage_bracket(symbol = _symbol)[0]["brackets"][0]["initialLeverage"]

    def __setLeverage(self, _symbol, _leverage):
        return self.__client.futures_change_leverage(
            symbol = _symbol,
            leverage = _leverage
        )

    def __setMarginTypeCross(self, _symbol):
        try:
            return self.__client.futures_change_margin_type(
            symbol = _symbol,
            marginType = "CROSSED"
        )["msg"]
        except Exception as e:
            pass

    def __getAccountBalance(self):
        for asset in self.__client.futures_account_balance():
            if asset["asset"] == "BNFCR":
                return float(asset["availableBalance"])

    def __getPrice(self, _symbol):
        return float(self.__client.futures_symbol_ticker(symbol = _symbol)["price"])