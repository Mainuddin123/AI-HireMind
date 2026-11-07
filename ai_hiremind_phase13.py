from pathlib import Path
import shutil
import compileall

files = [
    "backend/api/agentic.py",
    "agents/recruitment_nodes.py",
    "agents/recruitment_graph.py"
]

for filename in files:
    path = Path(filename)

    if not path.exists():
        print(f"Missing: {filename}")
        continue

    shutil.copy2(path, str(path) + ".bak")

    content = path.read_text(encoding="utf-8")

    content = content.replace("`r`n", "\n")
    content = content.replace("`n", "\n")

    path.write_text(content, encoding="utf-8")

    print(f"Repaired: {filename}")

print("\nChecking all Python files...")

backend_ok = compileall.compile_dir("backend", quiet=1)
agents_ok = compileall.compile_dir("agents", quiet=1)

if backend_ok and agents_ok:
    print("\nSUCCESS: All syntax checks passed!")
else:
    print("\nSyntax errors remain. Share the output.")