from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
import json
from Utils.Database import Database
from Utils.Logger import Logger
from Binance.InstanceManager import InstanceManager

class TelegramBot:
    def __init__(self):
        self.__instanceManager = InstanceManager()
        self.__database = Database()
        self.__logger = Logger("Telegram Bot")
        self.__settings = self.__load_settings("Telegram/settings.json")
        self.__client = self.__init_client()

    def __load_settings(self, path):
        try:
            settingsFile = open(path, encoding="utf8")
            return json.load(settingsFile)["telegram"]
        except Exception as e:
            self.__logger.Error(str(e))
            exit()

    def __init_client(self):
        client = TelegramClient("Telegram Bot", self.__settings["api_id"], self.__settings["api_hash"])
        self.__logger.Log("initiated..")
        client.start()
        self.__logger.Log("authenticated..")
        return client
    
    def start(self):
        self.__logger.Log("starting listening handle")
        self.__startHandle(self.__client)

    # # --------------- COMMAND HANDLING STUFF --------------
    
    def __argsHandler(self, command, n_args):
        try:
            cmd = command.split(" ")[0]
            args = command.split(" ")[1:]
        except:
            return "Invalid "+cmd+" arguments"
        else:
            if len(args) != n_args: return "Invalid "+cmd+" arguments*"
            return args

    def __checkExists(self, instance, username):
        if len(self.__database.getInstance(username, instance)) == 0:
            return False
        return True

    async def __startStopInstance(self, event, username, action):
        numArgs = 1
        args = self.__argsHandler(event.raw_text, numArgs)

        if len(args) != numArgs: 
            await event.respond(args)
            return
            
        instanceName = args[0]

        exist = self.__checkExists(instanceName, username)
        if exist != True:
            await event.respond("Instance '"+instanceName+"' does not exist")
            return
        
        if action == "start":
            self.__database.updateRunning(username, args[0], "1")
            instance = self.__database.getInstance(username, args[0])[0]
            self.__instanceManager.addInstance(instance[0], instance[1], instance[2], instance[3], instance[4], instance[5], instance[6])
            await event.respond("Started instance '"+args[0]+"'")
        else:
            self.__database.updateRunning(username, args[0], "0")
            user_id = self.__database.getUserId(username)
            self.__instanceManager.removeInstance(user_id, args[0])
            await event.respond("Stopped instance '"+args[0]+"'")

    async def __displayHelp(self, event, isAdmin):
        text = """
    Commands:
        /start *INSTANCE_NAME* - start an instance

        /stop *INSTANCE_NAME* - stop an instance

        /add *INSTANCE_NAME* *API_KEY* *API_SECRET* *RISK_PERCENT* *FIXED_BALANCE* - create an instance

        /remove *INSTANCE_NAME* - remove an instance

        /all - display all instances

        /risk *INSTANCE_NAME* *RISK_PERCENT* - edit risk percent for specific instance

        /fixed *INSTANCE_NAME* *FIXED_BALANCE* - edit fixed balance for specific instance
    """

        adminText = """
    Admin commands:
        /adduser *USERNAME* *IS_ADMIN*

        /removeuser *USERNAME*

        /users - display all users
    """

        if isAdmin:
            await event.respond(text+adminText)
        else:
            await event.respond(text)

    async def __addRemoveInstance(self, event, username, action, n_args):
        numArgs = n_args
        args = self.__argsHandler(event.raw_text, numArgs)

        if len(args) != numArgs: 
            await event.respond(args)
            return
        
        instanceName = args[0]

        exist = self.__checkExists(instanceName, username)
        if exist == True and action == "add":
            await event.respond("Instance '"+instanceName+"' already exists")
            return
        
        if exist != True and action != "add":
            await event.respond("Instance '"+instanceName+"' does not exist")
            return
            

        if action == "add":
            self.__database.addInstance(username, args[0], args[1], args[2], args[3], args[4])
            await event.respond("Added instance '"+args[0]+"'")
        else:
            self.__database.removeInstance(username, args[0])
            user_id = self.__database.getUserId(username)
            self.__instanceManager.removeInstance(user_id, args[0])
            await event.respond("Removed instance '"+args[0]+"'")

    async def __showInstances(self, event, username):
        instances = self.__database.getInstances(username)
        text = ""
        for x in instances:
            text += "\n" + x[2] + " | " + x[3] + " | " + x[4] + " | " + str(x[5]) + " | " + str(x[6]) + " | " + str(bool(x[7]))+"\n"

        if len(instances) > 0:
            await event.respond(text)
        else:
            await event.respond("You don't have any instances created")

    async def __showRunning(self, event, username):
        instances = self.__database.getRunningInstances(username)
        text = ""
        for x in instances:
            text += "\n" + x[2] + "\n"

        if len(instances) > 0:
            await event.respond(text)
        else:
            await event.respond("You don't have any running instances")

    async def __riskBalanceEdit(self, event, username, action):
        numArgs = 2
        args = self.__argsHandler(event.raw_text, numArgs)

        if len(args) != numArgs: 
            await event.respond(args)
            return
        
        instanceName = args[0]

        exist = self.__checkExists(instanceName, username)
        if exist != True:
            await event.respond("Instance '"+instanceName+"' does not exist")
            return
        
        if action == "risk":   
            self.__database.updateRiskPercent(username, instanceName, args[1])
            user_id = self.__database.getUserId(username)
            self.__instanceManager.updateRiskPercent(user_id, instanceName, args[1])
            await event.respond("Risk percent edited")

        else:
            self.__database.updateFixedBalance(username, instanceName, args[1])
            user_id = self.__database.getUserId(username)
            self.__instanceManager.updateFixedBalance(user_id, instanceName, args[1])
            await event.respond("Fixed balance edited")


    async def __addRemoveUser(self, event, action, n_args):
        numArgs = n_args
        args = self.__argsHandler(event.raw_text, numArgs)

        if len(args) != numArgs: 
            await event.respond(args)
            return

        username = args[0]

        allowedUsernames = self.__database.getAllowedUsernames()
        if username in allowedUsernames and action == "add":
            await event.respond("Username '"+username+"' already added")
            return
        
        if username not in allowedUsernames and action != "add":
            await event.respond("Username '"+username+"' does not exist")
            return
        
        if action == "add":   
            self.__database.addUser(args[0], args[1])
            await event.respond("Added user '"+args[0]+"'")
        else:
            self.__database.removeUser(args[0])
            await event.respond("Removed user '"+args[0]+"'")

    async def __showUsers(self, event):
        text = ""
        for x in self.__database.getAllowedUsernames():
            text += x+"\n"

        await event.respond(text)


    async def __detectCommand(self, event):
        sender = await event.get_sender()
        if sender.username not in self.__database.getAllowedUsernames(): return
        if not isinstance(event.peer_id, PeerUser): return

        isAdmin = self.__database.isAdmin(sender.username)
        text = event.raw_text

        self.__logger.Log("message from " + sender.username + " detected is admin: " + str(isAdmin))

        # ---------- ADMIN COMMANDS ----------

        if "/adduser" in text and isAdmin:
            await self.__addRemoveUser(event, "add", 2)
        
        elif "/removeuser" in text and isAdmin:
            await self.__addRemoveUser(event, "remove", 1)

        elif "/users" in text and isAdmin:
            await self.__showUsers(event)


        # ---------- NORMAL COMMANDS ----------
        elif "/start" in text:
            await self.__startStopInstance(event, sender.username, "start")

        elif "/stop" in text:
            await self.__startStopInstance(event, sender.username, "stop")

        elif "/help" in text:
            await self.__displayHelp(event, isAdmin)

        elif "/add" in text:
            await self.__addRemoveInstance(event, sender.username, "add", 5)
        
        elif "/remove" in text:
            await self.__addRemoveInstance(event, sender.username, "remove", 1)

        elif "/all" in text:
            await self.__showInstances(event, sender.username)

        elif "/running" in text:
            await self.__showRunning(event, sender.username)

        elif "/risk" in text:
            await self.__riskBalanceEdit(event, sender.username, "risk")

        elif "/fixed" in text:
            await self.__riskBalanceEdit(event, sender.username, "balance")

        else:
            await event.respond("unknown command")

    # --------------- SIGNAL DETECTION STUFF --------------

    def __argsFromText(self, msg, msgId):
        msgArgs = self.__settings["messages"][msgId]
        keywords = [msgArgs["coin"], msgArgs["current_price"], msgArgs["take_profit"], msgArgs["stop_loss"]]
        args = []

        for i, keywordType in enumerate(keywords):
            if i == 0:
                val = msg.split(keywordType[0]["after"])[0].split(keywordType[0]["before"])
                args.append(val[len(val)-1] + "USDT")
                continue
            
            values = []
            for keyword in keywordType:
                if keyword["before"] in msg:
                    val = msg.split(keyword["before"])[1].split(keyword["after"])[0]
                    val = float(val)
                    values.append([val, keyword["amount"]])

            if len(values) > 0: args.append(values)

        return args

    def __filterMessage(self, text):
        for i, msg in enumerate(self.__settings["messages"]):
            count = 0
            for word in msg["key_words"]:
                if word in text:
                    count += 1

            if count >= msg["minimum_threshold"]:
                return i
        return -1

    def __detectSignal(self, event):
        msgId = self.__filterMessage(event.raw_text)
        if msgId == -1: return False

        args = self.__argsFromText(event.raw_text, msgId)
        if len(args) < 4:
            return False
        return args


    # # --------------- MESSAGE LISTENER -------------------- 

    def __startHandle(self, client):
        @client.on(events.NewMessage(incoming=True))
        async def messageHandler(event):
            args = self.__detectSignal(event)
            if not args:
                await self.__detectCommand(event)
            else:
                self.__logger.Log("signal detected")
                self.__instanceManager.handleSignal(args)
        
        client.run_until_disconnected()