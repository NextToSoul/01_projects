"""PPCU TestBench — 累加和校验算法

PPCU 协议校验规则（协议文档 A04）:
  从第 3 字节（索引 2, 版本号 + APID）到数据域末尾，
  单字节累加求和 → 取反 → 取低 16bit → 高字节在前写入。
"""

from __future__ import annotations

import struct


def compute_checksum(payload: bytes) -> bytes:
    """计算 payload 的累加和（2 字节，大端序）。

    Args:
        payload: 从索引 2 到数据域末尾的字节段。

    Returns:
        2 字节累加和（已取反、截低 16bit、大端打包）。
    """
    total = sum(payload) & 0xFFFF
    inverted = (~total) & 0xFFFF
    return inverted.to_bytes(2, byteorder="big")


def verify_checksum(frame: bytes, start_byte: int = 2) -> bool:
    """校验整帧的累加和。

    Args:
        frame: 完整帧（含帧头、数据域、校验和尾部）。
        start_byte: 校验起始索引（PPCU 协议固定为 2）。

    Returns:
        校验结果 True / False。帧过短时返回 False。
    """
    if len(frame) < start_byte + 2:
        return False
    return frame[-2:] == compute_checksum(frame[start_byte:-2])
