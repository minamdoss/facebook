import pyodbc as db



class Database:

    def __init__(self):
        # self.dbconn = db.connect("Driver={SQL SERVER};Server=.;Database=CBT;Trusted_Connection=yes;")
        self.dbconn = db.connect("Driver={ODBC Driver 13 for SQL Server};Server=tcp:madyfa.database.windows.net,1433;Database=CBT;Uid=mohamed@madyfa;Pwd={3Oss199755};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;")
        self.cursor = self.dbconn.cursor()

    def DBconnect(self):
        print("Connecting to Database...")
        return self.dbconn , self.cursor

    def CursorConnection(self):
        return self.cursor

    def DBdisconnect(self):
        print("Disconnecting from Database...")
        self.cursor.close()
        self.dbconn.close()
