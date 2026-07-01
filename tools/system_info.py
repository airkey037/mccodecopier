# A part of MC Code Copier Reloaded
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
# File contains system_info function that returns dict with all possible system informations
def system_info():
    import sys
    import platform
    import os
    from json import dumps
    from pathlib import Path
    from locale import getlocale, getpreferredencoding
    from datetime import datetime, UTC
    from time import tzname
    VERSION_INFO={"Version":sys.version,"Version info":sys.version_info,"Implementation":platform.python_implementation(),"Compiler":platform.python_compiler(),"Build":platform.python_build(),"Executable":sys.executable,"Prefix":sys.prefix,"Base prefix":sys.base_prefix,"Platform":sys.platform,"Byte order":sys.byteorder,"Filesystem encoding":sys.getfilesystemencoding(),"Default encoding":sys.getdefaultencoding(),"Recursion limit":sys.getrecursionlimit(),"Command line":sys.argv,"System":platform.system(),"Release":platform.release(),"Version":platform.version(),"Machine":platform.machine(),"Processor":platform.processor(),"Architecture":platform.architecture(),"Hostname":platform.node(),"Platform":platform.platform(),"CPU count":os.cpu_count(),"Current working directory":os.getcwd(),"Script":Path(__file__).resolve(),"Home":Path.home(),"Temp":os.getenv("TMPDIR")or os.getenv("TEMP"),"Locales":getlocale(),"Preferred encoding":getpreferredencoding(False),"Local time":datetime.now().astimezone(),"UTC time":datetime.now(tz=UTC),"Timezone":tzname,"Flags":sys.flags,"Float info":sys.float_info,"Int info":sys.int_info,"Hash info":sys.hash_info,"Thread info":sys.thread_info,"Environment variables (in JSON)":dumps(dict(sorted(os.environ.items())))}
    return VERSION_INFO