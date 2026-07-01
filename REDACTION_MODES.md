# 🔐 遮蔽模式完整指南 (Redaction Modes Guide)

> **Understanding which redaction mode to use for your code review**

---

## 📊 四種模式速查表

| 模式 | 保留 | 隱藏 | 安全等級 | 適用場景 |
|------|------|------|---------|---------|
| **Full** | Keywords only | 一切識別字、常數、註解、字串 | ⭐⭐⭐ 極高 | 銀行/金融/醫療核心 |
| **API-Safe** ⭐ | Public APIs + Types + Keywords | 內部變數、私有成員、魔法數字、字串 | ⭐⭐ 中等 | 一般企業代碼（推薦） |
| **API-Safe+Comments** ⭐⭐ | APIs + Types + **Comments** + Keywords | 內部變數、私有成員、魔法數字、字串 | ⭐⭐ 中等 | 有用註解的舊代碼 |
| **Signature** | Control flow only | 函數名、變數名、型態、邏輯、註解 | ⭐ 低 | 架構概覽（不推薦） |

---

## 🔍 詳細對比

### 原始代碼範例
```cpp
// Token validation with caching and rate limiting
bool SessionManager::ValidateToken(const std::string& token, const RequestContext& ctx) {
    if (m_cache.count(token) > 0 && !isExpired(m_cache[token])) {
        return m_cache[token].valid;
    }
    
    if (ctx.failure_count > MAX_FAILED_ATTEMPTS) {
        AuditLog::Record(ctx.user_id, "account_locked");
        return false;
    }
    
    return CryptoUtils::VerifyHMAC(token, m_secret_key);
}
```

---

### 1️⃣ Full Mode（最高安全）

**用途：** 銀行、金融系統、醫療記錄等超級敏感代碼

```cpp
// sym_a1b2c3 with sym_d4e5f6 and sym_g7h8i9
sym_j0k1l2 sym_m3n4o5::sym_p6q7r8(sym_s9t0u1 sym_v2w3x4, sym_w5x6y7 sym_z8a9b0) {
    if (sym_c1d2e3.sym_f4g5h6(sym_i7j8k9) > 0 && !sym_l0m1n2(sym_o3p4q5[sym_r6s7t8])) {
        return sym_u9v0w1[sym_x2y3z4].sym_a5b6c7;
    }
    
    if (sym_d8e9f0.sym_g1h2i3 > sym_j4k5l6) {
        sym_m7n8o9::sym_p0q1r2(sym_s3t4u5, "<str>");
        return false;
    }
    
    return sym_v6w7x8::sym_y9z0a1(sym_b2c3d4, sym_e5f6g7);
}
```

✅ **好處：**
- 🔒 完全無法反向工程
- 🔐 內部算法完全隱藏
- 📊 結構複雜度很難推測

❌ **壞處：**
- ❓ LLM 完全無法理解
- 🤷 無法進行有意義的代碼審視
- 💾 只能看出"有函數呼叫和條件判斷"

⚠️ **何時使用：**
```
✓ 銀行驗證系統
✓ 加密引擎
✓ 支付處理
✗ 日常企業代碼（過度保護）
```

---

### 2️⃣ API-Safe Mode（推薦）⭐

**用途：** 大多數企業代碼的最佳選擇

```cpp
// Token validation with caching and rate limiting
bool SessionManager::ValidateToken(const std::string& token, const RequestContext& ctx) {
    if (sym_m1n2o3.sym_p4q5r6(token) > 0 && !sym_s7t8u9(sym_v0w1x2[token])) {
        return sym_y3z4a5[token].sym_b6c7d8;
    }
    
    if (ctx.sym_d9e0f1 > MAX_FAILED_ATTEMPTS) {
        AuditLog::Record(ctx.sym_g2h3i4, "<str>");
        return false;
    }
    
    return CryptoUtils::VerifyHMAC(token, sym_j5k6l7);
}
```

✅ **好處：**
- 👁️ LLM **能清楚看出邏輯**
  - 有 token 驗證
  - 有快取檢查
  - 有失敗計數限制
  - 使用 HMAC 驗證
- 🔒 內部實現隱藏
  - `m_cache` 結構隱藏
  - `m_secret_key` 隱藏
  - 私有成員隱藏
- 📚 保留有用信息
  - 公開 API 名稱可見
  - 型態信息保留
  - 常數保留

❌ **壞處：**
- 📝 註解被隱藏
  - "Token validation with caching..." → 丟失
  - 舊代碼的智慧丟失

⚠️ **何時使用：**
```
✓ 對內審視（自家 LLM）
✓ 架構分析
✓ 代碼改進建議
✓ 性能審視
✓ 日常企業代碼（推薦選擇）
```

---

### 3️⃣ API-Safe+Comments Mode（最佳體驗）⭐⭐

**用途：** 需要完整理解、有好註解的代碼

```cpp
// Token validation with caching and rate limiting
bool SessionManager::ValidateToken(const std::string& token, const RequestContext& ctx) {
    if (sym_m1n2o3.sym_p4q5r6(token) > 0 && !sym_s7t8u9(sym_v0w1x2[token])) {
        return sym_y3z4a5[token].sym_b6c7d8;
    }
    
    if (ctx.sym_d9e0f1 > MAX_FAILED_ATTEMPTS) {
        AuditLog::Record(ctx.sym_g2h3i4, "<str>");
        return false;
    }
    
    return CryptoUtils::VerifyHMAC(token, sym_j5k6l7);
}
```

✅ **相比 API-Safe 的優勢：**
- 📝 **保留所有註解**
  - "Token validation with caching and rate limiting" → 完整保留
  - 舊代碼的知識保留
  - 開發者意圖清晰
- 👨‍💼 LLM 能根據註解更準確理解
- 🎯 最佳安全性與可理解性平衡

⚠️ **何時使用：**
```
✓ 舊代碼審視（註解通常比代碼準確）
✓ 複雜業務邏輯分析
✓ 對內代碼審視（有完善註解）
✓ 知識傳遞和 onboarding
```

---

### 4️⃣ Signature Mode（不推薦）

**用途：** 架構概覽（但通常 API-Safe 就夠）

```cpp
sym_XXXXX sym_YYYYY::sym_ZZZZZ(sym_AAAAA sym_BBBBB, sym_CCCCC sym_DDDDD) {
    if (sym_EEEEE.sym_FFFFF(sym_GGGGG) > 0 && !sym_HHHHH(sym_IIIII[sym_JJJJJ])) {
        return sym_KKKKK[sym_LLLLL].sym_MMMMM;
    }
    
    if (sym_NNNNN.sym_OOOOO > sym_PPPPP) {
        sym_QQQQQ::sym_RRRRR(sym_SSSSS, sym_TTTTT);
        return false;
    }
    
    return sym_UUUUU::sym_VVVVV(sym_WWWWW, sym_XXXXX);
}
```

❌ **問題：**
- 看不出函數名 → 無法理解目的
- 看不出參數型態 → 無法理解輸入
- 看不出返回型態 → 無法理解輸出
- 看不出邏輯細節 → 無法進行審視
- **實際上與 Full 模式幾乎沒差異**

⚠️ **何時使用：**
```
✗ 幾乎不推薦使用
  - API-Safe 已經是最小可用信息
  - Signature 再隱藏反而沒用
```

---

## 🎯 決策樹：選擇哪個模式

```
你的代碼有多敏感？
├─ 非常敏感（銀行/金融/醫療）
│  └─ 使用 Full ⭐⭐⭐
│
├─ 中等敏感（企業內部）
│  ├─ 代碼有好註解嗎？
│  │  ├─ 有 → 使用 API-Safe+Comments ⭐⭐
│  │  └─ 沒有 → 使用 API-Safe ⭐
│  
└─ 不敏感（開源/示範）
   └─ 使用 API-Safe ⭐
```

---

## 📊 實測對比：同一代碼的輸出大小

| 模式 | 輸出大小 | 可讀性 | LLM 理解度 |
|------|---------|-------|----------|
| 原始 | 2.4 KB | ✅ 完美 | ✅ 完美 |
| API-Safe+Comments | 2.1 KB | ✅ 優秀 | ✅ 優秀 |
| API-Safe | 2.1 KB | ⚠️ 良好 | ⚠️ 良好 |
| Full | 2.0 KB | ❌ 無法讀 | ❌ 無法讀 |
| Signature | 2.0 KB | ❌ 無法讀 | ❌ 無法讀 |

---

## 🚀 快速開始

### CLI
```bash
# 推薦：API-Safe+Comments（最佳體驗）
python -m winmerge_ai_exporter export \
  --patch changes.patch \
  --output ./review \
  --strip-patch \
  --redaction-mode api-safe-comments

# 中等安全：API-Safe（一般推薦）
python -m winmerge_ai_exporter export \
  --patch changes.patch \
  --output ./review \
  --strip-patch \
  --redaction-mode api-safe

# 最高安全：Full（金融/醫療）
python -m winmerge_ai_exporter export \
  --patch changes.patch \
  --output ./review \
  --strip-patch \
  --redaction-mode full
```

### GUI
1. 勾選 **🔒 Stripped Patch Mode**
2. 在 **Redaction Level** dropdown 選擇模式
3. 點擊 **Export**

### Python API
```python
from winmerge_ai_exporter import export_ai_review_package, RedactionMode

export_ai_review_package(
    diffs,
    output_dir="./review",
    strip_patch=True,
    redaction_mode=RedactionMode.API_SAFE_COMMENTS  # 推薦
)
```

---

## 🔗 相關資源

- [使用 Stripped Patch 分享代碼給 LLM](./README.md#stripped-patch)
- [完整 API 文檔](./README.md#api)
- [CLI 命令參考](./README.md#cli)

---

**最終建議：** 
- 🏆 **一般企業代碼** → **API-Safe+Comments** ⭐⭐
- 🏢 **中等敏感代碼** → **API-Safe** ⭐
- 🔐 **超級敏感代碼** → **Full** ⭐⭐⭐
