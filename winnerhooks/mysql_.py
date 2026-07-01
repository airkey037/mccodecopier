# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains MySQL class that saves data to MySQL/MariaDB
# Import needed modules
import logging
# Class to save codes data to MySQL/MariaDB
class MySQL:
    def __init__(self,user:str,password:str,database:str,hostname:str="localhost",port:int=3306):
        CREATE_TABLE_QUERY='''CREATE TABLE IF NOT EXISTS`wins_log`(`id`int(11)NOT NULL AUTO_INCREMENT COMMENT'Primary key',`code`varchar(10)DEFAULT NULL COMMENT'String that contains key, that player had to re-write',`appear_time`timestamp NOT NULL DEFAULT current_timestamp()COMMENT'Shows exact time when code appeared',`rewrite_time`float NOT NULL COMMENT'Time (in seconds) in what time player have re-writed the code',`nick`varchar(16)NOT NULL COMMENT'Who sent the code',`is_it_me`tinyint(1)NOT NULL COMMENT'True if I won the code',PRIMARY KEY(`id`))ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;'''
        self.hostname = hostname if hostname else "localhost"
        self.user = user
        self.password = password
        self.database = database
        self.port = port if port else 3306
        # Define logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        try:
            self.logger.debug("Trying to import mysql.connector...")
            import mysql.connector
            self.logger.debug("Imported mysql.connector")
        except ImportError:
            raise ImportError("Can't connect with MySQL/MariaDB because mysql.connector isn't installed! Install it using: pip install mysql-connector-python")
        try:
            self.logger.debug(f"Connecting to server: {self.hostname}:{self.port}")
            self.logger.debug(f"Authenticating by user: {self.user} (Using password: {"Yes"if self.password else"No"})")
            self.logger.debug(f"Using database: {self.database}")
            self.logger.debug("Trying to connect...")
            conn = mysql.connector.connect(host=hostname,user=user,password=password,database=database,port=port,connection_timeout=10)
            if conn:
                self.logger.debug("Connection established")
                stmt = conn.cursor()
                stmt.execute(CREATE_TABLE_QUERY)
                self.logger.debug("Executed CREATE TABLE query")
                conn.commit()
                stmt.close()
                conn.close()
                self.logger.debug("Connection and cursor closed")
        except mysql.connector.Error as err:
            if err.errno == 1045:
                raise PermissionError(f"User {user} can't connect to the MySQL/MariaDB server: Permission Denied") from None
            elif err.errno == 2003:
                raise ConnectionRefusedError(f"Can't connect to the MySQL server {hostname}:{port} - Connection timeout or the server refused the connection") from None
            elif err.errno == 1044:
                raise PermissionError(f"User {user} can't access to the {database} DB: Permission Denied or this database doesn't exist") from None
            elif err.errno == 1142:
                raise PermissionError(f"User {user} can't execute required commands: Permission Denied. Please make sure user {user} can run at least CREATE and INSERT in {database} DB") from None
            else:
                raise RuntimeError(str(err)) from None
    def append_code_info(self,codeobj):
        self.logger.debug("Loading code info to append...")
        values = codeobj.to_mysql()
        self.logger.debug(f"Code info loaded: {values}")
        import mysql.connector
        self.logger.debug("Imported mysql.connector")
        try:
            self.logger.debug(f"Connecting to server: {self.hostname}:{self.port}")
            self.logger.debug(f"Authenticating by user: {self.user} (Using password: {"Yes"if self.password else"No"})")
            self.logger.debug(f"Using database: {self.database}")
            conn = mysql.connector.connect(host=self.hostname,user=self.user,password=self.password,database=self.database,port=self.port)
            if conn:
                self.logger.debug("Connection established")
                stmt = conn.cursor()
                stmt.execute("insert into`wins_log`(`code`,`appear_time`,`rewrite_time`,`nick`,`is_it_me`)values(%s,%s,%s,%s,%s);",values)
                conn.commit()
                self.logger.debug("Inserted new row to the database")
                stmt.close()
                conn.close()
                self.logger.debug("Connection and cursor closed")
        except mysql.connector.Error as err:
            raise RuntimeError(str(err)) from None