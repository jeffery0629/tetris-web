# Claire's Tetris 💖

俄羅斯方塊遊戲，專為 Claire 打造的休閒益智遊戲。

## 🎮 遊戲特色

- **3 種遊戲模式**：Casual (簡單) / Classic (經典) / Crazy (瘋狂)
- **27 種方塊**：Tromino (3格) + Tetromino (4格) + Pentomino (5格)
- **6 種道具**：炸彈、磁鐵、時間凍結、重力反轉、橡皮擦、幽靈模式
- **全球排行榜**：與朋友們分享成績並競爭！
- **跨平台**：桌面版 (Windows) + Web 版 (瀏覽器)

## 🚀 快速開始

### 線上遊玩 (Web 版)
👉 https://jeffery0629.github.io/tetris-web

### 本地安裝 (桌面版)

```bash
# 1. Clone 專案
git clone https://github.com/jeffery0629/claire.git
cd claire

# 2. 安裝依賴 (使用 uv)
uv pip install -e .

# 3. 執行遊戲
python main.py
```

## 📚 文檔

- **[遊戲說明](docs/HOW_TO_PLAY.md)** - 遊戲規則與操作
- **[產品規格](docs/product_spec.md)** - 完整設計文件
- **[開發進度](docs/PROGRESS.md)** - 開發歷程
- **[排行榜設定](docs/LEADERBOARD_SETUP.md)** - 啟用全球排行榜
- **[快速設定](docs/SETUP_CHECKLIST.md)** - 5 分鐘設定清單

## 🎯 遊戲模式

| 模式 | 格子大小 | 方塊種類 | 道具 | 分數倍率 |
|------|---------|---------|------|---------|
| **Casual** | 8×16 | 2 種 (3格) | ✅ | ×0.8 |
| **Classic** | 10×20 | 7 種 (4格) | ❌ | ×1.0 |
| **Crazy** | 12×22 | 18 種 (5格) | ✅ | ×2.0 |

## 🎮 操作方式

### 鍵盤 (桌面版)
- `←` `→` - 左右移動
- `↓` - 加速下降
- `↑` - 順時針旋轉
- `Z` - 逆時針旋轉
- `空白鍵` - 瞬間落下
- `C` - 保留方塊
- `E` - 使用道具
- `P` / `ESC` - 暫停

### 觸控 (Web/行動版)
- **左右區域** - 點擊移動方塊
- **ROT 按鈕** - 旋轉方塊
- **DROP 按鈕** - 瞬間落下
- **PWR 按鈕** - 使用道具
- **HLD 按鈕** - 保留方塊

## 🏆 排行榜功能

遊戲支援全球排行榜！朋友們可以看到彼此的分數。

**設定步驟**：
1. 建立 GitHub Gist 和 Personal Access Token
2. 設定環境變數 (`.env` 檔案)
3. 完整說明請見 [排行榜設定指南](docs/LEADERBOARD_SETUP.md)

## 🛠️ 技術棧

- **語言**: Python 3.10+
- **遊戲引擎**: Pygame 2.5.0+
- **套件管理**: uv
- **Web 版**: Pygbag (Pygame → WebAssembly)
- **排行榜**: GitHub Gist API
- **部署**: GitHub Pages + GitHub Actions

## 📁 專案結構

```
claire/
├── src/tetris/         # 遊戲原始碼
│   ├── main.py         # 主程式入口
│   ├── game.py         # 遊戲邏輯
│   ├── board.py        # 棋盤系統
│   ├── renderer.py     # 渲染引擎
│   ├── powerup.py      # 道具系統
│   ├── leaderboard_manager.py  # 排行榜管理
│   └── ...
├── docs/               # 文檔
├── images/             # 圖片資源
├── tests/              # 測試
└── main.py             # 啟動腳本
```

## 🔧 開發

### 執行測試
```bash
pytest tests/ -v
```

### 打包 Windows 執行檔
```bash
pyinstaller --onefile --windowed main.py
```

### 部署 Web 版
Push 到 `main` 分支後，GitHub Actions 會自動部署到 GitHub Pages。

## 📝 版本歷史

- **v1.0** - 基礎遊戲 (Classic 模式)
- **v1.1** - 新增 Simple 和 Crazy 模式
- **v1.2** - 道具系統
- **v1.3** - Web 版部署
- **v1.4** - 觸控操作優化
- **v1.5** - 全球排行榜功能 ⭐ (當前版本)

## 🤝 貢獻

這是私人專案，但如果你有建議或發現 Bug：
- 開 Issue: https://github.com/jeffery0629/tetris-web/issues

## 📄 授權

MIT License - 自由使用與修改

## ❤️ 特別感謝

給 Claire 的遊戲 💝

---

Made with ❤️ by Jeffery
