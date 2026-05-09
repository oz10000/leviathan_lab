import os
import re
import ast
import json
from pathlib import Path

STRATEGIES_DIR = Path("strategies_txt")
OUTPUT_DIR = Path("contracts")
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_python_code(file_content):
    """Extrae todos los bloques de código Python del texto."""
    blocks = re.findall(r"```python(.+?)```", file_content, re.DOTALL)
    return "\n".join(blocks)

def extract_config_vars(code):
    """Analiza el AST del código Python para extraer variables de configuración."""
    tree = ast.parse(code)
    config = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    key = target.id
                    try:
                        val = ast.literal_eval(node.value)
                        config[key] = val
                    except:
                        pass
    return config

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    code = extract_python_code(content)
    config = extract_config_vars(code)
    # Buscar nombre de versión en el contenido (ej: "LEVIATAN V7.2")
    version_match = re.search(r"LEVIATAN\s*V?(\d+\S*)", content, re.IGNORECASE)
    version = version_match.group(0) if version_match else filepath.stem

    contract = {
        "name": f"leviathan_{filepath.stem}",
        "version": version,
        "params": config,
        "source_file": filepath.name
    }
    return contract

def generate_all_contracts():
    for fpath in STRATEGIES_DIR.glob("*.txt"):
        contract = parse_file(fpath)
        out_name = contract["name"] + ".json"
        with open(OUTPUT_DIR / out_name, "w") as out:
            json.dump(contract, out, indent=2)
        print(f"✓ {fpath.name} → {out_name}")

if __name__ == "__main__":
    generate_all_contracts()
