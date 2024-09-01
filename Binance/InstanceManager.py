from threading import Thread
from Binance.BinanceInstance import BinanceInstance
from Utils.Logger import Logger
from Utils.Database import Database

class InstanceManager:
    def __init__(self):
        self.__logger = Logger("Instance Manager")
        self.__database = Database()

        self.__instances = []
        self.__initInstances(self.__database.getAllRunningInstances())

    def handleSignal(self, args):
        self.__logger.Log("handling instances with signal: ")
        self.__logger.Log(str(args))

        for acc in self.__instances:
            th = Thread(target=acc.handleArgs, args=(args, ))
            th.daemon = True
            th.start()

    def __initInstances(self, instances):
        for acc in instances:
            self.__instances.append(BinanceInstance(
                id = acc[0], 
                user_id = acc[1], 
                name = acc[2], 
                api_key = acc[3], 
                api_secret = acc[4], 
                risk = acc[5], 
                fixed_balance = acc[6]
            ))

    def addInstance(self, id, user_id, name, api_key, api_secret, risk, fixedBalance):
        self.__instances.append(BinanceInstance(id, user_id, name, api_key, api_secret, risk, fixedBalance))

    def removeInstance(self, user_id, name):
        if len(self.__instances) == 0: return
        
        for i, x in enumerate(self.__instances):       
            if x.name == name and str(x.user_id) == str(user_id):
                self.__instances[i].twm.stop()
                del self.__instances[i]

    def updateRiskPercent(self, user_id, name, risk):
        for i, x in enumerate(self.__instances):       
            if x.name == name and str(x.user_id) == str(user_id):
                self.__instances[i].risk = risk

    def updateFixedBalance(self, user_id, name, balance):
        for i, x in enumerate(self.__instances):       
            if x.name == name and str(x.user_id) == str(user_id):
                self.__instances[i].fixedBalance = balance