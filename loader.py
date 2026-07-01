# Anarchia.GG Code Copier (Loader)
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# Import all needed libraries
from argparse import ArgumentParser
import logging
from sys import stdout, exit
from signal import signal, SIGTERM, SIGINT, Signals
from time import sleep, time
from datetime import datetime, timedelta, timezone
from subprocess import check_output as subcheckout, CalledProcessError, DEVNULL as subdevnull
from platform import system
import os
import ctypes
from json import dumps
# Import all program parts
from tools import *
from minecraft import *
from codehooks import *
from winnerhooks import *
from config import Config
# Function to check program privileges
def is_root():
    if hasattr(os,"getuid"):
        return os.getuid()==0
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False
# Function to escape " and ' in strings
def escape_flat(s:str)->str:return(str(s).replace("\\","\\\\").replace('"','\\"').replace("'","\\'"))
# Function to get program version
def get_version():
    try:
        version=subcheckout(["git","describe","--tags","--always"],stderr=subdevnull).decode("utf-8").strip()
        return version
    except (CalledProcessError,FileNotFoundError):
        pass
    try:
        from version import __version__
        return __version__
    except ImportError:
        pass
    return "v0.0.0-unknown"
# Class to manage print format and additional printed info
class Printing:
    def parser_default(self)->str:
        self.logger.debug("Parsing mode: default")
        def default_pf(tree,prefix:str="",use_brackets=True)->tuple:
            pfx=f"{prefix}:"if prefix else""
            output=[]
            rv=tree
            if isinstance(tree,(list,tuple)):
                rv=dict(enumerate(tree))
            if isinstance(rv,dict):
                for key,value in rv.items():
                    usebrk=use_brackets and isinstance(value,(list,dict,tuple))
                    if usebrk:
                        output.append(f"[{str(key).upper()}]")
                    output.extend(default_pf(value,prefix=f"{pfx}{key}",use_brackets=False))
                    if usebrk:
                        output.append(f"[/{str(key).upper()}]")
            else:
                output.append(f"{prefix}={rv}")
            return tuple(output)
        return "\n".join(default_pf(self.tree))
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
    def parse(self):
        self.logger.debug("Parsing all elements using specified parser")
        self.logger.debug(f"Using parser: {self.using_parser.__name__}")
        return self.using_parser()
# Match log level names with log levels
LOGLVLS={"quiet":logging.CRITICAL+1,"critical":logging.CRITICAL,"error":logging.ERROR,"warning":logging.WARNING,"info":logging.INFO,"verbose":logging.INFO,"debug":logging.DEBUG}
# Main function contains all code that should be executed when this program is NOT IMPORTED
def main():
    # Save start time
    start_time = datetime.now()
    # Get version
    __version__=get_version()
    # Initalize argument parser
    parser = ArgumentParser(description="MC Code Copier is listening for reward codes (In Anarchia.GG's OneBlock) in the chat, copies it to clipboard and stores it")
    parser.add_argument("-loglevel","-v",choices=LOGLVLS.keys(),default="info",help="Logging level")
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
    logger.info(f"Version: {__version__}")
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
        print(output,file=stdout)
    logger.info("Program finished job")
if __name__=="__main__":
    main()