# src/ctx_pack/constants.py

# src/ctx_pack/constants.py

# =========================================================
# MEGA-LISTA DE EXCLUSIONES (Frameworks, Lenguajes, IDEs)
# =========================================================
EXCLUDED_DIRS_AND_FILES = {
    # 1. Control de versiones
    ".git", ".svn", ".hg", ".gitignore", ".dockerignore",

    # 2. Entornos e IDEs
    ".vscode", ".idea", ".vs", ".settings", ".project", ".classpath", 
    ".DS_Store", "Thumbs.db",

    # 3. Variables de entorno (Secretos)
    ".env", ".env.local", ".env.development", ".env.test", ".env.production",
    "secrets.json", "credentials.json",

    # 4. Archivos de bloqueo de dependencias (No aportan contexto lógico a la IA)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "pnpm-workspace.yaml", 
    "poetry.lock", "Pipfile.lock", "Cargo.lock", "composer.lock", "go.sum", 
    "Gemfile.lock",

    # 5. Ecosistema JavaScript / TypeScript (Web, Node, React, Vue, Angular)
    "node_modules", "bower_components", "dist", "build", "out", "coverage",
    ".next", ".nuxt", ".output", ".cache", ".parcel-cache", "public", ".serverless",

    # 6. Ecosistema Python
    "__pycache__", ".venv", "venv", "env", "virtualenv", "site-packages",
    ".pytest_cache", ".tox", ".mypy_cache", ".ruff_cache", "build", "dist", 
    "eggs", ".eggs",

    # 7. Ecosistema Java / Kotlin / Scala
    "target", ".gradle", "build", "out", "bin",

    # 8. Ecosistema C# / .NET
    "bin", "obj", "TestResults",

    # 9. Ecosistema PHP
    "vendor", "var/cache", "var/log",

    # 10. Ecosistema Rust & Go & C++
    "target", "vendor", "CMakeCache.txt", "CMakeFiles",

    # 11. Otros
    "TODO.md", "CHANGELOG.md", "logs", "tmp", "temp"
}

# =========================================================
# PREAJUSTES DE LENGUAJES (Extensiones permitidas)
# =========================================================
LANGUAGE_PRESETS = {
    "py": [".py"],
    "js": [".js", ".jsx", ".json"],
    "ts": [".ts", ".tsx", ".json"],
    "web": [".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".vue", ".svelte", ".astro"],
    "java": [".java", ".gradle", ".xml", ".kt"],
    "csharp": [".cs", ".csproj", ".xaml"],
    "cpp": [".cpp", ".hpp", ".c", ".h", ".cc", ".cxx"],
    "go": [".go", ".mod"],
    "rust": [".rs"],
    "php": [".php"],
    "ruby": [".rb"],
    "swift": [".swift"],
    "all": [
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h", 
        ".cs", ".go", ".rs", ".php", ".rb", ".json", ".html", ".css", 
        ".vue", ".svelte", ".astro", ".kt", ".swift", ".md"
    ]
}