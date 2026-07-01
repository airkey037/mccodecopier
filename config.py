# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains Config class that takes care about whole configuration
# Import needed modules
from pathlib import Path
from datetime import datetime
from tools import rtn
from platform import system
from sys import stderr
import logging
import os
try:
    from yaml import safe_load, YAMLError
except ImportError:
    print("pyyaml lib isn't installed! Install it using: pip install pyyaml",file=stderr)
    exit(rtn.EX_UNAVAILABLE)
# Class to manage configuration
class Config:
    def defaultconf(self,path:str):
        fullpath = Path(path)
        self.logger.debug(f"Trying to create new config file in {fullpath.resolve()}")
        if fullpath.exists():
            self.logger.error("Config file already exists!")
            exit(rtn.EX_CANTCREAT)
        DEFAULT_CONFIG_FILE=f'''# MC Code Copier default config file\n# Program maintainer: AirKeyooo <airkeyooo@gmail.com>\n# Generated: {datetime.now().astimezone().strftime("%d.%m.%Y %H:%M:%S %Z")}\n\n# Add path to your latest.log file\nlog_file: /path/to/latest.log\n\n# How many lines program should read. More lines = improved efficiency, but higher CPU and disk usage\nread_lines: 2\n\n# Should program send notifications about new codes?\n# WARNING: Works only on Linux and ends with error on any other OS!\nsend_notifications: false\n\n# Suggest when user should send code to don't look suspicious\n# Give value in seconds. If you don't want to use this function, comment it or set value to 0\nsuggest_timeout: 5\n\n# Change shuold program predict when next code will appear.\n# Program currently needs at least 2 codes in memory to predict next one\npredict_next_code: false\n\n# Should program automatically copy received code to the clipboard?\n# WARNING: Requires pyperclip module, which can be installed using: `pip install pyperclip`\ncopy_to_clipboard: false\n\n# Save results to .csv file\n# If you don't want to use this function, comment line below\nsave_to_csv: /path/to/file.csv\n\n# Set all nicknames that are yours\n# If you don't want to set your nicknames, comment/remove whole section below\nnicknames:\n  - Nickname1\n  - Nickname2\n\n# How frequently (in ms) chat should be scanned.\n# e.g. 200 -> messages will be scanned every 200ms\n# Smaller delay may improve efficiency, but will end up with higher CPU and disk usage\nscan_frequency: 300\n\n# MySQL DB Access config\n# If you want to use MySQL, uncomment all lines below and type your credentials\n# When optional is set to false, program will finish with an error when MySQL/MariaDB server is unreachable. When it is set to true, program will only warn that it can't save data to MySQL/MariaDB, but continue its work\n# If the user doesn't have password (VERY UNSAFE!), leave password field blank (nothing after ':')\n# Minimal required user permissions: CREATE, INSERT\n# WARNING: Requires mysql.connector module, which can be installed using: `pip install mysql-connector-python`\n#mysql:\n#  host: localhost\n#  port: 3306\n#  user: root\n#  password: \n#  database: my_database\n#  optional: false'''
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