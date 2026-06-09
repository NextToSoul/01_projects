import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import openpyxl
from pathlib import Path

EXCEL = Path(__file__).resolve().parent.parent.parent
EXCEL = EXCEL / "项目文档" / "通讯协议" / "excel版遥测大表" / "PPCU_Telemetry_Database_v2.xlsx"
OUT = Path(__file__).resolve().parent.parent / "protocol_defs" / "nebula_ppcu"

def safe_int(v):
    if v is None: return None
    try: return int(str(v), 0)
    except: return None

def gen(sname, prefix):
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
        bib = bo % 8
        if do < 0: continue
        cnt += 1
        lines.append("")
        lines.append("  - id: " + pid.strip())
        lines.append("    name: " + str(name).strip())
        lines.append("    byte_offset: " + str(do))
        ptype = str(ws.cell(r, 6).value or "").lower()
        is_enum = "enum" in ptype
        if bl in (1,2,3,4,5,6,7):
            lines.append("    bit_offset: " + str(bib))
            lines.append("    bit_length: " + str(bl))
            lines.append("    type: enum" if is_enum else "    type: uint8")
        else:
            lines.append("    byte_length: " + str(bl // 8))
            if bl == 32 and "float" in ptype:
                lines.append("    type: float32")
                lines.append("    scale: 1.0")
            else:
                lines.append("    type: " + ("uint16" if bl == 16 else ("uint32" if bl in (24,32) else "uint8")))
                lines.append("    scale: " + str(float(ws.cell(r, 8).value or 1.0)))
            lines.append("    endian: big")
        dec = ws.cell(r, 9).value
        lines.append("    decimal_places: " + str(int(dec) if dec else 0))
        unit = ws.cell(r, 10).value or ""
        if unit: lines.append("    unit: " + str(unit).strip())
        rmin = safe_int(ws.cell(r, 11).value)
        rmax = safe_int(ws.cell(r, 12).value)
        if rmin is not None: lines.append("    range_min: " + str(rmin))
        if rmax is not None: lines.append("    range_max: " + str(rmax))
    yml = chr(10).join(lines) + chr(10)
    out = OUT / ("telemetry_" + prefix + ".yaml")
    try:
        with open(out, "w", encoding="utf-8") as f: f.write(yml)
        print("Wrote", out.name, "-", cnt, "params")
    except PermissionError:
        print("Permission denied:", out)

if __name__ == "__main__":
    pairs = [("TM1 参数表","tm1"),("TM2 参数表","tm2"),("查询包 参数表","query")]
    for s, p in pairs:
        try: gen(s, p)
        except Exception as e: print("Error:", s, e)
