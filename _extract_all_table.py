import docx
doc = docx.Document(r"E:/Codex Workspace/01_Projects/项目文档/通讯协议/立即遥控指令与遥测应答.docx")
for ti, table in enumerate(doc.tables):
    print(f"TABLE {ti}: {len(table.rows)} rows x {len(table.columns)} cols")
    for ri, row in enumerate(table.rows):
        c2 = row.cells[2].text.strip() if len(row.cells)>2 else ""
        if any(k in c2 for k in ["??1","??2","??","???","??","??","TMHEDTZ"]):
            cols = [c.text.strip().replace(chr(10)," ") for c in row.cells]
            print(f"  T{ti}R{ri}: {" | ".join(cols)}")
