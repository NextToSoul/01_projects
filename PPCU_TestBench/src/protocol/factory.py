"""PPCU TestBench — 协议工厂

根据 config/products.yaml 中注册的产品信息动态加载对应的协议实现。
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml

from .interface import ProtocolInterface


def create_protocol(
    product_name: str, config_dir: str | Path
) -> ProtocolInterface:
    """根据产品名称创建协议实例。

    从 config/products.yaml 中查找产品注册信息，
    动态加载对应的协议实现类并初始化。

    Args:
        product_name: 产品标识（如 "nebula_ppcu"）。
        config_dir: config/ 目录路径。

    Returns:
        ProtocolInterface 子类实例。

    Raises:
        ValueError: 产品名称未在注册表中找到。
        ImportError: 协议类加载失败。
    """
    config_dir = Path(config_dir).resolve()
    products_path = config_dir / "products.yaml"

    with open(products_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    products: dict[str, Any] = data.get("products", {})
    if product_name not in products:
        available = ", ".join(products.keys())
        raise ValueError(
            f"未知产品: '{product_name}'，可用: [{available}]"
        )

    info = products[product_name]
    module_path: str = info["protocol_class"]
    def_dir = (config_dir.parent / info["protocol_def_dir"]).resolve()

    # 动态加载: "nebula_rs422.NebulaRS422Protocol"
    mod_name, cls_name = module_path.rsplit(".", 1)
    module = importlib.import_module(f"src.protocol.{mod_name}")
    cls = getattr(module, cls_name)

    return cls(def_dir)
