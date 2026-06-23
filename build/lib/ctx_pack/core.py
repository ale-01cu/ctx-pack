import json
import os
import re
from collections import Counter
from .constants import EXCLUDED_DIRS_AND_FILES

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens. Roughly 1 token = 4 characters."""
    return len(text) // 4

def minify_content(ext: str, content: str) -> str:
    """Minify content based on the file extension."""
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

def generate_symbol(index: int) -> str:
    chars = "abcdefghijklmnopqrstuvwxyz"
    symbol = ""
    index += 1 
    while index > 0:
        index -= 1
        symbol = chars[index % 26] + symbol
        index //= 26
    return f"§{symbol}"

def compress_with_dictionary(files_data: list) -> tuple:
    line_counts = Counter()
    
    # 1. Contar frecuencias de líneas idénticas
    for rel_path, content in files_data:
        lines = content.splitlines()
        line_counts.update(lines)
        
    # 2. Filtrar con un umbral estricto ( >=3 repeticiones y >15 caracteres)
    candidates = {}
    symbol_idx = 0
    total_chars_saved = 0
    
    for line, count in line_counts.most_common():
        if count >= 3 and len(line) > 15:
            symbol = generate_symbol(symbol_idx)
            # Ahorro = lo que ocupaba originalmente - lo que ocupará con el símbolo
            # menos el costo de añadirlo al diccionario (símbolo + espacio + línea + salto)
            original_cost = len(line) * count
            new_cost = (len(symbol) + 1) * count + len(symbol) + 1 + len(line) + 1
            saved = original_cost - new_cost
            
            if saved > 0:
                candidates[line] = symbol
                total_chars_saved += saved
                symbol_idx += 1
                
    if not candidates:
        return files_data, "", 0

    # 3. Reemplazar líneas
    compressed_files_data = []
    for rel_path, content in files_data:
        lines = content.splitlines()
        compressed_lines = [candidates.get(line, line) for line in lines]
        compressed_files_data.append((rel_path, "\n".join(compressed_lines)))
        
    # 4. Formato de diccionario ULTRACOMPACTO (sin comentarios pesados)
    dict_lines = ["[DICT]"]
    for original, symbol in candidates.items():
        dict_lines.append(f"{symbol} {original}") # Formato: §a codigo_original
    
    dictionary_text = "\n".join(dict_lines) + "\n"
    dict_size = len(dictionary_text)
    
    # 5. Verificación de seguridad: ¿El diccionario pesa más de lo que ahorramos?
    if dict_size > total_chars_saved:
        return files_data, "", 0 # Cancelar compresión, no es rentable
        
    return compressed_files_data, dictionary_text, total_chars_saved


def consolidate(root_dir: str, base_output: str, allowed_exts: tuple, max_size_bytes: int, compress: bool = False, flatten: bool = False) -> dict:
    current_part = 1
    out_file = None
    files_data = []

    stats = {
        "files_processed": 0,
        "total_loc": 0,
        "project_tokens": 0,
        "output_files": []
    }

    def get_output_path(part):
        return f"{base_output}.txt" if part == 1 else f"{base_output}_part{part}.txt"

    def write_part(content_str: str):
        nonlocal current_part
        path = get_output_path(current_part)
        size_bytes = len(content_str.encode("utf-8"))
        tokens = estimate_tokens(content_str)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content_str)
            
        stats["output_files"].append({
            "filename": path,
            "tokens": tokens,
            "size_kb": round(size_bytes / 1024, 2)
        })
        print(f"📄 Creating file: {path}")

    def should_exclude(full_path: str):
        return any(
            part in EXCLUDED_DIRS_AND_FILES or part.startswith(base_output)
            for part in full_path.replace(root_dir, "").split(os.sep) if part
        )

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

    def process_file(file_path: str):
        rel_path = os.path.relpath(file_path, root_dir)
        ext = os.path.splitext(file_path)[1].lower()
        try:
            with open(file_path, encoding="utf-8") as f:
                raw_content = f.read()
            minified = minify_content(ext, raw_content)
            if not minified:
                return
            
            stats["files_processed"] += 1
            loc = len(minified.splitlines())
            stats["total_loc"] += loc
            proj_tokens = estimate_tokens(minified)
            stats["project_tokens"] += proj_tokens
            
            files_data.append((rel_path, minified))
        except Exception:
            pass

    print(f"🔍 Scanning directory: {root_dir}")
    scan_dir(root_dir)
    
    # Compresión
    dictionary_text = ""
    if compress and files_data:
        print("🗜️  Compressing patterns...")
        files_data, dictionary_text, chars_saved = compress_with_dictionary(files_data)
        if dictionary_text:
            print(f"✅ Dictionary created. Approx {chars_saved} characters saved.")
        else:
            print("⚠️ No repetitive patterns found that justify compression.")

    # Aplanado y partición (Escritura)
    print(f"📦 Packing output (Flatten={'ON' if flatten else 'OFF'})...")
    
    current_buffer = ""
    if dictionary_text:
        current_buffer += dictionary_text

    for rel_path, minified in files_data:
        block = f"// FILE: {rel_path}\n{minified}\n"
        current_buffer += block
        
        # Si el buffer supera el tamaño máximo, escribimos el archivo y reiniciamos
        if len(current_buffer.encode("utf-8")) > max_size_bytes:
            # Aplicamos Flatten (quitar todos los saltos de línea) justo antes de escribir
            if flatten:
                current_buffer = current_buffer.replace("\n", " ")
                
            write_part(current_buffer)
            current_part += 1
            current_buffer = ""
            
            # Si pasamos a un nuevo archivo, volvemos a inyectar el diccionario
            if dictionary_text:
                current_buffer += dictionary_text

    # Escribir el resto que quedó en el buffer
    if current_buffer.strip():
        if flatten:
            current_buffer = current_buffer.replace("\n", " ")
        write_part(current_buffer)

    return stats