#!/usr/bin/env python3
import os
import argparse
import sys
import subprocess
import platform
import io
import fnmatch
from datetime import datetime

VERSION = "1.3.4"

# --- YAPILANDIRMA ---
# Log dizinleri senin önerin üzerine varsayılana eklendi
DEFAULT_IGNORE_DIRS = {
    ".git", "venv", ".venv", "node_modules", "__pycache__", "vendor", 
    "tmp", "dist", "build", ".idea", ".vscode", "reports", "log", "logs"
}

KNOWN_BINARY_EXTENSIONS = {
    ".zip", ".7z", ".tar", ".gz", ".rar", ".bz2", ".xz", ".iso", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg", ".webp", ".tiff",
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".pdf", ".exe", ".dll", ".so", 
    ".pyc", ".class", ".dat", ".db", ".sqlite", ".sqlite3"
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
            process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=False)
            process.communicate(input=text.encode('utf-16'))
        elif sys_type == "Darwin": 
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, shell=False)
            process.communicate(input=text.encode('utf-8'))
        else: 
            for cmd in ['xclip', 'xsel', 'wl-copy']:
                if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                    c = [cmd, "-selection", "clipboard"] if cmd == 'xclip' else [cmd, "-ib"] if cmd == 'xsel' else [cmd]
                    process = subprocess.Popen(c, stdin=subprocess.PIPE, shell=False)
                    process.communicate(input=text.encode('utf-8'))
                    return True
        return True
    except Exception: return False

def get_gitignore_rules(root_path):
    rules = []
    gitignore_path = os.path.join(root_path, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        rules.append(line)
        except Exception: pass
    return rules

def get_output_dir():
    home = os.path.expanduser("~")
    candidates = [os.path.join(home, "OneDrive", "Masaüstü"), os.path.join(home, "OneDrive", "Desktop"), 
                  os.path.join(home, "Masaüstü"), os.path.join(home, "Desktop")]
    for p in candidates:
        if os.path.exists(p):
            final = os.path.join(p, "ai-reports")
            os.makedirs(final, exist_ok=True)
            return final
    final = os.path.join(home, "ai-reports")
    os.makedirs(final, exist_ok=True)
    return final

def build_tree(files, skipped_dirs):
    tree = {}
    for rel_dir in sorted(skipped_dirs, key=len):
        parts = rel_dir.split("/")
        cur = tree
        stop = False
        for p in parts:
            if cur.get("__skipped__"):
                stop = True; break
            cur = cur.setdefault(p, {})
        if not stop: cur["__skipped__"] = True

    for rel in files:
        parts = rel.split("/")
        cur = tree
        path_ok = True
        for i, p in enumerate(parts):
            if cur.get("__skipped__"):
                path_ok = False; break
            if i == len(parts) - 1:
                cur.setdefault("__files__", []).append(p)
            else:
                cur = cur.setdefault(p, {})
        if not path_ok: continue
    return tree

def generate_tree_text(node, prefix=""):
    lines = []
    files = sorted(node.get("__files__", []))
    dirs = sorted(k for k in node.keys() if k not in ["__files__", "__skipped__"])
    for d in dirs:
        child = node[d]
        if child.get("__skipped__"):
            lines.append(f"{prefix}├── 📁 {d}/ [ATLANDI]")
            continue
        lines.append(f"{prefix}├── 📁 {d}/")
        lines.append(generate_tree_text(child, prefix + "│   "))
    for i, fn in enumerate(files):
        char = "└──" if i == len(files) - 1 and not dirs else "├──"
        lines.append(f"{prefix}{char} 📄 {fn}")
    return "\n".join(lines)

def write_report(root_path, files, skipped_dirs, args):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = io.StringIO()
    report.write(f"# 📜 PROJE DOKÜMÜ ({ts})\n")
    report.write(f"**Dizin:** `{root_path}` | **Dosya Sayısı:** {len(files)}\n\n")
    report.write("## 📂 YAPISAL ÖZET\n```text\n")
    report.write(generate_tree_text(build_tree(files, skipped_dirs)))
    report.write("\n```\n\n---\n")

    if not args.tree_only:
        for rel_path in files:
            full_path = os.path.join(root_path, rel_path)
            ext = os.path.splitext(rel_path)[1].lower().replace('.','') or "text"
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                report.write(f"\n### 📄 `{rel_path}`\n```{ext}\n{content}\n```\n")
            except Exception: continue

    report_text = report.getvalue()
    out_dir = get_output_dir()
    try:
        filename = os.path.join(out_dir, f"AI_CONTEXT_{datetime.now().strftime('%H%M%S')}.md")
        with open(filename, "w", encoding="utf-8-sig") as f: f.write(report_text)
        if platform.system() == "Windows": os.startfile(out_dir)
        print(f"Rapor kaydedildi: {filename}")
    except Exception as e: print(f"Hata: {e}")
    if args.tokens: print(f"Tahmini Baglam: ~{len(report_text)//4} Token")
    if args.clipboard and copy_to_clipboard(report_text): print("Sonuc panoya kopyalandi.")

def main():
    parser = argparse.ArgumentParser(description=f"ai-context v{VERSION}")
    parser.add_argument("path", nargs="?", default=os.getcwd())
    parser.add_argument("-c", "--clipboard", action="store_true")
    parser.add_argument("-tk", "--tokens", action="store_true")
    parser.add_argument("-to", "--tree-only", action="store_true")
    parser.add_argument("-git", "--git-ignore", action="store_true")
    parser.add_argument("-gf", "--git-force", nargs="+", default=[])
    parser.add_argument("-ms", "--max-size", type=int)

    args, unknown = parser.parse_known_args()
    root = os.path.abspath(args.path)
    git_rules = get_gitignore_rules(root) if args.git_ignore else []
    force_include = set(args.git_force)
    
    found_files = []
    skipped_dirs = set()

    for r, dirs, files in os.walk(root):
        rel_r = os.path.relpath(r, root).replace("\\", "/")
        # lstrip("./") kaldırıldı, root dizini eşleşmesi normalize edildi.
        if rel_r == ".": rel_r = "" 

        # Üst dizin kontrolü: rstrip('/') ile tam yol güvenliği sağlandı.
        if any(rel_r == sd or rel_r.startswith(sd + "/") for sd in skipped_dirs):
            dirs[:] = []; continue

        for d in list(dirs):
            rel_dir = os.path.join(rel_r, d).replace("\\", "/").strip("/")
            is_ex = d in DEFAULT_IGNORE_DIRS or d.startswith(".")
            
            if args.git_ignore and not is_ex:
                for pattern in git_rules:
                    p = pattern.rstrip('/')
                    if fnmatch.fnmatch(rel_dir, p) or fnmatch.fnmatch(d, p) or rel_dir.startswith(p + '/'):
                        is_ex = True; break
            
            if is_ex:
                skipped_dirs.add(rel_dir); dirs.remove(d)

        for f in files:
            full_p = os.path.join(r, f)
            rel_p = os.path.relpath(full_p, root).replace("\\", "/").lstrip("./")
            ext = os.path.splitext(f)[1].lower()
            
            # Üst dizinlerden biri skipped_dirs içindeyse dosyayı kesinlikle atla.
            if any(rel_p.startswith(sd + "/") for sd in skipped_dirs): continue

            is_gi = False
            if args.git_ignore:
                for pattern in git_rules:
                    p = pattern.rstrip('/')
                    if fnmatch.fnmatch(rel_p, p) or fnmatch.fnmatch(f, p):
                        is_gi = True; break

            if is_gi and rel_p not in force_include: continue
            if ext in KNOWN_BINARY_EXTENSIONS or f in DEFAULT_IGNORE_FILES: continue
            if not args.tree_only and ext not in ALLOWED_EXTS and rel_p not in force_include: continue
            found_files.append(rel_p)

    write_report(root, sorted(found_files), skipped_dirs, args)

if __name__ == "__main__":
    main()
