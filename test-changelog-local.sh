#!/bin/bash
# test-changelog-local.sh
# Simulates the exact same changelog generation logic used in ci-cd.yml,
# but runs locally so you can verify output before pushing a tag.
#
# Usage:
#   chmod +x test-changelog-local.sh
#   ./test-changelog-local.sh
#   ./test-changelog-local.sh v1.3.2  (compare against a specific previous tag)

set -e

PREV_TAG="${1:-}"

echo "========================================"
echo "  Changelog Generation — Local Dry Run"
echo "========================================"
echo ""

# Show recent commits so you can see what will be picked up
echo "--- Recent commits in this repo ---"
git log --oneline -15
echo ""

# Determine range
if [ -z "$PREV_TAG" ]; then
    PREV_TAG=$(git tag --sort=-creatordate | head -1)
fi

if [ -z "$PREV_TAG" ]; then
    RANGE="HEAD"
    echo "No tags found — scanning full history"
else
    RANGE="${PREV_TAG}..HEAD"
    echo "Scanning commits in range: ${RANGE}"
fi
echo ""

# Helper: extract commits of a given type (same grep as ci-cd.yml)
get_section() {
    TYPE=$1
    git log "$RANGE" --pretty=format:"%s|%h" \
        | grep -E "^${TYPE}(\([^)]+\))?[!:]" \
        | sed 's/|/ (/' | sed 's/$/)/' \
        | sed 's/^/- /' || true
}

FEATS=$(get_section "feat")
FIXES=$(get_section "fix")
PERF=$(get_section "perf")
REFACTORS=$(get_section "refactor")
DOCS=$(get_section "docs")
TESTS=$(get_section "test")
CHORES=$(get_section "chore\|build\|ci")
BREAKING=$(git log "$RANGE" --pretty=format:"%s|%h" \
    | grep "BREAKING CHANGE\|!:" \
    | sed 's/|/ (/' | sed 's/$/)/' | sed 's/^/- /' || true)

# Show what would be generated
echo "--- Changelog preview (what would be written to CHANGELOG.md) ---"
echo ""
echo "## [NEXT_VERSION] — $(date +%Y-%m-%d)"
[ -n "$BREAKING"  ] && echo "" && echo "### ⚠️ Breaking Changes" && echo "$BREAKING"
[ -n "$FEATS"     ] && echo "" && echo "### ✨ Features"          && echo "$FEATS"
[ -n "$FIXES"     ] && echo "" && echo "### 🐛 Bug Fixes"         && echo "$FIXES"
[ -n "$PERF"      ] && echo "" && echo "### ⚡ Performance"        && echo "$PERF"
[ -n "$REFACTORS" ] && echo "" && echo "### ♻️ Refactors"          && echo "$REFACTORS"
[ -n "$DOCS"      ] && echo "" && echo "### 📝 Docs"               && echo "$DOCS"
[ -n "$TESTS"     ] && echo "" && echo "### 🧪 Tests"              && echo "$TESTS"
[ -n "$CHORES"    ] && echo "" && echo "### 🔧 Chores / CI"        && echo "$CHORES"
echo ""

# Diagnose commits that won't appear (don't follow Conventional Commits)
echo "--- Commits that will NOT appear (non-conventional format) ---"
git log "$RANGE" --pretty=format:"%s" \
    | grep -vE "^(feat|fix|perf|refactor|docs|test|chore|build|ci)(\([^)]+\))?[!:]" \
    | grep -v "^\[skip ci\]" \
    | sed 's/^/  IGNORED: /' || echo "  (none — all commits follow Conventional Commits)"
echo ""
echo "========================================"
echo "  If the preview looks correct, push a tag to trigger the real job:"
echo "    git tag v1.x.x"
echo "    git push origin v1.x.x"
echo "========================================"
