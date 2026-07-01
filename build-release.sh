#!/bin/bash
################################################################################
# WinMerge AI Exporter — 一鍵發佈構建腳本
# 
# 功能：打包應用供外部使用，隱藏源代碼
# 推薦方案：PyInstaller (最簡單、最易用)
#
# 使用方法：
#   chmod +x build-release.sh
#   ./build-release.sh
#
# 輸出：
#   - dist/WinMergeAIExporter-gui-1.2.2.exe  (GUI 應用)
#   - dist/WinMergeAIExporter-cli-1.2.2.exe  (CLI 工具)
#   - release/WinMergeAIExporter-1.2.2.zip   (完整發行版)
################################################################################

set -e

# Read version from VERSION file if it exists (kept in sync by
# deploy-local.sh); otherwise fall back to a hardcoded default so this
# script still works standalone.
if [ -f VERSION ]; then
    VERSION=$(cat VERSION | tr -d '[:space:]')
else
    VERSION="1.2.2"
fi
PROJECT_NAME="WinMergeAIExporter"
DIST_DIR="dist"
RELEASE_DIR="release"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔨 開始構建 $PROJECT_NAME v$VERSION${NC}"
echo ""

# ============================================================================
# 步驟 1：檢查依賴
# ============================================================================
echo -e "${YELLOW}📋 步驟 1: 檢查依賴...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 錯誤：Python 3 未安裝${NC}"
    exit 1
fi

if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  PyInstaller 未安裝，正在安裝...${NC}"
    pip install pyinstaller -q
fi

echo -e "${GREEN}✅ 依賴檢查完成${NC}"
echo ""

# ============================================================================
# 步驟 2：清理舊版本
# ============================================================================
echo -e "${YELLOW}📋 步驟 2: 清理舊版本...${NC}"

rm -rf build $DIST_DIR *.spec __pycache__ .pytest_cache
mkdir -p $RELEASE_DIR

echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

# ============================================================================
# 步驟 3：運行測試
# ============================================================================
echo -e "${YELLOW}📋 步驟 3: 運行測試...${NC}"

if ! python3 -m pytest tests/ -q 2>/dev/null; then
    echo -e "${YELLOW}⚠️  測試有問題，仍然繼續構建${NC}"
else
    echo -e "${GREEN}✅ 所有測試通過${NC}"
fi
echo ""

# ============================================================================
# 步驟 4：打包 GUI 應用
# ============================================================================
echo -e "${YELLOW}📋 步驟 4: 打包 GUI 應用...${NC}"

python3 -m PyInstaller \
    gui/launcher.py \
    --onefile \
    --windowed \
    --name="${PROJECT_NAME}-gui-${VERSION}" \
    --distpath=./$DIST_DIR \
    --buildpath=./build \
    --specpath=./ \
    --add-data="LICENSE:." \
    --hidden-import=tkinter \
    --noconfirm \
    2>/dev/null

echo -e "${GREEN}✅ GUI 應用打包完成${NC}"
echo ""

# ============================================================================
# 步驟 5：打包 CLI 工具
# ============================================================================
echo -e "${YELLOW}📋 步驟 5: 打包 CLI 工具...${NC}"

python3 -m PyInstaller \
    -m winmerge_ai_exporter.cli \
    --onefile \
    --name="${PROJECT_NAME}-cli-${VERSION}" \
    --distpath=./$DIST_DIR \
    --buildpath=./build \
    --specpath=./ \
    --add-data="LICENSE:." \
    --noconfirm \
    2>/dev/null

echo -e "${GREEN}✅ CLI 工具打包完成${NC}"
echo ""

# ============================================================================
# 步驟 6：創建發行版本目錄
# ============================================================================
echo -e "${YELLOW}📋 步驟 6: 創建發行版本...${NC}"

RELEASE_FOLDER="${RELEASE_DIR}/${PROJECT_NAME}-${VERSION}"
mkdir -p "$RELEASE_FOLDER"

# 複製可執行文件
cp "$DIST_DIR"/${PROJECT_NAME}-gui-${VERSION}* "$RELEASE_FOLDER/" 2>/dev/null || true
cp "$DIST_DIR"/${PROJECT_NAME}-cli-${VERSION}* "$RELEASE_FOLDER/" 2>/dev/null || true

# 複製必要檔案
cp LICENSE "$RELEASE_FOLDER/"
cp README.md "$RELEASE_FOLDER/"

# 創建快速開始指南（簡化版，無源代碼路徑）
cat > "$RELEASE_FOLDER/QUICKSTART.txt" << 'EOF'
# WinMerge AI Review Exporter v1.2.2

## 快速開始

### Windows
1. 雙擊 WinMergeAIExporter-gui-1.2.2.exe
2. 選擇 Patch 檔案或文件夾
3. 選擇 Redaction 模式（推薦：api-safe）
4. 點擊 Export 按鈕

### macOS/Linux 
./WinMergeAIExporter-cli-1.2.2 export --patch changes.patch --output ./review

## 功能
✅ 導出 WinMerge Diffs 為 AI 可理解的格式
✅ 多種 Redaction 模式：
   - api-safe：隱藏內部實現，保留公開 API (推薦)
   - api-safe-comments：保留註解，更容易理解
   - full：完全隱藏（最安全）
   - signature：只顯示函數簽名

✅ 風險評分和架構分析
✅ Token 估計和 LLM API 成本計算

## 許可證
MIT License - 詳見 LICENSE 檔案
Original Author: Claude (Anthropic)
Copyright (c) 2024-2025

## 支持
如有問題，請查閱 README.md 檔案
EOF

echo -e "${GREEN}✅ 發行版本創建完成${NC}"
echo ""

# ============================================================================
# 步驟 7：打包為 ZIP
# ============================================================================
echo -e "${YELLOW}📋 步驟 7: 打包為 ZIP...${NC}"

cd "$RELEASE_DIR"
zip -r "${PROJECT_NAME}-${VERSION}.zip" "${PROJECT_NAME}-${VERSION}/" -q
cd ..

echo -e "${GREEN}✅ ZIP 打包完成${NC}"
echo ""

# ============================================================================
# 步驟 8：清理臨時文件
# ============================================================================
echo -e "${YELLOW}📋 步驟 8: 清理臨時文件...${NC}"

rm -rf build *.spec

echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

# ============================================================================
# 完成
# ============================================================================
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║          ✅ 構建完成！ — v$VERSION                          ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📂 輸出檔案：${NC}"
echo ""
echo "  GUI 應用（Windows）："
echo "  📄 $DIST_DIR/${PROJECT_NAME}-gui-${VERSION}.exe"
echo ""
echo "  CLI 工具："
echo "  📄 $DIST_DIR/${PROJECT_NAME}-cli-${VERSION}.exe"
echo ""
echo "  完整發行版本（推薦發佈）："
echo "  📦 $RELEASE_DIR/${PROJECT_NAME}-${VERSION}.zip"
echo ""
echo -e "${YELLOW}📋 發行版本內容：${NC}"
echo "  - ${PROJECT_NAME}-gui-${VERSION}.exe (GUI 應用)"
echo "  - ${PROJECT_NAME}-cli-${VERSION}.exe (CLI 工具)"
echo "  - LICENSE (MIT 許可證)"
echo "  - README.md (詳細說明)"
echo "  - QUICKSTART.txt (快速開始)"
echo ""
echo -e "${YELLOW}🚀 發佈建議：${NC}"
echo "  1. 上傳 .zip 檔案到 GitHub Releases"
echo "  2. 或上傳到你的網站供下載"
echo "  3. 外部用戶下載後可直接運行，無需安裝 Python"
echo ""
echo -e "${GREEN}✨ 完成！${NC}"
