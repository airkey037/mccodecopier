# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains Code class that stores and parses information about received codes
# Import needed modules
from datetime import datetime, timedelta
import logging
# Code class to store and manage code and winner info
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