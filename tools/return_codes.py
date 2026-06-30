# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains ReturnCodes class that holds all return codes
# Class to manage return codes (codes were taken from os.EX_* variables)
class ReturnCodes:
    def __init__(self):
        self.EX_OK=0
        self.EX_ERROR=1
        self.EX_USAGE=64
        self.EX_DATAERR=65
        self.EX_NOINPUT=66
        self.EX_NOUSER=67
        self.EX_NOHOST=68
        self.EX_UNAVAILABLE=69
        self.EX_SOFTWARE=70
        self.EX_OSERR=71
        self.EX_OSFILE=72
        self.EX_CANTCREAT=73
        self.EX_IOERR=74
        self.EX_TEMPFAIL=75
        self.EX_PROTOCOL=76
        self.EX_NOPERM=77
        self.EX_CONFIG=78