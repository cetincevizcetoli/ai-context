import platform
import shutil
import subprocess
from typing import Optional


def copy_to_clipboard(text: str) -> bool:
    try:
        system = platform.system()
        if system == "Windows":
            process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=False)
            process.communicate(input=text.encode("utf-16"))
            return process.returncode == 0
        if system == "Darwin":
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(input=text.encode("utf-8"))
            return process.returncode == 0

        commands = (
            ("wl-copy", ["wl-copy"]),
            ("xclip", ["xclip", "-selection", "clipboard"]),
            ("xsel", ["xsel", "-ib"]),
        )
        for executable, command in commands:
            if shutil.which(executable):
                process = subprocess.Popen(command, stdin=subprocess.PIPE)
                process.communicate(input=text.encode("utf-8"))
                return process.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
    return False
