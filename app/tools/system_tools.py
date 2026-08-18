import os
from typing import Dict, Any

import psutil


def get_system_info() -> Dict[str, Any]:
    """CPU, RAM, disk kullanım oranı ve çalışan süreç sayısını döndürür."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        current_drive = os.path.splitdrive(os.getcwd())[0] or "C:\\"
        disk_usage = psutil.disk_usage(current_drive if current_drive.endswith("\\") else current_drive + "\\")

        return {
            "cpu_percent": round(cpu_usage, 2),
            "ram_percent": round(memory.percent, 2),
            "disk_percent": round(disk_usage.percent, 2),
            "running_processes": len(psutil.pids()),
        }
    except Exception as exc:
        raise RuntimeError(f"Sistem bilgisi alınamadı: {exc}") from exc
