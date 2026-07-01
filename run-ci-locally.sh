#!/bin/bash
################################################################################
# run-ci-locally.sh — Run the same checks as .github/workflows/tests.yml
#
# Use this BEFORE pushing to catch failures early, without waiting for
# GitHub Actions. Mirrors the "test" job in the CI workflow exactly.
#
# Usage:
#   chmod +x run-ci-locally.sh
#   ./run-ci-locally.sh
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Running local CI checks (mirrors GitHub Actions)...${NC}"
echo ""

# ----------------------------------------------------------------------------
# Step 1: Syntax check (mirrors "Lint with syntax check" step)
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📋 Step 1: Syntax check (python -m py_compile)...${NC}"

FAILED=0
while IFS= read -r -d '' file; do
    if ! python3 -m py_compile "$file" 2>/tmp/py_compile_err; then
        echo -e "${RED}❌ Syntax error in: $file${NC}"
        cat /tmp/py_compile_err
        FAILED=1
    fi
done < <(find . -name "*.py" -type f -not -path "./.git/*" -not -path "*/__pycache__/*" -print0)

if [ "$FAILED" -eq 1 ]; then
    echo -e "${RED}❌ Syntax check FAILED${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All files compile${NC}"
echo ""

# ----------------------------------------------------------------------------
# Step 2: Install test dependencies (mirrors "Install dependencies" step)
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📋 Step 2: Checking test dependencies...${NC}"

if ! python3 -c "import pytest, pytest_cov" 2>/dev/null; then
    echo "Installing pytest + pytest-cov..."
    pip install pytest pytest-cov -q
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# ----------------------------------------------------------------------------
# Step 3: Run tests (mirrors "Run tests" step)
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📋 Step 3: Running pytest...${NC}"
echo ""

if pytest tests/ -v --tb=short --cov=winmerge_ai_exporter --cov-report=term-missing; then
    echo ""
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo ""
    echo -e "${RED}❌ Tests FAILED${NC}"
    exit 1
fi
echo ""

# ----------------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------------
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Local CI checks PASSED — safe to push          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
