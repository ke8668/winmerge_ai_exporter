#!/bin/bash
################################################################################
# deploy-local.sh — Local CI/CD Pipeline (macOS/Linux)
#
# This is the local equivalent of what GitHub Actions does automatically
# when you push a tag:
#   1. CI:  Run tests (run-ci-locally.sh logic)
#   2. CD:  Bump version, build executables, tag, and optionally push
#
# Usage:
#   ./deploy-local.sh             # patch bump (1.3.2 -> 1.3.3)
#   ./deploy-local.sh minor       # minor bump (1.3.2 -> 1.4.0)
#   ./deploy-local.sh major       # major bump (1.3.2 -> 2.0.0)
#   ./deploy-local.sh 1.5.0       # set exact version
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BUMP_ARG="${1:-patch}"

echo -e "${YELLOW}"
echo "================================================================================"
echo " 🚀 Local CI/CD Pipeline"
echo "================================================================================"
echo -e "${NC}"

# ----------------------------------------------------------------------------
# Step 0: Pre-flight checks
# ----------------------------------------------------------------------------
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ git not found in PATH${NC}"
    exit 1
fi

if [ ! -f VERSION ]; then
    echo "1.3.2" > VERSION
    echo "ℹ️  No VERSION file found — created one starting at 1.3.2"
fi

CURRENT_VERSION=$(cat VERSION | tr -d '[:space:]')
echo "Current version: $CURRENT_VERSION"
echo ""

# ----------------------------------------------------------------------------
# Step 1: CI — Run tests. Hard stop on failure (no broken version ships).
# ----------------------------------------------------------------------------
echo -e "${YELLOW}================================================================================${NC}"
echo -e "${YELLOW} 📋 STAGE 1/4: CI — Running tests${NC}"
echo -e "${YELLOW}================================================================================${NC}"
echo ""

if ! ./run-ci-locally.sh; then
    echo ""
    echo -e "${RED}❌ CI FAILED — deployment aborted. Fix tests before deploying.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ CI passed${NC}"
echo ""

# ----------------------------------------------------------------------------
# Step 2: Check working tree is clean
# ----------------------------------------------------------------------------
echo -e "${YELLOW}================================================================================${NC}"
echo -e "${YELLOW} 📋 STAGE 2/4: Checking git status${NC}"
echo -e "${YELLOW}================================================================================${NC}"
echo ""

if ! git diff --quiet; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes.${NC}"
    echo ""
    git status --short
    echo ""
    read -p "Continue anyway? Uncommitted changes will NOT be in the tagged release. (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Aborted. Commit your changes first."
        exit 1
    fi
fi

echo -e "${GREEN}✅ Git status checked${NC}"
echo ""

# ----------------------------------------------------------------------------
# Step 3: Compute new version number (CD versioning step)
# ----------------------------------------------------------------------------
echo -e "${YELLOW}================================================================================${NC}"
echo -e "${YELLOW} 📋 STAGE 3/4: Version bump${NC}"
echo -e "${YELLOW}================================================================================${NC}"
echo ""

NEW_VERSION=$(python3 -c "
v = '$CURRENT_VERSION'.split('.')
maj, mn, p = int(v[0]), int(v[1]), int(v[2])
arg = '$BUMP_ARG'
if arg.count('.') == 2:
    print(arg)
elif arg == 'major':
    print(f'{maj+1}.0.0')
elif arg == 'minor':
    print(f'{maj}.{mn+1}.0')
else:
    print(f'{maj}.{mn}.{p+1}')
")

echo "New version: $CURRENT_VERSION -> $NEW_VERSION"
echo ""

read -p "Proceed with build + tag v$NEW_VERSION? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo "$NEW_VERSION" > VERSION

# ----------------------------------------------------------------------------
# Step 4: CD — Build executables, tag, commit
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}================================================================================${NC}"
echo -e "${YELLOW} 📋 STAGE 4/4: CD — Building and tagging release${NC}"
echo -e "${YELLOW}================================================================================${NC}"
echo ""

chmod +x build-release.sh
./build-release.sh

echo ""
echo -e "${GREEN}✅ Build complete${NC}"
echo ""

# Commit the version bump
git add VERSION
git commit -m "chore(release): bump version to v${NEW_VERSION}"

# Tag
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"

echo ""
echo -e "${GREEN}✅ Tagged v${NEW_VERSION} locally${NC}"
echo ""

# ----------------------------------------------------------------------------
# Step 5: Ask before pushing (push = triggers GitHub Actions release job)
# ----------------------------------------------------------------------------
read -p "Push commit + tag to GitHub now? This triggers the Actions release job. (y/N): " PUSH_CONFIRM
if [[ "$PUSH_CONFIRM" =~ ^[Yy]$ ]]; then
    git push
    git push origin "v${NEW_VERSION}"
    echo ""
    echo -e "${GREEN}✅ Pushed. Check GitHub Actions tab for the automated release build.${NC}"
else
    echo ""
    echo "ℹ️  Not pushed. To push later, run:"
    echo "    git push && git push origin v${NEW_VERSION}"
fi

echo ""
echo -e "${GREEN}================================================================================${NC}"
echo -e "${GREEN} ✅ Local CI/CD complete — v${NEW_VERSION}${NC}"
echo -e "${GREEN}================================================================================${NC}"
echo ""
echo "📂 Local artifacts:"
echo "   release/WinMergeAIExporter-${NEW_VERSION}.zip"
echo "   dist/WinMergeAIExporter-gui-${NEW_VERSION}.exe"
echo "   dist/WinMergeAIExporter-cli-${NEW_VERSION}.exe"
echo ""
