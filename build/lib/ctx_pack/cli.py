# src\ctx_pack\cli.py
import argparse
import os
from .constants import LANGUAGE_PRESETS
from .core import consolidate

def auto_detect_language(root_dir: str) -> str:
    """Detecta el lenguaje principal del proyecto basándose en archivos clave."""
    
    # Diccionario de archivos clave -> preajuste de lenguaje
    signatures = {
        "tsconfig.json": "ts",
        "package.json": "web",
        "requirements.txt": "py",
        "pyproject.toml": "py",
        "pom.xml": "java",
        "build.gradle": "java",
        "Cargo.toml": "rust",
        "go.mod": "go",
        "composer.json": "php"
    }

    # Revisar si existe alguno de los archivos clave
    for filename, lang_preset in signatures.items():
        if os.path.exists(os.path.join(root_dir, filename)):
            return lang_preset

    # Detección especial para C# (archivos .csproj)
    try:
        for f in os.listdir(root_dir):
            if f.endswith(".csproj"):
                return "csharp"
    except OSError:
        pass

    # Si no reconoce nada, devuelve 'all' por defecto
    return "all"


def main():
    parser = argparse.ArgumentParser(
        description="ctx-pack: Empaqueta tu código fuente para dárselo de contexto a una IA."
    )
    
    parser.add_argument("-l", "--lang", choices=LANGUAGE_PRESETS.keys(), default="auto",
                        help="Preajuste de lenguaje (ej: ts, py). Por defecto: auto (detecta automáticamente)")
    parser.add_argument("-e", "--ext", type=str,
                        help="Extensiones personalizadas separadas por coma (ej: .php,.html)")
    parser.add_argument("-s", "--size", type=int, default=500,
                        help="Tamaño máximo por archivo en KB (por defecto: 500)")
    parser.add_argument("-o", "--output", type=str, default="ctx_pack_output",
                        help="Nombre base del archivo de salida")
                        
    args = parser.parse_args()
    root_dir = os.getcwd()
    max_size_bytes = args.size * 1024

    # Determinar las extensiones a usar
    detected_lang_msg = ""
    
    if args.ext:
        allowed_extensions = tuple(ext.strip() for ext in args.ext.split(","))
        detected_lang_msg = f"Personalizadas ({args.ext})"
    else:
        selected_lang = args.lang
        if selected_lang == "auto":
            selected_lang = auto_detect_language(root_dir)
            detected_lang_msg = f"Auto-detectado: '{selected_lang}'"
        else:
            detected_lang_msg = f"Manual: '{selected_lang}'"
            
        allowed_extensions = tuple(LANGUAGE_PRESETS[selected_lang])

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