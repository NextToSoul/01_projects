import docx
doc = docx.Document(r"E:/Codex Workspace/01_Projects/项目文档/通讯协议/立即遥控指令与遥测应答.docx")
for ti in [1,2,3]:
    table = doc.tables[ti]
    print(f"TABLE {ti}: {len(table.rows)} rows x {len(table.columns)} cols")
    for ri, row in enumerate(table.rows):
        cols = [c.text.strip().replace(chr(10)," ") for c in row.cells]
        label = cols[1] if len(cols)>1 else cols[0]
        vtype = cols[3] if len(cols)>3 else ""
        print(f"R{ri}: " + " | ".join(cols))
    print()
