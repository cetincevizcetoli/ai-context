import fnmatch
import os
from typing import Iterable, List, Set, Tuple

from .config import (
    CODE_EXTENSIONS,
    KNOWN_BINARY_EXTENSIONS,
    PROJECT_MARKERS,
    PROJECT_RECOMMENDED_EXTS,
    SENSITIVE_EXACT_NAMES,
    SENSITIVE_EXTENSIONS,
    SPECIAL_TEXT_FILENAMES,
)
from .utils import extension_for_name


_SENSITIVE_EXACT_NAMES_LOWER = {item.lower() for item in SENSITIVE_EXACT_NAMES}


def is_sensitive_path(rel_path: str) -> bool:
    name = os.path.basename(rel_path)
    lower_name = name.lower()
    extension = os.path.splitext(lower_name)[1]

    if lower_name in _SENSITIVE_EXACT_NAMES_LOWER:
        return True
    if extension in SENSITIVE_EXTENSIONS:
        return True
    if lower_name.startswith(".env") and lower_name not in {".env.example", ".env.sample", ".env.template"}:
        return True

    suspicious_patterns = (
        "*credential*.json", "*secret*.json", "*service-account*.json",
        "*service_account*.json", "*private*key*", "*.secrets.*",
    )
    return any(fnmatch.fnmatch(lower_name, pattern) for pattern in suspicious_patterns)


def is_binary_name(name: str) -> bool:
    return extension_for_name(name) in KNOWN_BINARY_EXTENSIONS


def classify_file(rel_path: str) -> Tuple[str, bool, bool]:
    name = os.path.basename(rel_path)
    lower_path = rel_path.lower()
    lower_name = name.lower()
    extension = extension_for_name(name)
    sensitive = is_sensitive_path(rel_path)
    binary = extension in KNOWN_BINARY_EXTENSIONS

    if sensitive:
        return "sensitive", binary, True
    if binary:
        return "binary", True, False
    if "/test/" in f"/{lower_path}/" or "/tests/" in f"/{lower_path}/" or lower_name.startswith("test_") or lower_name.endswith("_test.py"):
        return "test", False, False
    if extension in CODE_EXTENSIONS:
        return "code", False, False
    if (
        name in SPECIAL_TEXT_FILENAMES
        or lower_name.endswith((".env.example", ".env.sample", ".env.template"))
        or extension in {".json", ".jsonc", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties"}
    ):
        return "config", False, False
    if extension in {".md", ".mdx", ".rst", ".txt"} or lower_name.startswith("readme") or lower_name.startswith("license"):
        return "docs", False, False
    if extension in {".csv", ".tsv", ".graphql", ".gql", ".proto"}:
        return "data", False, False
    return "other", False, False


def detect_project_types(rel_paths: Iterable[str]) -> List[str]:
    names = {os.path.basename(path) for path in rel_paths}
    detected: List[str] = []
    for project_type, markers in PROJECT_MARKERS.items():
        if names.intersection(markers):
            detected.append(project_type)
    return detected or ["Genel / Karma"]


def default_selection(extension: str, name: str, category: str, project_types: Iterable[str]) -> Tuple[bool, str]:
    if category in {"binary", "sensitive"}:
        return False, "güvenlik/binary"
    if extension in CODE_EXTENSIONS:
        return True, "varsayılan kod uzantısı"
    if name in SPECIAL_TEXT_FILENAMES or name.lower().endswith((".env.example", ".env.sample", ".env.template")):
        return True, "proje yapılandırma dosyası"
    if name.lower().startswith("readme"):
        return True, "proje açıklaması"
    recommended: Set[str] = set()
    for project_type in project_types:
        recommended.update(PROJECT_RECOMMENDED_EXTS.get(project_type, set()))
    if extension and extension in recommended:
        return True, "proje profili önerisi"
    if category == "config" and name in {"package.json", "composer.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml"}:
        return True, "ana proje bildirimi"
    return False, "isteğe bağlı"
