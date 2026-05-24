# Anarchia.GG Code Copier (Loader)
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# Import all needed libraries
from argparse import ArgumentParser
import logging
from sys import stdout, exit
from yaml import safe_load, YAMLError
from pathlib import Path
from signal import signal, SIGTERM, SIGINT, Signals
from time import sleep, time
from datetime import datetime, timedelta, timezone
import os
from csv import DictReader, DictWriter, writer
# Function to read n last lines without loading whole log file
def tail(path, n=1):
    if n <= 0:
        return ()
    lines = []
    with open(path, "rb") as f:
        f.seek(0, 2)
        filesize = f.tell()
        if filesize == 0:
            return ()
        pos = filesize - 1
        f.seek(pos)
        while pos >= 0 and f.read(1) == b'\n':
            pos -= 1
            f.seek(pos)
        buffer = bytearray()
        while pos >= 0 and len(lines) < n:
            f.seek(pos)
            byte = f.read(1)
            if byte == b'\n':
                lines.append(buffer[::-1].decode(errors="replace"))
                buffer.clear()
            else:
                buffer.append(byte[0])
            pos -= 1
        if buffer and len(lines) < n:
            lines.append(buffer[::-1].decode(errors="replace"))
    return tuple(reversed(lines))
# Make class to manage chat messages
class Minecraft:
    def __init__(self,mc_log_file:str):
        # Get full path to log file and try to open it
        self.logfile = Path(mc_log_file)
        try:
            with open(self.logfile):
                pass
        except FileNotFoundError:
            raise FileNotFoundError(f"File {self.logfile} can't be found!") from None
        except PermissionError:
            raise PermissionError(f"Can't open {self.logfile}: Permission denied") from None
    def is_mc_running(self)->bool:
        # Check is Minecraft running by checking log
        lastlines = tail(self.logfile,n=5)
        return not " [Render thread/INFO]: Stopping!" in "".join(lastlines)
    def read_raw_messages(self,n=1)->tuple:
        # Read only messages from chat and remove all log-like formatting
        if not self.is_mc_running():
            return tuple()
        messages = []
        lastmsgs=tail(path=self.logfile,n=n)
        for msg in lastmsgs:
            if " [System] [CHAT] " in msg:
                messages.append(msg.split(" [System] [CHAT] ")[1])
        return tuple(messages)
class Code:
    def __init__(self,code:str,timestamp:datetime,player:str,time:float,nicknames:tuple):
        self.code = code
        if timestamp:
            self.tsobj = timestamp
            self.timestamp = timestamp.isoformat(timespec="seconds")
        else:
            timediff = datetime.now().astimezone()-timedelta(seconds=time)
            self.tsobj = timediff
            self.timestamp = timediff.isoformat(timespec="seconds")
        self.player = player
        self.time = time
        self.isitme = player in nicknames
    def __eq__(self,other):
        return self.code == other.code and self.timestamp == other.timestamp and self.player == other.player and self.time == other.time and self.isitme == other.isitme
    def to_csv(self):
        return (self.code,self.player,self.time,self.timestamp,self.isitme)
    def to_mysql(self):
        return (self.code,self.tsobj,self.time,self.player,self.isitme)
    def to_msg(self):
        if self.isitme:
            return f"You have re-writed the code in {self.time}s"
        else:
            return f"Player {self.player} re-writed the code in {self.time}s"
class AnarchiaGG(Minecraft):
    def __init__(self,mc_log_file:str,nicknames:list):
        super().__init__(mc_log_file=mc_log_file)
        # Load all accepted nicknames
        if nicknames == None:
            self.nicknames=tuple()
        else:
            self.nicknames=tuple(nicknames)
        self.codes = []
        self.wins = []
        self.my_wins = 0
        self.last_code = None
        self.last_code_ts = None
    def get_code(self,n=1)->str:
        # Search for code to copy
        lastlines=self.read_raw_messages(n=n)
        for l in lastlines:
            if "Przepisz kod " in l and " aby otrzymać nagrodę!" in l:
                code = l.split("Przepisz kod ")[1].split(" ")[0]
                if code not in self.codes:
                    self.codes.append(code)
                    self.last_code = code
                    self.last_code_ts = datetime.now().astimezone()
                    return code
        return None
    def get_winner(self,n=1):
        # Search for winner info to save it
        lastlines=self.read_raw_messages(n=n)
        for l in lastlines:
            if "Gracz " in l and " jako pierwszy przepisał kod w czasie " in l and "s i otrzymał(a) 3 Klucze AFK!" in l and self.last_code and self.last_code_ts:
                splitted = l.split(" jako pierwszy przepisał kod w czasie ")
                player = splitted[0].split("Gracz ")[1]
                time = float(splitted[1].split(" ")[0].replace("s",""))
                infoobj = Code(self.last_code,self.last_code_ts,player,time,self.nicknames)
                self.last_code = None
                self.last_code_ts = None
                if infoobj not in self.wins:
                    self.wins.append(infoobj)
                    if infoobj.isitme:
                        self.my_wins += 1
                    return infoobj
        return None
    def get_stats(self)->dict:
        try:
            my_wins_percentage = round(self.my_wins/len(self.codes)*100,2)
        except ZeroDivisionError:
            my_wins_percentage = 0
        return {"total_codes":len(self.codes),"total_keys":len(self.codes)*3,"my_codes":self.my_wins,"my_keys":self.my_wins*3,"my_wins_percentage":my_wins_percentage}
# Class to send notifications
class Notify:
    def __init__(self):
        # Throws ImportError when lib is not installed
        from plyer import notification
    def send_notification(self,title,msg):
        # Send notification
        from plyer import notification
        notification.notify(app_name="MC Code Copier",timeout=5,title=title,message=msg)
# Class to copy code to the clipboard
class CodeCopy:
    def __init__(self):
        # This part throws ImportError when library is not installed
        from pyperclip import copy as pypercopy, PyperclipException
        try:
            pypercopy("Hello World from MC Code Copier! :)")
        except PyperclipException as e:
            raise RuntimeError(str(e)) from None
    def copy(self,code):
        from pyperclip import copy
        copy(code)
# Class to create and use .csv files
class CSV:
    def __init__(self,file):
        # If file is set to None, we will not make any changes
        self.file = file
        self.field_names=["Code","Nick","Time","Timestamp","Me"]
        if file:
            try:
                with open(file,encoding="utf-8") as f:
                    reader=DictReader(f)
                    if reader.fieldnames != self.field_names:
                        raise ValueError("File that you specified have different header names")
            except FileNotFoundError:
                # Create new file
                with open(file,mode="w",newline="",encoding="utf-8") as f:
                    writer=DictWriter(f,fieldnames=self.field_names)
                    writer.writeheader()
            except PermissionError:
                raise PermissionError(f"Can't open {file}: Permission denied")
    def append_code_info(self,codeobj):
        if self.file:
            toappend = codeobj.to_csv()
            with open(self.file,mode="a",newline="",encoding="utf-8") as f:
                wrt=writer(f)
                wrt.writerow(toappend)
# Class to save codes data to MySQL/MariaDB
class MySQL:
    def __init__(self,hostname,user,password,database,port=3306):
        CREATE_TABLE_QUERY='''CREATE TABLE IF NOT EXISTS`wins_log`(`id`int(11)NOT NULL AUTO_INCREMENT COMMENT'Primary key',`code`varchar(10)DEFAULT NULL COMMENT'String that contains key, that player had to re-write',`appear_time`timestamp NOT NULL DEFAULT current_timestamp()COMMENT'Shows exact time when code appeared',`rewrite_time`float NOT NULL COMMENT'Time (in seconds) in what time player have re-writed the code',`nick`varchar(16)NOT NULL COMMENT'Who sent the code',`is_it_me`tinyint(1)NOT NULL COMMENT'True if I won the code',PRIMARY KEY(`id`))ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;'''
        self.hostname = hostname
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        import mysql.connector
        try:
            conn = mysql.connector.connect(host=hostname,user=user,password=password,database=database,port=port)
            if conn:
                stmt = conn.cursor()
                stmt.execute(CREATE_TABLE_QUERY)
                conn.commit()
                stmt.close()
                conn.close()
        except mysql.connector.Error as err:
            if err.errno == 1045:
                raise PermissionError(f"User {user} can't connect to the database {database}: Permission Denied") from None
            elif err.errno == 2003:
                raise ConnectionRefusedError(f"Can't connect to the MySQL server because server address {hostname}:{port} isn't known") from None
            elif err.errno == 1044:
                raise PermissionError(f"User {user} can't access to the {database} DB: Permission Denied or this database isn't existing") from None
            elif err.errno == 1142:
                raise PermissionError(f"User {user} can't execute required commands: Permission Denied. Please make sure user {user} can run at least CREATE and INSERT in {database} DB") from None
            else:
                raise RuntimeError(str(err)) from None
    def append_code_info(self,codeobj):
        values = codeobj.to_mysql()
        import mysql.connector
        try:
            conn = mysql.connector.connect(host=self.hostname,user=self.user,password=self.password,database=self.database,port=self.port)
            if conn:
                stmt = conn.cursor()
                stmt.execute("insert into`wins_log`(`code`,`appear_time`,`rewrite_time`,`nick`,`is_it_me`)values(%s,%s,%s,%s,%s);",values)
                conn.commit()
                stmt.close()
                conn.close()
        except mysql.connector.Error as err:
            raise RuntimeError(str(err)) from None
# Match log level names with log levels
LOGLVLS={"quiet":logging.CRITICAL+1,"critical":logging.CRITICAL,"error":logging.ERROR,"warning":logging.WARNING,"info":logging.INFO,"verbose":logging.INFO,"debug":logging.DEBUG}
# Main function contains all code that should be executed when this program is NOT IMPORTED
def main():
    # Initalize argument parser
    parser = ArgumentParser(description="Anarchia.GG Code Copier is listening for reward codes in the chat and copies it to clipboard")
    parser.add_argument("-loglevel","-v",choices=LOGLVLS.keys(),default="info",help="Logging level")
    parser.add_argument("-all_logs","-vv",action="store_true",help="Show logs from all libraries")
    parser.add_argument("-config",type=str,default="config.yml",help="Path to configuration file")
    args = parser.parse_args()
    # Initalize logger
    logging.basicConfig(level=logging.CRITICAL+1 if not args.all_logs else LOGLVLS[args.loglevel],stream=stdout,format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"if args.all_logs else"[%(asctime)s] [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(LOGLVLS[args.loglevel])
    logger.info("Anarchia.GG Code Copier started")
    # Read configuration file
    logger.debug("Trying to load config file")
    config_file = Path(args.config)
    logger.debug(f"Path to config file: {config_file.absolute()}")
    try:
        # Try to load config file
        with open(config_file.absolute(),encoding="utf-8") as f:
            config = safe_load(f)
            logger.debug("Configuration has been loaded successfully")
    except FileNotFoundError:
        logger.error("Config file doesn't exist!")
        exit(os.EX_NOINPUT)
    except PermissionError:
        logger.error(f"Can't open {config_file}: Permission Denied")
        exit(os.EX_NOPERM)
    except YAMLError:
        logger.error(f"Invalid YAML syntax")
        exit(os.EX_CONFIG)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error")
        exit(os.EX_SOFTWARE)
    # Create an object to manage chat reading
    try:
        logger.debug("Trying to create AnarchiaGG object")
        nicks = config.get("nicknames")
        chat = AnarchiaGG(mc_log_file=config["log_file"],nicknames=nicks)
        logger.debug("Object was created successfully")
        logger.debug(f"Log file path: {Path(config["log_file"]).absolute()}")
        if not nicks:
            logger.warning("Nick list is empty")
        else:
            logger.debug(f"Nicks marked as mine: {", ".join(nicks)}")
    except KeyError:
        logger.error("Can't read log file path from config file!")
        exit(os.EX_CONFIG)
    except FileNotFoundError as e:
        # AnarchiaGG class throws FileNotFoundError and PermissionError with already prepared message, so we can only catch it and exit with specific code
        logger.error(str(e))
        exit(os.EX_NOINPUT)
    except PermissionError as e:
        logger.error(str(e))
        exit(os.EX_NOPERM)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Define some variables
    running = True
    # Function will run when SIGINT or SIGTERM is received to safely stop program
    def stop(signum, frame):
        logger.info(f"Received {Signals(signum).name}, QUITTING!")
        nonlocal running
        running = False
    signal(SIGINT,stop)
    signal(SIGTERM,stop)
    # Read from config file how many lines should we read backwards
    linestoread = config.get("read_lines")
    if not linestoread:
        logger.error("Amount of lines to check isn't specified in config file!")
        exit(os.EX_CONFIG)
    else:
        logger.debug(f"Last lines to read: {linestoread}")
    # Read from config file how frequently should we scan the chat
    sleepms = config.get("scan_frequency")
    if not sleepms:
        logger.error("Scan frequency isn't specified in config file!")
        exit(os.EX_CONFIG)
    else:
        logger.debug(f"Sleep time: {sleepms}")
    # Initalize notification class
    sendnf = config.get("send_notifications")
    try:
        if sendnf:
            logger.debug("Trying to initalize Notify class")
            notifications = Notify()
            logger.debug("Initalized successfully!")
    except ImportError:
        logger.critical("Can't send notifications because plyer lib isn't installed! Disable notifications in config or run: pip install plyer")
        exit(os.EX_UNAVAILABLE)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Initalize CodeCopy class
    copysetting = config.get("copy_to_clipboard")
    try:
        if copysetting:
            logger.debug("Trying to initalize CodeCopy class")
            codecopy = CodeCopy()
            logger.debug("Initalized successfully!")
    except ImportError:
        logger.critical("Can't copy to clipboard because pyperclip lib is not installed! Disable copy_to_clipboard in config file or run: pip install pyperclip")
        exit(os.EX_UNAVAILABLE)
    except RuntimeError as e:
        logger.debug(f"Original error message: {e}")
        logger.critical("Can't copy anything to clipboard because copying backend is not installed! See -loglevel debug for more details")
        exit(os.EX_UNAVAILABLE)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Initalize CSV class
    savetocsv = config.get("save_to_csv")
    try:
        if savetocsv:
            logger.debug("Trying to initalize CSV class")
            csvf = CSV(savetocsv)
            logger.debug("Initalized successfully!")
    except PermissionError as e:
        logger.error(str(e))
        exit(os.EX_NOPERM)
    except ValueError as e:
        logger.warning(str(e))
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Initalize MySQL class
    savetomysql = config.get("mysql")
    try:
        if savetomysql:
            logger.debug("Trying to initalize MySQL class")
            mysqlf = MySQL(hostname=savetomysql["host"],port=savetomysql["port"],user=savetomysql["user"],password=savetomysql["password"],database=savetomysql["database"])
            logger.debug("Initalized successfully!")
    except ImportError:
        logger.critical("Can't connect with MySQL/MariaDB because mysql.connector isn't installed! Install it using: pip install mysql-connector-python")
        exit(os.EX_UNAVAILABLE)
    except PermissionError as perr:
        logger.error(str(perr))
        exit(os.EX_NOPERM)
    except ConnectionRefusedError as crerr:
        logger.error(str(crerr))
        exit(os.EX_NOHOST)
    except RuntimeError as rerr:
        logger.critical(f"Internal MySQL error: {rerr}")
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Start main loop
    logger.info("Started listening")
    while running:
        # Get tick start time
        stime = time()
        # Try to load code and winner info
        code = chat.get_code(n=linestoread)
        winner = chat.get_winner(n=linestoread)
        # If code has appeared...
        if code:
            # Process, copy and display info about it
            codets = datetime.now(timezone.utc).astimezone()
            addtots = config.get("suggest_timeout")
            if addtots:
                sendin = codets + timedelta(0,addtots)
                sendtxt = f"Code {code} was found! Send it at: {sendin.hour}:{sendin.minute}:{sendin.second}"
            else:
                sendtxt = f"Code {code} was found!"
            logger.info(sendtxt)
            if copysetting:
                codecopy.copy(code)
            if sendnf:
                notifications.send_notification("Code appeared",sendtxt)
        # If winer info has appeared...
        if winner:
            # Process and save it
            logger.info(winner.to_msg())
            if savetocsv:
                csvf.append_code_info(winner)
        # Sleep loop
        timetosleep = (sleepms/1000)-(time()-stime)
        if timetosleep > 0:
            sleep(timetosleep)
    # This part will be executed after loop ends
    logger.info("### STATISTICS ###")
    stats = chat.get_stats()
    logger.info(f"Total codes captured: {stats.get("total_codes")}")
    logger.info(f"Codes re-writed by me: {stats.get("my_codes")}")
    logger.info(f"Keys received by me: {stats.get("my_keys")}")
    logger.info(f"My wins percentage: {stats.get("my_wins_percentage")}%")
    logger.info("Program finished job")
if __name__=="__main__":
    main()