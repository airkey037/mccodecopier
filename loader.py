# Anarchia.GG Code Copier (Loader)
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# Import all needed libraries
from argparse import ArgumentParser
import logging
from sys import stdout
import os
# Function to read n last lines without loading whole log file
def read_last_messages(path, n=1):
    if n <= 0:
        return ()
    lines = []
    with open(path, "rb") as f:
        f.seek(0, 2)
        filesize = f.tell()
        if filesize == 0:
            return ()
        pos = filesize - 1
        f.seek(pos)
        while pos >= 0 and f.read(1) == b'\n':
            pos -= 1
            f.seek(pos)
        buffer = bytearray()
        while pos >= 0 and len(lines) < n:
            f.seek(pos)
            byte = f.read(1)
            if byte == b'\n':
                lines.append(buffer[::-1].decode(errors="replace"))
                buffer.clear()
            else:
                buffer.append(byte[0])
            pos -= 1
        if buffer and len(lines) < n:
            lines.append(buffer[::-1].decode(errors="replace"))
    return tuple(reversed(lines))
# Match log level names with log levels
LOGLVLS={"quiet":logging.CRITICAL+1,"critical":logging.CRITICAL,"error":logging.ERROR,"warning":logging.WARNING,"info":logging.INFO,"verbose":logging.INFO,"debug":logging.DEBUG}
# Initalize argument parser
parser = ArgumentParser(description="Anarchia.GG Code Copier is listening for reward codes in the chat and copies it to clipboard")
parser.add_argument("-loglevel","-v",choices=LOGLVLS.keys(),default="info",help="Logging level")
args = parser.parse_args()
# Initalize logger
logging.basicConfig(level=LOGLVLS[args.loglevel],stream=stdout,format="[%(asctime)s] [%(levelname)s] %(message)s")
logging.info("Anarchia.GG Code Copier started")