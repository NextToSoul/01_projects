"""
PPCU TestBench — 应用入口

用法:
    python main.py

启动后加载配置 → 显示产品选择对话框 → 进入主界面。
"""
import sys
import asyncio
from pathlib import Path


def main():
    print(f"PPCU TestBench v0.1.0")
    print(f"Config dir: {Path(__file__).parent / 'config'}")
    # M1 占位: 后续在此处完成初始化流程
    # 1. 加载 config/default.yaml
    # 2. 加载 config/products.yaml → 显示产品选择
    # 3. 根据选择加载对应协议栈
    # 4. 显示主窗口
    print("Ready.")


if __name__ == "__main__":
    main()
