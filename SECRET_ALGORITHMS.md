# ⚙️ 機密算法與拖曳改進指南 — v1.2.2

> 關於信號處理、跳頻等敏感算法的處理，以及優化的文件選擇體驗

---

## 1️⃣ 機密算法處理 (Secret Algorithms)

### 問題
信號處理、跳頻、自適應算法等涉及專利或機密的代碼，即使被遮蔽也可能從註解中推斷出來。

### 各模式的處理

#### **Full 模式** ⭐⭐⭐
```cpp
// 原始 - Airoha AB1565 跳頻算法
void ChannelAdaptation::UpdateChannel() {
    // 使用 LMS 算法自適應
    float error = signal - predicted;
    mu = 0.001;
    weights += mu * error * prev_signal;
    freq = baseFreq + hopSequence[count % 37];
}
```

```cpp
// Full 模式輸出
sym_a1b2 sym_c3d4::sym_e5f6() {
    // sym_g7h8 sym_i9j0 sym_k1l2 sym_m3n4
    sym_o5p6 sym_q7r8 = sym_s9t0 - sym_u1v2;
    sym_w3x4 = <n>;
    sym_y5z6 += sym_a7b8 * sym_c9d0 * sym_e1f2;
    sym_g3h4 = sym_i5j6 + sym_k7l8[sym_m9n0 % <n>];
}
```

✅ **優勢**：
- 完全隱藏算法意圖
- 即使有註解也看不出是什麼算法
- 最高安全級別

❌ **劣勢**：
- LLM 無法理解代碼目的
- 無法進行有意義的代碼審視
- 代碼維護困難

**推薦：** 金融交易算法、加密引擎、專利算法

---

#### **API-Safe 模式** 🏆
```cpp
// API-Safe 模式輸出
// sym_a1b2 sym_c3d4 sym_e5f6
void ChannelAdaptation::UpdateChannel() {
    // sym_g7h8 sym_i9j0 sym_k1l2 sym_m3n4
    float sym_o5p6 = sym_q7r8 - sym_s9t0;
    sym_u1v2 = <n>;
    sym_w3x4 += sym_y5z6 * sym_a7b8 * sym_c9d0;
    sym_e1f2 = sym_g3h4 + sym_i5j6[sym_k7l8 % <n>];
}
```

⚠️ **問題**：
- 註解也被隱藏了，無法推斷算法
- 但如果有代碼結構洩露（如 `freq = ... + hopSequence[... % 37]`），仍可能暗示跳頻

✅ **優勢**：
- API 名稱保留，基本功能清楚
- 註解遮蔽防止意圖洩露
- 安全性和可讀性平衡

**推薦：** 一般企業代碼、信號處理邏輯

---

#### **api-safe-comments 模式** ⭐⭐
```cpp
// api-safe-comments 模式輸出
// Airoha AB1565 跳頻算法 ← 註解暴露了算法！
void ChannelAdaptation::UpdateChannel() {
    // 使用 LMS 算法自適應 ← 明確告訴你用的是 LMS
    float sym_o5p6 = sym_q7r8 - sym_s9t0;
    sym_u1v2 = <n>;
    sym_w3x4 += sym_y5z6 * sym_a7b8 * sym_c9d0;
    sym_e1f2 = sym_g3h4 + sym_i5j6[sym_k7l8 % <n>];
}
```

❌ **風險**：
- 註解清晰暴露了算法 ("Airoha AB1565", "LMS 算法", "跳頻")
- LLM 從註解就能推斷算法機制

✅ **優勢**：
- 對於**非敏感算法**最佳理解度
- 註解幫助理解意圖
- 對於舊代碼審視很有用

**不推薦用於：** 專利算法、機密信號處理

---

### 📊 機密算法處理對比表

| 考量 | Full | API-Safe | api-safe-comments |
|------|------|----------|-------------------|
| **算法意圖隱蔽** | ✅✅✅ | ✅✅ | ❌ 註解暴露 |
| **代碼可讀性** | ❌ | ⚠️ | ✅ |
| **安全級別** | 極高 | 中等 | 中等 |
| **適合敏感算法** | ✅ 是 | ⚠️ 有風險 | ❌ 否 |
| **適合普通代碼** | ❌ 過度 | ✅ 推薦 | ✅⭐ |

---

## 2️⃣ 改進的文件選擇 (File Selection)

### ❌ 原有問題
- **拖曳功能不工作** → 系統顯示禁止符號 🚫
- tkinter 原生不支持跨應用拖曳
- 拖曳需要額外的 tkinterdnd 庫

### ✅ 改進方案

#### **方法 1：使用 Browse 按鈕** 🖱️
```
最直接、跨平台最相容的方法
1. 點擊 "Browse…" 按鈕
2. 選擇文件/文件夾
3. 自動填入路徑
```

#### **方法 2：鍵盤粘貼 (Ctrl+V)** ⌨️
```
最快速的替代方案
1. 複製路徑到剪貼板
   Windows: Ctrl+Shift+C (在文件瀏覽器)
   macOS:   Cmd+Option+C
   Linux:   根據文件管理器
2. 點擊 Entry 框
3. 按 Ctrl+V 自動填入
```

#### **方法 3：直接編輯路徑** ✏️
```
適合已知路徑或複製粘貼
1. 點擊 Entry 框
2. 手動輸入或粘貼路徑
3. 支持相對路徑和絕對路徑
```

### 🎯 GUI 改進

#### **清晰的標籤和提示**
```
📄 Patch/Diff File:          [         Browse…]  (Ctrl+V to paste)
📋 Left File (old):          [         Browse…]  (Ctrl+V to paste)
📋 Right File (new):         [         Browse…]  (Ctrl+V to paste)
📁 Left Folder (old):        [         Browse…]  (Ctrl+V to paste)
📁 Right Folder (new):       [         Browse…]  (Ctrl+V to paste)
```

✅ **優勢**：
- 清晰的圖標（📄 📋 📁）區分文件/文件夾
- 明確的 "Ctrl+V to paste" 提示
- Browse 按鈕更顯眼

---

## 3️⃣ 建議的文件選擇工作流

### 場景 A：快速編輯已知路徑 ⚡
```
1. 複製已有的路徑 (Ctrl+C)
2. 在 Entry 框中 Ctrl+V
3. 修改必要部分（如果需要）
4. 按 Export
```

### 場景 B：瀏覽磁盤選擇文件 🖱️
```
1. 點擊 "Browse…" 按鈕
2. 導航到文件位置
3. 選擇文件/文件夾
4. 按 "開啟" 或 "選擇"
5. 路徑自動填入
6. 按 Export
```

### 場景 C：從文件管理器拖曳（Windows）
```
❌ 不再支持直接拖曳（tkinter 限制）

改進：
1. 在文件管理器中右鍵點擊文件
2. 複製路徑 (或 Shift+Ctrl+C)
3. 回到應用程序
4. Ctrl+V 粘貼
5. 按 Export
```

---

## 📋 常見問題

### Q: 拖曳功能為什麼移除了？
**A:** tkinter 不支持原生拖曳。顯示禁止符號 🚫 會造成混淆。現在用 Browse 按鈕和 Ctrl+V 粘貼更可靠。

### Q: 機密算法用什麼模式最安全？
**A:** **Full 模式** 最安全。如果代碼含有專利算法，絕對不要用 `api-safe-comments`（會在註解中暴露）。

### Q: Ctrl+V 粘貼不工作怎麼辦？
**A:** 
1. 確保在 Entry 框中（點擊後會看到光標）
2. 確保路徑在剪貼板中（Ctrl+C 複製）
3. 使用 "Browse…" 按鈕作為替代

### Q: 可以直接拖曳文件到應用嗎？
**A:** 
- ❌ 不能直接拖進 Entry 框
- ✅ 可以複製路徑然後 Ctrl+V
- ✅ 使用 Browse 按鈕選擇

---

## 🔒 安全性建議

### 敏感代碼清單

| 類型 | 模式 | 理由 |
|------|------|------|
| **專利算法** | Full ⭐⭐⭐ | 完全隱蔽 |
| **跳頻/自適應** | Full ⭐⭐⭐ | 防止意圖洩露 |
| **加密實現** | Full ⭐⭐⭐ | 安全關鍵 |
| **安全驗證** | API-Safe ⭐⭐ | 隱藏實現細節 |
| **業務邏輯** | API-Safe ⭐⭐ | 內部處理隱蔽 |
| **普通代碼** | API-Safe ⭐⭐ | 推薦 |
| **有好註解的代碼** | api-safe-comments | 保留註解幫助理解 |

---

## 💡 最佳實踐

```
✅ DO:
- 使用 Browse 按鈕選擇文件
- 複製完整路徑然後粘貼
- 敏感代碼用 Full 模式
- 優先考慮 API-Safe + 好的代碼審視

❌ DON'T:
- 嘗試拖曳文件到 Entry（不支持）
- 用 api-safe-comments 分享機密算法
- 依賴自動路徑檢測（使用明確的 Browse）
- 在註解中暴露敏感信息（如果用 api-safe-comments）
```

---

**版本：** v1.2.2  
**改進日期：** 2026-06-24  
**下一版本計劃：** tkinterdnd 集成（可選）
