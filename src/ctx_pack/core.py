import json
import os
import re
import warnings
from collections import Counter
from .constants import EXCLUDED_DIRS_AND_FILES

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None


def list_models():
    """List available Google Gemini models."""
    if not genai:
        print("Google Generative AI library is not installed.")
        print("Run: pip install google-generativeai")
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable is not set.")
        print("Set it with: export GEMINI_API_KEY='your_key'")
        return
    
    try:
        genai.configure(api_key=api_key)
        print("Available Gemini Models")
        print("=" * 40)
        
        for m in genai.list_models():
            model_name = m.name.replace("models/", "")
            print(f"  {model_name}")
            if hasattr(m, 'description') and m.description:
                print(f"    {m.description}")
            if hasattr(m, 'supported_generation_methods'):
                print(f"    Methods: {', '.join(m.supported_generation_methods)}")
            print("=" * 40)
        
    except Exception as e:
        print(f"Error fetching models: {e}")

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


# =======================================================
# NUEVA FUNCIÓN: BÚSQUEDA SEMÁNTICA CON LLM
# =======================================================
def get_relevant_files_from_llm(root_dir: str, allowed_exts: tuple, query: str, model: str = "gemini-2.5-flash") -> set:
    if not genai:
        raise ImportError("Google Generative AI library is not installed. Please run: pip install google-generativeai")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    print(f"  LLM query: scanning files...")
    
    # 1. Construir el árbol del proyecto (solo nombres de archivos y rutas)
    tree_lines = []
    for current_root, dirs, files in os.walk(root_dir):
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIRS_AND_FILES and not d.startswith(".")
        ]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            # Solo mostramos al LLM los archivos que cumplen con las extensiones permitidas
            if ext in allowed_exts:
                rel_path = os.path.relpath(os.path.join(current_root, filename), root_dir)
                tree_lines.append(rel_path)
                
    project_tree = "\n".join(tree_lines)
    
    if not project_tree.strip():
        print("  LLM query: no files to scan")
        return set()

    # 2. Configurar y llamar a la API de Google Gemini
    genai.configure(api_key=api_key)
    # Add models/ prefix if not present
    model_name = model if model.startswith("models/") else f"models/{model}"
    model_instance = genai.GenerativeModel(model_name) # Usamos el modelo especificado por el usuario

    prompt = f"""You are an expert software architect. 
Here is the directory structure of a project (relative paths):

{project_tree}

The user wants to find files related to the following concept: "{query}"

Analyze the paths, filenames, and common software architecture patterns to identify which files are strictly relevant to this concept.
Return your answer STRICTLY as a JSON array of strings containing the relative paths. Do not include any other text, comments, or markdown formatting.
Example output format: ["src/payment/controller.py", "src/models/payment.py"]
If no files are relevant, return an empty array: []
"""

    print(f"  LLM query: asking model ({model})...")
    response = model_instance.generate_content(prompt)
    
    # 3. Parsear la respuesta del LLM
    try:
        # Limpiar posibles marcas de código markdown que el LLM añada por costumbre
        clean_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        relevant_files = json.loads(clean_response)
        
        if not isinstance(relevant_files, list):
            raise ValueError("LLM did not return a JSON array")
            
        # Normalizar las rutas para que coincidan con lo que os.walk devuelve
        normalized_files = {os.path.normpath(f) for f in relevant_files}
        
        print(f"  LLM query: {len(normalized_files)} files match")
        return normalized_files
        
    except Exception as e:
        print(f"  LLM query: parse error — {e}")
        print(f"  LLM raw: {response.text[:200]}")
        return set()


def consolidate(root_dir: str, base_output: str, allowed_exts: tuple, max_size_bytes: int, compress: bool = False, flatten: bool = False, query: str = None, model: str = "gemini-2.5-flash") -> dict:
    current_part = 1
    files_data = []

    stats = {
        "files_processed": 0,
        "total_loc": 0,
        "project_tokens": 0,
        "output_files": []
    }
    
    # Si hay un query, llamamos al LLM para obtener la lista blanca
    llm_allowed_files = None
    if query:
        llm_allowed_files = get_relevant_files_from_llm(root_dir, allowed_exts, query, model)

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
        print(f"  Created: {path}")

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
        
        # =======================================================
        # FILTRO DEL LLM: Si el LLM definió archivos, y este no está, lo saltamos
        # =======================================================
        if llm_allowed_files is not None:
            # Normalizamos la ruta para compararla correctamente
            if os.path.normpath(rel_path) not in llm_allowed_files:
                return # Ignoramos este archivo, no es relevante para el query
        
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

    print(f"  Scan: {root_dir}")
    scan_dir(root_dir)

    dictionary_text = ""
    if compress and files_data:
        files_data, dictionary_text, chars_saved = compress_with_dictionary(files_data)
        if dictionary_text:
            print(f"  Compression: dictionary saved ~{chars_saved} chars")
        else:
            print(f"  Compression: skipped (no gains)")

    print(f"  Packing: writing output...")
    
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