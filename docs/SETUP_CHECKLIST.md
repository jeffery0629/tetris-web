# GitHub Gist 排行榜設定檢查清單

## 你需要做的事情 ✅

### 1️⃣ 建立 GitHub Gist (2分鐘)
- [ ] 前往 https://gist.github.com/
- [ ] 建立新 Gist，檔名：`tetris_leaderboard.json`
- [ ] 內容貼上：
  ```json
  {
    "casual": [],
    "classic": [],
    "crazy": []
  }
  ```
- [ ] 設定為 **Public**
- [ ] 複製 Gist ID (網址最後一段)
  - 範例：`https://gist.github.com/你的帳號/abc123` → ID 是 `abc123`

---

### 2️⃣ 建立 GitHub Token (2分鐘)
- [ ] 前往 https://github.com/settings/tokens
- [ ] 點 "Generate new token (classic)"
- [ ] Note: 填 `Tetris Leaderboard`
- [ ] **只勾選** `gist` 權限
- [ ] 點 "Generate token"
- [ ] 複製 Token (只顯示一次！)
  - 格式：`ghp_xxxxxxxxxxxx...`

---

### 3️⃣ 在 Repo 設定環境變數 (1分鐘)

建立檔案 `d:/Jeffery/claire/.env`：
```bash
GIST_ID=你的Gist_ID
GITHUB_TOKEN=你的Token
```

**範例**：
```bash
GIST_ID=abc123def456789
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
```

---

### 4️⃣ 安裝套件 (30秒)
```bash
cd d:/Jeffery/claire
uv pip install requests python-dotenv
```

---

### 5️⃣ 程式碼整合 (10分鐘)

參考 `INTEGRATION_EXAMPLE.py` 修改 `src/tetris/game.py`：

**必要修改**：
1. 加 import
2. `__init__` 初始化 leaderboard_manager
3. `lock_block` 改變 game over 狀態
4. `handle_event` 處理輸入和排行榜
5. `render` 繪製新畫面

**或者讓我幫你修改** - 只要說「幫我整合排行榜」

---

## 測試步驟 🧪

### 本地測試
```bash
cd d:/Jeffery/claire
python src/tetris/main.py
```

1. 選擇任一模式開始遊戲
2. 故意 Game Over
3. 應該會彈出「Enter Your Player ID」輸入框
4. 輸入暱稱 → 按 Enter
5. 應該顯示排行榜（第一次會是空的）
6. 多玩幾次，確認分數有累積

---

## 檢查是否正常運作

✅ **成功的標誌**：
- Game Over 後彈出輸入框
- 輸入 ID 後看到排行榜畫面
- 前往 Gist 網頁，看到 JSON 已更新

❌ **失敗的標誌**：
- 輸入框沒出現 → 檢查 `.env` 是否存在
- 顯示 "Offline mode" → 檢查環境變數是否載入
- 上傳失敗 → 檢查 Token 權限和網路

---

## Web 版額外設定 (GitHub Pages)

如果要在 Web 版啟用排行榜：

1. 前往 https://github.com/jeffery0629/tetris-web/settings/secrets/actions
2. 新增兩個 secrets：
   - `GIST_ID`
   - `GITHUB_TOKEN`
3. 修改 `.github/workflows/deploy-pygbag.yml`
4. Push 後自動部署

詳見 `LEADERBOARD_SETUP.md` 的「方案B」

---

## 完成後

🎉 **恭喜！你的遊戲現在有全球排行榜了！**

朋友們玩遊戲時：
1. 輸入自己的 ID
2. 互相看得到彼此的分數
3. 競爭第一名！

---

## 需要協助？

如果遇到問題：
1. 檢查 console 是否有錯誤訊息
2. 確認 `.env` 檔案格式正確（沒有多餘空格或引號）
3. 測試 Gist 是否可以手動開啟網頁
4. 回報問題時附上錯誤訊息

或直接說「排行榜出問題了，錯誤訊息是 XXX」
