import sys, openpyxl
from pathlib import Path
import shutil, tempfile, os

ROOT = Path(__file__).resolve().parent.parent.parent
dir_path = ROOT / "项目文档" / "通讯协议" / "excel版遥测大表"
path_v3 = dir_path / "PPCU_Telemetry_Database_v3.xlsx"
path_v2 = dir_path / "PPCU_Telemetry_Database_v2.xlsx"

# Copy to temp to avoid path encoding issues
tmp_v3 = os.path.join(tempfile.gettempdir(), "PPCU_v3_temp.xlsx")
shutil.copy2(str(path_v3), tmp_v3)

wb3 = openpyxl.load_workbook(tmp_v3, data_only=True)
wb2 = openpyxl.load_workbook(tmp_v2, data_only=True)

errors = []
warnings = []

for sname in ["TM1 参数表", "TM2 参数表", "查询包 参数表"]:
    ws3 = wb3[sname]
    ws2 = wb2[sname]
    rows3 = ws3.max_row - 1
    rows2 = ws2.max_row - 1
    
    # Row count check
    if rows3 != rows2:
        errors.append(f"[{sname}] Missing rows! v3={rows3}, v2={rows2}")
    
    for r in range(2, ws3.max_row + 1):
        pid = ws3.cell(r, 2).value
        if not pid: continue
        
        name = str(ws3.cell(r, 3).value or "")
        bo = ws3.cell(r, 4).value
        do = ws3.cell(r, 5).value
        bl = ws3.cell(r, 6).value
        ptype = str(ws3.cell(r, 7).value or "").strip()
        enum_str = str(ws3.cell(r, 14).value or "").strip()
        
        # 1) data_offset = bo/8 - 8
        if bo is not None and do is not None:
            expected = int(bo) // 8 - 8
            if do != expected:
                errors.append(f"[{sname} R{r} {pid}] data_offset={do} != expected={expected}")
        
        # 2) Check type: no empty, no 'float'
        if not ptype:
            errors.append(f"[{sname} R{r} {pid}] Empty type!")
        if ptype == "float":
            errors.append(f"[{sname} R{r} {pid}] Ambiguous type='float', should be uint16 or float32")
        
        # 3) Check enum format: only decimal keys
        if "enum" in ptype.lower() and enum_str:
            parts = enum_str.replace("；", ";").replace("，", ";").split(";")
            for p in parts:
                p = p.strip()
                if ":" in p:
                    k = p.split(":")[0].strip()
                    if not k.isdigit():
                        errors.append(f"[{sname} R{r} {pid}] Non-decimal key '{k}' in '{enum_str[:50]}'")
        
        # 4) Check scaled params have decimal_places
        scale = ws3.cell(r, 9).value
        dec = ws3.cell(r, 10).value
        if scale and isinstance(scale, (int,float)) and 0 < float(scale) < 1 and (dec is None or str(dec).strip() == ""):
            warnings.append(f"[{sname} R{r} {pid}] No decimal_places for scale={scale}")
        
        # 5) Check data_offset < body_length
        if do is not None and do >= 0:
            max_byte = do + (bl // 8 if bl else 1)
            expected_max = {"TM1 参数表": 35, "TM2 参数表": 67, "查询包 参数表": 395}[sname]
            if max_byte > expected_max:
                warnings.append(f"[{sname} R{r} {pid}] data_offset={do} + len={bl//8 if bl else 1} exceeds body ({expected_max}B)")

print("=== ERROR CHECK RESULTS ===")
if errors:
    print(f"FAILED: {len(errors)} errors:")
    for e in errors:
        print(f"  {e}")
else:
    print("No errors found!")

if warnings:
    print(f"\nWarnings ({len(warnings)}):")
    for w in warnings[:10]:
        print(f"  {w}")
    if len(warnings) > 10:
        print(f"  ... and {len(warnings)-10} more")
else:
    print("No warnings.")
