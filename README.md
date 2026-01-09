# Desktop Auth SDK

通用桌面應用程式授權 SDK，整合 shpquery.com 用戶系統。

## 安裝

```bash
pip install git+https://github.com/age731129/desktop-auth-sdk.git
```

## 使用方式

```python
from desktop_auth import DesktopAuth

def main():
    # 初始化授權
    auth = DesktopAuth(
        app_name="YourAppName",  # 你的軟體名稱
        auth_server="https://api.shpquery.com"
    )
    
    # 檢查授權
    if not auth.check():
        print("授權失敗，程式退出")
        input("按 Enter 鍵退出...")
        return
    
    # 授權成功，繼續執行
    print(f"歡迎 {auth.user_name}!")
    print(f"Email: {auth.user_email}")
    
    # ... 你的程式邏輯 ...

if __name__ == "__main__":
    main()
```

## 自訂狀態訊息

```python
def my_status_handler(message: str):
    print(f"[狀態] {message}")

auth = DesktopAuth(
    app_name="MyApp",
    on_status=my_status_handler
)
```

## 與 Rich UI 整合

```python
from rich.console import Console
from desktop_auth import DesktopAuth

console = Console()

auth = DesktopAuth(
    app_name="MyApp",
    on_status=lambda msg: console.print(f"[cyan]{msg}[/cyan]")
)
```

## API 參數

### DesktopAuth

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| app_name | str | ✅ | 應用程式名稱 |
| auth_server | str | ❌ | 授權伺服器網址，預設 `https://api.shpquery.com` |
| license_file | str | ❌ | 授權檔案路徑，預設 `.{app_name}_license` |
| on_status | Callable | ❌ | 狀態回調函數 |

### 屬性

| 屬性 | 類型 | 說明 |
|------|------|------|
| user_email | str | 已授權用戶的 email |
| user_name | str | 已授權用戶的名稱 |
| is_authorized | bool | 是否已授權 |

### 方法

| 方法 | 說明 |
|------|------|
| check() | 同步檢查授權 |
| check_async() | 異步檢查授權 |

## 授權流程

```
程式啟動
    │
    ▼
檢查本地授權檔案 (.xxx_license)
    │
    ├── 有 → 向伺服器驗證
    │         │
    │         ├── 有效 → 進入程式
    │         └── 無效 → 刪除授權 → 登入流程
    │
    └── 沒有 → 登入流程
                 │
                 ▼
           開啟瀏覽器 → Google 登入
                 │
                 ▼
           等待授權完成 → 儲存授權 → 進入程式
```

## 注意事項

- 需要網路連線進行授權驗證
- 授權綁定電腦，換電腦需重新授權
- 用戶需在 shpquery.com 審核通過才能使用
- 授權檔案儲存在執行檔同目錄

## 錯誤處理

```python
from desktop_auth import DesktopAuth

auth = DesktopAuth(app_name="MyApp")

if not auth.check():
    # 授權失敗的處理
    print("無法驗證授權，可能的原因：")
    print("1. 網路連線問題")
    print("2. 帳號未通過審核")
    print("3. 授權已過期")
    return

# 正常執行
```

## License

MIT License
