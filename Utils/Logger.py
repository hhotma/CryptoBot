from datetime import datetime
from colorama import Fore, Style

class Logger:
    def __init__(self, logPre):
        self.filename = "Utils/logs.txt"
        self.__createFile()
        self.printLogs = True
        self.printErrors = True
        self.__logPre = logPre


    def __now(self):
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")

    def __createFile(self):
        f = open(self.filename, "w")
        f.close()

    def Log(self, msg):
        finalMsg = "Info | " + self.__logPre + " | " + self.__now() + " | " + msg
        self.Append(finalMsg)
        if self.printLogs: 
            print(Fore.LIGHTGREEN_EX + finalMsg + Style.RESET_ALL)
            # print(Style.RESET_ALL)

    def Error(self, msg):
        finalMsg = "Error | " + self.__logPre + " | " + self.__now() + " | " + msg
        self.Append(finalMsg)
        if self.printErrors: 
            print(Fore.LIGHTRED_EX + finalMsg + Style.RESET_ALL)
            # print(Style.RESET_ALL)


    def Append(self, msg):
        f = open(self.filename, "a")
        f.write(msg+"\n")
        f.close()