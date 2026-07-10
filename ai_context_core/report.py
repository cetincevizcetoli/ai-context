import io
import os
import platform
from datetime import datetime
from typing import Dict, List, Sequence, Set, Tuple

from .models import FileRecord, RunSummary, ScanResult, SelectionResult
from .utils import human_int, human_size, is_subpath_of


def get_output_dir(explicit_output: str = "") -> str:
    if explicit_output:
        target = os.path.abspath(os.path.expanduser(explicit_output))
        os.makedirs(target, exist_ok=True)
        return target

    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "OneDrive", "Masaüstü"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "Masaüstü"),
        os.path.join(home, "Desktop"),
    ]
    for candidate in candidates:
        if os.path.isdir(candidate):
            target = os.path.join(candidate, "ai-reports")
            os.makedirs(target, exist_ok=True)
            return target
    target = os.path.join(home, "ai-reports")
    os.makedirs(target, exist_ok=True)
    return target


def _is_under_any(path: str, parents: Set[str], *, include_self: bool = True) -> bool:
    for parent in parents:
        if path == parent:
            if include_self:
                return True
            continue
        if is_subpath_of(path, parent):
            return True
    return False


def _build_tree(
    file_paths: Sequence[str],
    dir_paths: Sequence[str],
    summary_dirs: Set[str],
    hidden_dirs: Set[str],
) -> Dict[str, dict]:
    tree: Dict[str, dict] = {}

    def add_dir(rel_path: str) -> None:
        if not rel_path or _is_under_any(rel_path, hidden_dirs):
            return
        if _is_under_any(rel_path, summary_dirs, include_self=False):
            return
        cursor = tree
        for part in rel_path.split("/"):
            cursor = cursor.setdefault(part, {})

    def add_file(rel_path: str) -> None:
        if not rel_path or _is_under_any(rel_path, hidden_dirs):
            return
        if _is_under_any(rel_path, summary_dirs, include_self=True):
            return
        parts = rel_path.split("/")
        cursor = tree
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor.setdefault("__files__", []).append((parts[-1], rel_path))

    for rel_path in sorted(set(dir_paths).union(summary_dirs)):
        add_dir(rel_path)
    for rel_path in sorted(set(file_paths)):
        add_file(rel_path)
    return tree


def _render_tree(
    node: Dict[str, dict],
    *,
    notes: Dict[str, str],
    omitted_counts: Dict[str, int],
    prefix: str = "",
    parent_path: str = "",
) -> List[str]:
    lines: List[str] = []
    dirs = sorted(key for key in node if key != "__files__")
    files = sorted(node.get("__files__", []), key=lambda item: item[0].lower())
    entries: List[Tuple[str, object]] = [("dir", item) for item in dirs] + [("file", item) for item in files]

    for index, (kind, value) in enumerate(entries):
        last = index == len(entries) - 1
        connector = "└── " if last else "├── "
        extension = "    " if last else "│   "

        if kind == "dir":
            name = str(value)
            rel_path = f"{parent_path}/{name}".strip("/")
            annotations: List[str] = []
            if rel_path in notes:
                annotations.append(notes[rel_path])
            if rel_path in omitted_counts:
                annotations.append(f"{omitted_counts[rel_path]} dosya adı daha listelenmedi")
            suffix = f" [{' | '.join(annotations)}]" if annotations else ""
            lines.append(prefix + connector + name + "/" + suffix)
            lines.extend(
                _render_tree(
                    node[name],
                    notes=notes,
                    omitted_counts=omitted_counts,
                    prefix=prefix + extension,
                    parent_path=rel_path,
                )
            )
        else:
            name, rel_path = value  # type: ignore[misc]
            note = notes.get(rel_path, "")
            suffix = f" [{note}]" if note else ""
            lines.append(prefix + connector + name + suffix)
    return lines


def _fence_language(record: FileRecord) -> str:
    if record.extension:
        return record.extension.lstrip(".")
    return "text"


def _markdown_fence(content: str) -> str:
    longest = 0
    current = 0
    for char in content:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return "`" * max(3, longest + 1)


def _looks_binary_during_read(path: str) -> bool:
    try:
        with open(path, "rb") as handle:
            chunk = handle.read(4096)
        return b"\x00" in chunk
    except OSError:
        return False


def build_report_text(
    scan: ScanResult,
    selection: SelectionResult,
    *,
    tree_only: bool,
) -> Tuple[str, int, int, int]:
    selected_records = [item for item in scan.files if item.rel_path in selection.selected_paths]
    selected_records.sort(key=lambda item: item.rel_path.lower())

    content_count = 0
    binary_count = 0
    names_only_count = 0
    report = io.StringIO()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    report.write(f"# PROJE DOKÜMÜ ({timestamp})\n\n")
    report.write(f"- **Dizin:** `{scan.root_path}`\n")
    report.write(f"- **Proje türü:** {', '.join(scan.project_types)}\n")
    report.write(f"- **Tarayıcı:** {scan.scanner_name}\n")
    report.write(f"- **Haritada görünen dosya:** {len(selection.map_file_paths)}\n")
    report.write(f"- **İçerik için seçilen dosya:** {len(selected_records)}\n")
    report.write(f"- **Tahmini içerik:** ~{human_int(selection.estimated_tokens)} token\n\n")

    if selection.folder_modes:
        report.write("### Klasör davranışları\n\n")
        for key, mode in sorted(selection.folder_modes.items(), key=lambda item: item[0].lower()):
            label = "Kök dosyalar" if key == "__root__" else key + "/"
            report.write(f"- `{label}`: **{mode.upper()}**\n")
        report.write("\n")

    if selection.blocked_sensitive_paths:
        report.write(
            f"> Güvenlik notu: {len(selection.blocked_sensitive_paths)} hassas dosyanın yalnızca varlığı gösterildi; içerikleri eklenmedi.\n\n"
        )

    report.write("## PROJE HARİTASI\n\n```text\n")
    tree = _build_tree(
        sorted(selection.map_file_paths),
        sorted(selection.map_dir_paths),
        selection.summary_dirs,
        selection.hidden_dirs,
    )
    tree_lines = _render_tree(
        tree,
        notes=selection.path_notes,
        omitted_counts=selection.omitted_map_counts,
    )
    if "__root__" in selection.omitted_map_counts:
        tree_lines.append(f"... [{selection.omitted_map_counts['__root__']} kök dosya adı daha listelenmedi]")
    report.write("\n".join(tree_lines) if tree_lines else "[Haritada gösterilecek öğe yok]")
    report.write("\n```\n\n---\n")

    if not tree_only:
        report.write("\n## DOSYA İÇERİKLERİ\n")
        for record in selected_records:
            report.write(f"\n### `{record.rel_path}`\n\n")
            if record.rel_path in selection.names_only_paths:
                names_only_count += 1
                report.write(
                    f"```text\n[BÜTÇE KORUMASI - içerik eklenmedi, boyut: {human_size(record.size_bytes)}]\n```\n"
                )
                continue
            if record.is_binary or _looks_binary_during_read(record.abs_path):
                binary_count += 1
                report.write("```text\n[BINARY DOSYA - içerik okunmadı]\n```\n")
                continue
            try:
                with open(record.abs_path, "r", encoding="utf-8", errors="replace") as handle:
                    content = handle.read()
                content_count += 1
                fence = _markdown_fence(content)
                report.write(f"{fence}{_fence_language(record)}\n{content}\n{fence}\n")
            except OSError as exc:
                report.write(f"```text\n[OKUNAMADI - {exc}]\n```\n")

    return report.getvalue(), content_count, binary_count, names_only_count


def write_report(
    scan: ScanResult,
    selection: SelectionResult,
    *,
    tree_only: bool,
    output_dir: str,
    open_output: bool,
) -> Tuple[str, str, RunSummary]:
    report_text, content_count, binary_count, names_only_count = build_report_text(
        scan, selection, tree_only=tree_only
    )
    out_dir = get_output_dir(output_dir)
    filename = os.path.join(out_dir, f"AI_CONTEXT_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.md")
    with open(filename, "w", encoding="utf-8-sig", newline="\n") as handle:
        handle.write(report_text)

    if open_output:
        try:
            if platform.system() == "Windows":
                os.startfile(out_dir)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.Popen(["open", out_dir])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", out_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    summary = RunSummary(
        report_path=filename,
        file_count=len(selection.selected_paths),
        content_count=content_count,
        binary_count=binary_count,
        names_only_count=names_only_count,
        map_file_count=len(selection.map_file_paths),
        estimated_tokens=selection.estimated_tokens,
        scanner_name=scan.scanner_name,
        project_types=scan.project_types,
        warnings=scan.warnings,
    )
    return filename, report_text, summary
