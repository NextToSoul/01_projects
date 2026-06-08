"""tests/test_comms.py — 通讯层集成测试"""
import asyncio, struct, sys
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TEST_ROOT))

from src.comms.tcp_client import TcpClient
from src.protocol.nebula_rs422 import NebulaRS422Protocol
from src.protocol.models import Command

PD = TEST_ROOT / "protocol_defs" / "nebula_ppcu"
HOST = "127.0.0.1"
PORT = 18999


def make_tm1_response(data: bytes) -> bytes:
    """组装一条合法的 TM1 应答帧。"""
    proto = NebulaRS422Protocol(PD)
    body = data if isinstance(data, bytes) else bytes(data)
    resp = bytes([0x1A, 0xCF, 0x05, 0x25, 0x00, 0x01])
    resp += (len(body) + 2).to_bytes(2, "big") + body
    resp += proto.compute_checksum(resp[2:])
    return resp


async def echo_server(stop_event):
    """回显服务器：接收指令帧，返回模拟 TM1 应答。"""
    server = await asyncio.start_server(
        lambda r, w: _handle(r, w), HOST, PORT
    )
    async with server:
        await stop_event.wait()


async def _handle(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(4096), timeout=5.0)
    except asyncio.TimeoutError:
        writer.close()
        return
    if not data:
        writer.close()
        return

    # 返回模拟 TM1 遥测（待机模式, 100V, 5A）
    tm = bytearray(20)
    tm[4] = 0x00            # 模式=0 (待机), data_offset 4
    tm[6:8] = struct.pack(">H", 18000)   # 100V
    tm[8:10] = struct.pack(">H", 5000)   # 5A
    resp = make_tm1_response(bytes(tm))
    writer.write(resp)
    await writer.drain()
    writer.close()


async def run_test():
    passed = 0
    failed = 0

    stop = asyncio.Event()
    srv_task = asyncio.create_task(echo_server(stop))
    await asyncio.sleep(0.1)  # 等服务器启动

    client = TcpClient()
    proto = NebulaRS422Protocol(PD)

    # 1) 连接
    ok = await client.connect(HOST, PORT, timeout=3.0)
    assert ok, "连接失败"
    print("[PASS] connect")
    passed += 1

    # 2) 发送 TM1 请求
    cmd = Command(cmd_id=0x005A, name="遥测1请求")
    frame = proto.build_request(cmd)
    assert proto.verify_checksum(frame)
    await client.send(frame)
    print("[PASS] send TM1 request")
    passed += 1

    # 3) 接收并解析应答
    resp_raw = await client.receive(timeout=5.0)
    assert resp_raw is not None, "未收到应答"
    print(f"[PASS] receive response ({len(resp_raw)} bytes)")
    passed += 1

    result = proto.parse_response(resp_raw)
    assert result is not None, "解析失败: None"
    assert result.parsed, f"解析失败: parsed={result.parsed}"
    assert result.tm_type == "tm1"
    print(f"[PASS] parse response: tm_type={result.tm_type}")
    passed += 1

    # 4) 验证遥测值
    tv = result.data
    assert tv is not None
    assert tv["TMHEDTZ1001"].eng_value == "待机模式"
    assert abs(float(tv["TMHEDTZ1003"].eng_value) - 100.0) < 0.5
    assert abs(float(tv["TMHEDTZ1005"].eng_value) - 5.0) < 0.5
    print(f"[PASS] telemetry: 模式={tv['TMHEDTZ1001'].eng_value} "
          f"电压={tv['TMHEDTZ1003'].eng_value}V "
          f"电流={tv['TMHEDTZ1005'].eng_value}A")
    passed += 1

    # 5) 断开
    await client.disconnect()
    print("[PASS] disconnect")
    passed += 1

    stop.set()
    await srv_task

    print(f"\n结果: {passed}/{passed + failed} 通过")
    return passed == (passed + failed)


if __name__ == "__main__":
    exit(0 if asyncio.run(run_test()) else 1)
