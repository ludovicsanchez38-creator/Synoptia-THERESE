"""Tests du garde-fou RAM pour les modèles Ollama locaux."""

from unittest.mock import patch

import app.services.system_resources as system_resources
import pytest
from app.services.system_resources import GIB, SystemMemory, _parse_linux_meminfo
from httpx import AsyncClient


def test_parse_linux_meminfo_converts_kibibytes_to_bytes():
    content = "MemFree: 123 kB\nMemTotal:       16384000 kB\n"

    assert _parse_linux_meminfo(content) == 16_384_000 * 1024


@pytest.mark.parametrize(
    ("platform_name", "detector_name", "expected_method"),
    [
        ("Darwin", "_macos_total_ram_bytes", "macos_sysctl"),
        ("Linux", "_linux_total_ram_bytes", "linux_proc_meminfo"),
        ("Windows", "_windows_total_ram_bytes", "windows_global_memory_status_ex"),
    ],
)
def test_detect_system_memory_uses_native_platform_detector(
    platform_name: str,
    detector_name: str,
    expected_method: str,
):
    with (
        patch("app.services.system_resources.platform.system", return_value=platform_name),
        patch.object(system_resources, detector_name, return_value=16 * GIB) as detector,
    ):
        memory = system_resources.detect_system_memory()

    detector.assert_called_once_with()
    assert memory == SystemMemory(total_bytes=16 * GIB, detection_method=expected_method)


@pytest.mark.asyncio
async def test_system_resources_exposes_half_ram_and_context_margin(client: AsyncClient):
    with patch(
        "app.routers.config.detect_system_memory",
        return_value=SystemMemory(total_bytes=16 * GIB, detection_method="test"),
    ):
        response = await client.get("/api/config/system-resources")

    assert response.status_code == 200
    assert response.json() == {
        "total_ram_bytes": 16 * GIB,
        "safe_local_model_ram_bytes": 8 * GIB,
        "ollama_context_margin_bytes": 2 * GIB,
        "detection_method": "test",
    }


@pytest.mark.asyncio
async def test_system_resources_remains_available_when_ram_detection_fails(client: AsyncClient):
    with patch(
        "app.routers.config.detect_system_memory",
        return_value=SystemMemory(total_bytes=None, detection_method="unavailable"),
    ):
        response = await client.get("/api/config/system-resources")

    assert response.status_code == 200
    assert response.json()["total_ram_bytes"] is None
    assert response.json()["safe_local_model_ram_bytes"] is None
