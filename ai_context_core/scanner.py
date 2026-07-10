import os
from typing import List, Set, Tuple

from .classifier import classify_file, default_selection, detect_project_types
from .config import DEFAULT_IGNORE_DIRS
from .git_tools import changed_git_files, is_git_repo, list_git_visible_files
from .models import FileRecord, ScanResult
from .utils import extension_for_name, is_subpath_of, normalize_rel_path


def _matches_target(rel_path: str, targets: Set[str]) -> bool:
    if not targets:
        return True
    name = os.path.basename(rel_path)
    return name in targets or rel_path in targets or any(is_subpath_of(rel_path, target) for target in targets)


def _filesystem_paths(root_path: str, excluded_dirs: Set[str]) -> Tuple[List[str], Set[str]]:
    paths: List[str] = []
    skipped_dirs: Set[str] = set()
    stack: List[Tuple[str, str]] = [(root_path, "")]

    while stack:
        abs_dir, rel_dir = stack.pop()
        try:
            with os.scandir(abs_dir) as entries:
                for entry in entries:
                    rel_path = normalize_rel_path(os.path.join(rel_dir, entry.name))
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name in DEFAULT_IGNORE_DIRS or entry.name.startswith(".") or entry.name in excluded_dirs or rel_path in excluded_dirs:
                                skipped_dirs.add(rel_path)
                                continue
                            stack.append((entry.path, rel_path))
                        elif entry.is_file(follow_symlinks=False):
                            paths.append(rel_path)
                    except OSError:
                        continue
        except (OSError, PermissionError):
            if rel_dir:
                skipped_dirs.add(rel_dir)
    return paths, skipped_dirs


def scan_project(
    root_path: str,
    *,
    use_git: bool,
    auto_git: bool,
    changed_only: bool,
    excluded_dirs: Set[str],
    excluded_files: Set[str],
    excluded_exts: Set[str],
    targets: Set[str],
    max_size_kb: int,
    force_include: Set[str],
) -> ScanResult:
    root_path = os.path.abspath(root_path)
    result = ScanResult(root_path=root_path)

    git_repo = is_git_repo(root_path)
    should_use_git = git_repo and (use_git or auto_git or changed_only)

    if should_use_git:
        try:
            rel_paths = list_git_visible_files(root_path)
            result.scanner_name = "git"
        except RuntimeError as exc:
            rel_paths, result.skipped_dirs = _filesystem_paths(root_path, excluded_dirs)
            result.scanner_name = "filesystem-fallback"
            result.warnings.append(f"Git taraması kullanılamadı: {exc}")
    else:
        rel_paths, result.skipped_dirs = _filesystem_paths(root_path, excluded_dirs)
        result.scanner_name = "filesystem"
        if use_git and not git_repo:
            result.warnings.append("-git istendi fakat geçerli Git deposu bulunamadı; dosya sistemi taraması kullanıldı.")

    for forced in force_include:
        normalized = normalize_rel_path(forced)
        abs_forced = os.path.join(root_path, normalized)
        if os.path.isfile(abs_forced) and normalized not in rel_paths:
            rel_paths.append(normalized)

    changed_paths: Set[str] = set()
    changed_filter_active = False
    if changed_only:
        if not git_repo:
            result.warnings.append("--changed-only yalnızca Git deposunda kullanılabilir; değişiklik filtresi uygulanmadı.")
        else:
            try:
                changed_paths = changed_git_files(root_path)
                changed_filter_active = True
            except RuntimeError as exc:
                result.warnings.append(f"Değişen dosyalar alınamadı: {exc}")

    filtered_entries: List[Tuple[str, os.stat_result]] = []
    for rel_path in rel_paths:
        rel_path = normalize_rel_path(rel_path)
        if not rel_path:
            continue
        if any(is_subpath_of(rel_path, item) for item in excluded_dirs):
            continue
        name = os.path.basename(rel_path)
        extension = extension_for_name(name)
        forced = rel_path in force_include or name in force_include
        if not forced and (name in excluded_files or rel_path in excluded_files):
            continue
        if not forced and extension in excluded_exts:
            continue
        if not _matches_target(rel_path, targets):
            continue
        if changed_filter_active and rel_path not in changed_paths:
            continue
        abs_path = os.path.join(root_path, rel_path)
        try:
            stat = os.stat(abs_path)
        except OSError:
            continue
        if max_size_kb > 0 and stat.st_size > max_size_kb * 1024 and not forced:
            continue
        filtered_entries.append((rel_path, stat))

    result.project_types = detect_project_types(path for path, _ in filtered_entries)

    records: List[FileRecord] = []
    for rel_path, stat in filtered_entries:
        abs_path = os.path.join(root_path, rel_path)
        name = os.path.basename(rel_path)
        extension = extension_for_name(name)
        category, is_binary, is_sensitive = classify_file(rel_path)
        selected, reason = default_selection(extension, name, category, result.project_types)
        records.append(
            FileRecord(
                rel_path=rel_path,
                abs_path=abs_path,
                name=name,
                extension=extension,
                size_bytes=stat.st_size,
                mtime_ns=getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
                category=category,
                is_binary=is_binary,
                is_sensitive=is_sensitive,
                default_selected=selected,
                selection_reason=reason,
            )
        )

    result.files = sorted(records, key=lambda item: item.rel_path.lower())
    return result
