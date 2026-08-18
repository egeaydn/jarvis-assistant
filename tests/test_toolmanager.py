# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, ".")
from main import build_tool_manager

tm = build_tool_manager()
print("Kayitli araclar:")
for t in tm.list_tools():
    print(" -", t)

info = tm.execute("get_system_info")
print(f"\nCPU: {info['cpu_percent']}%  RAM: {info['ram_percent']}%")
print("ToolManager OK")
