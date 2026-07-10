import os
import shutil
import subprocess
from typing import List, Optional, Set

from .utils import normalize_rel_path


def git_executable() -> Optional[str]:
    return shutil.which("git")


def is_git_repo(root_path: str) -> bool:
    git = git_executable()
    if not git:
        return False
    try:
        result = subprocess.run(
            [git, "-C", root_path, "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def list_git_visible_files(root_path: str) -> List[str]:
    git = git_executable()
    if not git:
        raise RuntimeError("Git bulunamadı.")
    result = subprocess.run(
        [git, "-C", root_path, "ls-files", "-co", "--exclude-standard", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or "git ls-files başarısız oldu.")
    return [normalize_rel_path(item.decode("utf-8", errors="surrogateescape")) for item in result.stdout.split(b"\0") if item]


def changed_git_files(root_path: str) -> Set[str]:
    git = git_executable()
    if not git:
        raise RuntimeError("Git bulunamadı.")
    result = subprocess.run(
        [git, "-C", root_path, "status", "--porcelain", "-z", "--untracked-files=all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or "git status başarısız oldu.")

    changed: Set[str] = set()
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    index = 0
    while index < len(entries):
        entry = entries[index].decode("utf-8", errors="surrogateescape")
        if len(entry) < 4:
            index += 1
            continue
        status = entry[:2]
        path = entry[3:]
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            changed.add(normalize_rel_path(path))
            index += 1
            if index < len(entries):
                changed.add(normalize_rel_path(entries[index].decode("utf-8", errors="surrogateescape")))
        else:
            changed.add(normalize_rel_path(path))
        index += 1
    return changed
