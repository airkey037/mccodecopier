# Anarchia.GG Code Copier (Loader)
# Maintainer: AirKeyooo <airkeyooo@gmail.com>
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