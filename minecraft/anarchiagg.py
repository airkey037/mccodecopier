# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains AnarchiaGG class that manages... Almost every parsing and logic in this program!
# Import needed modules
from datetime import datetime, timedelta
import logging
import re
# Import required elements
from ._code import Code
from ._mc_log_integrate import Minecraft
# Define AnarchiaGG class
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
    def read_messages(self,n=1)->tuple:
        lastlines=self.read_raw_messages(n=n)
        lines=[]
        for line in reversed(lastlines):
            lines.append(line)
            if re.search(r"Przepisz kod [a-z,A-Z,1-9]{10} aby otrzymać nagrodę!",line.strip()):
                break
        return tuple(reversed(lines))
    def get_code(self,messages:tuple)->str:
        # Search for code to copy
        codesearch = re.search(r"Przepisz kod ([a-z,A-Z,1-9]{10}) aby otrzymać nagrodę!","\n".join(messages))
        if codesearch:
            code = codesearch.group(1)
            if code not in self.codes:
                self.logger.debug(f"Found unknown code: {code}")
                self.codes.append(code)
                self.last_code = code
                self.last_code_ts = datetime.now().astimezone()
                self.logger.debug(f"Last code variable is set to {self.last_code}")
                self.logger.debug(f"Last code timestamp variable is set to {self.last_code_ts}")
                return code
        return None
    def get_winner(self,messages:tuple):
        # If code wasn't captured, exit immediately
        if not self.last_code and not self.last_code_ts:
            return None
        # Search for winner info to save it
        winnersearch = re.search(r"Gracz (.+) jako pierwszy przepisał kod w czasie (\d.\d{2})s i otrzymał\(a\) 3 Klucze AFK!","\n".join(messages))
        if winnersearch:
            player = winnersearch.group(1)
            time = float(winnersearch.group(2))
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
        if len(self.wins) < 1:
            return None
        self.logger.debug("Predicting next code appear time")
        last_code=self.wins[-1].tsobj
        self.logger.debug(f"Date from last code: {last_code}")
        predicted_time=last_code+timedelta(minutes=30)
        self.logger.debug(f"Predicted time to next code: {predicted_time}")
        return predicted_time.total_seconds()
    def get_stats(self)->dict:
        self.logger.debug("Calculating all statistics...")
        try:
            my_wins_percentage = round(self.my_wins/len(self.codes)*100,2)
        except ZeroDivisionError:
            my_wins_percentage = 0
        return {"total_codes":len(self.codes),"total_keys":len(self.codes)*3,"my_codes":self.my_wins,"my_keys":self.my_wins*3,"my_wins_percentage":my_wins_percentage}