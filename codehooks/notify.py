# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains Notify class that sends notifications about new codes
# Import needed modules
import logging
from subprocess import run as subrun
from platform import system
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