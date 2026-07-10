import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

from .models import FileRecord, ScanResult, SelectionResult
from .utils import human_int, human_size, parse_number_selection


@dataclass
class ExtensionGroup:
    key: str
    label: str
    files: List[FileRecord]
    @property
    def default_count(self) -> int:
        return sum(1 for item in self.files if item.default_selected and not item.is_sensitive)

    @property
    def default_selected(self) -> bool:
        return bool(self.files) and self.default_count == len(self.files)

    @property
    def partially_selected(self) -> bool:
        return 0 < self.default_count < len(self.files)

    @property
    def total_size(self) -> int:
        return sum(item.size_bytes for item in self.files)

    @property
    def estimated_tokens(self) -> int:
        return sum(item.estimated_tokens for item in self.files)

    @property
    def has_sensitive(self) -> bool:
        return any(item.is_sensitive for item in self.files)

    @property
    def binary_only(self) -> bool:
        return bool(self.files) and all(item.is_binary for item in self.files)


def _group_label(key: str) -> str:
    if key == "[uzantısız]":
        return "Uzantısız"
    if key == "[hassas]":
        return "Hassas dosyalar"
    return key


def build_extension_groups(files: Sequence[FileRecord]) -> List[ExtensionGroup]:
    grouped: Dict[str, List[FileRecord]] = defaultdict(list)
    for item in files:
        key = "[hassas]" if item.is_sensitive else (item.extension or "[uzantısız]")
        grouped[key].append(item)

    groups: List[ExtensionGroup] = []
    for key, records in grouped.items():
        groups.append(
            ExtensionGroup(
                key=key,
                label=_group_label(key),
                files=sorted(records, key=lambda item: item.rel_path.lower()),
            )
        )

    return sorted(
        groups,
        key=lambda group: (
            group.default_count == 0,
            group.has_sensitive,
            group.binary_only,
            -len(group.files),
            group.label.lower(),
        ),
    )


def _print_scan_summary(scan: ScanResult, groups: Sequence[ExtensionGroup], budget: int) -> None:
    total_size = sum(item.size_bytes for item in scan.files)
    default_tokens = sum(item.estimated_tokens for group in groups for item in group.files if item.default_selected and not item.is_sensitive)
    project_text = ", ".join(scan.project_types)
    print(f"\nAI-CONTEXT AKILLI SEÇİM")
    print(f"Proje       : {project_text}")
    print(f"Tarayıcı    : {scan.scanner_name}")
    print(f"Dosya       : {human_int(len(scan.files))}")
    print(f"Toplam boyut: {human_size(total_size)}")
    print(f"Öneri       : ~{human_int(default_tokens)} token")
    if budget > 0:
        print(f"Bütçe       : ~{human_int(budget)} token")
    print()

    print(" No  Seç  Tür / uzantı             Dosya       Boyut       Token")
    print("---  ---  ----------------------  -------  ----------  ----------")
    for index, group in enumerate(groups, 1):
        mark = "[x]" if group.default_selected else "[~]" if group.partially_selected else "[ ]"
        if group.has_sensitive:
            mark = "[!]"
        label = group.label
        if group.binary_only:
            label += " (binary)"
        print(
            f"{index:>3}  {mark:<3}  {label[:22]:<22}  {len(group.files):>7}  "
            f"{human_size(group.total_size):>10}  {human_int(group.estimated_tokens):>10}"
        )


def _paths_for_groups(groups: Sequence[ExtensionGroup], indices: Set[int]) -> Set[str]:
    selected: Set[str] = set()
    for index in indices:
        selected.update(item.rel_path for item in groups[index - 1].files)
    return selected


def _apply_sensitive_guard(
    files_by_path: Dict[str, FileRecord],
    selected_paths: Set[str],
    *,
    allow_sensitive: bool,
    force_include: Set[str],
) -> Tuple[Set[str], Set[str]]:
    allowed: Set[str] = set()
    blocked: Set[str] = set()
    for path in selected_paths:
        item = files_by_path[path]
        explicitly_forced = path in force_include or item.name in force_include
        if item.is_sensitive and not (allow_sensitive or explicitly_forced):
            blocked.add(path)
        else:
            allowed.add(path)
    return allowed, blocked


def _fit_budget(files: Sequence[FileRecord], selected_paths: Set[str], budget: int) -> Tuple[Set[str], int]:
    if budget <= 0:
        return set(), sum(item.estimated_tokens for item in files if item.rel_path in selected_paths)

    selected = [item for item in files if item.rel_path in selected_paths and not item.is_binary]
    total = sum(item.estimated_tokens for item in selected)
    if total <= budget:
        return set(), total

    names_only: Set[str] = set()
    for item in sorted(selected, key=lambda record: record.estimated_tokens, reverse=True):
        if total <= budget:
            break
        names_only.add(item.rel_path)
        total -= item.estimated_tokens
    return names_only, total


def interactive_select(
    scan: ScanResult,
    *,
    budget: int,
    allow_sensitive: bool,
    force_include: Set[str],
) -> SelectionResult:
    if not sys.stdin.isatty():
        raise RuntimeError("Etkileşimli mod için terminal girdisi gerekiyor.")

    groups = build_extension_groups(scan.files)
    if not groups:
        return SelectionResult()

    _print_scan_summary(scan, groups, budget)
    default_paths = {item.rel_path for item in scan.files if item.default_selected and not item.is_sensitive}

    print("Enter = önerilen seçim | all = tüm güvenli dosyalar | 1,3,5-7 = elle seç")
    print("list N = N numaralı gruptaki dosyaları göster | q = çık")

    while True:
        raw = input("\nSeçiminiz: ").strip().lower()
        if raw in {"q", "quit", "iptal", "exit"}:
            raise KeyboardInterrupt
        if raw.startswith("list "):
            try:
                index = int(raw.split(maxsplit=1)[1])
                if not 1 <= index <= len(groups):
                    raise ValueError
            except ValueError:
                print(f"Geçerli bir grup numarası girin: 1-{len(groups)}")
                continue
            group = groups[index - 1]
            print(f"\n{group.label}:")
            for item in group.files:
                flag = " [HASSAS]" if item.is_sensitive else ""
                print(f"  {item.rel_path} ({human_size(item.size_bytes)}){flag}")
            continue
        if raw in {"", "default", "öneri", "oneri"}:
            selected_paths = set(default_paths)
            break
        if raw in {"all", "hepsi", "all-safe", "hepsi-guvenli", "hepsi-güvenli"}:
            selected_indices = {index for index, group in enumerate(groups, 1) if not group.has_sensitive}
            selected_paths = _paths_for_groups(groups, selected_indices)
            break
        try:
            selected_indices = parse_number_selection(raw, len(groups))
            if not selected_indices:
                print("En az bir grup seçin veya Enter ile öneriyi kullanın.")
                continue
            selected_paths = _paths_for_groups(groups, selected_indices)
            break
        except ValueError as exc:
            print(exc)

    files_by_path = {item.rel_path: item for item in scan.files}
    selected_paths, blocked = _apply_sensitive_guard(
        files_by_path,
        selected_paths,
        allow_sensitive=allow_sensitive,
        force_include=force_include,
    )

    if blocked:
        print(f"\nGüvenlik nedeniyle {len(blocked)} hassas dosya içerik seçiminden çıkarıldı.")
        print("Gerekliyse tam yolu -gf ile verin veya --allow-sensitive kullanın.")

    current_tokens = sum(files_by_path[path].estimated_tokens for path in selected_paths)
    names_only: Set[str] = set()

    if budget > 0 and current_tokens > budget:
        suggested_names_only, fitted_tokens = _fit_budget(scan.files, selected_paths, budget)
        print(
            f"\nSeçim ~{human_int(current_tokens)} token; bütçe ~{human_int(budget)} token."
        )
        print(f"Enter = en büyük {len(suggested_names_only)} dosyayı yalnızca isim olarak ekle")
        print("p = bütçeyi aşarak devam et | f = büyük dosyaları tamamen çıkar")
        while True:
            action = input("Bütçe seçimi: ").strip().lower()
            if action in {"", "n", "name", "isim"}:
                names_only = suggested_names_only
                current_tokens = fitted_tokens
                break
            if action in {"p", "proceed", "devam"}:
                break
            if action in {"f", "remove", "çıkar", "cikar"}:
                selected_paths.difference_update(suggested_names_only)
                current_tokens = fitted_tokens
                break
            print("Enter, p veya f girin.")

    return SelectionResult(
        selected_paths=selected_paths,
        names_only_paths=names_only,
        blocked_sensitive_paths=blocked,
        estimated_tokens=current_tokens,
    )


def automatic_select(
    scan: ScanResult,
    *,
    allowed_exts: Set[str],
    unsafe: bool,
    allow_sensitive: bool,
    force_include: Set[str],
    budget: int,
) -> SelectionResult:
    selected: Set[str] = set()
    blocked: Set[str] = set()

    for item in scan.files:
        forced = item.rel_path in force_include or item.name in force_include
        if item.is_sensitive and not (allow_sensitive or forced):
            blocked.add(item.rel_path)
            continue
        if item.is_binary:
            selected.add(item.rel_path)
            continue
        if forced or unsafe or item.extension in allowed_exts:
            selected.add(item.rel_path)

    names_only, fitted_tokens = _fit_budget(scan.files, selected, budget)
    return SelectionResult(
        selected_paths=selected,
        names_only_paths=names_only,
        blocked_sensitive_paths=blocked,
        estimated_tokens=fitted_tokens,
    )
