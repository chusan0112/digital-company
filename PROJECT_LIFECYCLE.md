# 项目生命周期管理系统

## 概述

数字公司插件的项目生命周期管理系统，提供从项目立项到复盘总结的完整流程管理。

## 功能特性

### 1. 项目立项
- 创建新项目
- 发起立项会议（AI高管头脑风暴）
- AI高管们（CEO、CFO、CTO、COO、CHRO）根据角色发表观点
- 确定项目方案，评估可行性
- 自动保存会议记录

### 2. 会议系统
支持多种会议类型：
- `kickoff` - 立项会议（头脑风暴）
- `standup` - 晨会/例会
- `review` - 中期复盘会
- `retrospective` - 项目总结会
- `regular` - 常规会议

### 3. 项目执行
- 分配任务给AI员工
- 进度跟踪
- 里程碑管理
- 定期开会协调

### 4. 复盘总结
- 项目结束复盘
- 经验教训归档
- 保存到知识库

### 5. 知识库
- 所有会议记录
- 经验教训
- 项目总结
- 供以后调用参考

## 数据存储

```
storage/
  projects/
    proj_20260323_xxxxx/
      info.json          # 项目信息
      meetings/          # 会议记录
        meet_xxx.json
      tasks/            # 任务记录
        task_xxx.json
      lessons/          # 经验教训
      milestones.json   # 里程碑
      summary.json      # 项目总结
  knowledge/
    lessons/            # 全局经验教训
    summaries/          # 全局项目总结
```

## API 接口

### 项目管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/project` | POST | 创建项目 |
| `/api/lifecycle/project/{id}` | GET | 获取项目信息 |
| `/api/lifecycle/projects` | GET | 列出所有项目 |
| `/api/lifecycle/project/{id}` | PUT | 更新项目 |

### 会议管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/meeting` | POST | 创建会议 |
| `/api/lifecycle/meeting/{project_id}/{meeting_id}` | GET | 获取会议信息 |
| `/api/lifecycle/meetings/{project_id}` | GET | 列出项目会议 |
| `/api/lifecycle/kickoff/{project_id}` | POST | 发起立项会议(AI高管辩论) |

### 任务管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/task` | POST | 创建任务 |
| `/api/lifecycle/task/{project_id}/{task_id}` | GET | 获取任务信息 |
| `/api/lifecycle/tasks/{project_id}` | GET | 列出项目任务 |
| `/api/lifecycle/task/{project_id}/{task_id}` | PUT | 更新任务 |

### 里程碑

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/milestones/{project_id}` | GET | 获取项目里程碑 |

### 复盘总结

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/retrospective` | POST | 创建复盘会议 |
| `/api/lifecycle/complete` | POST | 完成项目 |

### 知识库

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/knowledge/lessons` | GET | 获取经验教训 |
| `/api/lifecycle/knowledge/summaries` | GET | 获取项目总结 |

### 统计

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/lifecycle/statistics` | GET | 获取项目统计 |

## 使用示例

### 1. 创建项目

```json
POST /api/lifecycle/project
{
  "name": "AI智能助手项目",
  "description": "开发一款基于大模型的AI智能助手",
  "budget": 100000,
  "owner": "张三",
  "tags": ["AI", "大模型"]
}
```

### 2. 发起立项会议

```json
POST /api/lifecycle/kickoff/proj_20260323_xxxxx
{
  "budget": 100000,
  "deadline": "T+90d",
  "priority": "high"
}
```

响应示例：
```json
{
  "success": true,
  "result": {
    "meeting": {
      "id": "meet_xxx",
      "summary": {
        "conclusion": "经讨论，该项目可行性评估为中等（平均76%），整体风险可控。建议在风险可控的前提下推进。",
        "feasibility": 0.76
      },
      "speeches": [...]
    },
    "project_status": "active",
    "feasibility_score": 0.76
  }
}
```

### 3. 创建任务

```json
POST /api/lifecycle/task
{
  "project_id": "proj_20260323_xxxxx",
  "name": "完成需求分析",
  "description": "分析用户需求并编写需求文档",
  "priority": "high",
  "due_date": "2026-04-01"
}
```

### 4. 更新任务状态

```json
PUT /api/lifecycle/task/proj_20260323_xxxxx/task_xxx
{
  "status": "in_progress",
  "progress": 50
}
```

### 5. 创建复盘会议

```json
POST /api/lifecycle/retrospective
{
  "project_id": "proj_20260323_xxxxx",
  "title": "项目复盘会议",
  "host": "项目经理",
  "what_went_well": ["团队协作好", "需求变更少"],
  "what_could_improve": ["沟通可以更及时", "测试覆盖不足"],
  "lessons_learned": ["早期需要更多技术评审", "要做好风险预案"]
}
```

### 6. 完成项目

```json
POST /api/lifecycle/complete
{
  "project_id": "proj_20260323_xxxxx",
  "conclusion": "项目成功上线，用户反馈良好"
}
```

### 7. 查询知识库

```json
GET /api/lifecycle/knowledge/lessons
GET /api/lifecycle/knowledge/summaries
```

## 触发方式

### 通过API调用
所有功能通过REST API触发，详见上方API接口文档。

### 通过飞书消息（需集成）
可以配置飞书机器人，通过消息触发项目操作。

## 状态流转

```
planning → kickoff → active → review → completed → archived
                      ↓
                   (可多次review)
```

## 项目状态说明

| 状态 | 说明 |
|------|------|
| planning | 规划中 |
| kickoff | 立项中（正在开立项会议）|
| active | 执行中 |
| review | 中期复盘 |
| completed | 已完成 |
| archived | 已归档 |

## 任务状态说明

| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| in_progress | 进行中 |
| review | 待审核 |
| completed | 已完成 |
| failed | 失败 |
