# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains CSV class that saves winner info to CSV
# Import needed modules
import logging
from pathlib import Path
from csv import DictReader, DictWriter, writer
# Class to create and use .csv files
class CSV:
    def __init__(self,file:str):
        # Create logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # If file is set to None, we will not make any changes
        self.field_names=["Code","Nick","Time","Timestamp","Me"]
        if file:
            self.file = Path(file)
            self.logger.debug(f"Given file path: {self.file.resolve()}")
            self.logger.debug("Checking does path exists")
            if self.file.exists():
                self.logger.debug("Path exists, checking is it file")
                if self.file.is_file():
                    try:
                        with open(file=self.file.resolve(),mode="r",encoding="utf-8") as f:
                            self.logger.debug("Opened CSV file")
                            reader=DictReader(f)
                            self.logger.debug(f"Loaded field names: {", ".join(reader.fieldnames)}")
                            self.logger.debug(f"Expected field names: {", ".join(self.field_names)}")
                            if reader.fieldnames != self.field_names:
                                self.logger.warning("File that you specified have different header names than expected!")
                    except PermissionError:
                        raise PermissionError(f"Can't open {self.file.resolve()}: Permission Denied")
                else:
                    raise IsADirectoryError(f"Can't open {self.file.resolve()} - this path points to a directory!")
            else:
                # Create new file
                self.logger.debug("File doesn't exists, creating a blank one")
                try:
                    with open(file=self.file.resolve(),mode="w",newline="",encoding="utf-8") as f:
                        self.logger.debug("File opened")
                        writer=DictWriter(f,fieldnames=self.field_names)
                        writer.writeheader()
                        self.logger.debug("File saved successfully")
                except PermissionError:
                    raise PermissionError(f"Can't create {self.file.resolve()}: Permission Denied")
        else:
            self.logger.debug(f"File path wasn't given, skipping")
    def append_code_info(self,codeobj):
        if self.file:
            self.logger.debug("Loading code info to append...")
            toappend = codeobj.to_csv()
            self.logger.debug(f"Loaded values: {toappend}")
            with open(self.file,mode="a",newline="",encoding="utf-8") as f:
                self.logger.debug("File was opened")
                wrt=writer(f)
                wrt.writerow(toappend)
                self.logger.debug("Successfully writed all needed data")