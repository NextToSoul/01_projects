# PPCU 自动化测试软件 — 初始版本方案 (V1)

> 最后更新: 2026-06-08
> 版本: v0.1 (初始版)

---

## 1. 项目概述

开发一个 Windows 桌面自动化测试软件，通过 TCP → 串口转以太网盒子 → RS422，对星云 400W
霍尔电推进系统的 PPCU（电源处理与控制单元）进行功能测试。软件自动发送指令帧、采集解析
遥测数据、验证各流程阶段时序是否符合协议规范，并生成多格式测试报告。

**被测对象**: PPCU（星云 400W 霍尔电推进，北京星辰空间科技）
**通讯链路**: 测试电脑(TCP) → 网络通讯盒 → RS422(115.2kbps, 奇校验) → PPCU
**通讯协议**: 帧头 EB 90（指令）/ 1A CF（应答），CCSDS 风格源包格式，累加和取反校验
**应用场景**: 单机台架测试（测试软件为唯一主控）；后续可扩展系统联试监听模式

---

## 2. 技术栈

| 层级 | 技术选型 | 说明 |
|---|---|---|
| 语言 | Python 3.11+ | 航天测试行业主流，生态成熟 |
| GUI 框架 | PySide6 (Qt6) | 原生 Windows 风格，表格/树/实时刷新支持好 |
| 异步通信 | asyncio + qasync | 非阻塞 TCP 通信，不卡 UI |
| 数据存储 | SQLite (标准库) | 零配置嵌入式，存储遥测历史与测试记录 |
| CSV 导出 | pandas | 规整的 .to_csv() 输出 |
| Word 导出 | python-docx | 直接读写 .docx，带表格/格式/页眉页脚 |
| HTML 导出 | Jinja2 + 内置 CSS | 模板化生成报告，可嵌入图表和着色 |
| 实时曲线 | pyqtgraph | 轻量高效，适合实时电压/电流趋势 |
| 配置管理 | YAML (PyYAML) | 测试用例、通讯参数外部化配置 |
| 打包分发 | PyInstaller / Nuitka | 冻结为单 exe，无需 Python 环境 |

---

## 3. 软件架构（六层 + 可插拔协议）

```
                    ┌──────────────────────────────┐
                    │          产品选择器            │
                    │  (启动时选择,加载对应协议栈)    │
                    └──────────────┬───────────────┘
                                   │
┌──────────────────────────────────┴───────────────────────────────┐
│                          UI 层 (PySide6)                         │
│  通讯面板 │ 遥测面板(动态渲染) │ 测试面板 │ 报告面板 │ 配置面板  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ Qt Signal/Slot
┌──────────────────────────────┴──────────────────────────────────┐
│                        测试引擎层 (产品无关)                      │
│  用例加载器 → 用例执行器 → 判定器 → 结果收集器                    │
│  时序验证器 (参数化预期值来自产品协议 YAML)                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                    协议工厂层 (可插拔)                            │
│  ProtocolInterface 抽象基类                                      │
│    ├── NebulaRS422Protocol  ← V1 实现                             │
│    ├── ProductBProtocol     ← 预留                                │
│    └── ProductCProtocol     ← 预留                                │
│  通信: CommsInterface (当前 TcpClient, 未来可扩展)               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                        数据层 (产品无关)                          │
│  SQLite (遥测历史/测试记录/报文日志)                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                        报告层 (产品无关)                          │
│  CSV 导出 | HTML 报告 (Jinja2) | Word 报告 (python-docx)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 项目目录结构

```
PPCU_TestBench/
├── PLAN.md                            # 本方案文档
├── main.py                            # 应用入口
├── requirements.txt                   # 依赖清单
├── config/
│   ├── default.yaml                   # 默认配置 (不直接修改)
│   ├── local.yaml.example             # 覆盖模板
│   └── products.yaml                  # 产品注册表
├── protocol_defs/                     # 产品协议定义 (纯YAML)
│   └── nebula_ppcu/                   # 星云PPCU
│       ├── protocol.yaml              # 帧头/校验/通讯参数
│       ├── telemetry_tm1.yaml         # TM1 遥测参数表
│       ├── telemetry_tm2.yaml         # TM2 遥测参数表
│       ├── telemetry_query.yaml       # 查询遥测包
│       ├── commands.yaml              # 遥控指令码
│       └── enums.yaml                 # 枚举定义
├── test_cases/
│   └── nebula_ppcu/                   # 按产品分目录
│       ├── telemetry_cycle.yaml
│       ├── remote_cmd.yaml
│       └── timing_verify.yaml
├── src/
│   ├── comms/                         # 通信层
│   │   ├── __init__.py
│   │   ├── interface.py               # CommsInterface ABC
│   │   └── tcp_client.py              # TCP 实现
│   ├── protocol/                      # 协议层 (可插拔)
│   │   ├── __init__.py
│   │   ├── interface.py               # ProtocolInterface ABC
│   │   ├── factory.py                 # 产品名→协议实例
│   │   ├── nebula_rs422.py            # 星云PPCU协议实现
│   │   ├── checksum.py                # 校验算法
│   │   ├── telemetry_loader.py        # YAML遥测定义加载
│   │   └── command_loader.py          # YAML指令定义加载
│   ├── engine/                        # 测试引擎
│   │   ├── test_case_loader.py        # YAML用例加载
│   │   ├── test_executor.py           # 用例执行
│   │   ├── checker.py                 # 判定器
│   │   └── timing_verifier.py         # 时序验证
│   ├── ui/                            # 界面
│   │   ├── __init__.py
│   │   ├── main_window.py             # 主窗口
│   │   ├── components/
│   │   │   ├── message_log.py         # 报文滚动视图
│   │   │   └── telemetry_table.py     # 遥测动态表格
│   │   └── panels/
│   │       ├── comm_panel.py          # 通讯面板
│   │       ├── telemetry_panel.py     # 遥测面板
│   │       ├── test_panel.py          # 测试面板
│   │       ├── report_panel.py        # 报告面板
│   │       └── config_panel.py        # 配置面板
│   ├── data/                          # 数据层
│   │   ├── database.py                # SQLite 管理
│   │   └── log_manager.py             # 报文日志
│   └── report/                        # 报告层
│       ├── csv_reporter.py
│       ├── html_reporter.py
│       ├── word_reporter.py
│       └── templates/
│           ├── report.html.j2
│           └── docx_template.docx
├── tests/                             # 单元测试
│   ├── test_protocol.py
│   ├── test_engine.py
│   └── test_comms.py
└── assets/
    └── icons/
```

---

## 5. 核心接口设计

### 5.1 CommsInterface — 通信层

```python
class CommsInterface(ABC):
    """通信层抽象。当前仅 TcpClient 实现，后续可扩展 USB/CAN 卡。"""

    @abstractmethod
    async def connect(self, host: str, port: int, timeout: float = 3.0) -> bool

    @abstractmethod
    async def disconnect(self)

    @abstractmethod
    async def send(self, data: bytes)

    @abstractmethod
    async def receive(self, timeout: float = 1.0) -> bytes | None

    @property
    def is_connected(self) -> bool
```

### 5.2 ProtocolInterface — 协议层

```python
class ProtocolInterface(ABC):
    """协议层抽象。每个产品实现一个子类。"""

    @property
    def product_name(self) -> str

    @abstractmethod
    def build_request(self, cmd: Command) -> bytes

    @abstractmethod
    def parse_response(self, raw: bytes) -> Response | None

    @abstractmethod
    def decode_telemetry(self, raw: bytes, tm_type: str) -> dict[str, TelemetryValue]

    def verify_checksum(self, frame: bytes) -> bool

    def compute_checksum(self, payload: bytes) -> bytes

    @abstractmethod
    def get_tm_params(self, tm_type: str) -> list[TmParamDef]

    @abstractmethod
    def get_commands(self) -> list[CommandDef]
```

### 5.3 核心数据类

```python
@dataclass
class Command:
    cmd_id: int               # 指令码 (如 0x005A)
    name: str                 # 指令名
    params: dict | None       # 参数 (注入指令的数值等)

@dataclass
class Response:
    raw: bytes                # 原始字节
    parsed: bool              # 解析是否成功
    tm_type: str | None       # 遥测类型 (tm1/tm2/query/ack)
    data: dict | None         # 解析后的数据

@dataclass
class TelemetryValue:
    param_id: str             # TMHEDTZ1001
    name: str                 # 模式字
    raw_value: int            # 原始值
    eng_value: float | str    # 工程量值
    unit: str                 # V / A / s
    status: str               # normal / warning / abnormal

@dataclass
class TmParamDef:
    id: str                   # TMHEDTZ1001
    name: str                 # 模式字
    byte_offset: int
    bit_offset: int
    byte_length: int
    type: str                 # uint16 / int16 / float32 / enum
    endian: str               # big
    scale: float
    unit: str
    enum_ref: str | None
```

### 5.4 产品注册表格式 (config/products.yaml)

```yaml
products:
  nebula_ppcu:
    display_name: "星云 400W 霍尔电推进 PPCU"
    protocol_class: nebula_rs422.NebulaRS422Protocol
    protocol_def_dir: protocol_defs/nebula_ppcu
    comms_defaults:
      type: tcp
      host: 192.168.117.26
      port: 20004
      timeout: 3.0
    test_case_dir: test_cases/nebula_ppcu
```

---

## 6. PPCU 协议实现关键细节

### 6.1 物理层 (来自协议文档)

| 参数 | 值 |
|---|---|
| 接口形式 | 异步 RS-422 |
| 波特率 | 115.2 kbps |
| 允许偏差 | 发送端 ±0.5%, 接收端 ±3% |
| UART 格式 | 1起始 + 8数据 + 1奇校验 + 1停止 |
| 字序 | 高字节在前 (big-endian) |

### 6.2 帧结构

**指令帧 (计算机 → PPCU)**:
```
字节 0~1:  帧头标识符      EB 90 (固定)
字节 2~3:  版本号(3bit) + 类型(1bit) + 副导头(1bit) + APID(11bit)
                           = 0x0520 (固定)
字节 4~5:  分组标志(2bit) + 源包序列计数(14bit)  分组标志固定 0b11 (standalone)
字节 6~7:  数据域长度 (16-bit word，不含校验和)
字节 8~9:  指令码 (如 0x005A = TM1请求)
字节 10~N: 数据域 (依指令码而定)
字节 N~N+1: 校验和 (从字节2到字节N累加取反取低16bit)
```

**应答帧 (PPCU → 计算机)**:
```
字节 0~1:  帧头标识符      1A CF (固定)
字节 2~3:  版本号(3bit) + 类型(1bit) + 副导头(1bit) + APID(11bit)
                           = 0x0525 (TM1应答)
字节 4~5:  分组标志(2bit) + 源包序列计数(14bit)
字节 6~7:  数据域长度
字节 8~N:  遥测数据
字节 N~N+1: 校验和
```

### 6.3 校验算法

```
从第 3 字节 (索引 2, 版本+APID) 到数据域末尾,
单字节累加求和 → 取反 → 取低 16bit → 高字节在前写入
```

### 6.4 指令码表 (核心)

| 指令码 | 名称 | 说明 |
|---|---|---|
| 0x005A | TM1 请求 | 常规遥测包 1, 周期 1s |
| 0x00AA | TM2 请求 | 常规遥测包 2, 周期 2s |
| 0x0310 | 查询请求 | 查询遥测包, 非周期 |
| 0x014A | 点火指令 | 立即遥控 (示例) |
| 0x0155 | 启动更新 | 上注升级用 |

### 6.5 遥测数据类型及转换

| 原始类型 | 编码 | 转换公式示例 |
|---|---|---|
| uint16 | 大端无符号 16bit | 电源电压: b = a × 1/180 (V) |
| int16 | 大端有符号 16bit | 压力传感器: b = a × 1/100 (kPa) |
| float32 | 大端 IEEE754 | 各种时限参数 |
| enum | 位域 (1~4bit) | 模式字 / 故障标志 |

---

## 7. 安全机制

### 7.1 安全设计原则

PPCU 涉及高压（母线 300V 级）和阳极放电等危险操作，软件必须在设计层面保证安全。
通讯验证阶段（M1）仅开放只读遥测指令，不发送任何改变 PPCU 运行模式的遥控指令。

**核心原则**: 只读遥测不越界，门限监控不遗漏，异常状态不沉默。

### 7.2 指令分级

| 等级 | 范围 | 说明 | 开放阶段 |
|---|---|---|---|
| 绿色（只读） | TM1/TM2/查询遥测请求 | 不改变 PPCU 任何状态，仅请求遥测数据 | M1 |
| 橙色（受限） | 点火、开关机等遥控指令 | 改变运行模式，需模式检查 + 确认对话框 | M3（需用户确认） |
| 红色（禁止） | 固件更新等 | 修改 PPCU 固件，需多重确认 | 待定 |

M1 阶段只实现绿色指令。橙色指令的参数和流程必须在开发前与用户沟通安全边界。

### 7.3 遥测安全门限

软件实时解析遥测数据，自动检查关键参数是否在安全范围内：

| 参数 | ID | 安全范围 | 超限动作 |
|---|---|---|---|
| 母线电压 | TMHEDTZ1003 | 0~300 V | 红色告警 |
| 母线电流 | TMHEDTZ1005 | 0~20 A | 红色告警 |
| 模式字 | TMHEDTZ1001 | 待机/自检（正常） | 跳变至点火/稳态 → 紧急告警 |

超限情况触发的动作：
1. 状态栏闪烁红色告警
2. 自动停止后续发包
3. 日志记录超限详情
4. 提示用户检查硬件状态

### 7.4 状态机守护

软件维护 PPCU 模式状态机，跟踪模式字变化：

```
待机 → 阴极加热 → 阴极点火 → 阳极点火 → 稳态 → 关机
```

- 通讯验证阶段预期状态应始终为「待机」或「自检」
- 非预期模式跳转（如待机→点火）触发紧急告警
- 状态变化记录到日志，供事后分析

### 7.5 通讯异常保护

| 异常场景 | 处理方式 |
|---|---|
| TCP 连接断开 | 停止后续发包，状态栏提示断连 |
| 连续 3 帧校验失败 | 告警"链路异常，数据不可信"，自动暂停轮询 |
| 应答超时 | 重试 2 次，仍超时则暂停并提示 |
| 遥测值长时间不变（超过 30s） | 提示"PPCU 可能已掉电或链路卡死" |

### 7.6 安全相关待定事项

- 部分遥控指令码的详细行为定义（需用户确认后才能实现）
- 高压测试的安全操作流程（是否需要在软件中加入硬件互锁状态读取）
- 异常情况下的自动恢复策略（自动重连 vs 人工介入）

---
## 8. 测试用例 YAML 格式

```yaml
name: 点火启动时序测试
suite_id: TC-001
description: 验证 PPCU 从待机到点火的完整时序

setup:
  - action: send_command
    command: 遥测1请求
    wait_response: true
    verify:
      response_timeout_ms: 1000

steps:
  - id: STEP-01
    description: 发送点火指令
    action: send_command
    command: 立即遥控指令
    params:
      cmd_id: 0x014A
    expect:
      response_timeout_ms: 5000
      check_points:
        - telemetry: 模式字
          param_id: TMHEDTZ1001
          expected: 点火模式
        - telemetry: 阳极点火累计时间
          param_id: TMHEDTZ2005
          expected_range: [0, 65535]
          unit: s

  - id: STEP-02
    description: 验证点火后遥测正常
    action: poll_telemetry
    tm_type: tm1
    count: 3
    interval_s: 1
    expect:
      - telemetry: 阳极电流
        param_id: TMHEDTZ1021
        expected_gt: 0.4
        unit: A

teardown:
  - action: send_command
    command: 立即遥控指令
    params:
      cmd_id: 待机模式
```

---

## 9. 实现里程碑 (4 个阶段)

> ✅ M1 通信+协议编解码 — 已完成
> ✅ M2 人机交互界面 — 已完成
> ❌ M3 测试引擎+用例执行 — 未开始
> ❌ M4 数据存储+报告生成 — 未开始

### M1 — 通信 + 协议编解码

| 文件 | 内容 |
|---|---|
| requirements.txt | 依赖清单 |
| src/comms/interface.py | CommsInterface ABC |
| config/local.yaml.example | 本地覆盖模板 |
| config/default.yaml | 默认配置 |
| config/products.yaml | 产品注册表 |
| src/protocol/nebula_rs422.py | FrameBuilder + FrameParser |
| src/protocol/telemetry_loader.py | YAML → TmParamDef |
| src/protocol/command_loader.py | YAML → CommandDef |
| src/protocol/factory.py | 协议工厂 |
| protocol_defs/nebula_ppcu/*.yaml | 5 个 YAML 定义文件 |
| main.py | 入口 + 初始化流程 |
| tests/test_protocol.py | 单元测试 |
| tests/test_comms.py | TCP 回显集成测试 |

**交付**: 可连通讯盒、发遥测请求、解析应答、还原工程量。

**帧格式说明**: CCSDS 分组标志固定 0x03 (standalone packet)，位于源包序列字段高 2 位。
长度字段以 16-bit word 为单位（不含校验和），即数据域字节数 ÷ 2。


### M2 — 遥测面板 + 实时显示
### M2 — 人机交互界面
| 文件 | 内容 |
|---|---|
| src/ui/main_window.py | 统一单页布局 (QSplitter), 连接/指令/遥测同屏显示 |
| src/ui/panels/comm_panel.py | 连接控制 + 报文滚动显示 |
| src/ui/panels/command_panel.py | 指令控制面板 (TM1/TM2/查询单次+轮询) |
| src/ui/panels/telemetry_panel.py | TM1/TM2/查询分页实时刷新 |
| src/ui/components/telemetry_table.py | 参数名/原始值/工程量/单位/状态 |
| src/ui/components/message_log.py | 方向色标 + HEX/文本 |
| src/comms/tcp_client.py | TCP keepalive (空闲超时保护) |
| src/ui/main_window.py | 文件菜单: 导入遥测定义 (QFileDialog) |
| tools/import_from_excel.py | 通用 Excel 导入 (支持任意 sheet 名动态扩展) |

**交付**: 统一单页布局无需切换标签页。连接与指令分离，手动触发 TM1/TM2 独立
单次 + 同时轮询，查询包单次查询。TCP keepalive 防止串口盒空闲断连。
**动态导入**: 文件菜单 → 导入遥测定义，支持任意数量遥测包类型的 Excel 模板。

### M3 — 测试引擎 + 用例执行

| 文件 | 内容 |
|---|---|
| src/engine/test_case_loader.py | YAML 用例加载 |
| src/engine/test_executor.py | 指令→等待→判定循环 |
| src/engine/checker.py | 值比较 (精确/区间/枚举/时序) |
| src/engine/timing_verifier.py | 阶段时间与协议范围比对 |
| src/ui/panels/test_panel.py | 用例树 + 执行控制 + 结果 |
| test_cases/nebula_ppcu/*.yaml | 配套测试用例 |

**交付**: 可加载用例集、自动执行、输出 PASS/FAIL。

### M4 — 数据存储 + 报告生成

| 文件 | 内容 |
|---|---|
| src/data/database.py | SQLite 表结构 |
| src/data/log_manager.py | 报文自动落盘 |
| src/report/csv_reporter.py | CSV 导出 |
| src/report/html_reporter.py | HTML 带样式 + 色标 |
| src/report/word_reporter.py | .docx 带封面目录 |
| src/report/templates/ | Jinja2 模板 |
| src/ui/panels/report_panel.py | 历史查询 + 导出 |
| src/ui/panels/config_panel.py | 通讯/产品/报告配置 |

**交付**: 测试完成自动生成 CSV/HTML/Word 报告。

---

## 10. 协议 YAML 定义文件规范

### 10.1 protocol.yaml

```yaml
protocol:
  name: "星云 RS422 通讯协议"
  version: "A04"

frame:
  command_header: [0xEB, 0x90]
  response_header: [0x1A, 0xCF]

checksum:
  algorithm: sum_invert_low16
  start_byte: 2

addressing:
  apid_command: 0x0520
  apid_tm1: 0x0525
  apid_tm2: 0x0526
  apid_query: 0x0521
  apid_ack: 0x0527

uart:
  baudrate: 115200
  databits: 8
  parity: odd
  stopbits: 1
```

### 10.2 telemetry_tm1.yaml (节选)

```yaml
tm_type: tm1
description: 常规遥测包 1
cycle_s: 1

params:
  - id: TMHEDTZ1001
    name: 模式字
    byte_offset: 12
    bit_offset: 4
    bit_length: 4
    type: enum
    enum_ref: mode_word
  - id: TMHEDTZ1002
    name: 工作子模式字
    byte_offset: 12
    bit_offset: 0
    bit_length: 4
    type: enum
    enum_ref: sub_mode_word
  - id: TMHEDTZ1003
    name: 被测电源母线电压
    byte_offset: 14
    byte_length: 2
    type: uint16
    endian: big
    scale: 0.0055556  # 1/180
    decimal_places: 2
    unit: V
    range_min: 0
    range_max: 300
  - id: TMHEDTZ1005
    name: 被测电源母线电流
    byte_offset: 16
    byte_length: 2
    type: uint16
    endian: big
    scale: 0.001  # 1/1000
    decimal_places: 2
    unit: A
    range_min: 0
    range_max: 20
```

### 10.3 commands.yaml (节选)

```yaml
commands:
  - id: 0x005A
    name: 遥测1请求
    category: telemetry_request
    description: 常规遥测包1请求
    data_length: 0
    response_type: tm1

  - id: 0x00AA
    name: 遥测2请求
    category: telemetry_request
    description: 常规遥测包2请求
    data_length: 0
    response_type: tm2

  - id: 0x0310
    name: 查询遥测请求
    category: telemetry_request
    description: 查询遥测包（非周期）
    data_length: 0
    response_type: query

  - id: 0x014A
    name: 进入点火模式1
    category: immediate_command
    description: 立即遥控: 进入点火模式1
    data_length: 0
    response_type: ack
```

### 10.4 enums.yaml (节选)

```yaml
enums:
  mode_word:
    0x0: 待机模式
    0x1: 点火模式
    0x2: 稳态工作模式
    0x3: 关机模式
    0x4: 故障模式
    0xF: 自检模式

  sub_mode_word:
    0x0: 待机
    0x1: 阴极加热
    0x2: 阴极点火
    0x3: 阳极点火
    0x4: 稳态
    0x5: 除气
    0x6: 冲洗

  fault_type:
    0x01: 电流异常1
    0x02: 电流异常2
    0x04: 压力异常1
    0x08: 压力异常2
    0x10: 温度异常
    0x20: 点火超时
```

---

## 11. 多协议扩展说明

V1 只实现 NebulaRS422Protocol，但架构已预留完整的可插拔能力：

| 机制 | 预留位置 | 新增一个产品需要改的部分 |
|---|---|---|
| 协议抽象 | ProtocolInterface | 实现一个约 50 行子类 |
| 通信抽象 | CommsInterface | 通常不改（都走 TCP） |
| 遥测定义 | protocol_defs/{产品}/ | 写 YAML 文件 |
| 指令码定义 | protocol_defs/{产品}/commands.yaml | 写 YAML 文件 |
| 产品注册 | config/products.yaml | 加一条记录 |
| 测试用例 | test_cases/{产品}/ | 写 YAML 用例 |
| 遥测 UI | 动态渲染 | 不改代码 |
| 测试引擎 | 产品无关 | 不改代码 |
| 报告层 | 产品无关 | 不改代码 |
| 数据层 | 产品无关 | 不改代码 |

---

## 12. 依赖清单 (requirements.txt)

```
PySide6>=6.6
qasync>=0.27
pyyaml>=6.0
pandas>=2.0
python-docx>=1.1
jinja2>=3.1
pyqtgraph>=0.13
numpy>=1.24
```

---

## 13. 待定事项

- 串口转以太网盒的具体型号与配置方式 (待用户提供后补充)
- PPCU 是否在台架上配置了专用测试 422 口，或需通过切换开关共用星务总线
- 报告模板的具体样式要求 (公司模板/Logo)
- 部分遥控指令码的详细参数定义 (协议文档可能未完全列出)
