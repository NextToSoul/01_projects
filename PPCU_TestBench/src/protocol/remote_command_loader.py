"""PPCU TestBench — 立即遥控指令配置加载器

从 Excel 配置表加载立即遥控指令定义，供遥控指令面板使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RemoteCommandDef:
    """一条立即遥控指令的定义。"""
    id: str          # 指令代号 e.g. TCHEDTTA003_1
    name: str        # 指令名称 e.g. 待机模式
    cmd_id: int      # 指令编码 e.g. 0x0030
    params: bytes    # 参数字节 (可空)
    data_len_words: int  # 总数据域字数（含 CmdID）


def load_remote_commands(excel_path: str | Path) -> list[RemoteCommandDef]:
    """从 Excel 加载所有立即遥控指令定义。"""
    try:
        import openpyxl
    except ImportError:
        raise ImportError("需要 openpyxl: pip install openpyxl")

    wb = openpyxl.load_workbook(str(excel_path), read_only=True)
    ws = wb["立即令配置表"]
    cmds: list[RemoteCommandDef] = []
    _blank_streak = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            _blank_streak += 1
            if _blank_streak > 5:
                break  # 连续空行，结束读取
            continue
        _blank_streak = 0
        cmd_id_str = str(row[6]).strip() if row[6] else ""
        param_str = str(row[7]).strip() if row[7] else ""
        len_str = str(row[5]).strip() if row[5] else ""

        if not cmd_id_str:
            continue

        # 解析指令编码
        parts = cmd_id_str.split()
        if len(parts) >= 2:
            cmd_id = (int(parts[0], 16) << 8) | int(parts[1], 16)
        else:
            cmd_id = int(parts[0], 16)

        # 解析参数
        if param_str:
            param_bytes = bytes(int(x, 16) for x in param_str.split())
        else:
            param_bytes = b""

        # 解析数据域字数（指令长度，含指令码）
        len_parts = len_str.split()
        if len(len_parts) >= 2:
            data_len = (int(len_parts[0], 16) << 8) | int(len_parts[1], 16)
        elif len(len_parts) == 1:
            data_len = int(len_parts[0], 16)
        else:
            data_len = 1

        cmds.append(RemoteCommandDef(
            id=str(row[1]).strip() if row[1] else "",
            name=str(row[2]).strip() if row[2] else "",
            cmd_id=cmd_id,
            params=param_bytes,
            data_len_words=data_len,
        ))

    return cmds


def group_commands(cmds: list[RemoteCommandDef]) -> dict[str, list[RemoteCommandDef]]:
    """按指令名称关键词自动分组。"""
    def get_group(name: str) -> str:
        if "模式" in name:
            return "模式切换"
        if "电磁阀" in name:
            return "电磁阀控制"
        if "比例阀" in name:
            return "比例阀控制"
        if "自锁阀" in name:
            return "自锁阀控制"
        if "流量" in name:
            return "流量控制"
        if "遥测" in name or "查询" in name or "自检" in name:
            return "遥测查询"
        if "复位" in name or "接口恢复" in name:
            return "系统控制"
        if "使能" in name or "屏蔽" in name:
            return "使能/屏蔽"
        if "开/关" in name or "切换" in name:
            return "电源/开关"
        if "清零" in name or "清除" in name or "故障" in name:
            return "故障处理"
        if "电压" in name or "电流" in name or "时间" in name or "系数" in name:
            return "参数设置"
        if "设定" in name or "设置" in name or "限幅" in name or "门限" in name:
            return "参数设置"
        return "其他"

    groups: dict[str, list[RemoteCommandDef]] = {}
    for c in cmds:
        g = get_group(c.name)
        groups.setdefault(g, []).append(c)
    return groups