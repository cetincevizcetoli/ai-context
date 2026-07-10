import os
import re
from typing import Iterable, Iterator, List, Sequence, Set


_RANGE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)$")


def normalize_rel_path(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value.strip("/")


def normalize_extension(value: str) -> str:
    value = value.strip().lower()
    if not value:
        return ""
    return value if value.startswith(".") else "." + value


def extension_for_name(name: str) -> str:
    lower = name.lower()
    if lower.startswith(".env."):
        return ".env.example" if lower.endswith("example") else ".env"
    if name in {"Dockerfile", "Containerfile"}:
        return ".dockerfile"
    if name in {"Makefile", "GNUmakefile"}:
        return ".makefile"
    return os.path.splitext(name)[1].lower()


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def human_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def parse_number_selection(text: str, maximum: int) -> Set[int]:
    result: Set[int] = set()
    if not text.strip():
        return result
    for raw_part in text.split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = _RANGE_RE.match(part)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            if start > end:
                start, end = end, start
            if start < 1 or end > maximum:
                raise ValueError(f"Aralık 1-{maximum} dışında: {part}")
            result.update(range(start, end + 1))
            continue
        try:
            number = int(part)
        except ValueError as exc:
            raise ValueError(f"Geçersiz seçim: {part}") from exc
        if number < 1 or number > maximum:
            raise ValueError(f"Seçim 1-{maximum} dışında: {number}")
        result.add(number)
    return result


def is_subpath_of(rel_path: str, parent: str) -> bool:
    rel_path = normalize_rel_path(rel_path)
    parent = normalize_rel_path(parent)
    return rel_path == parent or rel_path.startswith(parent + "/")


def unique_preserving_order(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
