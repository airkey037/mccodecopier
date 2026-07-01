# MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# Import all needed libraries
from argparse import ArgumentParser
import logging
from sys import stdout, exit
from signal import signal, SIGTERM, SIGINT, Signals
from time import sleep, time
from datetime import datetime, timedelta, timezone
import os
import ctypes
# Import all program parts
from tools import *
from minecraft import *
from codehooks import *
from winnerhooks import *
from config import Config
from printing import Printing
# Function to check program privileges
def is_root():
    if hasattr(os,"getuid"):
        return os.getuid()==0
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False
# Function to get program version
def get_version():
    from subprocess import check_output as subcheckout, CalledProcessError, DEVNULL as subdevnull
    try:
        version=subcheckout(["git","describe","--tags","--always"],stderr=subdevnull).decode("utf-8").strip()
        commit_hash=subcheckout(["git","rev-parse","HEAD"],stderr=subdevnull).decode("utf-8").strip()
        return version, commit_hash
    except (CalledProcessError,FileNotFoundError):
        pass
    try:
        from version import __version__, COMMIT_HASH
        return __version__, COMMIT_HASH
    except ImportError:
        pass
    return "v0.0.0-unknown", "UNKNOWN"
# Match log level names with log levels
LOGLVLS={"quiet":logging.CRITICAL+1,"critical":logging.CRITICAL,"error":logging.ERROR,"warning":logging.WARNING,"info":logging.INFO,"verbose":logging.INFO,"debug":logging.DEBUG}
# Main function contains all code that should be executed when this program is NOT IMPORTED
def main(args):
    # Define function-level logger
    logger=logging.getLogger(f"{__name__}.{main.__name__}")
    # Save start time
    start_time = datetime.now()
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
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Initalize Printing class
    try:
        logger.debug("Trying to initalize printing class")
        printcl=Printing(args.print_format)
        logger.debug("Initalized successfully")
    except TypeError as e:
        logger.error(e)
        exit(rtn.EX_DATAERR)
    except KeyError as e:
        logger.error(e.args[0])
        exit(rtn.EX_USAGE)
    except Exception as e:
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
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
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
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
    try:
        from signal import SIGHUP
        signal(SIGHUP,stop)
    except ImportError:
        pass
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
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
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
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
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
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Initalize MySQL class
    savetomysql = config.mysql
    try:
        if savetomysql:
            logger.debug("Trying to initalize MySQL class")
            mysqlf = MySQL(hostname=savetomysql.get("host","localhost"),port=savetomysql.get("port",3306),user=savetomysql["user"],password=savetomysql["password"],database=savetomysql["database"],)
            logger.debug("Initalized successfully!")
    except ImportError as e:
        logger.error(e)
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
        logger.error("Some values in config file are missing! Make sure you've set host (by default localhost), port (optional, by default 3306), user, password and database!")
        exit(rtn.EX_CONFIG)
    except RuntimeError as rerr:
        logger.error(f"Internal MySQL error: {rerr}")
        exit(rtn.EX_SOFTWARE)
    except Exception as e:
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
        logger.critical("Internal app error!")
        exit(rtn.EX_SOFTWARE)
    # Start main loop
    logger.info("Started listening")
    while running:
        # Get tick start time
        stime = time()
        # Try to load code and winner info
        messages = chat.read_messages(n=config.read_lines)
        code = chat.get_code(messages)
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
            winner = chat.get_winner(messages)
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
                        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
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
    stats["total_runtime"]=total_runtime.total_seconds()
    print_additional_info=False
    if args.show_statistics:
        try:
            logger.debug("User asked to show statistics, adding")
            printcl.add_element("statistics",stats)
            logger.debug("Added successfully")
            print_additional_info=True
        except FileExistsError as e:
            logger.error(e)
            exit(rtn.EX_CANTCREAT)
        except TypeError as e:
            logger.error(e)
            exit(rtn.EX_USAGE)
    if print_additional_info:
        logger.debug("Printing")
        output=printcl.parse()
        if args.report:
            file_handler.writeline("PRINT BEGINNING\n"+output+"\nPRINT ENDING")
        print(output,file=stdout)
    logger.info("Program finished job")
# Run whole program if this code is not imported
if __name__=="__main__":
    # Get version
    __version__,COMMIT_HASH=get_version()
    # Initalize argument parser
    parser = ArgumentParser(description="MC Code Copier is listening for reward codes (In Anarchia.GG's OneBlock) in the chat, copies it to clipboard and stores it")
    parser.add_argument("-loglevel","-v",choices=LOGLVLS.keys(),default="info",help="Logging level")
    parser.add_argument("-report",action="store_true",help="Create log file with all debugging informations")
    parser.add_argument("-version",action="store_true",help="Display current program version")
    parser.add_argument("-config",type=str,default="config.yml",help="Path to configuration file")
    parser.add_argument("-default_config",action="store_true",help="After specifying this flag, program will create default configuration file in pointed path")
    parser.add_argument("-runasroot",action="store_true",help="Make possible for program to run as root")
    parser.add_argument("-print_format","-output_format","-of",help="Choose output printing format",default="default",choices=("default","flat","ini","json","xml"),type=str)
    parser.add_argument("-show_statistics",action="store_true",help="Print statistics using format specified in -print_format option")
    args = parser.parse_args()
    if args.version:
        print(__version__)
        exit(rtn.EX_OK)
    # Define root logger with lowest possible level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # Add primary program logger with __name__
    logger = logging.getLogger(__name__)
    # Find used level's number
    used_loglevel = LOGLVLS.get(args.loglevel,logging.INFO)
    # Define some formatters
    advanced_formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
    basic_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    # If -report flag was given, open FileHandler
    if args.report:
        from tools import ReportFileHandler, system_info
        # Define file handler
        file_handler = ReportFileHandler(filename=datetime.now().astimezone().strftime("codecopier-%Y%m%d-%H%M%S.log"),mode="w",encoding="utf-8")
        file_handler.setFormatter(advanced_formatter)
        file_handler.setLevel(logging.DEBUG)
        # Add file handler to root logger
        root_logger.addHandler(file_handler)
        # Add system informations to log file
        information = system_info()
        file_handler.writeline(f"MC Code Copier Reloaded\nProgram version: {__version__}\nLast commit hash: {COMMIT_HASH}\nCommand line: {os.getenv("_","python3")} {" ".join(information["Command line"])}\nSystem information:")
        for k, v in information.items():
            if isinstance(v,dict):
                file_handler.writeline(f"+ {k}:")
                for key, value in v.items():
                    file_handler.writeline(f"|   {key} -> {value}")
            elif type(v)is list or type(v) is tuple:
                file_handler.writeline(f"+ {k}:")
                for element in v:
                    file_handler.writeline(f"|   {element}")
            else:
                file_handler.writeline(f"+ {k} -> {v}")
        file_handler.writeline("Arguments:")
        for arg in dir(args):
            if not arg.startswith("_"):
                file_handler.writeline(f"+ {arg} -> {getattr(args,arg)}")
    # Add console handler using StreamSplitHandler from tools/split_log_stream.py
    console_handler = StreamSplitHandler()
    console_handler.setLevel(used_loglevel)
    console_handler.setFormatter(advanced_formatter if used_loglevel == logging.DEBUG else basic_formatter)
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    # Show init message and version
    logger.info("Anarchia.GG Code Copier started")
    logger.info(f"Version: {__version__}")
    # Check program privileges
    logger.debug("Checking program privileges")
    amirooted=is_root()
    if amirooted:
        if args.runasroot:
            logger.critical("Program is running as root/admin! It is VERY UNSAFE to run this program with those privileges, because program doesn't need it.")
        else:
            logger.critical("Program is running as root/admin! It is VERY UNSAFE to run this program with those privileges, because program doesn't need it. Run it as a normal user! But if you really want to continue (VERY UNRECOMMENDED), add -runasroot flag (but keep in mind that you are doing it for YOUR OWN RESPONSIBILITY!!)")
            exit(rtn.EX_ERROR)
    else:
        logger.debug("Program is not running as root/admin, continuing safely")
    try:
        returncode = 0
        logger.debug("Starting function main()")
        main(args=args)
        logger.debug("Function main() finished")
    except SystemExit as e:
        returncode = e.code
        if returncode is None:
            returncode = 0
        elif isinstance(returncode,str):
            if args.report:
                file_handler.writeline(f"Program ended with message: {returncode}")
            returncode = 1
    except Exception as e:
        logger.debug(f"Program error: {e.__class__.__name__}: {e}")
        logger.critical("Internal app error!")
        returncode = 70
    finally:
        if args.report:
            file_handler.writeline(f"Return code: {returncode}")
        exit(returncode)