# Anarchia.GG Code Copier (Loader)
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# Import all needed libraries
from argparse import ArgumentParser
import logging
from sys import stdout, exit
try:
    from yaml import safe_load, YAMLError
except ImportError:
    print("pyyaml lib isn't installed! Install it using: pip install pyyaml")
    exit(1)
from pathlib import Path
from signal import signal, SIGTERM, SIGINT, Signals
from time import sleep, time
from datetime import datetime, timedelta, timezone
from subprocess import run as subrun
from platform import system
import os
from csv import DictReader, DictWriter, writer
import ctypes
from json import dumps
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
# Function to check program privileges
def is_root():
    if hasattr(os,"getuid"):
        return os.getuid()==0
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False
# Function that can escape recursive dicts
def flatten_dict(d:dict,parent_key:str="",separator:str=".")->dict:
	result={}
	for key,value in d.items():
		full_key=f"{parent_key}{separator}{key}"if parent_key else key
		if isinstance(value,(list,tuple)):
			readval=dict(enumerate(value))
		else:
			readval=value
		if isinstance(readval,dict):
			nested_dicts={}
			for k,v in readval.items():
				if isinstance(v,dict):
					nested_dicts[k]=v
			flat_values={}
			for k,v in readval.items():
				if not isinstance(v,dict):
					if isinstance(v,(list,tuple)):
						nested_dicts[k]=dict(enumerate(v))
					else:
						flat_values[k]=v
			if flat_values:
				result[full_key]=flat_values
			if nested_dicts:
				nested_result=flatten_dict(nested_dicts,full_key,separator)
				result.update(nested_result)
		else:
			result[key]=value
	return result
# Function to return flatten values
def flatten_values(d:dict,parent_key:str="")->dict:
	result={}
	flattened=flatten_dict(d=d)
	for key,value in flattened.items():
		if isinstance(value,dict):
			for k,v in value.items():
				result[f"{key}.{k}"]=v
		else:
			result[key]=value
	return result
# Function to escape " and ' in strings
def escape_flat(s:str)->str:return(str(s).replace("\\","\\\\").replace('"','\\"').replace("'","\\'"))
# Class to manage return codes
class ReturnCodes:
    def __init__(self):
        self.EX_CANTCREAT=getattr(os,"EX_CANTCREAT",73)
        self.EX_CONFIG=getattr(os,"EX_CONFIG",78)
        self.EX_DATAERR=getattr(os,"EX_DATAERR",65)
        self.EX_IOERR=getattr(os,"EX_IOERR",74)
        self.EX_NOHOST=getattr(os,"EX_NOHOST",68)
        self.EX_NOINPUT=getattr(os,"EX_NOINPUT",66)
        self.EX_NOPERM=getattr(os,"EX_NOPERM",77)
        self.EX_NOUSER=getattr(os,"EX_NOUSER",67)
        self.EX_OK=getattr(os,"EX_OK",0)
        self.EX_OSERR=getattr(os,"EX_OSERR",71)
        self.EX_OSFILE=getattr(os,"EX_OSFILE",72)
        self.EX_PROTOCOL=getattr(os,"EX_PROTOCOL",76)
        self.EX_SOFTWARE=getattr(os,"EX_SOFTWARE",70)
        self.EX_TEMPFAIL=getattr(os,"EX_TEMPFAIL",75)
        self.EX_UNAVAILABLE=getattr(os,"EX_UNAVAILABLE",69)
        self.EX_USAGE=getattr(os,"EX_USAGE",64)
# Initalize ReturnCodes class
rtn=ReturnCodes()
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
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.code = code
        self.logger.debug(f"Creating Code object for code: {code}")
        if timestamp:
            self.tsobj = timestamp.astimezone()
            self.timestamp = self.tsobj.isoformat(timespec="seconds")
            self.logger.debug(f"Date loaded from given parameter: {self.tsobj}")
        else:
            timediff = datetime.now().astimezone()-timedelta(seconds=time)
            self.tsobj = timediff
            self.timestamp = timediff.isoformat(timespec="seconds")
            self.logger.debug(f"Date calculated from current time and re-write time: {self.tsobj}")
        self.player = player
        self.time = time
        self.isitme = player in nicknames
        self.logger.debug(f"Loaded informations. Player: {self.player} ({"Me"if self.isitme else "Not me"}); Re-write time: {self.time}")
    def __eq__(self,other):
        return self.code == other.code and self.tsobj == other.tsobj and self.player == other.player and self.time == other.time and self.isitme == other.isitme
    def to_csv(self):
        self.logger.debug("Exporting data to format expected by CSV class")
        return (self.code,self.player,self.time,self.timestamp,self.isitme)
    def to_mysql(self):
        self.logger.debug("Exporting data to format expected by MySQL class")
        return (self.code,self.tsobj,self.time,self.player,self.isitme)
    def to_msg(self):
        self.logger.debug("Exporting data to plain text format")
        if self.isitme:
            return f"You have re-writed the code in {self.time}s"
        else:
            return f"Player {self.player} re-writed the code in {self.time}s"
class AnarchiaGG(Minecraft):
    def __init__(self,mc_log_file:str,nicknames:list):
        super().__init__(mc_log_file=mc_log_file)
        # Create in-class logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
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
    def read_messages_after_code(self,n=1)->tuple:
        lastlines=self.read_raw_messages(n=n)
        lines=[]
        for line in reversed(lastlines):
            if "Przepisz kod " in line and " aby otrzymać nagrodę!" in line:
                break
            else:
                lines.append(line)
        return tuple(reversed(lines))
    def get_code(self,n=1)->str:
        # Search for code to copy
        lastlines=self.read_raw_messages(n=n)
        for l in lastlines:
            if "Przepisz kod " in l and " aby otrzymać nagrodę!" in l:
                code = l.split("Przepisz kod ")[1].split(" ")[0]
                if code not in self.codes:
                    self.logger.debug(f"Found unknown code: {code}")
                    self.codes.append(code)
                    self.last_code = code
                    self.last_code_ts = datetime.now().astimezone()
                    self.logger.debug(f"Last code variable is set to {self.last_code}")
                    self.logger.debug(f"Last code timestamp variable is set to {self.last_code_ts}")
                    return code
        return None
    def get_winner(self,n=1):
        # Search for winner info to save it
        #lastlines=self.read_raw_messages(n=n) OLD VERSION
        lastlines=self.read_messages_after_code(n=n)
        for l in lastlines:
            if "Gracz " in l and " jako pierwszy przepisał kod w czasie " in l and "s i otrzymał(a) 3 Klucze AFK!" in l and self.last_code and self.last_code_ts:
                splitted = l.split(" jako pierwszy przepisał kod w czasie ")
                player = splitted[0].split("Gracz ")[1]
                time = float(splitted[1].split(" ")[0].replace("s",""))
                self.logger.debug(f"Found new winner info! Player: {player}; Time: {time}")
                infoobj = Code(self.last_code,self.last_code_ts,player,time,self.nicknames)
                self.logger.debug(f"Loaded last code variable: {self.last_code}")
                self.logger.debug(f"Loaded last code timestamp variable: {self.last_code_ts}")
                self.last_code = None
                self.last_code_ts = None
                self.logger.debug("Both values set to None")
                if infoobj not in self.wins:
                    self.wins.append(infoobj)
                    if infoobj.isitme:
                        self.my_wins += 1
                        self.logger.debug("Sender is classified as me, incrementing my_wins counter")
                    return infoobj
        return None
    def predict_next_code(self):
        # Predict, when next code will appear
        if len(self.wins) < 2:
            self.logger.debug(f"Not enough codes in memory to predict next's appear time. Function needs at least 2, but {len(self.wins)} is available")
            return None
        self.logger.debug("Predicting next code appear time")
        last_code=self.wins[-1].tsobj
        self.logger.debug(f"Date from last code: {last_code}")
        timediff=last_code-self.wins[-2].tsobj
        self.logger.debug(f"Time difference between last and second last code: {timediff}")
        time_since_last_code=datetime.now().astimezone()-last_code
        self.logger.debug(f"Time since last code: {time_since_last_code}")
        predicted_time=timediff-time_since_last_code
        self.logger.debug(f"Predicted time to next code: {predicted_time}")
        return predicted_time.total_seconds()
    def get_stats(self)->dict:
        self.logger.debug("Calculating all statistics...")
        try:
            my_wins_percentage = round(self.my_wins/len(self.codes)*100,2)
        except ZeroDivisionError:
            my_wins_percentage = 0
        return {"total_codes":len(self.codes),"total_keys":len(self.codes)*3,"my_codes":self.my_wins,"my_keys":self.my_wins*3,"my_wins_percentage":my_wins_percentage}
# Custom program exception
class MCError(Exception):
    def __init__(self,message:str,returncode:int=1,native_exception:Exception=Exception):
        super().__init__(message)
        self.returncode=returncode
        self.native_exception=native_exception
# Class to send notifications
class Notify:
    def __init__(self):
        # Define logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Try to find out is notify-send installed and are we operating on Linux
        self.logger.debug("Checking is your operating system supporting this function")
        SUPPORTED_OS=["Linux"]
        if system() not in SUPPORTED_OS:
            raise RuntimeError(f"You can't use notifications function because you are running on {system()}! Currently, you can only use it on those OSes: {", ".join(SUPPORTED_OS)}")
        if system() == "Linux":
            self.logger.debug(f"Running on Linux, checking is notify-send installed")
            try:
                nfsendver=subrun(["notify-send","--version"],text=True,capture_output=True)
                if nfsendver.returncode == 0:
                    self.logger.debug(f"notify-send is installed! Version: {nfsendver.stdout.strip()}")
                else:
                    self.logger.debug(f"notify-send error: {nfsendver.stderr}")
                    self.logger.warning("notify-send is installed but finished with an error. Program belives that everything is working correctly, so continuing its work. For more details please check -loglevel debug")
            except FileNotFoundError:
                raise RuntimeError("notify-send is not installed on your system! Install it using your package manager, like pacman -S libnotify, apt install libnotify-bin, etc.")
    def send_notification(self,title,msg):
        # Send notification
        self.logger.debug(f"Sending notification with app name 'MC Code Copier', title '{title}' and content '{msg}'")
        subrun(["notify-send","--app-name=MC Code Copier",title,msg])
# Class to copy code to the clipboard
class CodeCopy:
    def __init__(self):
        # Define logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # This part throws ImportError when library is not installed
        try:
            from pyperclip import copy as pypercopy, paste as pyperpaste, PyperclipException
            self.logger.debug("pyperclip lib was imported successfully")
        except ImportError:
            raise RuntimeError("Can't copy to clipboard because pyperclip lib is not installed! If you want to use this function, run: pip install pyperclip")
        try:
            sample_text="Hello World from MC Code Copier! :)"
            self.logger.debug(f"Trying to copy sample text: {sample_text}")
            pypercopy(sample_text)
            pasted_text=pyperpaste()
            self.logger.debug(f"Pasted text: {pasted_text}")
            if sample_text != pasted_text:
                self.logger.warning("Something went wrong: Copied and pasted texts aren't the same values!")
        except PyperclipException as e:
            self.logger.debug(f"Original error message: {e}")
            raise RuntimeError("Something went wrong and you can't copy anything to the clipboard! See -loglevel debug for more info"+". You are on Linux, so you can check is your copying backend (like wl-copy) installed"if system()=="Linux"else"")
    def copy(self,code:str):
        from pyperclip import copy
        self.logger.debug(f"Copying {code}")
        copy(code)
# Class to create and use .csv files
class CSV:
    def __init__(self,file:str):
        # Create logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # If file is set to None, we will not make any changes
        self.field_names=["Code","Nick","Time","Timestamp","Me"]
        if file:
            self.file = Path(file)
            self.logger.debug(f"Given file path: {self.file.resolve()}")
            self.logger.debug("Checking does path exists")
            if self.file.exists():
                self.logger.debug("Path exists, checking is it file")
                if self.file.is_file():
                    try:
                        with open(file=self.file.resolve(),mode="r",encoding="utf-8") as f:
                            self.logger.debug("Opened CSV file")
                            reader=DictReader(f)
                            self.logger.debug(f"Loaded field names: {", ".join(reader.fieldnames)}")
                            self.logger.debug(f"Expected field names: {", ".join(self.field_names)}")
                            if reader.fieldnames != self.field_names:
                                self.logger.warning("File that you specified have different header names than expected!")
                    except PermissionError:
                        raise PermissionError(f"Can't open {self.file.resolve()}: Permission Denied")
                else:
                    raise IsADirectoryError(f"Can't open {self.file.resolve()} - this path points to a directory!")
            else:
                # Create new file
                self.logger.debug("File doesn't exists, creating a blank one")
                try:
                    with open(file=self.file.resolve(),mode="w",newline="",encoding="utf-8") as f:
                        self.logger.debug("File opened")
                        writer=DictWriter(f,fieldnames=self.field_names)
                        writer.writeheader()
                        self.logger.debug("File saved successfully")
                except PermissionError:
                    raise PermissionError(f"Can't create {self.file.resolve()}: Permission Denied")
        else:
            self.logger.debug(f"File path wasn't given, skipping")
    def append_code_info(self,codeobj):
        if self.file:
            self.logger.debug("Loading code info to append...")
            toappend = codeobj.to_csv()
            self.logger.debug(f"Loaded values: {toappend}")
            with open(self.file,mode="a",newline="",encoding="utf-8") as f:
                self.logger.debug("File was opened")
                wrt=writer(f)
                wrt.writerow(toappend)
                self.logger.debug("Successfully writed all needed data")
# Class to save codes data to MySQL/MariaDB
class MySQL:
    def __init__(self,hostname:str,user:str,password:str,database:str,port=3306):
        CREATE_TABLE_QUERY='''CREATE TABLE IF NOT EXISTS`wins_log`(`id`int(11)NOT NULL AUTO_INCREMENT COMMENT'Primary key',`code`varchar(10)DEFAULT NULL COMMENT'String that contains key, that player had to re-write',`appear_time`timestamp NOT NULL DEFAULT current_timestamp()COMMENT'Shows exact time when code appeared',`rewrite_time`float NOT NULL COMMENT'Time (in seconds) in what time player have re-writed the code',`nick`varchar(16)NOT NULL COMMENT'Who sent the code',`is_it_me`tinyint(1)NOT NULL COMMENT'True if I won the code',PRIMARY KEY(`id`))ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;'''
        self.hostname = hostname
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        # Define logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        import mysql.connector
        self.logger.debug("Imported mysql.connector")
        try:
            self.logger.debug(f"Connecting to server: {self.hostname}:{self.port}")
            self.logger.debug(f"Authenticating by user: {self.user} (Using password: {"Yes"if self.password else"No"})")
            self.logger.debug(f"Using database: {self.database}")
            self.logger.debug("Trying to connect...")
            conn = mysql.connector.connect(host=hostname,user=user,password=password,database=database,port=port)
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
# Class to manage configuration
class Config:
    def defaultconf(self,path:str):
        fullpath = Path(path)
        self.logger.debug(f"Trying to create new config file in {fullpath.resolve()}")
        if fullpath.exists():
            self.logger.error("Config file already exists!")
            exit(rtn.EX_CANTCREAT)
        DEFAULT_CONFIG_FILE=f'''# MC Code Copier default config file\n# Program maintainer: AirKeyooo <airkeyooo@gmail.com>\n# Generated: {datetime.now().astimezone().strftime("%d.%m.%Y %H:%M:%S %Z")}\n\n# Add path to your latest.log file\nlog_file: /path/to/latest.log\n\n# How many lines program should read. More lines = improved efficiency, but higher CPU and disk usage\nread_lines: 2\n\n# Should program send notifications about new codes?\n# WARNING: Works only on Linux and ends with error on any other OS!\nsend_notifications: false\n\n# Suggest when user should send code to don't look suspicious\n# Give value in seconds. If you don't want to use this function, comment it or set value to 0\nsuggest_timeout: 5\n\n# Change shuold program predict when next code will appear.\n# Program currently needs at least 2 codes in memory to predict next one\npredict_next_code: false\n\n# Should program automatically copy received code to the clipboard?\n# WARNING: Requires pyperclib module, which can be installed using: `pip install pyperclip`\ncopy_to_clipboard: false\n\n# Save results to .csv file\n# If you don't want to use this function, comment line below\nsave_to_csv: /path/to/file.csv\n\n# Set all nicknames that are yours\n# If you don't want to set your nicknames, comment/remove whole section below\nnicknames:\n  - Nickname1\n  - Nickname2\n\n# How frequently (in ms) chat should be scanned.\n# e.g. 200 -> messages will be scanned every 200ms\n# Smaller delay may improve efficiency, but will end up with higher CPU and disk usage\nscan_frequency: 300\n\n# MySQL DB Access config\n# If you want to use MySQL, uncomment all lines below and type your credentials\n# When optional is set to false, program will finish with an error when MySQL/MariaDB server is unreachable. When it is set to true, program will only warn that it can't save data to MySQL/MariaDB, but continue its work\n# If the user doesn't have password (VERY UNSAFE!), leave password field blank (nothing after ':')\n# Minimal required user permissions: CREATE, INSERT\n# WARNING: Requires mysql.connector module, which can be installed using: `pip install mysql-connector-python`\n#mysql:\n#  host: localhost\n#  port: 3306\n#  user: root\n#  password: \n#  database: my_database\n#  optional: false'''
        try:
            with open(file=fullpath.resolve(),mode="w",encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG_FILE)
            self.logger.info("Default config file was created successfully")
            exit(rtn.EX_OK)
        except PermissionError:
            self.logger.error(f"Can't save file in {fullpath.resolve()}: Permission Denied")
            exit(rtn.EX_NOPERM)
        except Exception as e:
            self.logger.debug(f"Program error: {e}")
            self.logger.critical("Internal app error!")
            exit(rtn.EX_SOFTWARE)
    def __init__(self,args):
        # Create class-level logger
        self.logger=logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if args.default_config:
            # Create default configuration file
            self.defaultconf(args.config)
        # Try to read config from configuration file
        configfile=Path(args.config)
        self.logger.debug(f"Path to configuration file loaded from parameter: {configfile.resolve()}"+(" (default)"if configfile.name=="config.yml"else""))
        if not configfile.exists():
            self.logger.debug("Config file doesn't exist, trying to load it from other paths")
            if system()=="Linux":
                # Here you can add possible config files location - first items have bigger priority
                LINUX_PATHS=["/etc/codecopier.yml","/etc/codecopier/config.yml","/etc/codecopier/codecopier.yml"]
                LINUX_PATHS_WITH_HOME=[".config/codecopier.yml",".config/codecopier/config.yml",".config/codecopier/codecopier.yml"]
                homedir=Path(os.getenv("HOME"))
                self.logger.debug("Operating on Linux, trying to load some config files...")
                for path in reversed(LINUX_PATHS):
                    pathto=Path(path)
                    if pathto.exists():
                        self.logger.debug(f"Path {pathto.resolve()} exists, checking is it file")
                        if pathto.is_file():
                            self.logger.debug(f"File {pathto.resolve()} exists! Trying to read it...")
                            try:
                                with open(file=pathto.resolve(),mode="r",encoding="utf-8"):
                                    pass
                                configfile=pathto
                                self.logger.debug(f"Found readable file: {configfile.resolve()} Searching further for other possible file with higher priority...")
                            except PermissionError:
                                self.logger.warning(f"Possible config file {pathto.resolve()} exists, but program can't read it: No permission. Skipping it and searching other locations...")
                        else:
                            self.logger.warning(f"Possible config {pathto.resolve()} exists, but it is a directory! Skipping!")
                    else:
                        self.logger.debug(f"{pathto.resolve()} doesn't exist")
                for path in reversed(LINUX_PATHS_WITH_HOME):
                    pathto=homedir/path
                    if pathto.exists():
                        self.logger.debug(f"Path {pathto.resolve()} exists, checking is it file")
                        if pathto.is_file():
                            self.logger.debug(f"File {pathto.resolve()} exists! Trying to read it...")
                            try:
                                with open(file=pathto.resolve(),mode="r",encoding="utf-8"):
                                    pass
                                configfile=pathto
                                self.logger.debug(f"Found readable file: {configfile.resolve()} Searching further for other possible file with higher priority...")
                            except PermissionError:
                                self.logger.warning(f"Possible config file {pathto.resolve()} exists, but program can't read it: No permission. Skipping it and searching other locations...")
                        else:
                            self.logger.warning(f"Possible config {pathto.resolve()} exists, but it is a directory! Skipping!")
                    else:
                        self.logger.debug(f"{pathto.resolve()} doesn't exist")
            elif system()=="Windows":
                self.logger.debug("Operating on Windows, trying to load some config files...")
                WINDOWS_PROGRAM_PATHS=["codecopier/config.yml","codecopier/codecopier.yml","CodeCopier/config.yml","CodeCopier/codecopier.yml","CodeCopier/CodeCopier.yml"]
                WINDOWS_PROGRAM_LOCATIONS=[os.getenv("APPDATA"),os.getenv("PROGRAMDATA"),os.getenv("LOCALAPPDATA")]
                for progl in WINDOWS_PROGRAM_LOCATIONS:
                    for progp in WINDOWS_PROGRAM_PATHS:
                        pathto=Path(progl)/progp
                        if pathto.exists():
                            self.logger.debug(f"Path {pathto.resolve()} exists, checking is it file")
                            if pathto.is_file():
                                self.logger.debug(f"File {pathto.resolve()} exists! Trying to read it...")
                                try:
                                    with open(file=pathto.resolve(),mode="r",encoding="utf-8"):
                                        pass
                                    configfile=pathto
                                    self.logger.debug(f"Found readable file: {configfile.resolve()} Searching further for other possible file with higher priority...")
                                except PermissionError:
                                    self.logger.warning(f"Possible config file {pathto.resolve()} exists, but program can't read it: No permission. Skipping it and searching other locations...")
                            else:
                                self.logger.warning(f"Possible config {pathto.resolve()} exists, but it is a directory! Skipping!")
                        else:
                            self.logger.debug(f"{pathto.resolve()} doesn't exist")
            # Read config file from special env variable: CODECOPIER_CONFIG
            self.logger.debug("Trying to load config file path from environment variable CODECOPIER_CONFIG")
            pathfromenv=os.getenv("CODECOPIER_CONFIG")
            if pathfromenv:
                pathto=Path(pathfromenv)
                self.logger.debug(f"Variable exists! Path: {pathto.resolve()}")
                if pathto.exists():
                    self.logger.debug("Checking is it file")
                    if pathto.is_file():
                        self.logger.debug("File exists, so trying to read it")
                        try:
                            with open(file=pathto.resolve(),mode="r",encoding="utf-8"):
                                pass
                            self.logger.debug("File exists and it is readable, so using it as a primary config file")
                            configfile=pathto
                        except PermissionError:
                            self.logger.warning(f"Config file that you specified in CODECOPIER_CONFIG environment variable exists, but program don't have permissions to run it. Using path from -config parameter")
                    else:
                        self.logger.warning("Path that you have specified in CODECOPIER_CONFIG environment variable points to a directory! Skipping, using path from -config parameter")
                else:
                    self.logger.warning(f"Config file that you specified in CODECOPIER_CONFIG environment variable doesn't exist! Using path from -config parameter")
            else:
                self.logger.debug("Environment variable CODECOPIER_CONFIG doesn't exist")
        try:
            self.logger.debug(f"Trying to load config file from {configfile.resolve()}")
            with open(file=configfile.resolve(),mode="r",encoding="utf-8") as f:
                config = safe_load(f)
                self.logger.debug("Config file was loaded successfully. Configuration:")
        except FileNotFoundError:
            raise FileNotFoundError("Config file doesn't exist!")
        except IsADirectoryError:
            raise FileNotFoundError("Path that you have specified points to a directory!")
        except YAMLError:
            raise SyntaxError("Invalid YAML syntax in config file!")
        except PermissionError:
            raise PermissionError(f"Can't open {configfile.resolve()}: Permission Denied")
        if config.get("log_file"):
            if type(config.get("log_file"))is str:
                self.log_file=Path(config.get("log_file"))
                self.logger.debug(f"Path to latest.log file: {self.log_file.resolve()}")
                if not self.log_file.exists():
                    raise FileNotFoundError(f"Log file in {self.log_file.resolve()} doesn't exist!")
            else:
                raise TypeError(f"log_file can be only str, not {config.get("log_file").__class__.__name__}!")
        else:
            raise KeyError("Config file isn't specified in config file!")
        self.read_lines=config.get("read_lines")
        if self.read_lines:
            if type(self.read_lines)is int:
                self.logger.debug(f"Read n lines backwards: {self.read_lines}")
            else:
                raise TypeError(f"read_lines can be only int, not {self.read_lines.__class__.__name__}!")
        else:
            raise KeyError("read_lines value isn't specified!")
        self.send_notifications=bool(config.get("send_notifications"))
        self.logger.debug("Program will send notifications" if self.send_notifications else "Program won't send notifications")
        if config.get("suggest_timeout"):
            if type(config.get("suggest_timeout"))is int:
                self.suggest_timeout=config.get("suggest_timeout")
                self.logger.debug(f"Suggest timeout: {self.suggest_timeout}")
            else:
                raise TypeError(f"suggest_timeout can be only int, not {config.get("suggest_timeout").__class__.__name__}!")
        else:
            self.suggest_timeout=0
            self.logger.debug("Program won't suggest timeout")
        if config.get("predict_next_code"):
            if type(config.get("predict_next_code"))is bool:
                self.predict_next_code=config.get("predict_next_code")
                self.logger.debug("Program will predict next code appear time")
            else:
                raise TypeError(f"predict_next_code can be only bool, not {config.get("predict_next_code").__class__.__name__}!")
        else:
            self.predict_next_code=False
            self.logger.debug("Program won't predict next code appear time")
        self.copy_to_clipboard=bool(config.get("copy_to_clipboard"))
        self.logger.debug("Program will copy code to clipboard" if self.copy_to_clipboard else "Program won't copy code to clipboard")
        if config.get("save_to_csv"):
            if type(config.get("save_to_csv"))is str:
                self.save_to_csv=Path(config.get("save_to_csv"))
                self.logger.debug(f"Save history to CSV file: {self.save_to_csv.resolve()}")
            else:
                raise TypeError(f"save_to_csv can be only str, not {config.get("save_to_csv").__class__.__name__}!")
        else:
            self.save_to_csv=None
            self.logger.debug("Program won't save history to CSV file")
        if config.get("nicknames"):
            if type(config.get("nicknames"))is list:
                self.nicknames=config.get("nicknames")
                self.logger.debug(f"Nicknames marked as mine: {", ".join(self.nicknames)}")
            else:
                raise TypeError(f"nicknames can be only list, not {config.get("nicknames").__class__.__name__}!")
        else:
            self.nicknames=[]
            self.logger.warning("Nick list is empty")
        if config.get("scan_frequency"):
            if type(config.get("scan_frequency"))is int:
                self.scan_frequency=config.get("scan_frequency")
                self.logger.debug(f"Chat will be scanned every {self.scan_frequency}ms")
            else:
                raise TypeError(f"scan_frequency can be only int, not {config.get("scan_frequency").__class__.__name__}!")
        else:
            raise KeyError("scan_frequency isn't specified!")
        if config.get("mysql"):
            if type(config.get("mysql"))is dict:
                self.mysql=config.get("mysql")
                self.logger.debug("MySQL/MariaDB support is enabled")
            else:
                raise TypeError(f"mysql can be only dict, not {config.get("mysql").__class__.__name__}!")
        else:
            self.mysql=None
            self.logger.debug("MySQL/MariaDB support is disabled")
# Class to manage print format and additional printed info
class Printing:
    def parser_default(self)->str:
        self.logger.debug("Parsing mode: default")
        def parse_to_default_fmt(data: dict) -> str:
            output_lines = []
            for key,value in data.items():
                tag = key.upper()
                if isinstance(value,(list,tuple)):
                    for item in value:
                        output_lines.append(f"[{tag}]")
                        output_lines.extend(_format_sub_dict(item))
                        output_lines.append(f"[/{tag}]")
                else:
                    output_lines.append(f"[{tag}]")
                    output_lines.extend(_format_sub_dict(value))
                    output_lines.append(f"[/{tag}]")
            return "\n".join(output_lines)
        def _format_sub_dict(d: dict) -> list:
            lines = []
            if not isinstance(d, dict):
                return [f"value={d}"]
            for k,v in d.items():
                if isinstance(v,(list,tuple)):
                    for index,item in enumerate(v):
                        lines.append(f"{k}:{index}={item}")
                else:
                    lines.append(f"{k}={v}")
            return lines
        return parse_to_default_fmt(self.tree)
    def parser_flat(self)->str:
        self.logger.debug("Parsing mode: flat")
        el_list=[]
        escaped=flatten_values(self.tree)
        for k,v in escaped.items():
            el_list.append(f"{escape_flat(k)}=\"{escape_flat(v)}\"")
        return "\n".join(el_list)
    def parser_ini(self)->str:
        self.logger.debug("Parsing mode: ini")
        from configparser import ConfigParser
        from io import StringIO
        config=ConfigParser()
        escaped=flatten_dict(self.tree)
        for key,value in escaped.items():
            config[key]=value
        buf=StringIO()
        config.write(buf)
        return buf.getvalue().strip()
    def parser_json(self)->str:
        self.logger.debug("Parsing mode: json")
        return dumps(self.tree)
    def parser_xml(self)->str:
        self.logger.debug("Parsing mode: xml")
        import xml.etree.ElementTree as ET
        def dict_to_xml(data:dict,root_tag:str="root")->str:
            def build_element(parent:ET.Element,key:str,value):
                if isinstance(value,dict):
                    child=ET.SubElement(parent,key)
                    for k,v in value.items():
                        build_element(child,k,v)
                elif isinstance(value,(list,tuple)):
                    container=ET.SubElement(parent,key)
                    for item in value:
                        if isinstance(item,dict):
                            el=ET.SubElement(container,"item")
                            for k,v in item.items():
                                build_element(el,k,v)
                        else:
                            el=ET.SubElement(container,"item")
                            el.text=str(item)
                elif isinstance(value,(int,float,str,bool)):
                    parent.set(key,str(value))
                else:
                    parent.set(key,repr(value))
            root=ET.Element(root_tag)
            for key,value in data.items():
                build_element(root,key,value)
            ET.indent(root,space="  ")
            return ET.tostring(root,encoding="unicode",xml_declaration=True)
        return dict_to_xml(data=self.tree,root_tag="codecopy")
    def __init__(self,print_format:str="default"):
        # Get class-level logger
        self.logger=logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Define all parsers
        self.parsers={"default":self.parser_default,"flat":self.parser_flat,"ini":self.parser_ini,"json":self.parser_json,"xml":self.parser_xml}
        self.logger.debug("Checking print_format type")
        if type(print_format)is str:
            self.logger.debug("print_format is str; checking, is it correct format name")
            if print_format in self.parsers.keys():
                self.logger.debug(f"{print_format} is correct parser name, using this format's parser")
                self.using_parser=self.parsers[print_format]
            else:
                raise KeyError(f"{print_format} isn't correct print format! Allowed formats: {", ".join(self.parsers.keys())}")
        else:
            raise TypeError(f"print_format have to be str, not {print_format.__class__.__name__}!")
        self.tree={}
    def add_element(self,name:str,tree:dict):
        self.logger.debug("Checking is name a string")
        if type(name)is str:
            self.logger.debug("name is string; checking, is this element already in main tree")
            if name in self.tree.keys():
                raise FileExistsError(f"{name} is already added to main tree!")
            self.logger.debug(f"{name} doesn't exist in main tree! Checking, is given tree a dict, list or tuple")
            if isinstance(tree,(dict,list,tuple)):
                self.logger.debug(f"tree is {tree.__class__.__name__}, adding element to the main tree! Name: {name}; Tree: {tree}")
                self.tree[name]=tree
            else:
                raise TypeError(f"tree have to be dict, list or tuple, not {tree.__class__.__name__}!")
        else:
            raise TypeError(f"name have to be str, not {name.__class__.__name__}!")
# Match log level names with log levels
LOGLVLS={"quiet":logging.CRITICAL+1,"critical":logging.CRITICAL,"error":logging.ERROR,"warning":logging.WARNING,"info":logging.INFO,"verbose":logging.INFO,"debug":logging.DEBUG}
# Main function contains all code that should be executed when this program is NOT IMPORTED
def main():
    # Save start time
    start_time = datetime.now()
    # Initalize argument parser
    parser = ArgumentParser(description="MC Code Copier is listening for reward codes (In Anarchia.GG's OneBlock) in the chat, copies it to clipboard and stores it")
    parser.add_argument("-loglevel","-v",choices=LOGLVLS.keys(),default="info",help="Logging level")
    parser.add_argument("-config",type=str,default="config.yml",help="Path to configuration file. Settings passed as argumens will ALWAYS overwrite settings in config file")
    parser.add_argument("-default_config",action="store_true",help="After specifying this flag, program will create default configuration file in pointed path")
    parser.add_argument("-runasroot",action="store_true",help="Make possible for program to run as root")
    parser.add_argument("-print_format","-output_format","-of",help="Choose output printing format",default="default",choices=("default","flat","ini","json","xml"),type=str)
    parser.add_argument("-show_statistics",action="store_true",help="Print statistics using format specified in -print_format option")
    args = parser.parse_args()
    if args.loglevel == "debug":
        logger_format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
        logger_global_lvl=logging.DEBUG
    else:
        logger_format="[%(asctime)s] [%(levelname)s] %(message)s"
        logger_global_lvl=logging.CRITICAL+1
    # Initalize logger
    logging.basicConfig(level=logger_global_lvl,stream=stdout,format=logger_format)
    logger = logging.getLogger(__name__)
    logger.setLevel(LOGLVLS[args.loglevel])
    logger.info("Anarchia.GG Code Copier started")
    # Check program privileges
    logger.debug("Checking program privileges")
    amirooted=is_root()
    if amirooted:
        if args.runasroot:
            logger.critical("Program is running as root/admin! It is VERY UNSAFE to run this program with those privileges, because program doesn't need it.")
        else:
            logger.critical("Program is running as root/admin! It is VERY UNSAFE to run this program with those privileges, because program doesn't need it. Run it as a normal user! But if you really want to continue (VERY UNRECOMMENDED), add -runasroot flag (but keep in mind that you are doing it for YOUR OWN RESPONSIBILITY!!)")
            exit(1)
    else:
        logger.debug("Program is not running as root/admin, continuing safely")
    # Initalize Config class
    try:
        logger.debug("Trying to initalize config class")
        config = Config(args)
        logger.debug("Config class initalized successfully")
    except FileNotFoundError as e:
        logger.error(e)
        exit(rtn.EX_NOINPUT)
    except PermissionError as e:
        logger.error(e)
        exit(rtn.EX_NOPERM)
    except SyntaxError as e:
        logger.error(e)
        exit(rtn.EX_CONFIG)
    except KeyError as e:
        logger.error(e.args[0])
        exit(rtn.EX_CONFIG)
    except TypeError as e:
        logger.error(e)
        exit(rtn.EX_DATAERR)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Create an object to manage chat reading
    try:
        logger.debug("Trying to create AnarchiaGG object")
        nicks = config.nicknames
        chat = AnarchiaGG(mc_log_file=config.log_file,nicknames=nicks)
        logger.debug("Object was created successfully")
    except FileNotFoundError as e:
        # AnarchiaGG class throws FileNotFoundError and PermissionError with already prepared message, so we can only catch it and exit with specific code
        logger.error(e)
        exit(rtn.EX_NOINPUT)
    except PermissionError as e:
        logger.error(e)
        exit(rtn.EX_NOPERM)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
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
    linestoread = config.read_lines
    # Read from config file how frequently should we scan the chat
    sleepms = config.scan_frequency
    # Initalize notification class
    sendnf = config.send_notifications
    try:
        if sendnf:
            logger.debug("Trying to initalize Notify class")
            notifications = Notify()
            logger.debug("Initalized successfully!")
    except RuntimeError as e:
        logger.error(e)
        exit(rtn.EX_UNAVAILABLE)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Initalize CodeCopy class
    copysetting = config.copy_to_clipboard
    try:
        if copysetting:
            logger.debug("Trying to initalize CodeCopy class")
            codecopy = CodeCopy()
            logger.debug("Initalized successfully!")
    except RuntimeError as e:
        logger.error(e)
        exit(rtn.EX_UNAVAILABLE)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Initalize CSV class
    savetocsv = config.save_to_csv
    try:
        if savetocsv:
            logger.debug("Trying to initalize CSV class")
            csvf = CSV(savetocsv)
            logger.debug("Initalized successfully!")
    except PermissionError as e:
        logger.error(e)
        exit(rtn.EX_NOPERM)
    except IsADirectoryError as e:
        logger.error(e)
        exit(rtn.EX_OSFILE)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Initalize MySQL class
    savetomysql = config.mysql
    try:
        if savetomysql:
            logger.debug("Trying to initalize MySQL class")
            mysqlf = MySQL(hostname=savetomysql["host"],port=savetomysql.get("port")if savetomysql.get("port")else 3306,user=savetomysql["user"],password=savetomysql["password"],database=savetomysql["database"],)
            logger.debug("Initalized successfully!")
    except ImportError:
        logger.error("Can't connect with MySQL/MariaDB because mysql.connector isn't installed! Install it using: pip install mysql-connector-python")
        exit(rtn.EX_UNAVAILABLE)
    except PermissionError as perr:
        if savetomysql.get("optional"):
            logger.warning(str(perr))
        else:
            logger.error(str(perr))
            exit(rtn.EX_NOPERM)
    except ConnectionRefusedError as crerr:
        if savetomysql.get("optional"):
            logger.warning(str(crerr))
        else:
            logger.error(str(crerr))
            exit(rtn.EX_NOHOST)
    except KeyError:
        logger.error("Some values in config file are missing! Make sure you've set host, port (optional, by default 3306), user, password and database!")
        exit(rtn.EX_CONFIG)
    except RuntimeError as rerr:
        logger.error(f"Internal MySQL error: {rerr}")
        exit(rtn.EX_SOFTWARE)
    except Exception as e:
        logger.debug(f"Program error: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Start main loop
    logger.info("Started listening")
    while running:
        # Get tick start time
        stime = time()
        # Try to load code and winner info
        code = chat.get_code(n=linestoread)
        # If code has appeared...
        if code:
            # Process, copy and display info about it
            codets = datetime.now(timezone.utc).astimezone()
            addtots = config.suggest_timeout
            if addtots:
                sendin = codets + timedelta(0,addtots)
                sendtxt = f"Code {code} was found! Send it at: {sendin.hour:02}:{sendin.minute:02}:{sendin.second:02}"
            else:
                sendtxt = f"Code {code} was found!"
            logger.info(sendtxt)
            if copysetting:
                codecopy.copy(code)
            if sendnf:
                notifications.send_notification("Code appeared",sendtxt)
        else:
            winner = chat.get_winner(n=linestoread)
            if winner:
                # Process and save winner info
                logger.info(winner.to_msg())
                if savetocsv:
                    csvf.append_code_info(winner)
                if savetomysql:
                    try:
                        mysqlf.append_code_info(winner)
                    except RuntimeError as e:
                        logger.warning(f"Code info wasn't saved to MySQL. MySQL error: {e}")
                    except Exception as e:
                        logger.debug(f"Program error: {e}")
                        logger.critical("Internal app error!")
                        exit(rtn.EX_SOFTWARE)
                if config.predict_next_code:
                    prediction=chat.predict_next_code()
                    if prediction:
                        prediction_dt=datetime.now()+timedelta(seconds=prediction)
                        logger.info(f"Next code appear time prediction: {prediction_dt.hour:02}:{prediction_dt.minute:02}:{prediction_dt.second:02}")
        # Sleep loop
        timetosleep = (sleepms/1000)-(time()-stime)
        if timetosleep > 0:
            sleep(timetosleep)
    # This part will be executed after loop ends
    logger.info("### STATISTICS ###")
    stats = chat.get_stats()
    total_runtime = datetime.now()-start_time
    logger.info(f"Total runtime: {total_runtime}")
    logger.info(f"Total codes captured: {stats.get("total_codes")}")
    logger.info(f"Codes re-writed by me: {stats.get("my_codes")}")
    logger.info(f"Keys received by me: {stats.get("my_keys")}")
    logger.info(f"My wins percentage: {stats.get("my_wins_percentage")}%")
    logger.info("Program finished job")
if __name__=="__main__":
    main()