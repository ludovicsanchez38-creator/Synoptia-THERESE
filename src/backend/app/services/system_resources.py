"""Détection légère des ressources matérielles de la machine hôte."""

import ctypes
import os
import platform
import subprocess
from dataclasses import dataclass

GIB = 1024**3
OLLAMA_CONTEXT_MARGIN_BYTES = 2 * GIB


@dataclass(frozen=True)
class SystemMemory:
    """RAM physique détectée et méthode utilisée."""

    total_bytes: int | None
    detection_method: str


def _macos_total_ram_bytes() -> int:
    result = subprocess.run(
        ["sysctl", "-n", "hw.memsize"],
        check=True,
        capture_output=True,
        text=True,
        timeout=2,
    )
    return int(result.stdout.strip())


def _parse_linux_meminfo(content: str) -> int:
    for line in content.splitlines():
        if not line.startswith("MemTotal:"):
            continue
        parts = line.split()
        if len(parts) < 2:
            break
        return int(parts[1]) * 1024
    raise ValueError("MemTotal absent de /proc/meminfo")


def _linux_total_ram_bytes() -> int:
    with open("/proc/meminfo", encoding="utf-8") as meminfo:
        return _parse_linux_meminfo(meminfo.read())


def _windows_total_ram_bytes() -> int:
    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx a échoué")
    return int(status.ullTotalPhys)


def _sysconf_total_ram_bytes() -> int:
    page_size = os.sysconf("SC_PAGE_SIZE")
    page_count = os.sysconf("SC_PHYS_PAGES")
    return int(page_size * page_count)


def detect_system_memory() -> SystemMemory:
    """Détecte la RAM totale sans dépendance tierce, avec repli POSIX."""

    system = platform.system()
    detectors = {
        "Darwin": ("macos_sysctl", _macos_total_ram_bytes),
        "Linux": ("linux_proc_meminfo", _linux_total_ram_bytes),
        "Windows": ("windows_global_memory_status_ex", _windows_total_ram_bytes),
    }
    method, detector = detectors.get(system, ("posix_sysconf", _sysconf_total_ram_bytes))
    try:
        total_bytes = detector()
        if total_bytes <= 0:
            raise ValueError("RAM totale non positive")
        return SystemMemory(total_bytes=total_bytes, detection_method=method)
    except (AttributeError, OSError, ValueError, subprocess.SubprocessError):
        if method != "posix_sysconf":
            try:
                total_bytes = _sysconf_total_ram_bytes()
                if total_bytes > 0:
                    return SystemMemory(
                        total_bytes=total_bytes,
                        detection_method="posix_sysconf_fallback",
                    )
            except (AttributeError, OSError, ValueError):
                pass
        return SystemMemory(total_bytes=None, detection_method="unavailable")
