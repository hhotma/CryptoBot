import os
import tinytuya
import json
import time
from threading import Thread
from Utils.Logger import Logger

class BatteryManager:
    def __init__(self):
        self.outlet = tinytuya.OutletDevice(
            dev_id='bf9ece1a267f6ae82e5jme',
            address='192.168.1.142',
            local_key='C63<BRe}ig2LZ!!Z', 
            version=3.3
        )
        self.minimumCharge = 50
        self.maximumCharge = 80
        self.__logger = Logger("Battery Manager")
        self.__logger.Log("initiated..")

    def start(self):
        self.th = Thread(target=self.__handleCharging)
        self.th.daemon = True
        self.th.start()
        self.__logger.Log("main thread STARTED")

    def stop(self):
        del self.th
        self.__logger.Log("main thread STOPPED")

    def __handleCharging(self):
        while (True):
            percentage = self.__getBatteryPercentage()
            
            if percentage >= self.maximumCharge and self.__getOutletStatus():
                self.__turnOffOutlet()

            elif percentage <= self.minimumCharge and not self.__getOutletStatus():
                self.__turnOnOutlet()

            time.sleep(60)

    def __getOutletStatus(self):
        return self.outlet.status()["dps"]["1"]
    
    def __turnOnOutlet(self):
        self.outlet.turn_on()
        self.__logger.Log("turning ON")

    def __turnOffOutlet(self):
        self.outlet.turn_off()
        self.__logger.Log("turning OFF")

    def __getBatteryPercentage(self):
        batteryString = os.popen("termux-battery-status").read()
        return json.loads(batteryString)["percentage"]