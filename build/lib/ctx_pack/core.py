# src/ctx_pack/core.py
import json
import os
import re
from .constants import EXCLUDED_DIRS_AND_FILES

def minify_content(ext: str, content: str) -> str:
    """Minifica el contenido según la extensión del archivo."""
    if ext == ".json":
        try:
            obj = json.loads(content)
            return json.dumps(obj, separators=(",", ":"))
        except (json.JSONDecodeError, ValueError):
            return content.strip()

    minified_lines = []
    
    # Eliminar comentarios de bloque
    if ext in [".js", ".jsx", ".ts", ".tsx", ".css", ".java", ".cpp", ".h", ".cs", ".php"]:
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Ignorar comentarios de línea según lenguaje
        if ext in [".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".h", ".cs", ".go", ".php"] and line.startswith("//"):
            continue
        if ext in [".py", ".rb"] and line.startswith("#"):
            continue

        minified_lines.append(line)

    return "\n".join(minified_lines)

def consolidate(root_dir: str, base_output: str, allowed_exts: tuple, max_size_bytes: int):
    current_part = 1
    current_size = 0
    out_file = None

    def get_output_path(part):
        return f"{base_output}.txt" if part == 1 else f"{base_output}_part{part}.txt"

    def open_new_file():
        nonlocal out_file, current_size, current_part
        if out_file:
            out_file.close()
        path = get_output_path(current_part)
        out_file = open(path, "w", encoding="utf-8")
        current_size = 0
        print(f"📄 Creando archivo: {path}")

    def should_exclude(full_path: str):
        return any(
            part in EXCLUDED_DIRS_AND_FILES or part.startswith(base_output)
            for part in full_path.replace(root_dir, "").split(os.sep) if part
        )

    def process_file(file_path: str):
        nonlocal current_size, current_part
        rel_path = os.path.relpath(file_path, root_dir)
        ext = os.path.splitext(file_path)[1].lower()

        try:
            with open(file_path, encoding="utf-8") as f:
                raw_content = f.read()

            minified = minify_content(ext, raw_content)
            if not minified:
                return

            header = f"\n// FILE: {rel_path}\n"
            block = header + minified
            block_size = len(block.encode("utf-8"))

            if current_size + block_size > max_size_bytes and current_size > 0:
                current_part += 1
                open_new_file()

            out_file.write(block)
            current_size += block_size
        except Exception:
            pass # Ignorar archivos no-texto

    def scan_dir(directory: str):
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if should_exclude(entry.path):
                        continue
                    if entry.is_dir():
                        scan_dir(entry.path)
                    elif entry.is_file() and entry.name.endswith(allowed_exts):
                        process_file(entry.path)
        except OSError:
            pass

    print(f"🔍 Escaneando directorio: {root_dir}")
    open_new_file()
    scan_dir(root_dir)
    
    if out_file:
        out_file.close()
