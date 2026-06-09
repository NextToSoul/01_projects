import sys, os, tempfile
p = "E:/Codex Workspace/01_Projects/PPCU_TestBench/tests/test_protocol.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()
s = s.replace('== 22', '== 47')
s = s.replace('assert p.id == "TMHEDTZ0099"', 'assert p.id == "TM1001"')
s = s.replace('p = load_tm_defs(PD, "tm1")[6]', 'p = load_tm_defs(PD, "tm1")[7]')
s = s.replace('def test_tm2_empty', 'def test_tm2_not_empty')
s = s.replace('assert load_tm_defs(PD, "tm2") == []', 'assert len(load_tm_defs(PD, "tm2")) == 86')
s = s.replace('tm[4] = 0x10', 'tm[5] = 0x01')
s = s.replace('tm[6:8] = (18000).to_bytes(2, "big")', 'tm[7:9] = (18000).to_bytes(2, "big")')
s = s.replace('"TMHEDTZ1001"', '"TM1005"')
s = s.replace('"TMHEDTZ1003"', '"TM1008"')
s = s.replace('"点火模式"', '"0x1"')
s = s.replace('tm[4] = 0                  # 待机模式', 'tm[5] = 0                    # TM1005 mode=0')
s = s.replace('tm[6:8] = (27000).to_bytes(2, "big")   # 150V', 'tm[7:9] = (27000).to_bytes(2, "big")   # TM1008 150V')
s = s.replace('"待机模式"', '"0x0"')
s = s.replace('tm[6:8] = (60000).to_bytes(2, "big")   # ~333V > 300', 'tm[7:9] = (60000).to_bytes(2, "big")   # TM1008 ~333V > 300')
s = s.replace('tm[4] = rb', 'tm[5] = rb >> 4')
t = os.path.join(tempfile.gettempdir(), "test_protocol_fixed.py")
with open(t, "w", encoding="utf-8") as f:
    f.write(s)
print("Written to", t)
