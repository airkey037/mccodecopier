# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# __init__ file for tools/ directory
# Import all parts
from .return_codes import ReturnCodes
from .dict_operations import flatten_dict, flatten_values
from .tail import tail
# Define rtn object
rtn = ReturnCodes()
# Define all imported parts
__all__ = ["rtn","flatten_dict","flatten_values","tail"]