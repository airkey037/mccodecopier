# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains AnarchiaGG class that manages... Almost every parsing and logic in this program!
# Import needed modules
from datetime import datetime
import logging
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
    def read_messages_after_code(self,n=1)->tuple:
        lastlines=self.read_raw_messages(n=n)
        lines=[]
        for line in reversed(lastlines):
            lines.append(line)
            if "Przepisz kod " in line and " aby otrzymać nagrodę!" in line:
                break
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