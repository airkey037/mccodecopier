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
            self.timestamp = timestamp.isoformat(timespec="seconds")
        else:
            self.timestamp = None
        self.player = player
        self.time = time
        self.isitme = player in nicknames
    def __eq__(self,other):
        return self.code == other.code and self.timestamp == other.timestamp and self.player == other.player and self.time == other.time and self.isitme == other.isitme
    def to_csv(self):
        return [self.code,self.player,self.time,self.timestamp,self.isitme]
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
# Class to send notifications
class Notify:
    def __init__(self,send):
        # Throws ImportError when lib is not installed and "send" parameter is set to True
        if send:
            from plyer import notification
        self.send = send
    def send_notification(self,title,msg):
        # Send notification
        if self.send:
            from plyer import notification
            notification.notify(app_name="MC Code Copier",timeout=5,title=title,message=msg)
# Class to copy code to the clipboard
class CodeCopy:
    def __init__(self,copy):
        # This part throws ImportError when library is not installed but "copy" parameter is set to True
        if copy:
            from pyperclip import copy as pypercopy, PyperclipException
            try:
                pypercopy("Hello World from MC Code Copier! :)")
            except PyperclipException as e:
                raise RuntimeError(str(e)) from None
        self.copysw = copy
    def copy(self,code):
        if self.copysw:
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
# Match log level names with log levels
LOGLVLS={"quiet":logging.CRITICAL+1,"critical":logging.CRITICAL,"error":logging.ERROR,"warning":logging.WARNING,"info":logging.INFO,"verbose":logging.INFO,"debug":logging.DEBUG}
# Main function contains all code that should be executed when this program is NOT IMPORTED
def main():
    # Initalize argument parser
    parser = ArgumentParser(description="Anarchia.GG Code Copier is listening for reward codes in the chat and copies it to clipboard")
    parser.add_argument("-loglevel","-v",choices=LOGLVLS.keys(),default="info",help="Logging level")
    parser.add_argument("-config",type=str,default="config.yml",help="Path to configuration file")
    args = parser.parse_args()
    # Initalize logger
    logging.basicConfig(level=LOGLVLS[args.loglevel],stream=stdout,format="[%(asctime)s] [%(levelname)s] %(message)s")
    logging.info("Anarchia.GG Code Copier started")
    # Read configuration file
    logging.debug("Trying to load config file")
    config_file = Path(args.config)
    logging.debug(f"Path to config file: {config_file.absolute()}")
    try:
        # Try to load config file
        with open(config_file.absolute(),encoding="utf-8") as f:
            config = safe_load(f)
            logging.debug("Configuration has been loaded successfully")
    except FileNotFoundError:
        logging.error("Config file doesn't exist!")
        exit(os.EX_NOINPUT)
    except PermissionError:
        logging.error(f"Can't open {config_file}: Permission Denied")
        exit(os.EX_NOPERM)
    except YAMLError:
        logging.error(f"Invalid YAML syntax")
        exit(os.EX_CONFIG)
    except Exception as e:
        logging.debug(f"Program error: {e}")
        logging.critical("Internal app error")
        exit(os.EX_SOFTWARE)
    # Create an object to manage chat reading
    try:
        logging.debug("Trying to create AnarchiaGG object")
        nicks = config.get("nicknames")
        chat = AnarchiaGG(mc_log_file=config["log_file"],nicknames=nicks)
        logging.debug("Object was created successfully")
        logging.debug(f"Log file path: {Path(config["log_file"]).absolute()}")
        if not nicks:
            logging.warning("Nick list is empty")
        else:
            logging.debug(f"Nicks marked as mine: {", ".join(nicks)}")
    except KeyError:
        logging.error("Can't read log file path from config file!")
        exit(os.EX_CONFIG)
    except FileNotFoundError as e:
        # AnarchiaGG class throws FileNotFoundError and PermissionError with already prepared message, so we can only catch it and exit with specific code
        logging.error(str(e))
        exit(os.EX_NOINPUT)
    except PermissionError as e:
        logging.error(str(e))
        exit(os.EX_NOPERM)
    except Exception as e:
        logging.debug(f"Program error: {e}")
        logging.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Define some variables
    running = True
    # Function will run when SIGINT or SIGTERM is received to safely stop program
    def stop(signum, frame):
        logging.info(f"Received {Signals(signum).name}, QUITTING!")
        nonlocal running
        running = False
    signal(SIGINT,stop)
    signal(SIGTERM,stop)
    # Read from config file how many lines should we read backwards
    linestoread = config.get("read_lines")
    if not linestoread:
        logging.error("Amount of lines to check isn't specified in config file!")
        exit(os.EX_CONFIG)
    else:
        logging.debug(f"Last lines to read: {linestoread}")
    # Read from config file how frequently should we scan the chat
    sleepms = config.get("scan_frequency")
    if not sleepms:
        logging.error("Scan frequency isn't specified in config file!")
        exit(os.EX_CONFIG)
    else:
        logging.debug(f"Sleep time: {sleepms}")
    # Initalize notification class
    sendnf = config.get("send_notifications")
    try:
        logging.debug("Trying to initalize Notify class")
        if not sendnf:
            logging.debug("NOTE: Notification sending is disabled, so program is only initalizing class, not importing lib!")
        notifications = Notify(sendnf)
        logging.debug("Initalized successfully!")
    except ImportError:
        logging.critical("Can't send notifications because plyer lib isn't installed! Disable notifications in config or run: pip install plyer")
        exit(os.EX_UNAVAILABLE)
    except Exception as e:
        logging.debug(f"Program error: {e}")
        logging.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Initalize CodeCopy class
    copysetting = config.get("copy_to_clipboard")
    try:
        logging.debug("Trying to initalize CodeCopy class")
        if not copysetting:
            logging.debug("NOTE: Copying code to clipboard sending is disabled, so program is only initalizing class, not importing lib!")
        codecopy = CodeCopy(copysetting)
        logging.debug("Initalized successfully!")
    except ImportError:
        logging.critical("Can't copy to clipboard because pyperclip lib is not installed! Disable copy_to_clipboard in config file or run: pip install pyperclip")
        exit(os.EX_UNAVAILABLE)
    except RuntimeError as e:
        logging.debug(f"Original error message: {e}")
        logging.critical("Can't copy anything to clipboard because copying backend is not installed! See -loglevel debug for more details")
        exit(os.EX_UNAVAILABLE)
    except Exception as e:
        logging.debug(f"Program error: {e}")
        logging.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Initalize CSV class
    savetocsv = config.get("save_to_csv")
    try:
        logging.debug("Trying to initalize CSV class")
        if not savetocsv:
            logging.debug("NOTE: CSV report saving is disabled, so program is only initalizing class, not importing lib!")
        csvf = CSV(savetocsv)
        logging.debug("Initalized successfully!")
    except PermissionError as e:
        logging.error(str(e))
        exit(os.EX_NOPERM)
    except ValueError as e:
        logging.warning(str(e))
    except Exception as e:
        logging.debug(f"Program error: {e}")
        logging.critical("Internal app error!")
        exit(os.EX_SOFTWARE)
    # Start main loop
    logging.info("Started listening")
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
            codecopy.copy(code)
            logging.info(sendtxt)
            notifications.send_notification("Code appeared",sendtxt)
        # If winer info has appeared...
        if winner:
            # Process and save it
            logging.info(winner.to_msg())
            csvf.append_code_info(winner)
        # Sleep loop
        timetosleep = (sleepms/1000)-(time()-stime)
        if timetosleep > 0:
            sleep(timetosleep)
    # This part will be executed after loop ends
    logging.info("Program finished job")
if __name__=="__main__":
    main()