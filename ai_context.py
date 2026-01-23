#!/usr/bin/env python3
import os
import argparse
import sys
import subprocess
import platform
import io
import locale
from datetime import datetime

# Versiyon Güncellendi
VERSION = "1.2.0"

# Windows terminalinde emojilerin düzgün görünmesi için UTF-8 zorlaması
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# --- YAPILANDIRMA ---
KNOWN_BINARY_EXTENSIONS = {
    ".zip", ".7z", ".tar", ".gz", ".rar", ".bz2", ".xz", ".iso", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg", ".webp", ".tiff",
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".pdf", ".exe", ".dll", ".so", 
    ".pyc", ".class", ".dat", ".db", ".sqlite", ".sqlite3"
}

DEFAULT_IGNORE_DIRS = {
    ".git", "venv", ".venv", "node_modules", "__pycache__", "vendor", 
    "tmp", "dist", "build", ".idea", ".vscode", "reports"
}

DEFAULT_IGNORE_FILES = {
    ".DS_Store", "thumbs.db", "composer.lock", "package-lock.json", "yarn.lock"
}

ALLOWED_EXTS = {
    ".py", ".php", ".js", ".ts", ".html", ".css", ".sql", ".md", ".txt", 
    ".json", ".yaml", ".yml", ".htaccess", ".env", ".tsx", ".jsx", ".vue", 
    ".ini", ".conf", ".sh", ".log"
}

def copy_to_clipboard(text):
    try:
        sys_type = platform.system()
        if sys_type == "Windows":
            process = subprocess.Popen('clip', stdin=subprocess.PIPE, shell=True)
            process.communicate(input=text.encode('utf-16'))
        else:
            for cmd in ['xclip -selection clipboard', 'xsel -ib', 'wl-copy', 'pbcopy']:
                if subprocess.run(f"which {cmd.split()[0]}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
                    process.communicate(input=text.encode('utf-8'))
                    return True
        return True
    except: return False

def build_tree(root_path, files, all_dirs):
    tree = {}
    for rel in files:
        parts = rel.split("/")
        cur = tree
        for i, p in enumerate(parts):
            if i == len(parts) - 1:
                cur.setdefault("__files__", []).append(p)
            else:
                cur = cur.setdefault(p, {})
    for d in all_dirs:
        if os.path.isdir(os.path.join(root_path, d)) and d not in tree:
            tree[d] = {"__excluded__": True}
    return tree

def generate_tree_text(node, prefix=""):
    output = ""
    files = sorted(node.get("__files__", []))
    dirs = sorted(k for k in node.keys() if k not in ["__files__", "__excluded__"])
    for i, d in enumerate(dirs):
        output += f"{prefix}├── 📁 {d}/\n"
        output += generate_tree_text(node[d], prefix + "│   ")
    if node.get("__excluded__"):
        output = output.replace("/", "/ (excluded)")
    for i, fn in enumerate(files):
        char = "└──" if i == len(files) - 1 and len(dirs) == 0 else "├──"
        output += f"{prefix}{char} 📄 {fn}\n"
    return output

def write_report(root_path, files, ignored_dirs, clipboard=False, show_tokens=False, tree_only=False):
    output = io.StringIO()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    f_prefix = "TREE_ONLY" if tree_only else "AI_CONTEXT"
    output.write(f"# 📜 PROJE {'YAPISI' if tree_only else 'DOKÜMÜ'} ({ts})\n")
    output.write(f"**Dizin:** `{root_path}` | **Dosya Sayısı:** {len(files)}\n\n")
    
    output.write("## 📂 YAPISAL ÖZET\n```text\n")
    tree_dict = build_tree(root_path, files, ignored_dirs)
    output.write(generate_tree_text(tree_dict))
    output.write("```\n\n---\n")

    if not tree_only:
        for rel_path in files:
            full_path = os.path.join(root_path, rel_path)
            ext = os.path.splitext(rel_path)[1].lower().replace('.','') or "text"
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                output.write(f"\n### 📄 `{rel_path}`\n```{ext}\n{content}\n```\n")
            except: continue

    report_text = output.getvalue()
    
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    out_dir = os.path.join(desktop, "ai-reports")
    
    try:
        os.makedirs(out_dir, exist_ok=True)
    except:
        out_dir = os.path.join(os.path.expanduser("~"), "ai-context-reports")
        os.makedirs(out_dir, exist_ok=True)

    filename = os.path.join(out_dir, f"{f_prefix}_{datetime.now().strftime('%H%M%S')}.md")
    
    with open(filename, "w", encoding="utf-8-sig") as f:
        f.write(report_text)

    if show_tokens:
        print(f"📊 Tahmini Bağlam: ~{len(report_text)//4} Token")
    if clipboard:
        if copy_to_clipboard(report_text): print("✅ Sonuç panoya kopyalandı.")
    
    print(f"📄 Rapor kaydedildi: {filename}")
    print(f"✅ Toplam {len(files)} dosya başarıyla işlendi.")

def main():
    for arg in sys.argv:
        if arg.startswith('--') and arg not in ['--help']:
            print(f"⚠️ HATA: Geçersiz argüman formatı '{arg}'. Lütfen tek tire '-' kullanın.")
            sys.exit(1)

    parser = argparse.ArgumentParser(description=f"ai-context v{VERSION}", prefix_chars='-', add_help=False)
    
    parser.add_argument("-h", "-help", action="store_true", dest="help")
    parser.add_argument("path", nargs="?", default=os.getcwd())
    parser.add_argument("-t", "-target", nargs="+", dest="target")
    parser.add_argument("-i", "-include-ext", nargs="+", default=[], dest="include_ext")
    parser.add_argument("-xd", "-exclude-dir", nargs="+", default=[], dest="exclude_dir")
    parser.add_argument("-xf", "-exclude-file", nargs="+", default=[], dest="exclude_file")
    parser.add_argument("-xe", "-exclude-ext", nargs="+", default=[], dest="exclude_ext")
    parser.add_argument("-u", "-unsafe", action="store_true", dest="unsafe")
    parser.add_argument("-c", "-clipboard", action="store_true", dest="clipboard")
    parser.add_argument("-tk", "-tokens", action="store_true", dest="tokens")
    parser.add_argument("-to", "-tree-only", action="store_true", dest="tree_only")
    # Yeni Özellik: Max Size
    parser.add_argument("-ms", "-max-size", type=int, default=None, dest="max_size")

    args = parser.parse_args()

    if args.help:
        try: sys_lang = locale.getdefaultlocale()[0]
        except: sys_lang = "en"
        is_tr = sys_lang and sys_lang.startswith("tr")
        if is_tr:
            print(f"\n🚀 ai-context v{VERSION} | Yardım Menüsü")
            print("-" * 55)
            print("Kullanım: ai-context [yol] [seçenekler]")
            print("\nTemel Seçenekler:")
            print("  -ms [kb]         Belirlenen KB'dan büyük dosyaları atla")
            print("  -i [uzantı...]   Listede olmayan uzantıları ekle (Örn: -i log cfg)")
            print("  -t [dosya...]    Sadece belirli dosyaları tara")
            print("  -to              Sadece klasör yapısını çıkar (içerik okumaz)")
            print("  -c               Sonucu panoya kopyala")
            print("  -tk              Tahmini token sayısını göster")
            print("  -u               Güvenli listeyi bypass et (Tüm metinleri oku)")
            print("\nFiltreleme Seçenekleri:")
            print("  -xd [klasör...]  Belirli klasörleri hariç tut")
            print("  -xf [dosya...]   Belirli dosyaları hariç tut")
            print("  -xe [uzantı...]  Belirli uzantıları hariç tut")
            print("\nDiğer:")
            print("  -h               Bu yardım menüsünü gösterir")
        else:
            print(f"\n🚀 ai-context v{VERSION} | Help Menu")
            print("-" * 55)
            print("Usage: ai-context [path] [options]")
            print("\nCore Options:")
            print("  -ms [kb]         Skip files larger than KB")
            print("  -i [ext...]      Include extra extensions (e.g., -i log cfg)")
            print("  -t [file...]     Target specific files only")
            print("  -to              Tree-only mode (no content)")
            print("  -c               Copy output to clipboard")
            print("  -tk              Show estimated token count")
            print("  -u               Unsafe mode (Read all text files)")
            print("\nFiltering Options:")
            print("  -xd [dir...]     Exclude specific directories")
            print("  -xf [file...]    Exclude specific files")
            print("  -xe [ext...]     Exclude specific extensions")
            print("\nOther:")
            print("  -h               Show this help menu")
        print("-" * 55)
        return

    root = os.path.abspath(args.path)
    exclude_dirs = DEFAULT_IGNORE_DIRS.union(set(args.exclude_dir))
    exclude_files = DEFAULT_IGNORE_FILES.union(set(args.exclude_file))
    exclude_exts = set(args.exclude_ext)
    
    extra_exts = {f".{e.strip('.')}" for e in args.include_ext}
    effective_allowed = ALLOWED_EXTS.union(extra_exts)
    
    found_files = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in exclude_dirs]
        for f in files:
            full_path = os.path.join(r, f)
            # DOSYA BOYUTU KONTROLÜ
            try:
                file_size_kb = os.path.getsize(full_path) / 1024
                if args.max_size and file_size_kb > args.max_size:
                    continue
            except OSError:
                continue

            rel_path = os.path.relpath(full_path, root).replace("\\", "/")
            ext = os.path.splitext(f)[1].lower()
            if args.target and f not in args.target: continue
            if f in exclude_files or ext in exclude_exts: continue
            if not args.tree_only and not args.unsafe and ext not in effective_allowed: continue
            if ext in KNOWN_BINARY_EXTENSIONS: continue
            found_files.append(rel_path)

    write_report(root, sorted(found_files), exclude_dirs, args.clipboard, args.tokens, args.tree_only)

if __name__ == "__main__":
    main()