#!/usr/bin/env python3
"""PPCU TestBench v0.1.0 — 应用入口

用法:
    python main.py                    # 启动（暂占位，M2 接入 GUI）
    python main.py --self-test        # 运行自检
    python main.py --list-products    # 列出可用产品
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def run_gui():
    import os
    import PySide6
    from pathlib import Path
    plugin_path = str(Path(PySide6.__file__).parent / "plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

    import qasync
    from PySide6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow
    app = QApplication(sys.argv)
    app.setApplicationName("PPCU TestBench")
    win = MainWindow()
    win.show()
    loop = qasync.QEventLoop(app)
    with loop:
        loop.run_forever()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def load_config(config_dir: Path) -> dict:
    """加载 default.yaml，失败时抛出异常。"""
    path = config_dir / "default.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_products(config_dir: Path) -> dict[str, dict]:
    """列出 products.yaml 中注册的产品。"""
    path = config_dir / "products.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("products", {})


def run_self_test(config_dir: Path) -> bool:
    """快速自检：校验和 → 协议创建 → 指令/遥测加载 → 帧构建。"""
    from src.protocol.checksum import compute_checksum
    from src.protocol.factory import create_protocol
    from src.protocol.models import Command
    from src.protocol.telemetry_loader import load_enums

    log = logging.getLogger("self-test")
    log.info("=== 自检开始 ===")

    cs = compute_checksum(bytes([0x05, 0x20]))
    assert cs == bytes([0xFF, 0xDA])
    log.info("  校验和: OK")

    proto = create_protocol("nebula_ppcu", config_dir)
    log.info("  产品: %s", proto.product_name)

    cmds = proto.get_commands()
    log.info("  指令: %d 条", len(cmds))

    tm1 = proto.get_tm_params("tm1")
    log.info("  TM1 参数: %d 个", len(tm1))

    frame = proto.build_request(Command(cmd_id=0x005A, name="遥测1请求"))
    assert proto.verify_checksum(frame)
    log.info("  帧构建: %d 字节, 校验通过", len(frame))

    enums = load_enums(config_dir.parent / "protocol_defs" / "nebula_ppcu")
    log.info("  枚举: %d 组", len(enums))

    log.info("=== 自检通过 ===\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="PPCU TestBench v0.1.0")
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument(
        "--list-products", action="store_true",
        help="列出 products.yaml 中注册的产品",
    )
    parser.add_argument(
        "--self-test", action="store_true",
        help="运行自检：校验和、协议创建、帧构建",
    )
    parser.add_argument(
        "--product", default="nebula_ppcu",
        help="产品标识（默认 nebula_ppcu）",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)
    config_dir = BASE_DIR / "config"

    log = logging.getLogger("main")
    log.info("PPCU TestBench v0.1.0")
    log.info("配置目录: %s", config_dir)

    if args.list_products:
        print("\n可用产品:")
        for name, info in list_products(config_dir).items():
            print(f"  {name:20s} {info['display_name']}")
        print()
        return

    if args.self_test:
        run_self_test(config_dir)
        return

    log.info("产品: %s", args.product)
    run_gui()
    print("\nPPCU TestBench v0.1.0 — 就绪")
    print("  --self-test  运行自检")
    print("  --list-products  查看可用产品")
    print()


if __name__ == "__main__":
    main()
