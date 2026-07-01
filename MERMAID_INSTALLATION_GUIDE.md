# 📊 Mermaid 安裝指南 — 獲取可執行文件

> 如何安裝和使用 Mermaid 來渲染圖表

---

## 🎯 三種主要方式

### **方式 1：在線編輯器（最簡單，推薦）✅**

**無需安裝任何東西，直接使用！**

```
https://mermaid.live/
```

步驟：
1. 打開 https://mermaid.live/
2. 粘貼生成的 Mermaid 代碼
3. 實時查看圖表
4. 導出為 PNG/SVG

**優點：**
- ✅ 無需安裝
- ✅ 跨平台（在線）
- ✅ 實時預覽
- ✅ 支援導出

**缺點：**
- ❌ 需要網絡連接
- ❌ 無法自動化

---

### **方式 2：Mermaid CLI (mmdc)（本地安裝）**

#### **安裝方法**

**步驟 1: 安裝 Node.js**

下載頁面：https://nodejs.org/

選擇 LTS 版本（推薦）

```bash
# 驗證安裝
node --version
npm --version
```

**步驟 2: 安裝 mermaid-cli**

```bash
# 全局安裝
npm install -g @mermaid-js/mermaid-cli

# 或本地安裝（在項目目錄中）
npm install @mermaid-js/mermaid-cli
```

**步驟 3: 驗證安裝**

```bash
mmdc --version
```

#### **使用方法**

**生成 SVG**
```bash
mmdc -i diagram.mmd -o diagram.svg
```

**生成 PNG**
```bash
mmdc -i diagram.mmd -o diagram.png -e png
```

**完整示例**
```bash
# 1. 創建 Mermaid 文件
cat > flowchart.mmd << 'END'
graph TD
    Start([Start])
    A[Process A]
    B{Decision}
    C[Process C]
    End([End])
    
    Start --> A
    A --> B
    B -->|Yes| C
    B -->|No| End
    C --> End
END

# 2. 生成 SVG
mmdc -i flowchart.mmd -o flowchart.svg

# 3. 生成 PNG
mmdc -i flowchart.mmd -o flowchart.png -e png

# 4. 查看結果
open flowchart.svg  # macOS
xdg-open flowchart.svg  # Linux
start flowchart.svg  # Windows
```

#### **常用選項**

```bash
mmdc -i input.mmd -o output.svg          # SVG 輸出
mmdc -i input.mmd -o output.png -e png   # PNG 輸出
mmdc -i input.mmd -o output.pdf -e pdf   # PDF 輸出（需要額外依賴）

# 配置主題
mmdc -i input.mmd -o output.svg -t dark

# 指定寬度和高度
mmdc -i input.mmd -o output.png -w 1200 -H 800
```

---

### **方式 3：Docker（容器化）**

**無需安裝 Node.js，使用 Docker 執行**

```bash
# 拉取 Mermaid CLI 鏡像
docker pull minlag/mermaid-cli

# 運行
docker run --rm -v $(pwd):/data minlag/mermaid-cli mmdc -i diagram.mmd -o diagram.svg

# Windows PowerShell
docker run --rm -v ${PWD}:/data minlag/mermaid-cli mmdc -i diagram.mmd -o diagram.svg

# Windows CMD
docker run --rm -v %cd%:/data minlag/mermaid-cli mmdc -i diagram.mmd -o diagram.svg
```

---

## 🚀 快速開始（推薦方案）

### **選項 A：使用在線編輯器（最快）**

```
1. 打開 https://mermaid.live/
2. 粘貼 Mermaid 代碼
3. 看圖表渲染
4. 導出為 PNG/SVG
```

### **選項 B：本地安裝 mermaid-cli**

```bash
# Windows/macOS/Linux 統一步驟

# 1. 安裝 Node.js (如果未安裝)
# 訪問 https://nodejs.org/

# 2. 安裝 mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# 3. 創建 diagram.mmd 文件
cat > diagram.mmd << 'END'
[粘貼您的 Mermaid 代碼]
END

# 4. 生成 PNG
mmdc -i diagram.mmd -o diagram.png -e png

# 5. 查看圖表
# Windows: start diagram.png
# macOS: open diagram.png
# Linux: xdg-open diagram.png
```

---

## 📋 安裝檢查清單

```
安裝 Node.js:
  □ 訪問 https://nodejs.org/
  □ 下載 LTS 版本
  □ 運行安裝程序
  □ 重啟終端/命令行
  □ 驗證: node --version, npm --version

安裝 mermaid-cli:
  □ 打開終端/命令行
  □ 運行: npm install -g @mermaid-js/mermaid-cli
  □ 等待安裝完成
  □ 驗證: mmdc --version

使用:
  □ 創建 .mmd 文件
  □ 粘貼 Mermaid 代碼
  □ 運行 mmdc 命令
  □ 查看輸出
```

---

## 🐛 常見問題

### **Q1: mmdc 命令未找到**

```
A: 確認已安裝並重啟終端
  
  # 檢查安裝位置
  npm list -g @mermaid-js/mermaid-cli
  
  # 重新安裝
  npm uninstall -g @mermaid-js/mermaid-cli
  npm install -g @mermaid-js/mermaid-cli
```

### **Q2: 生成 PNG 失敗**

```
A: 可能缺少 chromium 依賴
  
  # 重新安裝（帶依賴）
  npm install -g @mermaid-js/mermaid-cli --build-from-source
  
  # 或使用在線編輯器導出
```

### **Q3: Windows 中文路徑問題**

```
A: 使用帶引號的路徑
  
  mmdc -i "C:\用戶\名稱\diagram.mmd" -o "C:\用戶\名稱\diagram.png" -e png
```

### **Q4: 權限拒絕**

```
A: 使用 sudo (macOS/Linux)
  
  sudo npm install -g @mermaid-js/mermaid-cli
```

---

## 📚 在不同環境中使用

### **Windows**

```batch
REM 安裝
npm install -g @mermaid-js/mermaid-cli

REM 使用
mmdc -i diagram.mmd -o diagram.png -e png
start diagram.png
```

### **macOS**

```bash
# 安裝
npm install -g @mermaid-js/mermaid-cli

# 使用
mmdc -i diagram.mmd -o diagram.png -e png
open diagram.png
```

### **Linux**

```bash
# 安裝
npm install -g @mermaid-js/mermaid-cli

# 使用
mmdc -i diagram.mmd -o diagram.png -e png
xdg-open diagram.png
```

---

## 🔗 相關資源

| 資源 | URL |
|------|-----|
| Mermaid 在線編輯器 | https://mermaid.live/ |
| Mermaid 官方文檔 | https://mermaid.js.org/ |
| mermaid-cli GitHub | https://github.com/mermaid-js/mermaid-cli |
| Node.js 官方網站 | https://nodejs.org/ |
| Docker 官方鏡像 | https://hub.docker.com/r/minlag/mermaid-cli |

---

## 💡 在 WinMerge AI Exporter 中集成

### **自動導出圖表**

修改 `gui/mermaid_panel.py` 中的 `export_png` 方法：

```python
def export_png(self):
    """Export diagram as PNG using mermaid-cli."""
    import subprocess
    
    # 檢查 mermaid-cli
    result = subprocess.run(['mmdc', '--version'], capture_output=True)
    if result.returncode != 0:
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.current_mermaid_code)
        messagebox.showinfo(
            "已複製到剪貼板",
            "Mermaid 代碼已複製。\n\n"
            "在 mermaid.live 中粘貼以查看圖表。\n\n"
            "或安裝 mermaid-cli:\n"
            "npm install -g @mermaid-js/mermaid-cli"
        )
        return
    
    # 生成 PNG
    # ...
```

---

## ✅ 最終建議

| 場景 | 推薦方式 |
|------|---------|
| **快速查看圖表** | 在線編輯器 (mermaid.live) |
| **自動化生成** | mermaid-cli |
| **無需安裝** | 在線編輯器 |
| **持續集成** | Docker 或 mermaid-cli |
| **不想安裝** | 在線編輯器 |

**推薦：** 大多數用戶應該使用 **在線編輯器**，無需安裝任何東西！

---

**Last Updated**: 2026-06-28
