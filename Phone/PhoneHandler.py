from Phone.BatteryManager import BatteryManager
from Telegram.TelegramBot import TelegramBot

class PhoneHandler:
    def __init__(self):
        self.__telegramBot = TelegramBot()
        self.__batteryManager = BatteryManager()

    def start(self):
        self.__telegramBot.start()
        # self.__batteryManager.start()