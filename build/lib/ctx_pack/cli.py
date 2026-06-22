import argparse
import os
from .constants import LANGUAGE_PRESETS, EXCLUDED_DIRS_AND_FILES
from .core import consolidate

# Archivos clave que indican el lenguaje/ecosistema de un (sub)proyecto
LANGUAGE_SIGNATURES = {
    "tsconfig.json": "ts",
    "package.json": "web",
    "requirements.txt": "py",
    "pyproject.toml": "py",
    "Pipfile": "py",
    "setup.py": "py",
    "manage.py": "py",
    "pom.xml": "java",
    "build.gradle": "java",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "composer.json": "php",
    "Gemfile": "ruby",
    "Package.swift": "swift",
    "CMakeLists.txt": "cpp",
    "mix.exs": "elixir",
}

# Mapa extensión → lenguaje para detección secundaria por extensión
EXT_TO_LANG = {
    ".py": "py",
    ".js": "js",
    ".jsx": "web",
    ".ts": "ts",
    ".tsx": "ts",
    ".java": "java",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
    ".c": "cpp",
    ".h": "cpp", ".hpp": "cpp",
}


def auto_detect_languages(root_dir: str) -> set:
    """Detecta TODOS los lenguajes presentes en el proyecto.

    Escanea el directorio raíz y subdirectorios (hasta profundidad 3)
    buscando archivos de firma (package.json, requirements.txt, etc.).

    Si no encuentra ninguna firma, usa detección secundaria por extensión
    de archivos como respaldo.

    Retorna un conjunto de claves de lenguaje (ej: {'py', 'web', 'ts'}).
    """
    detected_by_signature = set()
    detected_by_extension = set()
    max_depth = 3

    for current_root, dirs, files in os.walk(root_dir):
        # Filtrar directorios excluidos y ocultos para no perder tiempo
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIRS_AND_FILES and not d.startswith(".")
        ]

        # Limitar profundidad: no necesitamos escanear node_modules anidados, etc.
        depth = current_root[len(root_dir):].count(os.sep)
        if depth >= max_depth:
            dirs[:] = []  # No descender más, pero sí escanear archivos aquí

        for filename in files:
            # --- Detección primaria: archivos de firma ---
            if filename in LANGUAGE_SIGNATURES:
                detected_by_signature.add(LANGUAGE_SIGNATURES[filename])
            if filename.endswith(".csproj"):
                detected_by_signature.add("csharp")

            # --- Detección secundaria: por extensión (siempre recolectar) ---
            ext = os.path.splitext(filename)[1].lower()
            if ext in EXT_TO_LANG:
                detected_by_extension.add(EXT_TO_LANG[ext])

    # Priorizar firmas; si hay firmas, combinar con extensiones
    # para no perder lenguajes que no tienen archivo de firma
    if detected_by_signature:
        return detected_by_signature | detected_by_extension
    # Si no hay firmas, usar detección por extensión
    if detected_by_extension:
        return detected_by_extension
    # Si no hay nada, devolver conjunto vacío (el caller usa "all")
    return set()


def merge_extensions(langs: set) -> tuple:
    """Combina las extensiones de múltiples lenguajes en una tupla única,
    manteniendo orden consistente y sin duplicados.
    """
    merged = []
    seen = set()
    for lang in sorted(langs):
        for ext in LANGUAGE_PRESETS.get(lang, []):
            if ext not in seen:
                seen.add(ext)
                merged.append(ext)
    return tuple(merged)


def main():
    parser = argparse.ArgumentParser(
        description="ctx-pack: Empaqueta tu código fuente para dárselo de contexto a una IA."
    )
    parser.add_argument(
        "-l", "--lang",
        choices=list(LANGUAGE_PRESETS.keys()) + ["auto"],
        default="auto",
        help="Preajuste de lenguaje (ej: ts, py, all). Por defecto: auto (detecta automáticamente)"
    )
    parser.add_argument(
        "-e", "--ext", type=str,
        help="Extensiones personalizadas separadas por coma (ej: .php,.html)"
    )
    parser.add_argument(
        "-s", "--size", type=int, default=500,
        help="Tamaño máximo por archivo en KB (por defecto: 500)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="ctx_pack_output",
        help="Nombre base del archivo de salida"
    )
    args = parser.parse_args()

    root_dir = os.getcwd()
    max_size_bytes = args.size * 1024
    detected_lang_msg = ""

    if args.ext:
        allowed_extensions = tuple(ext.strip() for ext in args.ext.split(","))
        detected_lang_msg = f"Personalizadas ({args.ext})"
    else:
        if args.lang == "auto":
            detected_langs = auto_detect_languages(root_dir)
            if detected_langs:
                allowed_extensions = merge_extensions(detected_langs)
                langs_str = ", ".join(sorted(detected_langs))
                detected_lang_msg = f"Auto-detectado: [{langs_str}]"
            else:
                allowed_extensions = tuple(LANGUAGE_PRESETS["all"])
                detected_lang_msg = "Auto-detectado: 'all' (sin firmas encontradas)"
        else:
            allowed_extensions = tuple(LANGUAGE_PRESETS[args.lang])
            detected_lang_msg = f"Manual: '{args.lang}'"

    print("🚀 Iniciando ctx-pack...")
    print(f"🤖 Modo de lenguaje: {detected_lang_msg}")
    print(f"⚙️  Extensiones: {allowed_extensions}")
    print(f"📦 Tamaño máx/archivo: {args.size} KB")

    try:
        consolidate(
            root_dir=root_dir,
            base_output=args.output,
            allowed_exts=allowed_extensions,
            max_size_bytes=max_size_bytes
        )
        print("-" * 30)
        print("✅ ¡Contexto empaquetado con éxito!")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    main()