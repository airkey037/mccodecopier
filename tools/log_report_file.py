# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains ReportFileHandler class to manage log file
# Import all needed libs
import logging
# Define ReportFileHandler class
class ReportFileHandler(logging.FileHandler):
    def writeline(self,msg):
        # Acquire file to lock other threads from writing to this file
        self.acquire()
        try:
            # If file is closed...
            if self.stream is None:
                # ...open it
                self.stream=self._open()
            # Write message
            self.stream.write(msg+self.terminator)
            # Flush changes
            self.flush()
        finally:
            # Release file
            self.release()