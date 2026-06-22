import json
import os
import re
from .constants import EXCLUDED_DIRS_AND_FILES

def estimate_tokens(text: str) -> int:
    """Estima la cantidad de tokens. Aproximadamente 1 token = 4 caracteres."""
    return len(text) // 4

def minify_content(ext: str, content: str) -> str:
    """Minifica el contenido según la extensión del archivo."""
    if ext == ".json":
        try:
            obj = json.loads(content)
            return json.dumps(obj, separators=(",", ":"))
        except (json.JSONDecodeError, ValueError):
            return content.strip()

    minified_lines = []
    if ext in [".js", ".jsx", ".ts", ".tsx", ".css", ".java", ".cpp", ".h", ".cs", ".php"]:
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if ext in [".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".h", ".cs", ".go", ".php"] and line.startswith("//"):
            continue
        if ext in [".py", ".rb"] and line.startswith("#"):
            continue
        minified_lines.append(line)
    return "\n".join(minified_lines)

def consolidate(root_dir: str, base_output: str, allowed_exts: tuple, max_size_bytes: int) -> dict:
    current_part = 1
    current_size = 0
    current_file_tokens = 0
    out_file = None
    
    stats = {
        "files_processed": 0,
        "total_loc": 0,  # Líneas de código empaquetadas
        "project_tokens": 0, # Tokens solo del código fuente
        "output_files": [] # Lista de ficheros generados con sus métricas
    }

    def get_output_path(part):
        return f"{base_output}.txt" if part == 1 else f"{base_output}_part{part}.txt"

    def open_new_file():
        nonlocal out_file, current_size, current_part, current_file_tokens
        # Si ya había un archivo abierto, lo cerramos y guardamos sus estadísticas
        if out_file:
            out_file.close()
            stats["output_files"].append({
                "filename": get_output_path(current_part),
                "tokens": current_file_tokens,
                "size_kb": round(current_size / 1024, 2)
            })
            current_part += 1
        
        path = get_output_path(current_part)
        out_file = open(path, "w", encoding="utf-8")
        current_size = 0
        current_file_tokens = 0
        print(f"📄 Creando archivo: {path}")

    def should_exclude(full_path: str):
        return any(
            part in EXCLUDED_DIRS_AND_FILES or part.startswith(base_output)
            for part in full_path.replace(root_dir, "").split(os.sep) if part
        )

    def process_file(file_path: str):
        nonlocal current_size, current_file_tokens
        rel_path = os.path.relpath(file_path, root_dir)
        ext = os.path.splitext(file_path)[1].lower()

        try:
            with open(file_path, encoding="utf-8") as f:
                raw_content = f.read()

            minified = minify_content(ext, raw_content)
            if not minified:
                return

            # --- Estadísticas del proyecto ---
            stats["files_processed"] += 1
            loc = len(minified.splitlines())
            stats["total_loc"] += loc
            
            proj_tokens = estimate_tokens(minified)
            stats["project_tokens"] += proj_tokens

            header = f"\n// FILE: {rel_path}\n"
            block = header + minified
            block_size = len(block.encode("utf-8"))

            # Si el bloque excede el tamaño, abrimos un nuevo archivo
            if current_size + block_size > max_size_bytes and current_size > 0:
                open_new_file()

            out_file.write(block)
            current_size += block_size
            
            # Tokens de este bloque (incluye el header) para el archivo de salida
            current_file_tokens += estimate_tokens(block)

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
    
    # Cerrar y guardar estadísticas del último archivo abierto
    if out_file:
        out_file.close()
        stats["output_files"].append({
            "filename": get_output_path(current_part),
            "tokens": current_file_tokens,
            "size_kb": round(current_size / 1024, 2)
        })
        
    return stats