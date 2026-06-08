# User Rules

## Software Installation

- 禁止将软件、工具、依赖包安装到系统盘 (C:\\)。
- 优先使用非系统盘路径：如 D:/, E:/, 或项目所在工作区。
- 如果因技术限制（如仅系统盘可写或必须注册到系统目录）必须安装在系统盘，必须先向用户说明原因并获得明确许可。

## Git Sync

- 当用户说"上传git"或"sync to git"时，自动执行：
  1. git add -A
  2. git commit -m "descriptive message"
  3. git -c http.proxy=http://127.0.0.1:17897 push
- 提交信息根据变更内容自动生成语义化格式。

## Power-Related Parameter Safety

- 在软件开发调试阶段，涉及需要用到功率相关参数的功能开发以及指令参数的修改，必须提前与用户沟通确认安全边界。
- 不允许仅凭自身经验去设定参数值并执行流程测试。
- 安全边界须由用户确认后，方可写入配置文件或代码中。

## Environment Setup First

- 项目工作开始之前，首先配置好 Python 虚拟环境和依赖。
- 依赖安装优先使用国内 PyPI 镜像（如清华源 `https://pypi.tuna.tsinghua.edu.cn/simple`）加速下载。
- pip install 命令必须带上代理参数 `--proxy http://127.0.0.1:17897`。
- 虚拟环境放置在项目所在非系统盘目录下。
