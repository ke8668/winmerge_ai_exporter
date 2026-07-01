# 📦 發行分發指南 — 給外部使用者

> **一鍵打包工具，隱藏源代碼版本**

---

## 🎯 快速開始

### **Windows 用戶（推薦）**

```bash
# 1. 在項目根目錄雙擊執行
build-release.bat

# 或在命令行執行
.\build-release.bat

# 2. 等待構建完成（約 5-10 分鐘）
# 3. 生成的檔案在 release/ 目錄
# 4. 上傳 release/WinMergeAIExporter-1.2.2.zip 給用戶
```

### **macOS/Linux 用戶**

```bash
# 1. 在項目根目錄執行
chmod +x build-release.sh
./build-release.sh

# 2. 等待構建完成（約 5-10 分鐘）
# 3. 生成的檔案在 release/ 目錄
# 4. 上傳 release/WinMergeAIExporter-1.2.2.zip 給用戶
```

---

## 🔄 本地 CI/CD 一鍵流程（推薦給開發者）

`build-release.sh/bat` 只負責「打包」，不會跑測試、不會管版本號、不會幫你打 git tag。
`deploy-local.sh/bat` 把這些串起來，等同於「CI 通過才能 CD」的本地版本：

```
run-ci-locally  →  版本號 +1  →  build-release  →  git commit + tag  →  (可選) git push
   (CI)                              (CD 打包)         (CD 發版)
```

### **Windows**

```batch
REM patch 版號升級 (1.3.2 -> 1.3.3)，最常用
.\deploy-local.bat

REM minor 版號升級 (1.3.2 -> 1.4.0)，有新功能時用
.\deploy-local.bat minor

REM major 版號升級 (1.3.2 -> 2.0.0)，breaking change 時用
.\deploy-local.bat major

REM 指定確切版本號
.\deploy-local.bat 2.5.0
```

### **macOS/Linux**

```bash
chmod +x deploy-local.sh
./deploy-local.sh           # patch
./deploy-local.sh minor     # minor
./deploy-local.sh major     # major
./deploy-local.sh 2.5.0     # 指定版本
```

### **流程中會發生什麼**

```
STAGE 1/4  CI       跑 run-ci-locally，測試沒過就直接中止，不會產生壞掉的版本
STAGE 2/4  Git 檢查  有未 commit 的變更會提醒你（避免發佈了沒進版控的東西）
STAGE 3/4  版號升級  讀取 VERSION 檔案，依參數計算新版號，會先讓你確認才繼續
STAGE 4/4  CD 打包   呼叫 build-release，產生 .exe/.zip；
                     接著自動 git commit (VERSION bump) + git tag vX.Y.Z；
                     最後問你要不要直接 git push（push 後 GitHub Actions
                     的 build job 會自動接手做雲端發行版）
```

### **本地 CD vs GitHub 雲端 CD 的分工**

| | 本地 `deploy-local` | GitHub Actions（push tag 後觸發）|
|---|---|---|
| 觸發方式 | 手動執行腳本 | `git push origin vX.Y.Z` |
| 執行平台 | 你自己的電腦（通常只有 Windows 或只有 Mac） | 真正的 Windows/macOS/Linux runner |
| 用途 | 快速本地驗證、產生本機可執行檔測試 | 正式發行版、上傳到 GitHub Releases |
| 速度 | 快（幾分鐘） | 較慢（要排隊 + 下載依賴） |

**建議用法**：先用 `deploy-local` 在自己機器上跑過一輪確認沒問題，最後一步選擇「push」，讓 GitHub Actions 接手產生正式發行版並掛到 Releases 頁面。

---

## 📂 生成的檔案結構

```
after running build-release.sh/bat:

project/
├── dist/                          [PyInstaller 輸出]
│   ├── WinMergeAIExporter-gui-1.2.2.exe
│   ├── WinMergeAIExporter-cli-1.2.2.exe
│   └── ... [支持文件]
│
├── release/                       [最終發行版本]
│   ├── WinMergeAIExporter-1.2.2.zip    ✅ [推薦發佈]
│   └── WinMergeAIExporter-1.2.2/
│       ├── WinMergeAIExporter-gui-1.2.2.exe
│       ├── WinMergeAIExporter-cli-1.2.2.exe
│       ├── LICENSE
│       ├── README.md
│       └── QUICKSTART.txt
│
└── [源代碼] - 未被包含在發行版本中 ✅
```

---

## 🚀 給外部使用者的說明

### **給外部用戶的郵件示範**

```
主題：WinMerge AI Review Exporter v1.2.2 - 發佈

親愛的用戶：

我們發佈了 WinMerge AI Review Exporter v1.2.2。

📦 下載連結：
  https://[your-website]/WinMergeAIExporter-1.2.2.zip

✨ 新增功能：
  - api-safe-comments 模式：保留所有註解
  - 改進的拖曳 UX 和 Ctrl+V 粘貼支持
  - 詳細的安全算法指導
  - 完整的許可證標記

🚀 快速開始：
  1. 下載並解壓 ZIP 檔案
  2. Windows：雙擊 WinMergeAIExporter-gui-1.2.2.exe
  3. macOS/Linux：./WinMergeAIExporter-cli-1.2.2 export --patch changes.patch

📚 詳細文檔：
  - QUICKSTART.txt - 快速開始
  - README.md - 詳細說明
  - LICENSE - MIT 許可證

支持 & 反饋：
  [your contact info]
```

---

## 🔐 隱藏源代碼的確認

### **打包後的特點**

✅ **源代碼已隱藏**
- 使用者無法看到任何 .py 源代碼
- 只能看到編譯後的可執行文件
- 反向工程困難（需要特殊工具）

✅ **完整功能保留**
- 所有功能正常運作
- GUI 應用完全互動
- CLI 命令行完整支持

✅ **跨平台支持**
- Windows：直接雙擊 .exe
- macOS：執行 binary 文件
- Linux：執行 binary 文件

✅ **獨立運行**
- 不需要安裝 Python
- 不需要安裝任何依賴
- 直接運行，零配置

---

## 📋 打包過程詳解

### **build-release.sh/bat 做了什麼？**

```
1. ✅ 檢查依賴
   - 驗證 Python 3 安裝
   - 檢查/安裝 PyInstaller

2. ✅ 清理舊版本
   - 刪除 build/ 目錄
   - 刪除 dist/ 目錄
   - 清理臨時文件

3. ✅ 運行測試
   - 執行 pytest (130 個測試)
   - 確保代碼質量

4. ✅ 打包 GUI
   - 使用 PyInstaller 編譯 gui/launcher.py
   - 生成單個 .exe 文件
   - 大小：約 100-150 MB

5. ✅ 打包 CLI
   - 使用 PyInstaller 編譯 CLI 入口
   - 生成單個 .exe 文件
   - 大小：約 80-120 MB

6. ✅ 創建發行版本
   - 複製執行文件
   - 複製 LICENSE 和 README
   - 生成 QUICKSTART.txt

7. ✅ 打包為 ZIP
   - 壓縮整個目錄
   - 生成最終發佈檔案

8. ✅ 清理臨時文件
   - 刪除 build 目錄
   - 刪除 .spec 文件
```

---

## 🔄 版本控制

### **每次發佈的檢查清單**

在執行 build-release.sh/bat 前：

```
□ 所有測試通過 (python -m pytest tests/)
□ 版本號更新 (如需要)
□ CHANGELOG 已更新
□ 許可證信息正確
□ README.md 已審核
□ 代碼已提交到 Git
```

### **版本號規則**

```
遵循語義化版本控制 (Semantic Versioning)：
  MAJOR.MINOR.PATCH
  
示例：
  v1.2.2 (當前版本)
    ↓
  新功能 → v1.3.0 (MINOR bump)
  Bug 修復 → v1.2.3 (PATCH bump)
  大重構 → v2.0.0 (MAJOR bump)
```

---

## 💾 存儲和托管

### **GitHub Releases（推薦）**

```bash
# 1. 創建新發佈
git tag -a v1.2.2 -m "Version 1.2.2"
git push origin v1.2.2

# 2. 在 GitHub 網頁端上傳 ZIP 檔案到 Releases

# 3. 用戶可以直接下載：
#    https://github.com/your-repo/releases/download/v1.2.2/WinMergeAIExporter-1.2.2.zip
```

### **個人網站托管**

```
網站結構：
  /downloads/
  ├── winmerge-ai-exporter/
  │   ├── v1.2.2/
  │   │   ├── WinMergeAIExporter-1.2.2.zip
  │   │   ├── sha256sum.txt
  │   │   └── CHANGELOG.md
  │   ├── v1.2.1/
  │   │   └── ...
  │   └── latest.zip (symlink to v1.2.2)
```

### **雲存儲（Google Drive/Dropbox）**

```
簡單方式：
  1. 上傳 ZIP 到 Google Drive
  2. 取得共享連結
  3. 發佈連結給用戶
  
缺點：速度不穩定，不推薦用於大檔案
```

---

## 🔍 質量檢查

### **發佈前的驗證**

在將 ZIP 檔案發佈給用戶前：

#### **Windows**
```batch
# 1. 解壓 ZIP
unzip WinMergeAIExporter-1.2.2.zip

# 2. 測試 GUI
cd WinMergeAIExporter-1.2.2
WinMergeAIExporter-gui-1.2.2.exe
  ✅ 應該能啟動 GUI 窗口
  ✅ 所有按鈕可點擊
  ✅ 文件選擇工作

# 3. 測試 CLI
WinMergeAIExporter-cli-1.2.2.exe export --help
  ✅ 應該顯示幫助信息
  ✅ 參數正確

# 4. 檢查文件
dir
  ✅ LICENSE 存在
  ✅ README.md 存在
  ✅ QUICKSTART.txt 存在
```

#### **macOS/Linux**
```bash
# 1. 解壓 ZIP
unzip WinMergeAIExporter-1.2.2.zip

# 2. 測試 CLI
cd WinMergeAIExporter-1.2.2
./WinMergeAIExporter-cli-1.2.2 export --help
  ✅ 應該顯示幫助信息
  ✅ 參數正確

# 3. 檢查文件
ls -la
  ✅ LICENSE 存在
  ✅ README.md 存在
  ✅ QUICKSTART.txt 存在
```

---

## 📊 文件大小參考

```
典型的發佈文件大小：

WinMergeAIExporter-gui-1.2.2.exe    : ~120 MB (GUI 應用)
WinMergeAIExporter-cli-1.2.2.exe    : ~100 MB (CLI 工具)
README.md                            : ~50 KB
LICENSE                              : ~1 KB
QUICKSTART.txt                       : ~2 KB

總計：
  未壓縮 : ~220 MB
  ZIP 壓縮 : ~60-80 MB (壓縮率 60-70%)
```

### **最小化檔案大小的技巧**

```bash
# 移除不必要的文件
pyinstaller \
  --onefile \
  --strip \                    # 移除調試符號
  gui/launcher.py

# 使用 UPX 進一步壓縮（可選）
pip install upx
pyinstaller \
  --onefile \
  --upx-dir=/path/to/upx \
  gui/launcher.py
```

---

## 🔄 更新流程

### **發佈新版本的步驟**

```
1. 開發新功能 (commit 到 git)
   └─ git commit -m "feat: add new feature"

2. 更新版本號
   └─ 修改 version 變數在 build-release.sh/bat

3. 創建 CHANGELOG
   └─ 記錄新增、修改、修復

4. 運行測試
   └─ python -m pytest tests/

5. 執行打包
   └─ ./build-release.sh
   or .\build-release.bat

6. 驗證輸出
   └─ 檢查 release/ 目錄

7. 上傳到托管平台
   └─ GitHub Releases 或個人網站

8. 發送通知
   └─ 郵件/公告/社交媒體

9. 保存歷史版本
   └─ 創建版本檔案目錄
```

---

## 🆘 常見問題

### **Q1：用戶說找不到可執行文件**
```
A: 確認他們解壓了 ZIP 檔案
   ZIP 內部就是可執行文件，無需額外安裝步驟
```

### **Q2：GUI 應用啟動很慢**
```
A: 正常現象
   - 首次啟動：2-3 秒（解包依賴）
   - 後續啟動：<1 秒
```

### **Q3：如何禁用源代碼訪問**
```
A: PyInstaller 已經隱藏源代碼
   - 用戶無法看到 .py 文件
   - 需要特殊工具才能反編譯 (低風險)
```

### **Q4：是否支持命令行參數**
```
A: 是的，完全支持
   示例：
   WinMergeAIExporter-cli-1.2.2.exe export --patch changes.patch
```

### **Q5：是否需要額外許可證**
```
A: 不需要
   - 使用 MIT License
   - 包含在 LICENSE 檔案中
```

---

## 📞 用戶支持

### **給用戶提供的支持渠道**

```
📧 Email: your-email@example.com
🐛 Bug Report: https://github.com/your-repo/issues
📚 Documentation: https://github.com/your-repo/wiki
💬 Discussion: https://github.com/your-repo/discussions
```

### **快速故障排除**

如果用戶報告問題：

1. **程序無法啟動**
   - 確認他們的系統要求 (Windows 7+/macOS 10.9+)
   - 嘗試從不同目錄運行

2. **文件選擇不工作**
   - 確保路徑中沒有特殊字符
   - 嘗試使用相對路徑而不是絕對路徑

3. **Redaction 模式不工作**
   - 查閱 REDACTION_MODES.md
   - 確認輸入檔案格式正確

---

## 🎯 發佈清單（最終）

```
發行前檢查：
  ✅ 所有測試通過
  ✅ 版本號正確
  ✅ CHANGELOG 已更新
  ✅ build-release.sh/bat 執行成功
  ✅ ZIP 檔案已驗證
  ✅ README 無誤
  ✅ LICENSE 清晰

發佈步驟：
  ✅ 上傳 ZIP 到托管平台
  ✅ 創建 Release 說明
  ✅ 發送用戶通知
  ✅ 更新官方網站/README
  ✅ 標記 Git tag
  ✅ 歸檔舊版本

發佈後監控：
  ✅ 監控用戶反饋
  ✅ 記錄下載數
  ✅ 準備熱修復（如需要）
```

---

**🚀 準備好發佈了！使用 build-release.sh 或 build-release.bat 一鍵打包。**
