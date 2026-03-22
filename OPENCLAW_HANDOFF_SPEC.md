# Digital Company Plugin — OpenClaw 自主迭代交接规范（V2 最详细版）

> 适用对象：接手 `skills/digital-company` 的 OpenClaw Agent / 开发者
> 
> 核心目标：把插件从“可运行MVP”稳定迭代为“董事长一句话驱动的数字公司操作系统”
> 
> 核心约束：**不得改动 OpenClaw 本体**，仅在插件目录内完成所有功能。

---

## 目录

1. [范围与约束（必须遵守）](#1-范围与约束必须遵守)
2. [当前基线能力（已完成）](#2-当前基线能力已完成)
3. [架构与文件责任地图](#3-架构与文件责任地图)
4. [目标能力模型（终局）](#4-目标能力模型终局)
5. [任务分解（P0/P1/P2）](#5-任务分解p0p1p2)
6. [文件级改造清单（逐文件）](#6-文件级改造清单逐文件)
7. [接口规范（请求/响应/错误）](#7-接口规范请求响应错误)
8. [数据模型规范](#8-数据模型规范)
9. [治理规则与决策策略规范](#9-治理规则与决策策略规范)
10. [测试与验收（Definition of Done）](#10-测试与验收definition-of-done)
11. [发布/回滚/故障处理SOP](#11-发布回滚故障处理sop)
12. [迭代节奏建议（2周冲刺模板）](#12-迭代节奏建议2周冲刺模板)
13. [给 OpenClaw 的可执行任务模板](#13-给-openclaw-的可执行任务模板)

---

## 1. 范围与约束（必须遵守）

## 1.1 允许修改目录
- `~/.openclaw/skills/digital-company/**`

## 1.2 禁止修改目录
- `~/.openclaw/agents/**`
- OpenClaw 核心加载器、主路由、主执行器
- 非 `digital-company` 相关 skill

## 1.3 环境约束
- OS：Windows + PowerShell
- 端口：默认 `8080`
- 编码：必须兼容 UTF-8（Windows 控制台环境）
- 启动脚本必须可用：`run-bg.ps1`, `run.ps1`, `stop.ps1`, `status.ps1`

## 1.4 质量约束
每次迭代必须满足：
1. 不破坏现有 API（除非在文档中声明版本升级）
2. `health-check.ps1` 通过
3. `smoke-test.ps1` 通过
4. 驾驶舱可打开且治理中心可见
5. 失败可回滚

---

## 2. 当前基线能力（已完成）

## 2.1 治理闭环
- 董事长指令提交：`POST /api/chairman/command`
- 指令预览：`POST /api/chairman/command/preview`
- 决策查询：`GET /api/decisions/{id}`
- 审批通过/驳回：
  - `POST /api/approvals/{id}/approve`
  - `POST /api/approvals/{id}/reject`
- 审批查询：`GET /api/approvals/{id}`
- 审批后自动执行（组织/项目/任务）

## 2.2 治理配置
- `governance_config.json` 已接入
- 支持预算阈值、风险阈值、必审意图

## 2.3 数据持久化
- 决策和审批持久化到 JSON repository
- ID 使用 UUID

## 2.4 驾驶舱与监控
- 主页面：`http://127.0.0.1:8080/`
- 健康检查：`GET /api/health`
- 董事长快照：`GET /api/chairman/snapshot`
- 治理中心显示最近决策/审批，含高风险与待审批优先展示

## 2.5 运维脚本
- `run.ps1`, `run-bg.ps1`, `stop.ps1`, `status.ps1`, `health-check.ps1`, `smoke-test.ps1`

---

## 3. 架构与文件责任地图

## 3.1 入口层
- `api.py`：外部接口总入口，负责参数解析、调用编排、返回结构
- `web/server.py`：驾驶舱HTTP服务和UI

## 3.2 编排层
- `core/orchestrator.py`：董事长指令 -> 决策包 -> 审批后执行
- `core/intent_parser.py`：自然语言解析为结构化意图
- `core/policy_engine.py`：治理策略判定
- `core/approval_center.py`：审批记录生命周期
- `core/audit_log.py`：审计事件（当前为轻量）

## 3.3 业务域层
- `domains/org_service.py`
- `domains/hr_service.py`
- `domains/project_service.py`
- `domains/finance_service.py`
- `domains/risk_service.py`

## 3.4 工作流层
- `workflows/launch_business.py`
- `workflows/weekly_review.py`

## 3.5 存储层
- `storage/repository.py`
- `storage/governance_data.json`

---

## 4. 目标能力模型（终局）

终局能力闭环：

1. 董事长自然语言下达方向
2. CEO 拉起高管评估并产出多方案
3. 治理引擎给出审批建议与风险解释
4. 审批后自动执行组织/项目/预算动作
5. 自动生成里程碑检查与异常告警
6. 董事长快照实时给出“下一步最重要决策”
7. 周期复盘沉淀到组织记忆

---

## 5. 任务分解（P0/P1/P2）

## P0（必须完成，直接影响“可控可用”）

### P0-1 审批SLA与超时告警
**目标**：待审批超过 SLA 自动变为 `overdue` 并在快照高亮。

**实现要求**：
- `governance_config.json` 增加：
  - `approval_sla_hours`
- `storage/repository.py` 增加：
  - 计算/筛选 `overdue_approvals`
- `api.py`：
  - `GET /api/approvals/overdue`
  - `GET /api/chairman/snapshot` 中加入 `overdue_approvals_count`

**验收标准**：
- 人工把审批创建时间回拨后，snapshot 能显示超时审批

---

### P0-2 里程碑检查状态机
**目标**：里程碑检查有状态并可更新，不是静态数组。

**实现要求**：
- 数据结构：`pending|at_risk|done|overdue`
- 新增接口：
  - `POST /api/milestone-check/{id}/status`
  - `GET /api/milestone-checks/alerts`
- 快照中新增：
  - `milestone_alerts`

**验收标准**：
- 能把检查状态改为 `at_risk`
- 快照能提取这条风险

---

### P0-3 审批治理条件结构化落库
**目标**：`governance_conditions` 成为审批记录字段，非拼接字符串。

**实现要求**：
- `approval_center.py` 存储：`governance_conditions: []`
- `/approve` 写入并回显
- 驾驶舱治理中心可显示条件摘要

**验收标准**：
- 查询审批记录可读到条件数组

---

## P1（高价值增强）

### P1-1 董事长快照 Top3 决策清单
规则：
1. overdue approvals
2. high-risk pending approvals
3. at-risk milestones

输出：`top3_actions`

### P1-2 预算释放机制（Stage-Gate 真正执行）
- 仅释放 phase1
- 里程碑达标后释放下一阶段预算
- 新增预算释放日志

### P1-3 决策解释增强
- summary 中增加：
  - 推荐原因3条
  - 反对意见2条
  - 不执行代价1条

---

## P2（规模化）
- 多角色权限
- AI董事会会议机制
- OKR/绩效体系闭环
- CRM/市场模块
- 财务三表自动化

---

## 6. 文件级改造清单（逐文件）

## 6.1 `governance_config.json`
新增字段建议：
```json
{
  "approval": {
    "budget_threshold": 200000,
    "high_risk_budget_threshold": 500000,
    "approval_sla_hours": 24,
    "always_require_approval_intents": ["launch_new_business"]
  },
  "milestone": {
    "default_check_sla_days": 7
  }
}
```

## 6.2 `storage/repository.py`
新增函数建议：
- `list_overdue_approvals(sla_hours)`
- `upsert_milestone_check(check)`
- `get_milestone_check(id)`
- `list_milestone_checks(status=None)`
- `list_milestone_alerts()`

## 6.3 `core/approval_center.py`
- 写入 `governance_conditions`
- 审批状态可演进到 `overdue`

## 6.4 `workflows/launch_business.py`
- 生成结构化里程碑检查（含ID）
- 高风险时绑定预算闸门策略

## 6.5 `api.py`
新增/增强接口：
- `GET /api/approvals/overdue`
- `POST /api/milestone-check/{id}/status`
- `GET /api/milestone-checks/alerts`
- `GET /api/chairman/snapshot` 增强字段

## 6.6 `web/server.py`
治理中心增强显示：
- 超时审批数
- 里程碑告警数
- Top3 actions

---

## 7. 接口规范（请求/响应/错误）

## 7.1 `POST /api/chairman/command`
请求：
```json
{ "command": "评估并落地A股量化，预算上限100万，季度内试运行" }
```
响应：
```json
{ "success": true, "decision": { "id": "uuid", "summary": {}, "approval_id": "uuid" } }
```
错误：
- `command_required`

## 7.2 `POST /api/chairman/command/preview`
响应新增：
```json
{
  "success": true,
  "preview": {},
  "chairman_recommendation": {
    "execute_now": false,
    "suggested_action": "require_stage_gate_and_finance_review",
    "reason_messages": ["..."]
  }
}
```

## 7.3 `POST /api/approvals/{id}/approve`
请求：
```json
{
  "reason": "战略匹配，批准执行",
  "comments": "可选",
  "governance_conditions": ["分阶段拨款", "财务周审"]
}
```

## 7.4 `GET /api/chairman/snapshot`
目标响应结构：
```json
{
  "success": true,
  "snapshot": {
    "company": {},
    "pending_approvals_count": 0,
    "overdue_approvals_count": 0,
    "milestone_alerts": [],
    "top_risk": {},
    "top3_actions": ["..."],
    "next_actions": ["..."]
  }
}
```

---

## 8. 数据模型规范

## 8.1 Approval
```json
{
  "id": "uuid",
  "title": "string",
  "status": "pending|approved|rejected|overdue",
  "payload": {},
  "comments": "string",
  "governance_conditions": ["string"],
  "created_at": "iso",
  "updated_at": "iso"
}
```

## 8.2 MilestoneCheck
```json
{
  "id": "uuid",
  "project_id": "string",
  "name": "T+7里程碑检查",
  "due_at": "iso",
  "status": "pending|at_risk|done|overdue",
  "check_items": ["string"],
  "notes": "string",
  "created_at": "iso",
  "updated_at": "iso"
}
```

## 8.3 SnapshotAction
```json
{
  "priority": 1,
  "type": "approval|risk|milestone",
  "title": "string",
  "id": "string",
  "reason": "string"
}
```

---

## 9. 治理规则与决策策略规范

## 9.1 风险分级规则
- `budget > high_risk_budget_threshold` => `high`
- 否则 `medium`

## 9.2 审批规则
- 命中 `always_require_approval_intents` 必审
- 预算超过 `budget_threshold` 必审

## 9.3 建议动作规则
- high risk => `require_stage_gate_and_finance_review`
- medium risk => `proceed_with_controls`

## 9.4 快照优先级规则
- overdue approval > pending high-risk approval > at-risk milestone > pending tasks

---

## 10. 测试与验收（Definition of Done）

每次迭代都必须执行并记录：

1) 启动
```powershell
powershell -ExecutionPolicy Bypass -File .\run-bg.ps1
```

2) 健康检查
```powershell
powershell -ExecutionPolicy Bypass -File .\health-check.ps1
```

3) 核心回归
```powershell
powershell -ExecutionPolicy Bypass -File .\smoke-test.ps1
```

4) 手工验证
- 打开 `http://127.0.0.1:8080/`
- 治理中心渲染正常
- 最近决策展示推荐方案、风险标记

5) DoD 判定（全部满足才算完成）
- [ ] 无 linter 错误
- [ ] 健康检查通过
- [ ] smoke 测试通过
- [ ] 新接口有样例请求/响应
- [ ] 失败场景有可读错误返回

---

## 11. 发布/回滚/故障处理SOP

## 11.1 发布步骤
1. `stop.ps1`
2. 更新代码
3. `run-bg.ps1`
4. `health-check.ps1`
5. `smoke-test.ps1`

## 11.2 回滚步骤
1. 回滚本轮涉及文件
2. `stop.ps1`
3. `run-bg.ps1`
4. 验证 health/smoke

## 11.3 故障排查优先级
1. 端口是否占用（8080）
2. `status.ps1` 是否运行
3. `logs/server.err.log` 是否有异常
4. `/api/health` 是否可达
5. smoke-test 失败在哪一步

---

## 12. 迭代节奏建议（2周冲刺模板）

## Week 1
- D1: P0-1 设计 + 配置接入
- D2: P0-1 实现 + 测试
- D3: P0-2 数据模型 + 接口
- D4: P0-2 驾驶舱展示
- D5: P0-3 结构化审批条件

## Week 2
- D1: snapshot top3 actions
- D2: stage-gate 预算释放
- D3: 决策解释增强
- D4: 回归与修复
- D5: 文档更新 + 交付

---

## 13. 给 OpenClaw 的可执行任务模板

将以下文本直接交给 OpenClaw Agent：

```text
你接管 skills/digital-company 的持续迭代。
必须遵守：
1) 禁改 OpenClaw 本体，仅改 skills/digital-company。
2) 每次迭代结束必须运行并通过：run-bg.ps1、health-check.ps1、smoke-test.ps1。
3) 先做 P0，再做 P1。

当前请执行：
- P0-1 审批SLA与超时告警
- P0-2 里程碑检查状态机
- P0-3 审批治理条件结构化落库

输出格式必须包含：
A. 修改文件清单
B. 接口变更清单（含请求/响应样例）
C. 验证命令与结果
D. 剩余待办与下一步计划
```

---

## 附：当前完成度（对外汇报口径）

- MVP闭环完成度：约 70%
- 全蓝图完成度：约 35%
- 上线前硬门槛：P0 三项必须完成

---

> 本文档为最高优先级交接规范。若代码与文档冲突，以“保持系统可运行 + 通过回归测试 + 不改 OpenClaw 本体”为第一原则。
