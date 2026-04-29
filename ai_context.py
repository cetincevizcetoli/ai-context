#!/usr/bin/env python3
import os
import argparse
import sys
import subprocess
import platform
import io
import locale
import fnmatch
from datetime import datetime

# Versiyon Güncellendi
VERSION = "1.3.2"

# Windows terminalinde emojilerin düzgün görünmesi için UTF-8 zorlaması
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
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
    """Güvenli ve shell=False kullanarak panoya kopyalama yapar."""
    try:
        sys_type = platform.system()
        if sys_type == "Windows":
            process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=False)
            process.communicate(input=text.encode('utf-16'))
        elif sys_type == "Darwin": # macOS
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, shell=False)
            process.communicate(input=text.encode('utf-8'))
        else: # Linux
            for cmd in ['xclip', 'xsel', 'wl-copy']:
                if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                    c = [cmd, "-selection", "clipboard"] if cmd == 'xclip' else [cmd, "-ib"] if cmd == 'xsel' else [cmd]
                    process = subprocess.Popen(c, stdin=subprocess.PIPE, shell=False)
                    process.communicate(input=text.encode('utf-8'))
                    return True
        return True
    except Exception:
        return False

def get_gitignore_rules(root_path):
    """.gitignore dosyasını okur ve basit kuralları döndürür."""
    rules = []
    gitignore_path = os.path.join(root_path, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        rules.append(line)
        except Exception:
            pass
    return rules

def build_tree(files, skipped_dirs):
    tree = {}
    
    # İşlenecek dosyaları ağaca ekle
    for rel in files:
        parts = rel.split("/")
        cur = tree
        for i, p in enumerate(parts):
            if i == len(parts) - 1:
                cur.setdefault("__files__", []).append(p)
            else:
                cur = cur.setdefault(p, {})
                
    # Atlanan klasörleri ağaca boş düğüm olarak ekle
    for rel_dir in skipped_dirs:
        if rel_dir == ".": continue
        parts = rel_dir.split("/")
        cur = tree
        for p in parts:
            cur = cur.setdefault(p, {})
        cur["__excluded__"] = True
        
    return tree

def generate_tree_text(node, prefix=""):
    lines = []
    files = sorted(node.get("__files__", []))
    dirs = sorted(k for k in node.keys() if k not in ["__files__", "__excluded__"])
    
    for d in dirs:
        child_node = node[d]
        has_children = len([k for k in child_node.keys() if k not in ["__files__", "__excluded__"]]) > 0
        has_files = len(child_node.get("__files__", [])) > 0
        is_excluded = child_node.get("__excluded__", False)
        
        tag = " [ATLANDI]" if (is_excluded and not has_children and not has_files) else ""
        
        lines.append(f"{prefix}├── 📁 {d}/{tag}")
        
        if has_children or has_files:
            lines.append(generate_tree_text(child_node, prefix + "│   "))

    for i, fn in enumerate(files):
        char = "└──" if i == len(files) - 1 else "├──"
        lines.append(f"{prefix}{char} 📄 {fn}")
    
    return "\n".join(lines)

def write_report(root_path, files, skipped_dirs, clipboard=False, show_tokens=False, tree_only=False):
    report_parts = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    f_prefix = "TREE_ONLY" if tree_only else "AI_CONTEXT"
    
    report_parts.append(f"# 📜 PROJE {'YAPISI' if tree_only else 'DOKÜMÜ'} ({ts})\n")
    report_parts.append(f"**Dizin:** `{root_path}` | **Dosya Sayısı:** {len(files)}\n\n")
    report_parts.append("## 📂 YAPISAL ÖZET\n```text\n")
    
    tree_dict = build_tree(files, skipped_dirs)
    report_parts.append(generate_tree_text(tree_dict))
    report_parts.append("\n```\n\n---\n")

    if not tree_only:
        for rel_path in files:
            full_path = os.path.join(root_path, rel_path)
            ext = os.path.splitext(rel_path)[1].lower().replace('.','') or "text"
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                report_parts.append(f"\n### 📄 `{rel_path}`\n```{ext}\n{content}\n```\n")
            except Exception:
                continue

    report_text = "".join(report_parts)
    
    # Yerelleştirme ve Kayıt Dizini Ayarı
    home = os.path.expanduser("~")
    possible_desktops = ["Desktop", "Masaüstü", "Schreibtisch", "Escritorio", "Bureau"]
    out_dir = None
    for d in possible_desktops:
        p = os.path.join(home, d, "ai-reports")
        if os.path.exists(os.path.join(home, d)):
            out_dir = p
            break
    
    if not out_dir:
        out_dir = os.path.join(home, "ai-reports")

    try:
        os.makedirs(out_dir, exist_ok=True)
        filename = os.path.join(out_dir, f"{f_prefix}_{datetime.now().strftime('%H%M%S')}.md")
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(report_text)
        
        if platform.system() == "Windows":
            os.startfile(out_dir)
            
        print(f"📄 Rapor kaydedildi: {filename}")
    except Exception as e:
        print(f"⚠️ Dosya yazılamadı: {e}")

    if show_tokens:
        print(f"📊 Tahmini Bağlam: ~{len(report_text)//4} Token")
    
    if clipboard:
        if copy_to_clipboard(report_text):
            print("✅ Sonuç panoya kopyalandı.")
    
    print(f"✅ Toplam {len(files)} dosya başarıyla işlendi.")

def main():
    parser = argparse.ArgumentParser(
        description=f"ai-context v{VERSION}",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Taranacak dizin yolu")
    parser.add_argument("-t", "--target", nargs="+", help="Sadece belirli dosyaları tara")
    parser.add_argument("-i", "--include-ext", nargs="+", default=[], help="Ekstra uzantı ekle (Örn: log cfg)")
    parser.add_argument("-xd", "--exclude-dir", nargs="+", default=[], help="Dizinleri hariç tut")
    parser.add_argument("-xf", "--exclude-file", nargs="+", default=[], help="Dosyaları hariç tut")
    parser.add_argument("-xe", "--exclude-ext", nargs="+", default=[], help="Uzantıları hariç tut")
    parser.add_argument("-u", "--unsafe", action="store_true", help="Tüm metin dosyalarını oku")
    parser.add_argument("-c", "--clipboard", action="store_true", help="Panoya kopyala")
    parser.add_argument("-tk", "--tokens", action="store_true", help="Token sayısını göster")
    parser.add_argument("-to", "--tree-only", action="store_true", help="Sadece klasör yapısı")
    parser.add_argument("-ms", "--max-size", type=int, help="Maksimum dosya boyutu (KB)")
    parser.add_argument("-git", "--git-ignore", action="store_true", help=".gitignore kurallarını uygula")
    parser.add_argument("-gf", "--git-force", nargs="+", default=[], help="Git yoksaysa bile zorla dahil et")

    args = parser.parse_args()

    root = os.path.abspath(args.path)
    exclude_dirs = DEFAULT_IGNORE_DIRS.union(set(args.exclude_dir))
    exclude_files = DEFAULT_IGNORE_FILES.union(set(args.exclude_file))
    exclude_exts = {f".{e.lstrip('.')}" for e in args.exclude_ext}
    
    git_rules = get_gitignore_rules(root) if args.git_ignore else []
    force_include = set(args.git_force)

    extra_exts = {f".{e.lstrip('.')}" for e in args.include_ext}
    effective_allowed = ALLOWED_EXTS.union(extra_exts)
    
    found_files = []
    skipped_dirs = set()

    for r, dirs, files in os.walk(root):
        rel_r = os.path.relpath(r, root).replace("\\", "/")
        
        # 1. Klasör filtreleme ve atlananları kaydetme
        for d in list(dirs):
            full_dir = os.path.join(r, d)
            rel_dir = os.path.relpath(full_dir, root).replace("\\", "/")

            is_excluded = d.startswith(".") or d in exclude_dirs

            if args.git_ignore and not is_excluded:
                for pattern in git_rules:
                    clean_pattern = pattern.rstrip('/')
                    if fnmatch.fnmatch(rel_dir, pattern) or fnmatch.fnmatch(d, pattern):
                        is_excluded = True; break
                    if rel_dir.startswith(clean_pattern + '/'):
                        is_excluded = True; break
                    if '/' not in clean_pattern and f"/{clean_pattern}/" in f"/{rel_dir}":
                        is_excluded = True; break

            if is_excluded:
                skipped_dirs.add(rel_dir)
                dirs.remove(d) # İçine girmeyi engelle

        # 2. Dosya filtreleme
        dir_has_valid_files = False
        for f in files:
            full_path = os.path.join(r, f)
            rel_path = os.path.relpath(full_path, root).replace("\\", "/")
            ext = os.path.splitext(f)[1].lower()

            try:
                if args.max_size and (os.path.getsize(full_path) / 1024) > args.max_size:
                    continue
            except OSError: continue

            is_git_ignored = False
