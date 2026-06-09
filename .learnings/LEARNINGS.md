# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---
## [LRN-20260607-001] best_practice

**Logged**: 2026-06-07T22:15:00+08:00
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
安装/下载软件时禁止安装在系统盘(C:)，如需安装在系统盘必须先征求用户允许。

### Details
用户明确要求：任何下载或安装软件的操作，不得使用系统盘(C:\)作为目标路径。
如果由于技术限制必须安装在系统盘，必须先向用户说明原因并获得明确许可。

### Suggested Action
- 下载软件时优先选择非系统盘路径（如 D:/, E:/ 等）
- 如果只有系统盘可用，先向用户请示
- 在项目规则文件中长期记录此约束

### Metadata
- Source: user_feedback
- Tags: install, download, system_drive, safety

---

## [LRN-20260607-002] best_practice

**Logged**: 2026-06-07T22:16:00+08:00
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
当用户说"上传git"/"sync to git"/"push to github"时，自动执行 git add → commit → push（通过代理）。

### Details
用户期望一条口令完成本地提交和云端同步。操作流程：
1. `git add -A`
2. `git commit -m "提交信息"`（自动生成描述性的提交信息）
3. `git -c http.proxy=http://127.0.0.1:17897 push`

### Suggested Action
在 CLAUDE.md 中记录为全局规则，直接响应。

### Metadata
- Source: user_feedback
- Tags: git, push, sync, workflow

---

## [LRN-20260608-001] best_practice

**Logged**: 2026-06-08T22:20:00+08:00
**Priority**: critical
**Status**: promoted
**Area**: config

### Summary
功率相关参数的功能开发和指令参数修改，必须先与用户沟通安全边界，不得自行设定执行。

### Details
用户明确要求：在软件开发调试阶段，任何与功率相关的参数（如电压、电流门限、时序参数等）
以及遥控指令参数的修改，必须先与用户确认安全边界。禁止仅凭自身经验设定参数值并执行流程测试。

### Metadata
- Source: user_feedback
- Tags: safety, power, parameters, communication

---

## [LRN-20260608-002] best_practice

**Logged**: 2026-06-08T22:50:00+08:00
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
项目开始前须先配置 Python 虚拟环境，依赖安装使用国内 PyPI 镜像。

### Details
- 项目工作开始之前先建 .venv，配置解释器
- pip install 必须用国内镜像（清华源 https://pypi.tuna.tsinghua.edu.cn/simple）
- 必须带代理 --proxy http://127.0.0.1:17897
- .venv 放在项目所在非系统盘

### Metadata
- Source: user_feedback
- Tags: environment, pip, mirror, proxy

---
## [LRN-20250609-001] best_practice

**Logged**: 2026-06-09T18:00:00+08:00
**Priority**: high
**Status**: pending
**Area**: frontend

### Summary
QTableWidget 实时刷新场景必须复用 Item、批量更新 UI、避免每变化一个值就创建一个 QTimer，否则大量参数轮询时会导致界面严重卡顿。

### Details
PPCU TestBench 的遥测面板在轮询模式下每秒刷新 238+ 个参数，每个参数 8 个单元格。旧方案每帧更新时每次都 
ew QTableWidgetItem() 再 setItem()，Qt 内部对每个 setItem 触发一次 UI 排版重绘；同时值变化高亮功能为每个变化的值 
ew QTimer()，模拟量持续变化导致定时器每秒创建销毁数十次。三者叠加→ UI 线程被排版和定时器调度淹没，界面卡顿。

### Suggested Action
三个优化点应同时实施：
1. **复用 Item**: self._items 字典按 (param_id, col) 缓存 Item，首次创建后后续只 setText()
2. **批量刷新**: 整个更新循环用 setUpdatesEnabled(False) / setUpdatesEnabled(True) 包裹
3. **单定时器批量清除高亮**: 用 _hl_dirty 集合记录所有变化过的 key，单一 QTimer + _sweep_highlights 批量恢复背景色

### Resolution
- **Resolved**: 2026-06-09T18:30:00+08:00
- **Notes**: 三项优化已在 telemetry_table.py 中实施：QTableWidgetItem 复用（self._items 字典）、setUpdatesEnabled(False/True) 批量刷新、单 QTimer + hl_dirty 集合批量清除高亮。验证通过，轮询卡顿消除。

### Metadata
- Source: user_feedback
- Related Files: PPCU_TestBench/src/ui/components/telemetry_table.py
- Tags: performance, qt, telemetry, frontend
- Pattern-Key: perf.qtablewidget.realTime
- Recurrence-Count: 1
- First-Seen: 2026-06-09
- Last-Seen: 2026-06-09

---
