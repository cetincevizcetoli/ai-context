import argparse
import os
import sys
from typing import Optional, Sequence, Set

from . import VERSION
from .clipboard import copy_to_clipboard
from .config import LEGACY_ALLOWED_EXTS, DEFAULT_IGNORE_FILE_NAMES
from .scanner import scan_project
from .selection import automatic_select, interactive_select
from .report import write_report
from .utils import human_int, normalize_extension, normalize_rel_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-context",
        description=f"ai-context v{VERSION} - projeleri LLM bağlamına dönüştürür",
    )
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Taranacak proje klasörü")

    legacy = parser.add_argument_group("Mevcut / geriye uyumlu seçenekler")
    legacy.add_argument("-c", "--clipboard", action="store_true", help="Sonucu panoya kopyala")
    legacy.add_argument("-tk", "--tokens", action="store_true", help="Tahmini token sayısını göster")
    legacy.add_argument("-to", "--tree-only", action="store_true", help="Yalnızca klasör ağacını çıkar")
    legacy.add_argument("-ms", "--max-size", type=int, default=0, metavar="KB", help="KB sınırını aşan dosyaları atla")
    legacy.add_argument("-i", "--include-ext", nargs="+", default=[], help="Ek uzantıları dahil et")
    legacy.add_argument("-t", "--target", nargs="+", default=[], help="Yalnızca belirli dosya/yolları tara")
    legacy.add_argument("-u", "--unsafe", action="store_true", help="Bilinmeyen metin uzantılarını da içerik olarak al")
    legacy.add_argument("-xd", "--exclude-dir", nargs="+", default=[], help="Klasörleri hariç tut")
    legacy.add_argument("-xf", "--exclude-file", nargs="+", default=[], help="Dosyaları hariç tut")
    legacy.add_argument("-xe", "--exclude-ext", nargs="+", default=[], help="Uzantıları hariç tut")
    legacy.add_argument("-git", "--git-ignore", action="store_true", help="Git görünür dosya listesini ve ignore kurallarını kullan")
    legacy.add_argument("-gf", "--git-force", nargs="+", default=[], help="Belirtilen yolu ignore/güvenlik filtresine rağmen zorla dahil et")

    smart = parser.add_argument_group("v1.5 akıllı proje haritası seçenekleri")
    smart.add_argument("-it", "--interactive", action="store_true", help="Klasör merkezli akıllı proje haritası ve etkileşimli seçim")
    smart.add_argument("--budget", type=int, default=50000, metavar="TOKEN", help="İçerik token bütçesi; 0 sınırsız (varsayılan: 50000)")
    smart.add_argument("--changed-only", action="store_true", help="Yalnızca Git'te değişen/yeni dosyaları al")
    smart.add_argument("--allow-sensitive", action="store_true", help="Hassas dosyaların seçilebilmesine izin ver")
    smart.add_argument("--no-auto-git", action="store_true", help="Interaktif modda otomatik Git hızlandırmasını kapat")
    smart.add_argument("--map-limit", type=int, default=120, metavar="ADET", help="Klasör başına haritada gösterilecek azami dosya adı; 0 sınırsız (varsayılan: 120)")
    smart.add_argument("--output", default="", help="Rapor çıktı klasörü")
    smart.add_argument("--no-open", action="store_true", help="Rapor klasörünü otomatik açma")
    smart.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser


def _normalized_paths(values: Sequence[str]) -> Set[str]:
    return {normalize_rel_path(value) for value in values if value.strip()}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isdir(root):
        parser.error(f"Klasör bulunamadı: {root}")

    include_exts = {normalize_extension(value) for value in args.include_ext}
    exclude_exts = {normalize_extension(value) for value in args.exclude_ext}
    allowed_exts = set(LEGACY_ALLOWED_EXTS) | include_exts
    excluded_dirs = _normalized_paths(args.exclude_dir)
    if args.output:
        output_abs = os.path.abspath(os.path.expanduser(args.output))
        try:
            if os.path.commonpath([root, output_abs]) == root and output_abs != root:
                excluded_dirs.add(normalize_rel_path(os.path.relpath(output_abs, root)))
        except ValueError:
            pass
    excluded_files = set(args.exclude_file) | set(DEFAULT_IGNORE_FILE_NAMES)
    targets = _normalized_paths(args.target)
    force_include = _normalized_paths(args.git_force)

    try:
        scan = scan_project(
            root,
            use_git=args.git_ignore,
            auto_git=args.interactive and not args.no_auto_git,
            changed_only=args.changed_only,
            excluded_dirs=excluded_dirs,
            excluded_files=excluded_files,
            excluded_exts=exclude_exts,
            targets=targets,
            max_size_kb=max(0, args.max_size),
            force_include=force_include,
            smart_map=args.interactive,
        )

        if args.interactive:
            selection = interactive_select(
                scan,
                budget=max(0, args.budget),
                allow_sensitive=args.allow_sensitive,
                force_include=force_include,
                map_limit=max(0, args.map_limit),
            )
        else:
            # Geriye uyum: bütçe yalnızca kullanıcı açıkça --budget yazdıysa uygulanır.
            budget_explicit = argv is not None and "--budget" in argv
            if argv is None:
                budget_explicit = "--budget" in sys.argv[1:]
            automatic_budget = max(0, args.budget) if budget_explicit else 0
            selection = automatic_select(
                scan,
                allowed_exts=allowed_exts,
                unsafe=args.unsafe,
                allow_sensitive=args.allow_sensitive,
                force_include=force_include,
                budget=automatic_budget,
            )

        if not selection.selected_paths and not selection.map_file_paths and not selection.summary_dirs:
            print("Seçime uyan dosya veya proje haritası öğesi bulunamadı.")
            if selection.blocked_sensitive_paths:
                print(f"{len(selection.blocked_sensitive_paths)} hassas dosya güvenlik nedeniyle engellendi.")
            return 1

        filename, report_text, summary = write_report(
            scan,
            selection,
            tree_only=args.tree_only,
            output_dir=args.output,
            open_output=not args.no_open,
        )

        print(f"\nRapor kaydedildi: {filename}")
        print(f"Tarayıcı: {summary.scanner_name} | Harita: {summary.map_file_count} | Seçilen: {summary.file_count} | İçerik: {summary.content_count}")
        if summary.binary_count:
            print(f"Binary: {summary.binary_count}")
        if summary.names_only_count:
            print(f"Bütçe nedeniyle yalnızca isim: {summary.names_only_count}")
        if args.tokens or args.interactive:
            print(f"Tahmini bağlam: ~{human_int(summary.estimated_tokens)} token")
        if selection.blocked_sensitive_paths:
            print(f"Güvenlik: {len(selection.blocked_sensitive_paths)} hassas dosya engellendi")
        for warning in summary.warnings:
            print(f"Uyarı: {warning}")

        if args.clipboard:
            if copy_to_clipboard(report_text):
                print("Sonuç panoya kopyalandı.")
            else:
                print("Pano kopyalama kullanılamadı.")
        return 0
    except KeyboardInterrupt:
        print("\nİşlem iptal edildi.")
        return 130
    except RuntimeError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Dosya sistemi hatası: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
