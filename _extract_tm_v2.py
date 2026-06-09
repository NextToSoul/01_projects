
import docx
path = r'E:/Codex Workspace/01_Projects/项目文档/通讯协议/立即遥控指令与遥测应答.docx'
doc = docx.Document(path)
out = []
for ti in [1, 2]:
    table = doc.tables[ti]
    name = 'TM1' if ti == 1 else 'TM2'
    out.append(f'=== {name} Parameters ===')
    out.append('byte | id | name | type | formula | unit | bit_len')
    for ri, row in enumerate(table.rows):
        cols = [c.text.strip() for c in row.cells]
        if ri < 11:
            continue
        name_val = cols[2] if len(cols) > 2 else ''
        if not name_val or '校验' in name_val:
            continue
        byte_idx = cols[0].strip() if len(cols) > 0 and cols[0].strip() else str(ri-10)
        tm_id = cols[1].strip() if len(cols) > 1 else ''
        vtype = cols[3].strip() if len(cols) > 3 else ''
        formula = cols[4].strip() if len(cols) > 4 else ''
        unit = cols[6].strip() if len(cols) > 6 else ''
        bit_len = cols[7].strip() if len(cols) > 7 else ''
        out.append(f'{byte_idx:3s} | {tm_id:15s} | {name_val:30s} | {vtype:10s} | {formula:20s} | {unit:6s} | {bit_len:6s}')
p = 'E:/Codex Workspace/01_Projects/PPCU_TestBench/protocol_defs/nebula_ppcu/extracted_tm.txt'
with open(p, 'w', encoding='utf-8') as f:
    f.write(chr(10).join(out))
print(f'Written to {p}, {len(out)} lines')
