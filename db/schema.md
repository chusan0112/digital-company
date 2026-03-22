# 数据库Schema设计文档

本文档描述数字公司插件的SQLite数据库结构。

## 数据库概述
- **数据库类型**: SQLite
- **版本**: 1.0
- **字符编码**: UTF-8

---

## 表结构

### 1. users (用户表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户ID |
| username | TEXT | NOT NULL UNIQUE | 用户名 |
| password_hash | TEXT | NOT NULL | 密码哈希 |
| role | TEXT | NOT NULL | 角色（admin/user/guest） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 2. departments (部门表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 部门ID |
| name | TEXT | NOT NULL | 部门名称 |
| description | TEXT | | 部门描述 |
| parent_id | INTEGER | REFERENCES departments(id) | 父部门ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 3. employees (员工表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 员工ID |
| name | TEXT | NOT NULL | 员工姓名 |
| role | TEXT | NOT NULL | 职位/角色 |
| department_id | INTEGER | REFERENCES departments(id) | 所属部门ID |
| skills | TEXT | JSON格式 | 技能列表 |
| status | TEXT | DEFAULT 'active' | 状态（active/inactive） |
| hire_date | DATE | | 入职日期 |
| salary | REAL | | 薪资 |
| performance | REAL | | 绩效评分(0-100) |

---

### 4. projects (项目表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 项目ID |
| name | TEXT | NOT NULL | 项目名称 |
| description | TEXT | | 项目描述 |
| status | TEXT | DEFAULT 'planning' | 状态（planning/active/completed/archived） |
| priority | TEXT | DEFAULT 'medium' | 优先级（low/medium/high/urgent） |
| department_id | INTEGER | REFERENCES departments(id) | 负责部门ID |
| start_date | DATE | | 开始日期 |
| end_date | DATE | | 结束日期 |
| budget | REAL | | 预算 |
| progress | REAL | DEFAULT 0 | 进度百分比(0-100) |

---

### 5. tasks (任务表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 任务ID |
| name | TEXT | NOT NULL | 任务名称 |
| description | TEXT | | 任务描述 |
| project_id | INTEGER | REFERENCES projects(id) | 所属项目ID |
| assignee_id | INTEGER | REFERENCES employees(id) | 负责人ID |
| status | TEXT | DEFAULT 'pending' | 状态（pending/in_progress/review/completed） |
| priority | TEXT | DEFAULT 'medium' | 优先级（low/medium/high/urgent） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| due_date | DATE | | 截止日期 |

---

### 6. decisions (决策表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 决策ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | | 更新时间 |
| intent | TEXT | NOT NULL | 决策意图 |
| policy | TEXT | | 相关政策 |
| executive_panel | TEXT | JSON格式 | 决策委员会成员 |
| options | TEXT | JSON格式 | 可选方案 |
| summary | TEXT | | 决策摘要 |
| status | TEXT | DEFAULT 'pending' | 状态（pending/approved/rejected/implemented） |
| execution_result | TEXT | | 执行结果 |

---

### 7. approvals (审批表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 审批ID |
| title | TEXT | NOT NULL | 审批标题 |
| status | TEXT | DEFAULT 'pending' | 状态（pending/approved/rejected） |
| payload | TEXT | JSON格式 | 审批内容 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | | 更新时间 |
| decided_at | DATETIME | | 决策时间 |
| decision | TEXT | | 审批决定 |
| comments | TEXT | | 审批意见 |

---

### 8. audit_logs (审计日志表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 日志ID |
| event_type | TEXT | NOT NULL | 事件类型 |
| actor | TEXT | | 操作者 |
| target | TEXT | | 操作目标 |
| details | TEXT | JSON格式 | 详细信息 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 9. meetings (会议表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 会议ID |
| title | TEXT | NOT NULL | 会议标题 |
| host_id | INTEGER | REFERENCES employees(id) | 主持人ID |
| start_time | DATETIME | NOT NULL | 开始时间 |
| end_time | DATETIME | NOT NULL | 结束时间 |
| status | TEXT | DEFAULT 'scheduled' | 状态（scheduled/ongoing/completed/cancelled） |
| notes | TEXT | | 会议记录 |
| action_items | TEXT | JSON格式 | 行动项 |

---

### 10. meeting_rooms (会议室表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 会议室ID |
| name | TEXT | NOT NULL | 会议室名称 |
| capacity | INTEGER | NOT NULL | 容纳人数 |
| location | TEXT | | 位置 |
| status | TEXT | DEFAULT 'available' | 状态（available/occupied/maintenance） |

---

## 表关系图

```
users
  ↑
  │ (host_id)
  ↓
meetings ← employees (assignee_id)
  ↑              ↑ (department_id)
  │              ↓
  │          departments ← departments (parent_id)
  │              ↑
  │              │ (department_id)
  │              ↓
  │          projects → tasks
  │
  ├─ decisions
  ├─ approvals
  └─ audit_logs

meeting_rooms (独立表)
```

---

## 索引设计

为提升查询性能，建议在以下字段创建索引：
- `users.username`
- `employees.department_id`
- `projects.department_id`
- `projects.status`
- `tasks.project_id`
- `tasks.assignee_id`
- `tasks.status`
- `decisions.status`
- `approvals.status`
- `audit_logs.event_type`
- `audit_logs.created_at`
- `meetings.host_id`
- `meetings.start_time`
