import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .config import (
    CONTENT_FOLDER_NAMES,
    LIST_FOLDER_NAMES,
    MIXED_FOLDER_NAMES,
    MODE_LABELS,
    SUMMARY_FOLDER_NAMES,
)
from .models import FileRecord, ScanResult, SelectionResult, StructureEntry
from .utils import human_int, human_size, parse_number_selection


_ROOT_KEY = "__root__"




@dataclass
class ExtensionGroup:
    """Compatibility helper retained from v1.4 for callers that inspect groups."""

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


def build_extension_groups(files: Sequence[FileRecord]) -> List[ExtensionGroup]:
    grouped: Dict[str, List[FileRecord]] = {}
    for item in files:
        key = "[hassas]" if item.is_sensitive else (item.extension or "[uzantısız]")
        grouped.setdefault(key, []).append(item)

    def label(key: str) -> str:
        if key == "[uzantısız]":
            return "Uzantısız"
        if key == "[hassas]":
            return "Hassas dosyalar"
        return key

    groups = [
        ExtensionGroup(key=key, label=label(key), files=sorted(records, key=lambda item: item.rel_path.lower()))
        for key, records in grouped.items()
    ]
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


@dataclass
class FolderGroup:
    key: str
    label: str
    role: str
    mode: str
    files: List[FileRecord] = field(default_factory=list)
    dirs: List[StructureEntry] = field(default_factory=list)
    extra_files: List[StructureEntry] = field(default_factory=list)
    explicit_paths: Set[str] = field(default_factory=set)
    is_pruned: bool = False

    @property
    def total_size(self) -> int:
        known = {item.rel_path: item.size_bytes for item in self.files}
        for item in self.extra_files:
            known.setdefault(item.rel_path, item.size_bytes)
        return sum(known.values())

    @property
    def file_count(self) -> int:
        return len({item.rel_path for item in self.files}.union(item.rel_path for item in self.extra_files))


def _group_key(rel_path: str) -> str:
    return rel_path.split("/", 1)[0] if "/" in rel_path else _ROOT_KEY


def _safe_text_files(files: Iterable[FileRecord]) -> List[FileRecord]:
    return [item for item in files if not item.is_binary and not item.is_sensitive]


def _default_mode_and_role(key: str, files: Sequence[FileRecord], is_pruned: bool) -> Tuple[str, str]:
    if key == _ROOT_KEY:
        return "mixed", "Proje giriş ve yapılandırma dosyaları"

    name = key.lower()
    if is_pruned or name in {item.lower() for item in SUMMARY_FOLDER_NAMES}:
        return "summary", "Varlığı önemli; içerik taranmaz"
    if name in {item.lower() for item in CONTENT_FOLDER_NAMES}:
        return "content", "Uygulamanın çalışan kodu"
    if name in {item.lower() for item in MIXED_FOLDER_NAMES}:
        return "mixed", "Kod içerikleri + diğer dosya adları"
    if name in {item.lower() for item in LIST_FOLDER_NAMES}:
        return "list", "Dosya adları görünür; içerik isteğe bağlı"

    text_files = _safe_text_files(files)
    if not text_files:
        return "list", "Yapısal/yardımcı klasör"
    default_count = sum(1 for item in text_files if item.default_selected)
    ratio = default_count / len(text_files)
    if ratio >= 0.65:
        return "content", "Kod ağırlıklı klasör"
    if default_count:
        return "mixed", "Karma proje içeriği"
    return "list", "İsteğe bağlı proje içeriği"


def build_folder_groups(scan: ScanResult) -> List[FolderGroup]:
    file_groups: Dict[str, List[FileRecord]] = {}
    dir_groups: Dict[str, List[StructureEntry]] = {}
    extra_groups: Dict[str, List[StructureEntry]] = {}
    top_dirs: Set[str] = set()
    recorded_paths = {item.rel_path for item in scan.files}

    for item in scan.files:
        file_groups.setdefault(_group_key(item.rel_path), []).append(item)
        if "/" in item.rel_path:
            top_dirs.add(item.rel_path.split("/", 1)[0])

    for entry in scan.structure_entries:
        key = _group_key(entry.rel_path)
        if entry.kind == "dir":
            top = entry.rel_path.split("/", 1)[0]
            top_dirs.add(top)
            dir_groups.setdefault(top, []).append(entry)
        elif entry.rel_path not in recorded_paths:
            extra_groups.setdefault(key, []).append(entry)

    keys: Set[str] = set(top_dirs)
    keys.update(file_groups)
    keys.update(extra_groups)
    if _ROOT_KEY not in keys and any("/" not in item.rel_path for item in scan.files):
        keys.add(_ROOT_KEY)

    groups: List[FolderGroup] = []
    for key in keys:
        files = sorted(file_groups.get(key, []), key=lambda item: item.rel_path.lower())
        dirs = sorted(dir_groups.get(key, []), key=lambda item: item.rel_path.lower())
        extras = sorted(extra_groups.get(key, []), key=lambda item: item.rel_path.lower())
        top_entry = next((item for item in dirs if item.rel_path == key), None)
        is_pruned = bool(top_entry and top_entry.is_pruned)
        mode, role = _default_mode_and_role(key, files, is_pruned)
        groups.append(
            FolderGroup(
                key=key,
                label="Kök dosyalar" if key == _ROOT_KEY else key + "/",
                role=role,
                mode=mode,
                files=files,
                dirs=dirs,
                extra_files=extras,
                is_pruned=is_pruned,
            )
        )

    return sorted(groups, key=lambda group: (group.key != _ROOT_KEY, group.label.lower()))


def _selected_for_group(group: FolderGroup) -> Set[str]:
    if group.mode == "content":
        return {item.rel_path for item in group.files if not item.is_binary and not item.is_sensitive}
    if group.mode == "mixed":
        return {
            item.rel_path
            for item in group.files
            if item.default_selected and not item.is_binary and not item.is_sensitive
        }
    if group.mode == "pick":
        return set(group.explicit_paths)
    return set()


def _tokens_for_group(group: FolderGroup) -> int:
    selected = _selected_for_group(group)
    return sum(item.estimated_tokens for item in group.files if item.rel_path in selected)


def _print_folder_summary(scan: ScanResult, groups: Sequence[FolderGroup], budget: int) -> None:
    total_size = sum(item.size_bytes for item in scan.files)
    proposed_tokens = sum(_tokens_for_group(group) for group in groups)
    print("\nAI-CONTEXT PROJE HARİTASI")
    print(f"Proje       : {', '.join(scan.project_types)}")
    print(f"Tarayıcı    : {scan.scanner_name} + yapı haritası")
    print(f"Dosya       : {human_int(len(scan.files))}")
    print(f"Toplam boyut: {human_size(total_size)}")
    print(f"Öneri       : ~{human_int(proposed_tokens)} token")
    if budget > 0:
        print(f"Bütçe       : ~{human_int(budget)} token")
    print()
    print(" No  Mod      Klasör / bölüm         Dosya      Boyut      İçerik       Rol")
    print("---  -------  --------------------  -------  ---------  ----------  -----------------------------")
    for index, group in enumerate(groups, 1):
        mode = MODE_LABELS[group.mode]
        print(
            f"{index:>3}  {mode:<7}  {group.label[:20]:<20}  {group.file_count:>7}  "
            f"{human_size(group.total_size):>9}  {human_int(_tokens_for_group(group)):>10}  {group.role[:29]}"
        )


def _print_group_files(group: FolderGroup, *, candidates_only: bool = False) -> List[FileRecord]:
    files = [item for item in group.files if not item.is_binary]
    if candidates_only:
        files = [item for item in files if not item.is_sensitive]
    files.sort(key=lambda item: item.rel_path.lower())
    if not files:
        print("Bu bölümde seçilebilir metin dosyası yok.")
        return []

    shown = files
    if len(files) > 200:
        query = input(f"{len(files)} metin dosyası var. Arama kelimesi (boş = ilk 200): ").strip().lower()
        if query:
            shown = [item for item in files if query in item.rel_path.lower()]
        shown = shown[:200]
        if not shown:
            print("Aramaya uyan dosya bulunamadı.")
            return []

    print(f"\n{group.label}")
    print(" No  Seç  Dosya                                                        Token")
    print("---  ---  -----------------------------------------------------------  ----------")
    for index, item in enumerate(shown, 1):
        mark = "[x]" if item.rel_path in group.explicit_paths else "[ ]"
        sensitive = " [HASSAS]" if item.is_sensitive else ""
        print(f"{index:>3}  {mark:<3}  {item.rel_path[:59]:<59}  {human_int(item.estimated_tokens):>10}{sensitive}")
    return shown


def _pick_files(
    group: FolderGroup,
    *,
    allow_sensitive: bool,
    force_include: Set[str],
) -> None:
    candidates = [
        item
        for item in group.files
        if not item.is_binary
        and (
            not item.is_sensitive
            or allow_sensitive
            or item.rel_path in force_include
            or item.name in force_include
        )
    ]
    candidates.sort(key=lambda item: item.rel_path.lower())
    if not candidates:
        print("Bu klasör taranmadı veya seçilebilir metin dosyası yok.")
        return

    shown = candidates
    if len(candidates) > 200:
        query = input(f"{len(candidates)} metin dosyası var. Arama kelimesi (boş = ilk 200): ").strip().lower()
        if query:
            shown = [item for item in candidates if query in item.rel_path.lower()]
        shown = shown[:200]
    if not shown:
        print("Aramaya uyan dosya bulunamadı.")
        return

    print(f"\n{group.label} içinden içerik olarak eklenecek dosyalar:")
    for index, item in enumerate(shown, 1):
        current = item.rel_path in group.explicit_paths
        mark = "[x]" if current else "[ ]"
        print(f"{index:>3}) {mark} {item.rel_path} (~{human_int(item.estimated_tokens)} token)")
    print("Örnek: 1,3,5-8 | all = listedekilerin tümü | none = içerik seçme")

    while True:
        raw = input("Dosya seçimi: ").strip().lower()
        if raw in {"none", "yok", "0"}:
            group.explicit_paths.clear()
            group.mode = "pick"
            return
        if raw in {"all", "hepsi"}:
            group.explicit_paths = {item.rel_path for item in shown}
            group.mode = "pick"
            return
        try:
            indices = parse_number_selection(raw, len(shown))
            if not indices:
                print("En az bir dosya seçin veya 'none' yazın.")
                continue
            group.explicit_paths = {shown[index - 1].rel_path for index in indices}
            group.mode = "pick"
            return
        except ValueError as exc:
            print(exc)


def _edit_group(
    group: FolderGroup,
    *,
    allow_sensitive: bool,
    force_include: Set[str],
) -> None:
    print(f"\n{group.label} | mevcut mod: {MODE_LABELS[group.mode]}")
    if group.is_pruned:
        print("Bu klasör hız için özet tarandı. Varlığı gösterilir, içine girilmez.")
        print("1) ÖZET olarak bırak  2) GİZLE  0) Geri")
        while True:
            choice = input("Seçim: ").strip().lower()
            if choice in {"0", "", "geri"}:
                return
            if choice == "1":
                group.mode = "summary"
                return
            if choice == "2":
                group.mode = "hide"
                return
            print("0, 1 veya 2 girin.")

    print("1) İÇERİK  - bütün güvenli metin dosyalarını oku")
    print("2) KARMA   - önemli kodları oku, diğer dosya adlarını göster")
    print("3) LİSTE   - dosya adlarını göster, içerik okuma")
    print("4) ÖZET    - yalnızca klasörün varlığını göster")
    print("5) SEÇİLİ  - içinden belirli dosyaları seç")
    print("6) GİZLE   - raporda gösterme")
    print("7) DOSYALAR- metin dosyalarını yalnızca ekranda incele")
    print("0) Geri")

    while True:
        choice = input("Seçim: ").strip().lower()
        if choice in {"0", "", "geri"}:
            return
        if choice == "1":
            group.mode = "content"
            return
        if choice == "2":
            group.mode = "mixed"
            return
        if choice == "3":
            group.mode = "list"
            return
        if choice == "4":
            group.mode = "summary"
            return
        if choice == "5":
            _pick_files(group, allow_sensitive=allow_sensitive, force_include=force_include)
            return
        if choice == "6":
            group.mode = "hide"
            return
        if choice == "7":
            _print_group_files(group)
            continue
        print("0-7 arasında seçim yapın.")


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


def _summary_note(entry: StructureEntry) -> str:
    details: List[str] = []
    if entry.immediate_dir_count:
        details.append(f"{entry.immediate_dir_count}{'+' if entry.count_capped else ''} alt klasör")
    if entry.immediate_file_count:
        details.append(f"{entry.immediate_file_count}{'+' if entry.count_capped else ''} dosya")
    base = entry.reason or "içerik taranmadı"
    return base + (("; " + ", ".join(details)) if details else "")


def _build_selection_from_groups(
    scan: ScanResult,
    groups: Sequence[FolderGroup],
    *,
    allow_sensitive: bool,
    force_include: Set[str],
    budget: int,
    map_limit: int,
) -> SelectionResult:
    files_by_path = {item.rel_path: item for item in scan.files}
    structure_files = {item.rel_path: item for item in scan.structure_entries if item.kind == "file"}
    selected: Set[str] = set()
    map_files: Set[str] = set()
    map_dirs: Set[str] = set()
    summary_dirs: Set[str] = set()
    hidden_dirs: Set[str] = set()
    notes: Dict[str, str] = {}
    folder_modes: Dict[str, str] = {}
    omitted: Dict[str, int] = {}
    blocked: Set[str] = set()

    for group in groups:
        folder_modes[group.key] = group.mode
        content_paths = _selected_for_group(group)
        selected.update(content_paths)

        if group.mode == "hide":
            if group.key != _ROOT_KEY:
                hidden_dirs.add(group.key)
            continue
        if group.mode == "summary":
            if group.key != _ROOT_KEY:
                summary_dirs.add(group.key)
                top_entry = next((item for item in group.dirs if item.rel_path == group.key), None)
                if top_entry:
                    notes[group.key] = _summary_note(top_entry)
                else:
                    notes[group.key] = "yalnızca klasör özeti"
            else:
                for item in group.extra_files:
                    map_files.add(item.rel_path)
            continue

        group_file_paths = {item.rel_path for item in group.files}
        group_file_paths.update(item.rel_path for item in group.extra_files)
        selected_first = sorted(content_paths)
        remaining = sorted(group_file_paths.difference(content_paths))
        if map_limit > 0 and len(group_file_paths) > map_limit:
            capacity = max(0, map_limit - len(selected_first))
            included = set(selected_first)
            included.update(remaining[:capacity])
            map_files.update(included)
            omitted[group.key] = len(group_file_paths) - len(included)
        else:
            map_files.update(group_file_paths)

        for entry in group.dirs:
            if entry.is_pruned:
                summary_dirs.add(entry.rel_path)
                notes[entry.rel_path] = _summary_note(entry)
            else:
                map_dirs.add(entry.rel_path)

    # Forced files always win, even if their folder was hidden by the plan.
    for forced in force_include:
        for item in scan.files:
            if forced in {item.rel_path, item.name}:
                selected.add(item.rel_path)
                map_files.add(item.rel_path)

    selected, newly_blocked = _apply_sensitive_guard(
        files_by_path,
        selected,
        allow_sensitive=allow_sensitive,
        force_include=force_include,
    )
    blocked.update(newly_blocked)

    # Sensitive paths remain useful structural facts, but never leak content by
    # default. This includes ignored root .env files found by the map scan.
    for path in list(map_files):
        record = files_by_path.get(path)
        structure = structure_files.get(path)
        is_sensitive = bool((record and record.is_sensitive) or (structure and structure.is_sensitive))
        if is_sensitive and path not in selected:
            blocked.add(path)
            notes[path] = "HASSAS - varlığı gösterildi, içerik eklenmedi"

    names_only, fitted_tokens = _fit_budget(scan.files, selected, budget)
    for path in names_only:
        notes[path] = "BÜTÇE - yalnızca dosya adı"
    for path in map_files:
        if path in selected and path not in names_only:
            notes.setdefault(path, "İÇERİK")
            continue
        record = files_by_path.get(path)
        if record and record.is_binary:
            notes.setdefault(path, "BINARY - yalnızca dosya adı")
        elif path not in blocked:
            notes.setdefault(path, "yalnızca dosya adı")

    return SelectionResult(
        selected_paths=selected,
        names_only_paths=names_only,
        blocked_sensitive_paths=blocked,
        estimated_tokens=fitted_tokens,
        map_file_paths=map_files,
        map_dir_paths=map_dirs,
        summary_dirs=summary_dirs,
        hidden_dirs=hidden_dirs,
        path_notes=notes,
        folder_modes=folder_modes,
        omitted_map_counts=omitted,
    )


def interactive_select(
    scan: ScanResult,
    *,
    budget: int,
    allow_sensitive: bool,
    force_include: Set[str],
    map_limit: int = 120,
) -> SelectionResult:
    if not sys.stdin.isatty():
        raise RuntimeError("Etkileşimli mod için terminal girdisi gerekiyor.")

    groups = build_folder_groups(scan)
    if not groups:
        return SelectionResult()

    while True:
        _print_folder_summary(scan, groups, budget)
        print("\nEnter = bu planla rapor oluştur | N = klasör/bölüm ayarını değiştir")
        print("all = taranan bütün klasörleri İÇERİK yap | q = çık")
        raw = input("\nSeçiminiz: ").strip().lower()
        if raw in {"q", "quit", "iptal", "exit"}:
            raise KeyboardInterrupt
        if raw in {"", "run", "çalıştır", "calistir"}:
            break
        if raw in {"all", "hepsi"}:
            for group in groups:
                if not group.is_pruned:
                    group.mode = "content"
            continue
        try:
            index = int(raw)
            if not 1 <= index <= len(groups):
                raise ValueError
        except ValueError:
            print(f"Bir klasör numarası (1-{len(groups)}), Enter, all veya q girin.")
            continue
        _edit_group(
            groups[index - 1],
            allow_sensitive=allow_sensitive,
            force_include=force_include,
        )

    selection = _build_selection_from_groups(
        scan,
        groups,
        allow_sensitive=allow_sensitive,
        force_include=force_include,
        budget=0,
        map_limit=max(0, map_limit),
    )

    current_tokens = sum(
        item.estimated_tokens
        for item in scan.files
        if item.rel_path in selection.selected_paths
    )
    if budget > 0 and current_tokens > budget:
        suggested_names_only, fitted_tokens = _fit_budget(scan.files, selection.selected_paths, budget)
        print(f"\nSeçim ~{human_int(current_tokens)} token; bütçe ~{human_int(budget)} token.")
        print(f"Enter = en büyük {len(suggested_names_only)} dosyayı yalnızca isim olarak ekle")
        print("p = bütçeyi aşarak devam et | f = büyük dosyaları içerik seçiminden çıkar")
        while True:
            action = input("Bütçe seçimi: ").strip().lower()
            if action in {"", "n", "name", "isim"}:
                selection.names_only_paths = suggested_names_only
                selection.estimated_tokens = fitted_tokens
                for path in suggested_names_only:
                    selection.path_notes[path] = "BÜTÇE - yalnızca dosya adı"
                break
            if action in {"p", "proceed", "devam"}:
                selection.estimated_tokens = current_tokens
                break
            if action in {"f", "remove", "çıkar", "cikar"}:
                selection.selected_paths.difference_update(suggested_names_only)
                selection.estimated_tokens = fitted_tokens
                for path in suggested_names_only:
                    selection.path_notes[path] = "yalnızca dosya adı"
                break
            print("Enter, p veya f girin.")
    else:
        selection.estimated_tokens = current_tokens

    return selection


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
    notes: Dict[str, str] = {}
    for item in scan.files:
        if item.rel_path not in selected:
            continue
        if item.rel_path in names_only:
            notes[item.rel_path] = "BÜTÇE - yalnızca dosya adı"
        elif item.is_binary:
            notes[item.rel_path] = "BINARY - yalnızca dosya adı"
        else:
            notes[item.rel_path] = "İÇERİK"

    summary_dirs = set(scan.skipped_dirs)
    structure_by_path = {item.rel_path: item for item in scan.structure_entries if item.kind == "dir"}
    for path in summary_dirs:
        entry = structure_by_path.get(path)
        notes[path] = _summary_note(entry) if entry else "ATLANDI - içerik taranmadı"

    return SelectionResult(
        selected_paths=selected,
        names_only_paths=names_only,
        blocked_sensitive_paths=blocked,
        estimated_tokens=fitted_tokens,
        map_file_paths=set(selected),
        summary_dirs=summary_dirs,
        path_notes=notes,
    )
