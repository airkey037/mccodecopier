# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains CodeCopy class that copies codes to clipboard
# Import needed modules
import logging
from platform import system
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
            raise RuntimeError("Something went wrong and you can't copy anything to the clipboard! See -loglevel debug for more info"+". You are on Linux, so you can check is your copying backend (like wl-copy, xclip, xselect) installed"if system()=="Linux"else"")
    def copy(self,code:str):
        from pyperclip import copy
        self.logger.debug(f"Copying {code}")
        copy(code)