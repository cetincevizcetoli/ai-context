import os
from typing import Dict, List, Set, Tuple

from .classifier import classify_file, default_selection, detect_project_types, is_sensitive_path
from .config import DEFAULT_IGNORE_DIRS, SUMMARY_FOLDER_NAMES
from .git_tools import changed_git_files, is_git_repo, list_git_visible_files
from .models import FileRecord, ScanResult, StructureEntry
from .utils import extension_for_name, is_subpath_of, normalize_rel_path


_STRUCTURE_COUNT_LIMIT = 250


def _matches_target(rel_path: str, targets: Set[str]) -> bool:
    if not targets:
        return True
    name = os.path.basename(rel_path)
    return name in targets or rel_path in targets or any(is_subpath_of(rel_path, target) for target in targets)


def _dir_is_excluded(name: str, rel_path: str, excluded_dirs: Set[str], *, smart_map: bool) -> bool:
    if name in DEFAULT_IGNORE_DIRS:
        return True
    if smart_map and name.lower() in {item.lower() for item in SUMMARY_FOLDER_NAMES}:
        return True
    return name in excluded_dirs or rel_path in excluded_dirs or any(is_subpath_of(rel_path, item) for item in excluded_dirs)


def _filesystem_paths(root_path: str, excluded_dirs: Set[str], *, smart_map: bool) -> Tuple[List[str], Set[str]]:
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
                            if _dir_is_excluded(entry.name, rel_path, excluded_dirs, smart_map=smart_map):
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


def _sample_directory(abs_path: str) -> Tuple[int, int, bool]:
    files = 0
    dirs = 0
    capped = False
    try:
        with os.scandir(abs_path) as entries:
            for index, entry in enumerate(entries, 1):
                if index > _STRUCTURE_COUNT_LIMIT:
                    capped = True
                    break
                try:
                    if entry.is_dir(follow_symlinks=False):
                        dirs += 1
                    elif entry.is_file(follow_symlinks=False):
                        files += 1
                except OSError:
                    continue
    except (OSError, PermissionError):
        capped = True
    return files, dirs, capped


def _discover_structure(
    root_path: str,
    excluded_dirs: Set[str],
    *,
    smart_map: bool,
) -> Tuple[List[StructureEntry], Set[str]]:
    """Discover directory names without reading file contents.

    Pruned directories are recorded and sampled only at their first level. This
    exposes facts such as ``env/`` or ``.git/`` while avoiding a walk through
    dependency trees, uploads, caches and repository internals.
    """

    entries: Dict[Tuple[str, str], StructureEntry] = {}
    skipped: Set[str] = set()
    stack: List[Tuple[str, str]] = [(root_path, "")]

    while stack:
        abs_dir, rel_dir = stack.pop()
        try:
            with os.scandir(abs_dir) as children:
                for child in children:
                    rel_path = normalize_rel_path(os.path.join(rel_dir, child.name))
                    try:
                        if child.is_dir(follow_symlinks=False):
                            is_pruned = _dir_is_excluded(child.name, rel_path, excluded_dirs, smart_map=smart_map)
                            if is_pruned:
                                file_count, dir_count, capped = _sample_directory(child.path)
                                reason = "kullanıcı tarafından hariç tutuldu" if (
                                    child.name in excluded_dirs or rel_path in excluded_dirs
                                ) else "özet klasör; içerik taranmadı"
                                entries[("dir", rel_path)] = StructureEntry(
                                    rel_path=rel_path,
                                    name=child.name,
                                    kind="dir",
                                    is_pruned=True,
                                    reason=reason,
                                    immediate_file_count=file_count,
                                    immediate_dir_count=dir_count,
                                    count_capped=capped,
                                )
                                skipped.add(rel_path)
                                continue

                            entries[("dir", rel_path)] = StructureEntry(
                                rel_path=rel_path,
                                name=child.name,
                                kind="dir",
                            )
                            stack.append((child.path, rel_path))
                            continue

                        if child.is_file(follow_symlinks=False):
                            # Root files and sensitive files are useful structural
                            # facts even when Git ignores them. Do not read them.
                            if not rel_dir or is_sensitive_path(rel_path):
                                try:
                                    stat = child.stat(follow_symlinks=False)
                                    size = stat.st_size
                                except OSError:
                                    size = 0
                                entries[("file", rel_path)] = StructureEntry(
                                    rel_path=rel_path,
                                    name=child.name,
                                    kind="file",
                                    size_bytes=size,
                                    is_sensitive=is_sensitive_path(rel_path),
                                )
                    except OSError:
                        continue
        except (OSError, PermissionError):
            if rel_dir:
                skipped.add(rel_dir)
                entries[("dir", rel_dir)] = StructureEntry(
                    rel_path=rel_dir,
                    name=os.path.basename(rel_dir),
                    kind="dir",
                    is_pruned=True,
                    reason="erişim sağlanamadı",
                    count_capped=True,
                )

    return sorted(entries.values(), key=lambda item: (item.rel_path.lower(), item.kind)), skipped


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
    smart_map: bool = False,
) -> ScanResult:
    root_path = os.path.abspath(root_path)
    result = ScanResult(root_path=root_path)

    structure_entries, structure_skipped = _discover_structure(
        root_path,
        excluded_dirs,
        smart_map=smart_map,
    )
    result.structure_entries = structure_entries
    result.skipped_dirs.update(structure_skipped)

    git_repo = is_git_repo(root_path)
    should_use_git = git_repo and (use_git or auto_git or changed_only)

    if should_use_git:
        try:
            rel_paths = list_git_visible_files(root_path)
            result.scanner_name = "git"
        except RuntimeError as exc:
            rel_paths, skipped = _filesystem_paths(root_path, excluded_dirs, smart_map=smart_map)
            result.skipped_dirs.update(skipped)
            result.scanner_name = "filesystem-fallback"
            result.warnings.append(f"Git taraması kullanılamadı: {exc}")
    else:
        rel_paths, skipped = _filesystem_paths(root_path, excluded_dirs, smart_map=smart_map)
        result.skipped_dirs.update(skipped)
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
        if smart_map and any(is_subpath_of(rel_path, item) for item in result.skipped_dirs):
            # A Git repository may track files under a directory that the smart
            # map intentionally treats as summary-only (for example uploads/).
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
