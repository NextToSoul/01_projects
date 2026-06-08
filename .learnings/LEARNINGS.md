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
