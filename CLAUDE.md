# CLAUDE.md - Desktop Auth SDK

## 專案概述

**專案名稱**：Desktop Auth SDK  
**專案類型**：Python SDK 套件  
**版本**：1.0.0  
**目的**：提供通用的桌面應用程式授權機制，讓新軟體可以快速整合 shpquery.com 的用戶授權系統

## 已整合專案

| 專案 | 狀態 | 說明 |
|------|------|------|
| ThreadsBot | ✅ 已整合 | Threads 自動發文機器人 |

## 技術架構

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.8+ |
| HTTP | httpx（異步支援）|
| 異步 | asyncio |
| 打包 | setuptools |

## 檔案結構

```
desktop-auth-sdk/
├── desktop_auth/
│   ├── __init__.py      # 套件入口，匯出 DesktopAuth, License
│   ├── auth.py          # 核心授權邏輯
│   └── utils.py         # 工具函數（機器碼、路徑）
├── setup.py             # 套件安裝設定
├── requirements.txt     # 依賴套件
├── README.md            # 使用說明
├── CLAUDE.md            # 本文件
└── .gitignore
```

## 核心元件

### DesktopAuth 類別

主要的授權檢查器，提供以下功能：

1. **本地授權快取**：檢查和儲存授權檔案
2. **遠端驗證**：向伺服器驗證 token 有效性
3. **登入流程**：開啟瀏覽器進行 Google 登入
4. **輪詢機制**：等待用戶完成網頁授權

### License 資料類別

儲存授權資訊：
- token: JWT token
- email: 用戶 email
- name: 用戶名稱
- machine_id: 電腦識別碼
- app_name: 應用程式名稱
- created_at: 授權時間

## API 端點（後端）

後端位於 `shopee-affiliate-query-system` 專案。

| 端點 | 方法 | 說明 |
|------|------|------|
| /api/desktop/request-auth | POST | 請求授權碼 |
| /api/desktop/verify | POST | 驗證 token |
| /api/desktop/check-auth/:code | GET | 輪詢授權狀態 |
| /api/desktop/confirm-auth | POST | 確認授權（網頁端呼叫）|

## 授權流程

```
1. 程式啟動，檢查 .{app_name}_license 檔案
2. 若有本地授權：
   - 驗證 machine_id 是否匹配
   - 向伺服器驗證 token
   - 有效則進入程式
3. 若無授權或驗證失敗：
   - 呼叫 /api/desktop/request-auth 取得授權碼
   - 開啟瀏覽器到登入頁面
   - 輪詢 /api/desktop/check-auth/:code
   - 用戶登入後取得 token
   - 儲存授權檔案
```

## 機器碼生成

```python
import hashlib
import platform
import uuid

info = f"{platform.node()}-{platform.machine()}-{uuid.getnode()}"
machine_id = hashlib.sha256(info.encode()).hexdigest()[:32]
```

組合以下資訊：
- platform.node(): 電腦名稱
- platform.machine(): CPU 架構
- uuid.getnode(): MAC 地址

## 使用範例

### 基本使用

```python
from desktop_auth import DesktopAuth

auth = DesktopAuth(app_name="MyApp")
if auth.check():
    print(f"歡迎 {auth.user_name}")
```

### 整合 Rich UI

```python
from desktop_auth import DesktopAuth

auth = DesktopAuth(
    app_name="MyApp",
    on_status=lambda msg: ui.show_message(msg)
)
```

## 安裝方式

```bash
pip install git+https://github.com/age731129/desktop-auth-sdk.git
```

## 開發注意事項

1. **跨平台相容**：確保 Windows/Mac/Linux 都能正常運作
2. **編碼處理**：檔案讀寫使用 UTF-8 編碼
3. **錯誤處理**：網路錯誤要優雅處理，不能讓程式崩潰
4. **異步支援**：提供 check() 和 check_async() 兩種方式
5. **PyInstaller 支援**：utils.py 的 get_app_dir() 支援打包後的路徑

## 安全考量

1. Token 儲存在本地檔案，建議加入 .gitignore
2. Machine ID 綁定，防止授權檔案被複製
3. Token 有過期時間（30 天），需定期驗證
4. 所有 API 通訊使用 HTTPS

## 相關專案

- **shopee-affiliate-query-system**：後端 API 和前端授權頁面
- **ThreadsBot**：第一個整合此 SDK 的桌面應用

## 版本歷史

### v1.0.0 (2026-01-09)
- 初始版本
- 基本授權流程
- Google OAuth 整合
- 機器碼綁定
