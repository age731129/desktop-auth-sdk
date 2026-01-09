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