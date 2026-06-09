import docx
doc = docx.Document(r"E:/Codex Workspace/01_Projects/项目文档/通讯协议/立即遥控指令与遥测应答.docx")
table = doc.tables[0]
for ri, row in enumerate(table.rows):
    if ri < 180:
        continue
    cols = [c.text.strip().replace(chr(10)," ").replace(chr(13),"") for c in row.cells]
    result = " | ".join(cols)
    if "????1??" in result or "????2??" in result or "TMHEDTZ" in result:
        print(result)
