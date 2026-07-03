#!/bin/bash
# run-ci-locally.sh — mirrors GitHub Actions, uses isolated venv.
set -e

echo ""
echo "================================================================================"
echo "  Running local CI checks (isolated venv)..."
echo "================================================================================"
echo ""

# Step 1: Create / reuse venv
echo "Step 1: Preparing isolated virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created new .venv"
else
    echo "Reusing existing .venv"
fi

source .venv/bin/activate
echo ""

# Step 2: Install pinned dependencies
echo "Step 2: Installing pinned dependencies from requirements-dev.txt..."
pip install -r requirements-dev.txt -q
echo "Dependencies installed."
echo ""

# Step 3: Syntax check
echo "Step 3: Syntax check (py_compile)..."
python -c "
import sys, pathlib, py_compile
errors = []
skip = {'.git', '__pycache__', '.pytest_cache', 'build', 'dist', '.venv'}
for f in pathlib.Path('.').rglob('*.py'):
    if any(p in f.parts for p in skip):
        continue
    try:
        py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as e:
        errors.append(str(e))
        print(f'FAIL: {f}  ->  {e}')
if errors:
    print(f'{len(errors)} file(s) failed.')
    sys.exit(1)
else:
    print('All .py files OK.')
"
echo ""

# Step 4: Run tests
echo "Step 4: Running pytest..."
pytest tests/ -v --tb=short --cov=winmerge_ai_exporter --cov-report=term-missing

echo ""
echo "================================================================================"
echo "  Local CI checks PASSED - safe to push"
echo "================================================================================"
echo ""
