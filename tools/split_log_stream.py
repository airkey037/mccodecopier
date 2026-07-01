# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains StreamSplitHandler class that will split log levels to stdout and stderr in logging lib
# Import all needed libs
from sys import stdout, stderr
import logging
# Define StreamSplitHandler class
class StreamSplitHandler(logging.StreamHandler):
    def emit(self,record):
        try:
            msg=self.format(record)
            if record.levelno >= logging.WARNING:
                stream = stderr
            else:
                stream = stdout
            stream.write(msg+self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)