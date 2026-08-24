"""ToolManager birim testleri."""

from main import build_tool_manager


def test_build_tool_manager_registers_expected_tools() -> None:
    """Ana arac kaydinin beklenen araclari içerdigini dogrular."""
    tool_manager = build_tool_manager()

    assert {
        "open_application",
        "get_system_info",
        "copy_file",
        "run_terminal_command",
    }.issubset(tool_manager.list_tools())


def test_system_info_returns_expected_fields() -> None:
    """Sistem bilgisi aracinin temel ölçümleri döndürdüğünü dogrular."""
    info = build_tool_manager().execute("get_system_info")

    assert {"cpu_percent", "ram_percent", "disk_percent", "running_processes"}.issubset(info)
