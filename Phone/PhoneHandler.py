from Phone.BatteryManager import BatteryManager
from Telegram.TelegramBot import TelegramBot
# from Binance.SignalsBot import SignalsBot
# from time import sleep

class PhoneHandler:
    def __init__(self):
        self.__telegramBot = TelegramBot()
        self.__batteryManager = BatteryManager()
        # self.__signalsBot = SignalsBot()

    def start(self):
        self.__telegramBot.start()
        # self.__batteryManager.start()

        # self.__signalsBot.start()
        # sleep(3)
        # # self.__signalsBot.AddAssetListener("ethusdt@kline_1m")
        # self.__signalsBot.AddAssetListener("ethusdt@miniTicker")
        # sleep(5)
        # self.__signalsBot.AddAssetListener("btcusdt@kline_1m")
        # sleep(5)
        # self.__signalsBot.RemoveAssetListener("btcusdt@kline_1m")
        # sleep(5)
        # self.__signalsBot.stop()


        # for x in range(5):
        #     sleep(1)
        #     print(self.__signalsBot.getAssetData("BTCUSDT"))
        #     print()

        # self.__signalsBot.stop()
        # sleep(5)
        # print(self.__signalsBot.getAssetData("BTCUSDT"))