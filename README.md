# ctx-pack

**Consolidate, minify, and package source code for AI context windows.**

`ctx-pack` scans your project, strips noise (comments, empty lines, lock files, build artifacts), and produces a single compact text file ready to feed into any LLM, Gemini, or AI coding assistant.

## Features

- **Language auto-detection** — scans `go.mod`, `Cargo.toml`, `tsconfig.json`, and 15+ other signatures to pick the right file extensions automatically.
- **Minification** — removes comments and blank lines per-language (JS, TS, Python, Java, Go, Rust, C++, and more).
- **Semantic file selection** — `-q "payment module"` uses Google Gemini to select only files relevant to a concept.
- **Dictionary compression** — `-c` replaces repeated lines (boilerplate, imports, types) with short symbols.
- **Flatten mode** — `--flatten` joins everything into a single line for extreme token efficiency.
- **Configurable output** — split across multiple files with a max-size limit.

## Installation

```bash
pip install ctx-pack
```

Requires Python ≥ 3.9.

## Usage

```bash
# Auto-detect language and pack everything
ctx-pack

# Specify a language preset
ctx-pack -l py
ctx-pack -l ts

# Custom file extensions
ctx-pack -e .php,.html,.twig

# Semantic selection (requires GEMINI_API_KEY)
ctx-pack -q "authentication flow"

# Enable dictionary compression
ctx-pack -c

# Extreme minification
ctx-pack --flatten

# Split into 200 KB chunks
ctx-pack -s 200
```

### Output

- `ctx_pack_output.txt` — packed context
- `ctx_pack_output_part2.txt`, etc. — when content exceeds the size limit
- The output includes the original file path as `// FILE: path/to/file.ext` headers.

## Configuration

Set your Gemini API key for semantic search:

```bash
export GEMINI_API_KEY="your-key-here"
```

The selected model is persisted in `~/.ctx-pack-config.json`.

### Available models

```bash
ctx-pack --list-models
```

## API

```python
from ctx_pack.core import consolidate

stats = consolidate(
    root_dir="./my-project",
    base_output="ctx_pack_output",
    allowed_exts=(".py",),
    max_size_bytes=500 * 1024,
    compress=True,
    flatten=False,
    query="user auth",
    model="gemini-2.5-flash",
)
```

Returns statistics: `files_processed`, `total_loc`, `project_tokens`, `output_files`.

## CLI reference

| Flag | Description |
|------|-------------|
| `-l` / `--lang` | Language preset: `py`, `js`, `ts`, `web`, `go`, `rust`, `all`, `auto` (default) |
| `-e` / `--ext` | Custom extensions: `.php,.html` |
| `-s` / `--size` | Max KB per output file (default: 500) |
| `-o` / `--output` | Base output filename (default: `ctx_pack_output`) |
| `-c` / `--compress` | Dictionary compression for repeated lines |
| `--flatten` | Join all code into a single line |
| `-q` / `--query` | Semantic file selection (requires `GEMINI_API_KEY`) |
| `--model` | Gemini model for semantic search (default: `gemini-2.5-flash`) |
| `--list-models` | List available Gemini models |
| `--show-model` | Show currently configured model |

## License

MIT
