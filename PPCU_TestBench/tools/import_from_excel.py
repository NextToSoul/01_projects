#!/usr/bin/env python3
import os, sys, tempfile, openpyxl

def sheet_to_tm_type(name):
    name = name.strip().split(" ", 1)[0]
    for s in [chr(34920), chr(21442), chr(36947)]:  # 表, 参, 遥
        if name.endswith(s): name = name[:-1]
    return name.lower().strip()

def safe_int(v):
    if v is None: return None
    try: return int(str(v), 0)
    except: return None

def import_excel(filepath, out_dir=None):
    if out_dir is None: out_dir = tempfile.gettempdir()
    wb = openpyxl.load_workbook(filepath, data_only=True)
    results = []
    all_enums = {}
    for sheet_name in wb.sheetnames:
        if sheet_name == chr(20135)+chr(21697)+chr(37197)+chr(32622): continue  # 产品配置
        tm_type = sheet_to_tm_type(sheet_name)
        if not tm_type: continue
        ws = wb[sheet_name]
        lines = ["tm_type: " + tm_type, "description: " + sheet_name, "params:"]
        cnt = 0
        for r in range(2, ws.max_row + 1):
            pid = ws.cell(r, 2).value
            if not pid: continue
            do_raw = ws.cell(r, 4).value
            bl_raw = ws.cell(r, 6).value
            ptype = str(ws.cell(r, 7).value or "").lower()
            try: do = int(str(do_raw).strip(), 0) if do_raw is not None else -1
            except: do = -1
            if do < 0: continue
            cnt += 1; lines.append("")
            lines.append("  - id: " + str(pid).strip())
            lines.append("    name: " + str(ws.cell(r, 3).value or "").strip())
            lines.append("    byte_offset: " + str(do))
            try: bl = int(str(bl_raw).strip(), 0) if bl_raw is not None else 0
            except: bl = 0
            is_enum = "enum" in ptype
            if bl in (1,2,3,4,5,6,7):
                try: bib = int(str(ws.cell(r,5).value or "0").strip(), 0) % 8
                except: bib = 0
                lsb = 8 - bib - bl
                lines.append("    bit_offset: " + str(lsb))
                lines.append("    bit_length: " + str(bl))
                lines.append("    type: enum" if is_enum else "    type: uint8")
            else:
                lines.append("    byte_length: " + str(bl // 8 if bl else 1))
                if bl == 32 and "float" in ptype:
                    lines.append("    type: float32")
                    lines.append("    scale: 1.0")
                else:
                    t = "uint16" if bl == 16 else ("uint32" if bl in (24,32) else "uint8")
                    lines.append("    type: " + t)
                    lines.append("    scale: " + str(float(ws.cell(r,9).value or 1.0)))
                lines.append("    endian: big")
            dec = ws.cell(r, 10).value
            lines.append("    decimal_places: " + str(int(dec) if dec else 0))
            unit = ws.cell(r, 11).value or ""
            if unit: lines.append("    unit: " + str(unit).strip())
            rmin = safe_int(ws.cell(r, 12).value)
            rmax = safe_int(ws.cell(r, 13).value)
            if rmin is not None: lines.append("    range_min: " + str(rmin))
            if rmax is not None: lines.append("    range_max: " + str(rmax))
            enum_str = ws.cell(r, 14).value or ""
            if is_enum and enum_str:
                enum_ref = tm_type + "_" + str(pid).strip().lower()
                lines.append("    enum_ref: " + enum_ref)
                vals = {}
                for p in str(enum_str).replace(chr(65292),";").replace(chr(65307),";").split(";"):
                    p = p.strip()
                    if ":" in p:
                        try: vals[int(p.split(":",1)[0].strip())] = p.split(":",1)[1].strip()
                        except: pass
                if vals: all_enums[enum_ref] = vals
        if cnt > 0:
            out = os.path.join(out_dir, "telemetry_" + tm_type + ".yaml")
            with open(out, "w", encoding="utf-8") as f: f.write("\n".join(lines) + "\n")
            results.append((tm_type, cnt))
            print("  [" + tm_type + "] " + str(cnt) + " params")
    if all_enums:
        el = ["enums:"]
        for ref, vals in sorted(all_enums.items()):
            el.append("  " + ref + ":")
            for k, v in sorted(vals.items()): el.append("    " + str(k) + ": " + v)
        ep = os.path.join(out_dir, "enums.yaml")
        with open(ep, "w", encoding="utf-8") as f: f.write("\n".join(el) + "\n")
        print("  [enums] " + str(len(all_enums)) + " entries")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        print("Importing: " + sys.argv[1])
        r = import_excel(sys.argv[1])
        print("Done: " + str(len(r)) + " types")
    else:
        print("Usage: python tools/import_from_excel.py <path_to.xlsx>")
        print("Then: Copy-Item $env:TEMP\\telemetry_*.yaml <target_dir>\\ -Force")
        print("      Copy-Item $env:TEMP\\enums.yaml <target_dir>\\ -Force")
