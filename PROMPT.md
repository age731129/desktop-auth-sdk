# PROMPT.md - Claude Code 建立指令

請將以下內容複製給 Claude Code 執行。

---

## 任務：建立 Desktop Auth SDK 套件

這是一個通用的桌面應用程式授權 SDK，讓新軟體可以快速整合 shpquery.com 的用戶授權系統。

## 建立以下檔案結構：

```
desktop-auth-sdk/
├── desktop_auth/
│   ├── __init__.py
│   ├── auth.py
│   └── utils.py
├── setup.py
├── requirements.txt
├── README.md
├── CLAUDE.md
└── .gitignore
```

---

## 1. desktop_auth/__init__.py

```python
from .auth import DesktopAuth, License

__version__ = "1.0.0"
__all__ = ["DesktopAuth", "License"]
```

---

## 2. desktop_auth/utils.py

```python
import sys
import hashlib
import platform
import uuid
from pathlib import Path


def get_machine_id() -> str:
    """取得電腦唯一識別碼"""
    info = f"{platform.node()}-{platform.machine()}-{uuid.getnode()}"
    return hashlib.sha256(info.encode()).hexdigest()[:32]


def get_app_dir() -> Path:
    """取得應用程式所在目錄（支援 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包後
        return Path(sys.executable).parent
    else:
        # 開發環境
        return Path.cwd()
```

---

## 3. desktop_auth/auth.py

```python
"""
通用桌面應用授權 SDK

使用方式：
    from desktop_auth import DesktopAuth
    
    auth = DesktopAuth(
        app_name="YourAppName",
        auth_server="https://api.shpquery.com"
    )
    
    if auth.check():
        print(f"歡迎 {auth.user_name}!")
        # 繼續執行程式...
"""

import json
import time
import webbrowser
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable
import httpx

from .utils import get_machine_id, get_app_dir


@dataclass
class License:
    """授權資訊"""
    token: str
    email: str
    name: str
    machine_id: str
    app_name: str
    created_at: float


class DesktopAuth:
    """桌面應用授權檢查器"""
    
    def __init__(
        self,
        app_name: str,
        auth_server: str = "https://api.shpquery.com",
        license_file: str = None,
        on_status: Callable[[str], None] = None
    ):
        """
        初始化授權檢查器
        
        Args:
            app_name: 應用程式名稱（例如 "ThreadsBot"）
            auth_server: 授權伺服器網址
            license_file: 授權檔案路徑（預設為 .{app_name}_license）
            on_status: 狀態回調函數（用於顯示訊息）
        """
        self.app_name = app_name
        self.auth_server = auth_server.rstrip('/')
        
        if license_file:
            self.license_file = Path(license_file)
        else:
            self.license_file = get_app_dir() / f".{app_name.lower()}_license"
        
        self.on_status = on_status or (lambda msg: print(f"[AUTH] {msg}"))
        self.license: Optional[License] = None
    
    def _load_license(self) -> Optional[License]:
        """讀取本地授權"""
        if not self.license_file.exists():
            return None
        try:
            data = json.loads(self.license_file.read_text(encoding='utf-8'))
            return License(**data)
        except Exception:
            return None
    
    def _save_license(self, license: License):
        """儲存授權"""
        data = {
            'token': license.token,
            'email': license.email,
            'name': license.name,
            'machine_id': license.machine_id,
            'app_name': license.app_name,
            'created_at': license.created_at
        }
        self.license_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def _delete_license(self):
        """刪除授權"""
        if self.license_file.exists():
            self.license_file.unlink()
    
    async def _verify_token(self, token: str, machine_id: str) -> tuple:
        """向伺服器驗證 token"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.auth_server}/api/desktop/verify",
                    json={
                        'token': token,
                        'machineId': machine_id,
                        'appName': self.app_name
                    }
                )
                data = resp.json()
                if data.get('valid'):
                    return True, data.get('user'), None
                return False, None, data.get('reason', 'unknown')
            except Exception as e:
                return False, None, str(e)
    
    async def _request_auth(self, machine_id: str) -> tuple:
        """請求授權碼"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.auth_server}/api/desktop/request-auth",
                    json={
                        'machineId': machine_id,
                        'appName': self.app_name
                    }
                )
                data = resp.json()
                return data.get('authCode'), data.get('loginUrl')
            except Exception:
                return None, None
    
    async def _poll_auth_status(self, auth_code: str, machine_id: str, timeout: int = 300) -> Optional[License]:
        """輪詢授權狀態"""
        start = time.time()
        async with httpx.AsyncClient(timeout=30) as client:
            while time.time() - start < timeout:
                try:
                    resp = await client.get(
                        f"{self.auth_server}/api/desktop/check-auth/{auth_code}",
                        params={'machineId': machine_id, 'appName': self.app_name}
                    )
                    data = resp.json()
                    status = data.get('status')
                    
                    if status == 'completed':
                        return License(
                            token=data['desktopToken'],
                            email=data['user']['email'],
                            name=data['user']['name'],
                            machine_id=machine_id,
                            app_name=self.app_name,
                            created_at=time.time()
                        )
                    elif status == 'expired':
                        return None
                    
                    await asyncio.sleep(2)
                except Exception:
                    await asyncio.sleep(5)
        return None
    
    async def _login_flow(self) -> Optional[License]:
        """登入流程"""
        machine_id = get_machine_id()
        
        self.on_status("正在連接授權伺服器...")
        auth_code, login_url = await self._request_auth(machine_id)
        
        if not auth_code:
            self.on_status("無法連接授權伺服器，請檢查網路連線")
            return None
        
        self.on_status(f"授權碼: {auth_code}")
        self.on_status("正在開啟瀏覽器，請登入您的帳號...")
        webbrowser.open(login_url)
        
        self.on_status("等待授權中... (5 分鐘內有效)")
        license = await self._poll_auth_status(auth_code, machine_id)
        
        if license:
            self._save_license(license)
            self.on_status(f"授權成功！歡迎 {license.name}")
            return license
        
        self.on_status("授權失敗或超時，請重試")
        return None
    
    async def check_async(self) -> bool:
        """檢查授權（異步版本）"""
        machine_id = get_machine_id()
        license = self._load_license()
        
        if license:
            # 檢查機器碼是否匹配
            if license.machine_id != machine_id:
                self.on_status("偵測到裝置變更，需要重新授權")
                self._delete_license()
                license = None
            # 檢查軟體名稱是否匹配
            elif license.app_name != self.app_name:
                self._delete_license()
                license = None
            else:
                # 向伺服器驗證
                self.on_status("正在驗證授權...")
                valid, user, reason = await self._verify_token(license.token, machine_id)
                
                if valid:
                    self.on_status(f"授權有效！歡迎 {user['name']}")
                    self.license = license
                    return True
                else:
                    self.on_status(f"授權無效: {reason}，需要重新登入")
                    self._delete_license()
        
        # 需要登入
        license = await self._login_flow()
        if license:
            self.license = license
            return True
        return False
    
    def check(self) -> bool:
        """檢查授權（同步版本）"""
        return asyncio.run(self.check_async())
    
    @property
    def user_email(self) -> Optional[str]:
        """取得已授權用戶的 email"""
        return self.license.email if self.license else None
    
    @property
    def user_name(self) -> Optional[str]:
        """取得已授權用戶的名稱"""
        return self.license.name if self.license else None
    
    @property
    def is_authorized(self) -> bool:
        """是否已授權"""
        return self.license is not None
```

---

## 4. setup.py

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="desktop-auth-sdk",
    version="1.0.0",
    author="Ryan",
    description="Desktop application authorization SDK for shpquery.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/age731129/desktop-auth-sdk",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
```

---

## 5. requirements.txt

```
httpx>=0.25.0
```

---

## 6. .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.eggs/
*.egg-info/
dist/
build/

# Virtual Environment
.venv/
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# License files (測試用)
.*_license
```

---

## 7. 把 README.md 和 CLAUDE.md 複製到專案

從我提供的文件複製到專案目錄。

---

## 完成後執行

```bash
# 測試套件可以正常 import
python -c "from desktop_auth import DesktopAuth; print('SDK OK')"

# 提交到 GitHub
git add .
git commit -m "Initial commit: Desktop Auth SDK v1.0.0"
git remote add origin https://github.com/age731129/desktop-auth-sdk.git
git branch -M main
git push -u origin main
```
