"""tests/test_protocol.py -- unit tests for protocol layer"""

import sys
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TEST_ROOT))

import pytest
from src.protocol.checksum import compute_checksum, verify_checksum
from src.protocol.telemetry_loader import load_tm_defs, load_enums
from src.protocol.command_loader import load_commands
from src.protocol.nebula_rs422 import NebulaRS422Protocol
from src.protocol.models import Command

PD = TEST_ROOT / "protocol_defs" / "nebula_ppcu"


class TestChecksum:
    def test_cs_known(self):
        assert compute_checksum(bytes([0x05])) == bytes([0xFF, 0xFA])

    def test_cs_two(self):
        assert compute_checksum(bytes([0x05, 0x20])) == bytes([0xFF, 0xDA])

    def test_verify_valid(self):
        f = bytes([0, 0, 0x05, 0x20]) + compute_checksum(bytes([0x05, 0x20]))
        assert verify_checksum(f)

    def test_verify_trunc(self):
        assert verify_checksum(bytes([0x01])) is False

    def test_verify_empty(self):
        cs = compute_checksum(bytes([]))
        assert cs == bytes([0xFF, 0xFF])
class TestTL:
    def test_tm1_count(self):
        assert len(load_tm_defs(PD, "tm1")) == 47

    def test_tm1_first(self):
        p = load_tm_defs(PD, "tm1")[0]
        assert p.id == "TM1001"

    def test_tm1_v(self):
        p = load_tm_defs(PD, "tm1")[7]
        assert abs(p.scale - 0.0055555556) < 0.0001

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            load_tm_defs(PD, "x")

    def test_tm2_not_empty(self):
        assert len(load_tm_defs(PD, "tm2")) == 86

    def test_enums(self):
        assert "tm1_tm1005" in load_enums(PD)


class TestCL:
    def test_count(self):
        assert len(load_commands(PD)) == 4

    def test_tm1(self):
        c = next(c for c in load_commands(PD) if c.id == 0x005A)
        assert c.name == "遥测1请求"

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            load_commands(PD / "x")
class TestN422:
    @pytest.fixture
    def p(self):
        return NebulaRS422Protocol(PD)

    def test_build(self, p):
        f = p.build_request(Command(cmd_id=0x005A, name="T"))
        assert f[:2] == bytes([0xEB, 0x90])
        assert f[8:10] == bytes([0x00, 0x5A])
        assert p.verify_checksum(f)

    def test_build_param(self, p):
        f = p.build_request(Command(cmd_id=0x14A, name="X", params={"v": 0x1234}))
        assert f[10:12] == bytes([0x12, 0x34])

    def test_parse_bad(self, p):
        assert p.parse_response(bytes([0xFF] * 12)) is None
        assert p.parse_response(bytes([0x1A, 0xCF])) is None

    def test_parse_apid(self, p):
        f = bytes([0x1A, 0xCF, 0xFF, 0xFF, 0, 1, 0, 4, 0xA1, 0xB2])
        r = p.parse_response(f + p.compute_checksum(f[2:]))
        assert r is not None and not r.parsed

    def test_parse_cs(self, p):
        f = bytes([0x1A, 0xCF, 5, 0x25, 0, 1, 0, 4, 0, 0])
        r = p.parse_response(f + bytes([0, 1]))
        assert r is not None and not r.parsed
    def test_parse_tm1(self, p):
        tm = bytearray(20)
        tm[5] = 0x01                # mode=1 (点火), sub=0 (data_offset 4)
        tm[7:9] = (18000).to_bytes(2, "big")   # 100V
        tm[8:10] = (5000).to_bytes(2, "big")   # 5A
        body = bytes(tm)
        resp = bytes([0x1A, 0xCF, 5, 0x25, 0, 1]) + (len(body) + 2).to_bytes(2, "big") + body
        resp += p.compute_checksum(resp[2:])
        r = p.parse_response(resp)
        assert r is not None and r.parsed and r.tm_type == "tm1"
        assert "0x" not in str(r.data["TM1005"].eng_value)
        assert abs(float(r.data["TM1008"].eng_value) - 100.0) < 0.5

    def test_seq(self, p):
        cmd = Command(cmd_id=0x5A, name="T")
        p._sequence = 0x3FFE
        assert p.build_request(cmd)[4:6] == bytes([0xFF, 0xFE])
        assert p.build_request(cmd)[4:6] == bytes([0xFF, 0xFF])
        assert p.build_request(cmd)[4:6] == bytes([0xC0, 0x00])
        assert p.build_request(cmd)[4:6] == bytes([0xC0, 0x01])

    def test_verify_cs(self, p):
        f = p.build_request(Command(cmd_id=0x5A, name="T"))
        assert p.verify_checksum(f)
        b = bytearray(f)
        b[-1] ^= 0xFF
        assert not p.verify_checksum(bytes(b))
class TestInt:
    @pytest.fixture
    def p(self):
        return NebulaRS422Protocol(PD)

    def test_tm1(self, p):
        tm = bytearray(20)
        tm[5] = 0                    # TM1005 mode=0
        tm[7:9] = (27000).to_bytes(2, "big")   # TM1008 150V
        body = bytes(tm)
        resp = bytes([0x1A, 0xCF, 5, 0x25, 0, 1]) + (len(body) + 2).to_bytes(2, "big") + body
        resp += p.compute_checksum(resp[2:])
        r = p.parse_response(resp)
        assert "0x" not in str(r.data["TM1005"].eng_value)
        assert abs(float(r.data["TM1008"].eng_value) - 150.0) < 0.5

    def test_high_v(self, p):
        tm = bytearray(20)
        tm[7:9] = (60000).to_bytes(2, "big")   # TM1008 ~333V > 300
        body = bytes(tm)
        resp = bytes([0x1A, 0xCF, 5, 0x25, 0, 1]) + (len(body) + 2).to_bytes(2, "big") + body
        resp += p.compute_checksum(resp[2:])
        r = p.parse_response(resp)
        assert float(r.data["TM1008"].eng_value) > 300

    def test_modes(self, p):
        cases = [
            (0, "0x0"), (0x10, "0x1"),
            (0x20, "稳态工作模式"), (0x30, "关机模式"),
            (0x40, "故障模式"), (0xF0, "自检模式"),
        ]
        for rb, exp in cases:
            tm = bytearray(20)
            tm[5] = rb
            body = bytes(tm)
            resp = bytes([0x1A, 0xCF, 5, 0x25, 0, 1]) + (len(body) + 2).to_bytes(2, "big") + body
            resp += p.compute_checksum(resp[2:])
            r = p.parse_response(resp)
        assert "0x" not in str(r.data["TM1005"].eng_value)
