from typing import Dict, Set


LEGACY_ALLOWED_EXTS: Set[str] = {
    ".py", ".php", ".js", ".ts", ".html", ".sql",
    ".tsx", ".jsx", ".vue", ".sh", ".inc", ".module", ".twig",
}

CODE_EXTENSIONS: Set[str] = {
    ".py", ".pyi", ".php", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".html", ".htm", ".sql", ".vue", ".sh", ".bash", ".zsh", ".ps1",
    ".inc", ".module", ".twig", ".css", ".scss", ".less", ".go", ".rs",
    ".java", ".kt", ".kts", ".c", ".h", ".cpp", ".hpp", ".cs", ".rb",
    ".swift", ".dart", ".lua", ".r", ".pl", ".pm", ".ex", ".exs",
}

DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git", ".hg", ".svn", "venv", ".venv", "env", ".envdir", "node_modules",
    "__pycache__", "vendor", "tmp", "temp", "dist", "build", ".idea", ".vscode",
    "reports", "ai-reports", "log", "logs", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", "coverage", ".coverage", "target", "out",
    ".next", ".nuxt", ".cache", ".parcel-cache", ".turbo", "site-packages",
}

DEFAULT_IGNORE_FILE_NAMES: Set[str] = {
    ".DS_Store", "thumbs.db", "Thumbs.db", "desktop.ini",
    "composer.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "bun.lockb", "poetry.lock", "Pipfile.lock",
}

KNOWN_BINARY_EXTENSIONS: Set[str] = {
    ".zip", ".7z", ".tar", ".gz", ".rar", ".bz2", ".xz", ".iso", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp", ".tiff",
    ".psd", ".ai", ".eps", ".mp3", ".wav", ".flac", ".ogg", ".mp4",
    ".avi", ".mkv", ".mov", ".webm", ".pdf", ".doc", ".docx", ".xls",
    ".xlsx", ".ppt", ".pptx", ".exe", ".dll", ".so", ".dylib", ".pyd",
    ".pyc", ".class", ".o", ".obj", ".a", ".lib", ".dat", ".db",
    ".sqlite", ".sqlite3", ".woff", ".woff2", ".ttf", ".otf", ".eot",
}

TEXT_OPTIONAL_EXTENSIONS: Set[str] = {
    ".md", ".mdx", ".txt", ".rst", ".json", ".jsonc", ".xml", ".yaml",
    ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".csv",
    ".graphql", ".gql", ".proto", ".env.example", ".http", ".lock",
}

SPECIAL_TEXT_FILENAMES: Set[str] = {
    "Dockerfile", "Containerfile", "Makefile", "GNUmakefile", "Procfile",
    "requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py",
    "setup.cfg", "tox.ini", "Pipfile", "package.json", "tsconfig.json",
    "vite.config.js", "vite.config.ts", "webpack.config.js", "composer.json",
    "Cargo.toml", "go.mod", "go.sum", "pom.xml", "build.gradle",
    "build.gradle.kts", "Gemfile", "mix.exs", "pubspec.yaml", ".htaccess",
    ".editorconfig", ".gitignore", ".dockerignore",
}

SENSITIVE_EXACT_NAMES: Set[str] = {
    ".env", ".npmrc", ".pypirc", ".netrc", "id_rsa", "id_ed25519",
    "credentials.json", "credential.json", "secrets.json", "secret.json",
    "service-account.json", "service_account.json", "auth.json", "token.json",
}

SENSITIVE_EXTENSIONS: Set[str] = {
    ".pem", ".key", ".pfx", ".p12", ".jks", ".keystore", ".kdbx",
}

CATEGORY_LABELS: Dict[str, str] = {
    "code": "Kod",
    "config": "Yapılandırma",
    "docs": "Dokümantasyon",
    "data": "Veri",
    "test": "Test",
    "binary": "Binary",
    "other": "Diğer metin",
    "sensitive": "Hassas",
}

PROJECT_MARKERS = {
    "Python": {"pyproject.toml", "requirements.txt", "setup.py", "Pipfile"},
    "Node.js": {"package.json"},
    "PHP / Composer": {"composer.json"},
    "Rust": {"Cargo.toml"},
    "Go": {"go.mod"},
    "Java / Maven": {"pom.xml"},
    "Java / Gradle": {"build.gradle", "build.gradle.kts"},
    "Ruby": {"Gemfile"},
    "Elixir": {"mix.exs"},
    "Dart / Flutter": {"pubspec.yaml"},
    "Docker": {"Dockerfile", "Containerfile"},
}

PROJECT_RECOMMENDED_EXTS = {
    "Python": {".py", ".pyi", ".html", ".jinja", ".jinja2", ".sql"},
    "Node.js": {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".html", ".css", ".scss"},
    "PHP / Composer": {".php", ".inc", ".module", ".twig", ".html", ".js", ".css", ".sql"},
    "Rust": {".rs", ".toml"},
    "Go": {".go", ".mod", ".sum"},
    "Java / Maven": {".java", ".xml", ".properties"},
    "Java / Gradle": {".java", ".kt", ".kts", ".gradle", ".properties"},
    "Ruby": {".rb"},
    "Elixir": {".ex", ".exs"},
    "Dart / Flutter": {".dart", ".yaml"},
    "Docker": {".dockerfile", ".yml", ".yaml"},
}
