import sqlite3

class Database:
    def __init__(self):
        self.conn = self.initDatabase()

    def initDatabase(self):
        conn = sqlite3.connect('Utils/database.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                        username text NOT NULL,
                        admin bool DEFAULT false NOT NULL,
                        UNIQUE(username)
                    );''')
        conn.execute('''CREATE TABLE IF NOT EXISTS instances (
                        id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                        user_id integer,
                        name text NOT NULL,
                        api_key text NOT NULL,
                        api_secret text NOT NULL,
                        risk_percent integer NOT NULL,
                        fixed_balance integer NOT NULL,
                        running bool DEFAULT false NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        UNIQUE(api_key, api_secret)
                    );''')

        conn.execute("INSERT OR IGNORE INTO users (username, admin) VALUES ('matthewxprg', true)")
        conn.commit()
        return conn
    
    def getAllowedUsernames(self):
        query = "SELECT username FROM users"
        usernames = []
        for x in self.conn.execute(query):
            usernames.append(x[0])
        return usernames
    
    def isAdmin(self, username):
        query = "SELECT admin FROM users WHERE username =='"+username+"'"
        return bool(self.conn.execute(query).fetchone()[0])
    
    def addUser(self, username, admin):
        query = "INSERT OR IGNORE INTO users (username, admin) VALUES ('"+username+"', "+admin+")"
        self.conn.execute(query)
        self.conn.commit()

    def removeUser(self, username):
        query = "DELETE FROM users WHERE username == '"+username+"'"
        self.conn.execute(query)
        self.conn.commit()

    def removeAllUserInstances(self, username):
        user_id = self.getUserId(username)
        query = "DELETE FROM instances WHERE user_id == "+user_id
        self.conn.execute(query)
        self.conn.commit()

    def getUserId(self, username):
        return str(self.conn.execute("SELECT id FROM users WHERE username == '"+username+"'").fetchone()[0])

    def getInstances(self, username):
        user_id = self.getUserId(username)

        query = "SELECT * FROM instances WHERE user_id == "+user_id
        return self.conn.execute(query).fetchall()
    
    def getRunningInstances(self, username):
        user_id = self.getUserId(username)

        query = "SELECT * FROM instances WHERE user_id == "+user_id+" and running == 1"
        return self.conn.execute(query).fetchall()

    def addInstance(self, username, name, api_key, api_secret, risk_percent, fixed_balance):
        user_id = self.getUserId(username)

        query = "INSERT OR IGNORE INTO instances (user_id, name, api_key, api_secret, risk_percent, fixed_balance) VALUES ("+user_id+", '"+name+"', '"+api_key+"', '"+api_secret+"', "+risk_percent+", "+fixed_balance+")"
        self.conn.execute(query)
        self.conn.commit()

    def removeInstance(self, username, name):
        user_id = self.getUserId(username)

        query = "DELETE FROM instances WHERE name == '"+name+"' and user_id == "+user_id
        self.conn.execute(query)
        self.conn.commit()

    def updateRiskPercent(self, username, name, risk_percent):
        user_id = self.getUserId(username)

        query = "UPDATE instances SET risk_percent = "+risk_percent+" WHERE user_id == "+user_id+" and name == '"+name+"'"
        self.conn.execute(query)
        self.conn.commit()

    def updateFixedBalance(self, username, name, fixed_balance):
        user_id = self.getUserId(username)

        query = "UPDATE instances SET fixed_balance = "+fixed_balance+" WHERE user_id == "+user_id+" and name == '"+name+"'"
        self.conn.execute(query)
        self.conn.commit()

    def updateRunning(self, username, name, running):
        user_id = self.getUserId(username)

        query = "UPDATE instances SET running = "+running+" WHERE user_id == "+user_id+" and name == '"+name+"'"
        self.conn.execute(query)
        self.conn.commit()

    def getAllRunningInstances(self):
        query = "SELECT * FROM instances WHERE running == 1"
        return self.conn.execute(query).fetchall()
    
    def getInstance(self, username, name):
        user_id = self.getUserId(username)

        query = "SELECT * FROM instances WHERE user_id == "+user_id+" and name == '"+name+"'"
        return self.conn.execute(query).fetchall()

    def getInstanceId(self, user_id, name):
        return str(self.conn.execute("SELECT id FROM instances WHERE user_id == "+user_id+" and name == '"+name+"'").fetchone()[0])