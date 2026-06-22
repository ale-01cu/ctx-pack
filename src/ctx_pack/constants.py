# src/ctx_pack/constants.py

# =========================================================
# MEGA-LIST OF EXCLUSIONS (Frameworks, Languages, IDEs)
# =========================================================
EXCLUDED_DIRS_AND_FILES = {
    # 1. Version control
    ".git", ".svn", ".hg", ".gitignore", ".dockerignore",

    # 2. Environments and IDEs
    ".vscode", ".idea", ".vs", ".settings", ".project", ".classpath",
    ".DS_Store", "Thumbs.db",

    # 3. Environment variables (secrets)
    ".env", ".env.local", ".env.development", ".env.test", ".env.production",
    "secrets.json", "credentials.json",

    # 4. Dependency lock files (do not add logical context to the AI)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "pnpm-workspace.yaml",
    "poetry.lock", "Pipfile.lock", "Cargo.lock", "composer.lock", "go.sum",
    "Gemfile.lock",

    # 5. JavaScript / TypeScript ecosystem (Web, Node, React, Vue, Angular)
    "node_modules", "bower_components", "dist", "build", "out", "coverage",
    ".next", ".nuxt", ".output", ".cache", ".parcel-cache", "public", ".serverless",

    # 6. Python ecosystem
    "__pycache__", ".venv", "venv", "env", "virtualenv", "site-packages",
    ".pytest_cache", ".tox", ".mypy_cache", ".ruff_cache", "build", "dist",
    "eggs", ".eggs",

    # 7. Java / Kotlin / Scala ecosystem
    "target", ".gradle", "build", "out", "bin",

    # 8. C# / .NET ecosystem
    "bin", "obj", "TestResults",

    # 9. PHP ecosystem
    "vendor", "var/cache", "var/log",

    # 10. Rust, Go, and C++ ecosystem
    "target", "vendor", "CMakeCache.txt", "CMakeFiles",

    # 11. Other files
    "TODO.md", "CHANGELOG.md", "logs", "tmp", "temp"
}

# =========================================================
# LANGUAGE PRESETS (Allowed extensions)
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