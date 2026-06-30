# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains Minecraft class that can read some information from Minecraft through latest.log file
# Import needed modules
from pathlib import Path
# Import needed tools
from tools import tail
# Class to parse info from latest.log file
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