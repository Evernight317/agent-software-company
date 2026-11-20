# Agent Software Company

LLM 多 Agent 自主协作软件开发公司。多个角色（PM、架构师、开发者、QA、DevOps）从需求到交付，自主协作开发出可运行的软件。

## 快速开始

### 1. 配置环境

```bash
# 复制环境配置
cp .env.example .env

# 编辑 .env，填入你的 LLM API Key 和 Base URL
vi .env
```

### 2. 安装依赖

```bash
pip install -e ".[dev]"
```

### 3. 运行

```bash
# 查看配置状态
asc status

# 运行开发流水线
asc run -r "构建一个 Todo 应用，支持增删改查" -n todo-app
```

## 架构

```
User Requirement
    │
    ▼
  PM ──→ PRD + Issues
    │
    ▼
  Architect ──→ Technical Design + Tasks
    │
    ▼
  Backend Dev ─┐
  Frontend Dev ─┤── Code + Tests + PRs
    │          │
    ▼          ▼
  QA ──→ Integration Tests + Bug Reports
    │
    ▼
  DevOps ──→ Dockerfile + docker-compose
    │
    ▼
  Deliverable: 可运行的软件
```

## 核心模块

| 模块 | 说明 |
|------|------|
| `engine/board.py` | 看板系统（Issue + Kanban） |
| `engine/sandbox.py` | 代码沙箱（文件操作 + 命令执行） |
| `engine/git.py` | Git 模拟（commit + PR + Review） |
| `engine/artifacts.py` | 制品管理（PRD → 设计 → 代码 → 测试） |
| `engine/channel.py` | Agent 通信（Issue 评论 + PR Review） |
| `agents/base.py` | Agent 基类（记忆 + 任务执行） |
| `llm/client.py` | LLM 客户端（OpenAI 兼容） |
| `pipeline/orchestrator.py` | 协调器（驱动完整流水线） |

## 配置

- `.env` — LLM API 配置（用户自行填写）
- `config/company.yaml` — 角色定义
- `config/models.yaml` — 模型映射
- `config/settings.yaml` — 全局参数

## 测试

```bash
pytest -v
```

## 技术栈

- Python 3.12+ / FastAPI
- OpenAI API (兼容多种 LLM)
- Rich (终端 UI) / Typer (CLI)
- ChromaDB (记忆检索) / SQLite (持久化)
