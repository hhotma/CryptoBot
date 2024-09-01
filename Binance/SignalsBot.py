# import pandas as pd
from threading import Thread
from Utils.Logger import Logger
import websocket
import json


class SignalsBot:
    def __init__(self):
        self.__logger = Logger("Signals Bot")

        self.__assets = {}
        self.__streams = {}
        self.__socketUrl = "wss://fstream.binance.com/stream?streams="
        self.__assetListeners = []

        # TODO:
        # meet all binance conditions such as reconnect every 24 hours
        # max 10 sockets every second


    # -------------------------------------------------------------------

    def start(self):
        self.__logger.Log("started websocket listener")
        self.__startThreaded()

    def stop(self):
        self.__logger.Log("closed websocket listener")
        self.__stopThreaded()

    def __startThreaded(self):
        self.__th = Thread(target=self.__initSocket)
        self.__th.start()

    def __stopThreaded(self):
        self.__stopSocket()

    def __onMessage(self, ws, data):
        print(json.loads(data))

    def __initSocket(self):
        self.__ws = websocket.WebSocketApp(self.__FlattenUrl(), on_message=self.__onMessage)
        self.__ws.run_forever()

    def __stopSocket(self):
        self.__ws.close()

    def __resetSocket(self):
        self.__logger.Log("resetting websocket listener")
        self.__stopThreaded()
        self.__startThreaded()

    # -------------------------------------------------------------------

    def AddAssetListener(self, asset):
        if asset in self.__assetListeners: return
        self.__logger.Log("adding " + asset + " listener")
        self.__assetListeners.append(asset)
        self.__resetSocket()

    def RemoveAssetListener(self, asset):
        if asset not in self.__assetListeners: return
        self.__logger.Log("removing " + asset + " listener")
        self.__assetListeners.remove(asset)
        self.__resetSocket()

    def __FlattenUrl(self):
        url = self.__socketUrl
        for i, asset in enumerate(self.__assetListeners):
            if i == 0:
                url += asset
            else:
                url += "/" + asset
        return url