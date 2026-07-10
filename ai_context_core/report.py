import io
import os
import platform
from datetime import datetime
from typing import Dict, List, Sequence, Tuple

from .models import FileRecord, RunSummary, ScanResult, SelectionResult
from .utils import human_int, human_size


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


def _build_tree(paths: Sequence[str]) -> Dict[str, dict]:
    tree: Dict[str, dict] = {}
    for rel_path in sorted(paths):
        parts = rel_path.split("/")
        cursor = tree
        for index, part in enumerate(parts):
            if index == len(parts) - 1:
                cursor.setdefault("__files__", []).append(part)
            else:
                cursor = cursor.setdefault(part, {})
    return tree


def _render_tree(node: Dict[str, dict], prefix: str = "") -> List[str]:
    lines: List[str] = []
    dirs = sorted(key for key in node if key != "__files__")
    files = sorted(node.get("__files__", []))
    entries: List[Tuple[str, str]] = [("dir", item) for item in dirs] + [("file", item) for item in files]
    for index, (kind, name) in enumerate(entries):
        last = index == len(entries) - 1
        connector = "└── " if last else "├── "
        lines.append(prefix + connector + name + ("/" if kind == "dir" else ""))
        if kind == "dir":
            extension = "    " if last else "│   "
            lines.extend(_render_tree(node[name], prefix + extension))
    return lines


def _fence_language(record: FileRecord) -> str:
    if record.extension:
        return record.extension.lstrip(".").replace("dockerfile", "dockerfile").replace("makefile", "makefile")
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
    report.write(f"- **Seçilen dosya:** {len(selected_records)}\n")
    report.write(f"- **Tahmini içerik:** ~{human_int(selection.estimated_tokens)} token\n\n")

    if selection.blocked_sensitive_paths:
        report.write(
            f"> Güvenlik notu: {len(selection.blocked_sensitive_paths)} hassas dosya içerikten çıkarıldı.\n\n"
        )

    report.write("## YAPISAL ÖZET\n\n```text\n")
    tree_lines = _render_tree(_build_tree([item.rel_path for item in selected_records]))
    report.write("\n".join(tree_lines) if tree_lines else "[Seçilen dosya yok]")
    report.write("\n```\n\n---\n")

    if not tree_only:
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
        estimated_tokens=selection.estimated_tokens,
        scanner_name=scan.scanner_name,
        project_types=scan.project_types,
        warnings=scan.warnings,
    )
    return filename, report_text, summary
