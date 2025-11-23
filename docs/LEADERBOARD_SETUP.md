# Leaderboard Setup Guide

## 功能說明
遊戲現在支援**全球排行榜**功能，使用 GitHub Gist 作為雲端儲存。朋友們可以看到彼此的分數並互相競爭！

---

## 設定步驟 (5分鐘)

### Step 1: 建立 GitHub Gist

1. 登入你的 GitHub 帳號
2. 前往 https://gist.github.com/
3. 點擊右上角 **"+"** → **"New gist"**
4. 設定如下：
   - **Filename**: `tetris_leaderboard.json`
   - **Content**:
     ```json
     {
       "casual": [],
       "classic": [],
       "crazy": []
     }
     ```
   - **Public/Secret**: 選擇 **Public** (這樣所有人都能讀取)
5. 點擊 **"Create public gist"**
6. **複製 Gist ID** (網址最後一段)
   - 例如：`https://gist.github.com/jeffery0629/abc123def456`
   - Gist ID 就是 `abc123def456`

---

### Step 2: 建立 GitHub Personal Access Token

1. 前往 GitHub Settings: https://github.com/settings/tokens
2. 點擊 **"Generate new token"** → **"Generate new token (classic)"**
3. 設定：
   - **Note**: `Tetris Leaderboard`
   - **Expiration**: `No expiration` (或選擇你想要的期限)
   - **Scopes**: 只勾選 **`gist`** (允許讀寫 Gist)
4. 點擊 **"Generate token"**
5. **複製 Token** (只會顯示一次！請妥善保存)
   - 格式類似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### Step 3: 設定環境變數

#### 方案A：本地桌面版 (PyInstaller .exe)

建立檔案 `.env` 在專案根目錄：
```bash
# d:/Jeffery/claire/.env
GIST_ID=abc123def456
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**注意**：`.env` 檔案不會被提交到 Git (已在 .gitignore)

#### 方案B：Web 版 (GitHub Pages)

需要在 **GitHub Actions Secrets** 設定：

1. 前往你的 repo: https://github.com/jeffery0629/tetris-web
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **"New repository secret"**
4. 新增兩個 secrets：
   - Name: `GIST_ID`, Value: `abc123def456`
   - Name: `GITHUB_TOKEN`, Value: `ghp_xxx...`

5. 修改 `.github/workflows/deploy-pygbag.yml`，在 build 步驟前加入：
   ```yaml
   - name: Set environment variables
     run: |
       echo "GIST_ID=${{ secrets.GIST_ID }}" >> $GITHUB_ENV
       echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> $GITHUB_ENV
   ```

---

### Step 4: 安裝依賴套件

排行榜功能需要 `requests` 套件：

```bash
# 使用 uv 安裝
uv pip install requests

# 或使用 pip
pip install requests
```

---

### Step 5: 測試排行榜

1. 啟動遊戲
2. 完成一局遊戲
3. Game Over 時會自動顯示排行榜
4. 確認能看到 "No scores yet!" 或已有的分數

---

## 使用說明

### 玩家流程

1. **遊戲結束** → Game Over 畫面彈出
2. **輸入 Player ID** → 最多12字元的暱稱
3. **自動上傳** → 成績提交到雲端
4. **查看排行** → 自動顯示該模式 Top 10

### 排行榜特點

- ✅ **即時更新**：朋友們玩完立刻看到
- ✅ **分模式排行**：Casual / Classic / Crazy 各自獨立
- ✅ **Top 10 顯示**：顯示前10名
- ✅ **自動排序**：依分數高到低
- ✅ **高亮顯示**：你的成績會用橘色標記
- ✅ **防止膨脹**：每個模式最多保留100筆紀錄

---

## 離線模式

如果沒有設定 `GIST_ID` 和 `GITHUB_TOKEN`：
- ✅ 遊戲可以正常遊玩
- ❌ 排行榜功能會停用
- ℹ️ 不會顯示錯誤，只是無法上傳/查看分數

---

## 安全性注意事項

### GitHub Token 安全
- ❌ **絕對不要**將 Token 提交到 Git
- ✅ Token 只有 `gist` 權限（無法存取你的其他資料）
- ✅ 可隨時在 GitHub 撤銷 Token

### Gist 公開性
- ⚠️ Gist 是公開的，任何人都能讀取
- ⚠️ 理論上有人可以手動編輯 Gist 作弊
- ℹ️ 如果發現作弊，可以在 Gist 頁面手動刪除該筆紀錄

### 建議作法
- 定期備份 Gist (GitHub 會保留版本歷史)
- 如果 Token 洩漏，立即到 GitHub Settings 撤銷舊 Token 並重新生成

---

## 常見問題

### Q: 為什麼上傳失敗？
A: 檢查：
1. `.env` 檔案是否存在且格式正確
2. `GIST_ID` 和 `GITHUB_TOKEN` 是否正確
3. 網路連線是否正常
4. GitHub Token 是否過期或被撤銷

### Q: 可以看到排行榜但無法上傳？
A: Token 可能只有讀取權限，需要重新生成並勾選 `gist` scope

### Q: 多個玩家同時上傳會衝突嗎？
A: 程式已實作重試機制（最多3次），20人以下使用不會有問題

### Q: 如何手動管理排行榜？
A: 前往你的 Gist 頁面：
- 查看所有分數
- 手動編輯 JSON
- 查看修改歷史 (右上角 "Revisions")
- 刪除作弊成績

### Q: 如何關閉排行榜功能？
A: 刪除 `.env` 檔案或移除 `GIST_ID` / `GITHUB_TOKEN` 環境變數

---

## 進階：本地測試

如果想在不影響正式排行榜的情況下測試：

1. 建立第二個 Gist (測試用)
2. 在 `.env` 使用測試 Gist ID
3. 測試完畢後改回正式 Gist ID

---

## 技術細節

- **儲存格式**：JSON (純文字)
- **資料大小**：每筆約 100 bytes，100 筆 = 10KB
- **API 限制**：5000 次/小時 (使用 Token)
- **快取機制**：30 秒本地快取減少 API 呼叫
- **重試機制**：最多 3 次，指數退避 (0.5s → 1.0s → 1.5s)
- **併發處理**：樂觀鎖 (Optimistic Locking)

---

## 支援

如有問題請在 GitHub Issues 回報：
https://github.com/jeffery0629/tetris-web/issues

祝遊戲愉快！💖
