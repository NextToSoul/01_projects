"""Generate enums.yaml from Excel enum descriptions, update telemetry YAMLs."""
import os, tempfile, openpyxl
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXCEL = BASE.parent / "项目文档" / "通讯协议" / "excel版遥测大表" / "PPCU_Telemetry_Database_v2.xlsx"
YAML_DIR = BASE / "protocol_defs" / "nebula_ppcu"

def parse_enum_str(s):
    """Parse '00b:desc; 11b:desc' or '0x0:desc; 0x1:desc' into {int: str}"""
    result = {}
    if not s: return result
    parts = str(s).replace("，", ";").replace("\n", ";").strip().split(";")
    for part in parts:
        part = part.strip()
        if not part or ":" not in part: continue
        key, val = part.split(":", 1)
        key = key.strip()
        val = val.strip()
        if not key: continue
        try:
            if key.endswith("b"):
                v = int(key[:-1], 2)
            elif key.endswith("H"):
                v = int(key[:-1], 16)
            else:
                v = int(key, 0)
            result[v] = val
        except ValueError:
            continue
    return result

def gen_enums_yaml():
    wb = openpyxl.load_workbook(EXCEL, data_only=True)
    all_enums = {}
    for sname, prefix in [("TM1 参数表", "tm1"), ("TM2 参数表", "tm2"), ("查询包 参数表", "query")]:
        ws = wb[sname]
        for r in range(2, ws.max_row + 1):
            pid = ws.cell(r, 2).value
            ptype = str(ws.cell(r, 6).value or "").lower()
            enum_str = ws.cell(r, 13).value or ""
            if not pid or "enum" not in ptype or not enum_str:
                continue
            enum_ref = prefix + "_" + pid.strip().lower()
            values = parse_enum_str(enum_str)
            if values:
                all_enums[enum_ref] = values
    return all_enums

def write_files(all_enums):
    # Write enums.yaml
    lines = ["# PPCU Telemetry Enum Definitions", "# Auto-generated from Excel", "enums:"]
    for ref, vals in sorted(all_enums.items()):
        lines.append(f"  {ref}:")
        for k, v in sorted(vals.items()):
            lines.append(f"    {k}: {v}")
    enum_yml = "\n".join(lines) + "\n"
    ep = YAML_DIR / "enums.yaml"
    try:
        with open(ep, "w", encoding="utf-8") as f: f.write(enum_yml)
        print("Written:", ep)
    except PermissionError:
        tmp = os.path.join(tempfile.gettempdir(), "enums.yaml")
        with open(tmp, "w", encoding="utf-8") as f: f.write(enum_yml)
        print("Written to temp:", tmp)
    
    # Update telemetry YAML files with enum_ref
    for sname, prefix in [("TM1 参数表", "tm1"), ("TM2 参数表", "tm2"), ("查询包 参数表", "query")]:
        ws = openpyxl.load_workbook(EXCEL, data_only=True)[sname]
        lines = ["tm_type: " + prefix, "description: " + sname, "params:"]
        cnt = 0
        for r in range(2, ws.max_row + 1):
            pid = ws.cell(r, 2).value
            name = ws.cell(r, 3).value
            bo = ws.cell(r, 4).value
            bl = ws.cell(r, 5).value
            if not pid or bo is None: continue
            do = bo // 8 - 8
            if do < 0: continue
            cnt += 1; lines.append("")
            lines.append("  - id: " + pid.strip())
            lines.append("    name: " + str(name).strip())
            lines.append("    byte_offset: " + str(do))
            ptype = str(ws.cell(r, 6).value or "").lower()
            is_enum = "enum" in ptype
            if bl in (1,2,3,4,5,6,7):
                lines.append("    bit_offset: " + str(8 - (int(bo) % 8) - int(bl)))
                lines.append("    bit_length: " + str(bl))
                lines.append("    type: enum" if is_enum else "    type: uint8")
                if is_enum:
                    enum_ref = prefix + "_" + pid.strip().lower()
                    if enum_ref in all_enums:
                        lines.append("    enum_ref: " + enum_ref)
            else:
                lines.append("    byte_length: " + str(bl // 8))
                if bl == 32 and "float" in ptype:
                    lines.append("    type: float32")
                    lines.append("    scale: 1.0")
                else:
                    t = "uint16" if bl == 16 else ("uint32" if bl in (24,32) else "uint8")
                    lines.append("    type: " + t)
                    lines.append("    scale: " + str(float(ws.cell(r,8).value or 1.0)))
                lines.append("    endian: big")
            lines.append("    decimal_places: " + str(int(ws.cell(r,9).value) if ws.cell(r,9).value else 0))
            unit = ws.cell(r,10).value or ""
            if unit: lines.append("    unit: " + str(unit).strip())
        yml = "\n".join(lines) + "\n"
        out_name = "telemetry_" + prefix + ".yaml"
        out_path = YAML_DIR / out_name
        try:
            with open(out_path, "w", encoding="utf-8") as f: f.write(yml)
            print("Written:", out_path)
        except PermissionError:
            tmp = os.path.join(tempfile.gettempdir(), out_name)
            with open(tmp, "w", encoding="utf-8") as f: f.write(yml)
            print("Written to temp:", tmp)

if __name__ == "__main__":
    enums = gen_enums_yaml()
    print(f"Found {len(enums)} enum definitions")
    for ref, vals in sorted(enums.items()):
        print(f"  {ref}: {len(vals)} values")
    write_files(enums)
    print("Done")
