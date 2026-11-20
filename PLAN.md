# Agent Software Company — 项目规划

> LLM 多 Agent 自主协作软件开发公司

## 一、项目愿景

构建一个由 LLM Agent 组成的"虚拟软件公司"，多个角色（PM、架构师、开发者、测试、DevOps）自主协作，从需求到交付，**真正开发出可运行的软件**。

### 核心问题

> *多个 LLM Agent 能否像真实软件团队一样，通过分工协作、代码审查、迭代修复，自主交付一个完整可运行的软件项目？*

### 对标项目

| 项目 | 做法 | 本项目差异 |
|------|------|-----------|
| ChatDev | 固定流水线，剧本式 | Agent 自主认领任务，动态协作 |
| MetaGPT | SOP 驱动 | 有自主性 + 记忆 + 迭代修复 |
| AutoGen | 自由对话 | 有角色分工 + 工程规范 + 代码执行 |
| Devin | 单 Agent | 多 Agent 协作，角色互补 |

### 核心差异化
- **自主协作**：不是固定流水线，Agent 根据 Issue 看板自主认领任务
- **真实执行**：Agent 写的代码在沙箱中真实运行、测试、迭代修复
- **记忆驱动**：Agent 记住设计决策、历史 Bug，避免重复犯错
- **代码审查**：Agent 间互相 Review，不是各写各的
- **迭代闭环**：测试失败 → 自动修复 → 重新测试，直到通过
- **可交互**：用户可随时介入调整需求、审查产出

---

## 二、核心架构

```
┌──────────────────────────────────────────────────────────┐
│                    Company Engine                          │
│                                                           │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │  Project   │  │  Artifact  │  │  Code Sandbox     │    │
│  │  Board     │  │  Store     │  │  (Docker/沙箱)     │    │
│  │  Issue看板  │  │  制品管理   │  │  代码执行/测试     │    │
│  └────────────┘  └────────────┘  └──────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Message Channel                       │    │
│  │   (Agent 间通过 Issue 评论 / PR Review / 会议沟通)   │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌──────────┐     ┌──────────┐       ┌──────────┐
│   PM     │     │ Architect│       │ Backend  │
│  需求管理  │     │ 技术设计  │       │  后端开发 │
└──────────┘     └──────────┘       └──────────┘
    ▲                    ▲                    ▲
    │                    │                    │
┌──────────┐     ┌──────────┐       ┌──────────┐
│ Frontend │     │   QA     │       │ DevOps   │
│  前端开发 │     │  测试质量 │       │ 部署运维  │
└──────────┘     └──────────┘       └──────────┘

                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    Output Layer                           │
│   开发日志流 / 项目看板 / Git 历史 / 质量报告 / 最终产物    │
└──────────────────────────────────────────────────────────┘
```

---

## 三、角色设计

### 3.1 角色 + 职责

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **PM** | 需求分析、用户故事、验收标准、优先级排序 | 用户需求 | PRD 文档、Issue 列表 |
| **Architect** | 技术方案、架构设计、技术选型、任务拆解 | PRD | 技术设计文档、任务拆解 |
| **Backend Dev** | 后端代码、API 实现、数据库设计 | 技术设计 + 任务 | 代码 + 单元测试 |
| **Frontend Dev** | 前端代码、UI 实现、交互逻辑 | 技术设计 + 任务 | 代码 + 单元测试 |
| **QA** | 测试用例、集成测试、Bug 报告、质量评估 | 代码 + 需求 | 测试报告、Bug Issue |
| **DevOps** | 构建脚本、部署配置、CI/CD、环境管理 | 代码 + 配置 | Dockerfile、部署脚本 |

### 3.2 Agent 能力模型

```python
@dataclass
class Agent:
    # 身份
    id: str
    name: str
    role: Role                    # 角色枚举
    skills: List[str]             # 技能标签（如 python, react, docker）
    
    # 认知
    memory: AgentMemory           # 记忆系统
    current_task: Optional[Task]  # 当前认领的任务
    
    # 协作
    inbox: List[Message]          # 待处理消息（Issue 评论、PR Review）
    
    # 产出
    commits: List[str]            # Git 提交历史
    artifacts: List[Artifact]     # 产出制品
```

### 3.3 角色协作流程

```
用户需求
    │
    ▼
┌─ PM ──────────────────────────────────┐
│  1. 分析需求，生成 PRD                  │
│  2. 拆解为 User Story + 验收标准        │
│  3. 创建 Issue 到看板                   │
└───────────────────────────────────────┘
    │
    ▼
┌─ Architect ──────────────────────────┐
│  1. 阅读 PRD，设计技术方案              │
│  2. 技术选型（框架、数据库等）           │
│  3. 拆解为具体开发任务                   │
│  4. 更新 Issue 到看板                   │
└───────────────────────────────────────┘
    │
    ▼
┌─ Devs (Backend + Frontend) ──────────┐
│  1. 从看板认领任务                      │
│  2. 编写代码 + 单元测试                 │
│  3. 提交 PR                            │
│  4. 互相 Code Review                   │
│  5. 修复 Review 意见                    │
└───────────────────────────────────────┘
    │
    ▼
┌─ QA ─────────────────────────────────┐
│  1. 编写集成测试 / E2E 测试            │
│  2. 在沙箱中运行全部测试               │
│  3. 发现 Bug → 创建 Bug Issue          │
│  4. 回归验证                           │
└───────────────────────────────────────┘
    │
    ▼  (Bug → 回到 Devs 修复)
┌─ DevOps ─────────────────────────────┐
│  1. 编写 Dockerfile / docker-compose  │
│  2. 配置 CI/CD                        │
│  3. 构建并验证部署                     │
│  4. 产出可运行产物                     │
└───────────────────────────────────────┘
    │
    ▼
  交付物：可运行的软件 + 文档 + 测试
```

**关键：这不是固定流水线，而是事件驱动的自主协作**
- Agent 完成任务后主动查看看板认领下一个
- QA 发现 Bug 自动创建 Issue，Dev 自动认领修复
- PR Review 是双向的，Dev 间互相审查
- 用户可随时介入调整需求

---

## 四、核心模块设计

### 4.1 Project Board — 项目看板

```python
@dataclass
class Issue:
    id: str
    title: str
    description: str
    type: IssueType           # requirement / task / bug / improvement
    status: IssueStatus       # backlog / todo / in_progress / review / done
    priority: int             # 0-4
    assignee: Optional[str]   # Agent ID
    labels: List[str]         # backend / frontend / testing / devops
    comments: List[Comment]   # 讨论记录
    created_at: int
    updated_at: int

class KanbanBoard:
    issues: List[Issue]
    
    def create_issue(self, ...): ...
    def assign_issue(self, issue_id, agent_id): ...
    def move_issue(self, issue_id, status): ...
    def get_available_tasks(self, role: Role) -> List[Issue]: ...
    def add_comment(self, issue_id, comment): ...
```

- Agent 完成当前任务后调用 `get_available_tasks(role)` 认领新任务
- 认领后状态自动变为 `in_progress`
- 提交 PR 后变为 `review`，Reviewer 审查后变为 `done`

### 4.2 Code Sandbox — 代码执行沙箱

```python
class CodeSandbox:
    """隔离的代码执行环境"""
    
    def write_file(self, path: str, content: str): ...
    def read_file(self, path: str) -> str: ...
    def list_files(self, dir: str) -> List[str]: ...
    def run_tests(self) -> TestResult: ...
    def run_command(self, cmd: str) -> CommandResult: ...
    def install_deps(self, deps: List[str]): ...
    def snapshot(self) -> str: ...        # 保存当前状态
    def restore(self, snapshot_id: str): ...  # 恢复到某状态
```

- **隔离执行**：每个项目运行在独立沙箱（基于 Docker 或 subprocess + 临时目录）
- **真实运行**：Agent 写的代码在沙箱中真实编译、运行、测试
- **结果反馈**：测试结果（通过/失败 + 错误信息）返回给 Agent
- **快照机制**：支持回滚到之前的代码状态（修复失败时恢复）

### 4.3 Git 模拟 — 版本控制

```python
class GitRepo:
    """简化版 Git，管理代码提交和 PR"""
    
    def commit(self, agent_id: str, files: Dict[str, str], message: str): ...
    def create_branch(self, name: str): ...
    def create_pr(self, branch: str, title: str, description: str) -> PR: ...
    def review_pr(self, pr_id: str, reviewer_id: str, comments: List[ReviewComment]): ...
    def merge_pr(self, pr_id: str): ...
    def get_diff(self, pr_id: str) -> str: ...
    def log(self) -> List[Commit]: ...
```

- 每次代码变更都通过 PR 流程（非直接提交 main）
- PR 创建后自动分配 Reviewer（其他 Dev 角色）
- Reviewer 查看 diff，给出审查意见
- 合并后代码进入主分支

### 4.4 Artifact Store — 制品管理

```python
@dataclass
class Artifact:
    id: str
    type: ArtifactType        # prd / design / code / test_report / deploy_config
    title: str
    content: str              # 文本内容 / 代码内容
    file_path: Optional[str]  # 沙箱中的文件路径
    author: str               # Agent ID
    version: int
    dependencies: List[str]   # 依赖的其他制品 ID
    created_at: int

class ArtifactStore:
    def save(self, artifact: Artifact): ...
    def get(self, artifact_id: str) -> Artifact: ...
    def get_by_type(self, type: ArtifactType) -> List[Artifact]: ...
    def get_latest(self, type: ArtifactType) -> Optional[Artifact]: ...
```

制品流转链：
```
PRD → 技术设计文档 → 代码 → 测试报告 → 部署配置
```
- 每个制品有版本号，支持回溯
- Agent 可引用上游制品（如 Dev 引用设计文档）

### 4.5 Agent Memory — 记忆系统

```python
class AgentMemory:
    """Agent 的工作记忆 + 长期记忆"""
    
    # 工作记忆：当前任务的上下文
    working: List[str]           # 最近读取的文件、讨论、设计决策
    
    # 长期记忆：跨任务的知识
    long_term: List[MemoryItem]  # 设计决策、历史 Bug、Review 经验
    
    def remember(self, item: MemoryItem): ...
    def recall(self, query: str, top_k: int = 5) -> List[MemoryItem]: ...
    def forget(self, item_id: str): ...
```

记忆内容示例：
- "后端选了 FastAPI + SQLite，因为项目轻量"（架构决策）
- "上次 QA 报的空指针 Bug，以后要注意 None 检查"（经验教训）
- "前端用的是 React + Tailwind"（技术选型）

### 4.6 Message Channel — 协作通信

Agent 间通信方式（非自由对话，而是工程化协作）：

| 通信方式 | 场景 | 示例 |
|---------|------|------|
| Issue 评论 | 任务讨论 | Backend 在 Issue 上问 PM："这个 API 需要鉴权吗？" |
| PR Review | 代码审查 | Frontend Review Backend 的 PR："接口返回格式不一致" |
| 会议 | 跨角色讨论 | PM 召开需求评审会，Architect + Devs 参加 |
| 直接消息 | 快速沟通 | QA 通知 Dev："测试环境挂了，帮看一下" |

---

## 五、技术方案

### 5.1 技术栈

| 层 | 技术 | 理由 |
|----|------|------|
| 语言 | Python 3.12+ | LLM 生态成熟 |
| LLM | OpenAI API (GPT-4o) | 代码生成质量高 |
| 代码沙箱 | Docker / subprocess | 隔离执行 Agent 产出 |
| 向量存储 | ChromaDB | Agent 记忆检索 |
| 持久化 | SQLite | 项目/Issue/制品 |
| CLI | Rich + Typer | 终端 UI + 日志流 |
| Web | FastAPI + WebSocket | 实时看板 + 日志 |
| 测试 | pytest | 项目自身测试 |

### 5.2 项目结构

```
agent-software-company/
├── PLAN.md
├── README.md
├── pyproject.toml
├── config/
│   ├── company.yaml          # 公司配置（角色、流程）
│   ├── models.yaml           # LLM 模型配置
│   └── templates/            # Prompt 模板
│       ├── pm.yaml
│       ├── architect.yaml
│       ├── backend.yaml
│       ├── frontend.yaml
│       ├── qa.yaml
│       └── devops.yaml
│
├── src/
│   └── company/
│       ├── __init__.py
│       │
│       ├── engine/           # 公司引擎
│       │   ├── board.py      # 看板系统
│       │   ├── sandbox.py    # 代码沙箱
│       │   ├── git.py        # Git 模拟
│       │   ├── artifacts.py  # 制品管理
│       │   └── channel.py    # 通信系统
│       │
│       ├── agents/           # Agent 实现
│       │   ├── base.py       # Agent 基类
│       │   ├── memory.py     # 记忆系统
│       │   ├── pm.py         # PM Agent
│       │   ├── architect.py  # 架构师 Agent
│       │   ├── developer.py  # 开发者 Agent（前后端通用）
│       │   ├── qa.py         # QA Agent
│       │   └── devops.py     # DevOps Agent
│       │
│       ├── llm/              # LLM 接口
│       │   ├── client.py     # 统一 LLM 客户端
│       │   └── prompts.py    # Prompt 构建
│       │
│       ├── pipeline/         # 协作流程
│       │   ├── orchestrator.py  # 协调器（驱动 Agent 协作）
│       │   └── phases.py     # 阶段定义
│       │
│       ├── output/           # 输出层
│       │   ├── logger.py     # 开发日志
│       │   ├── dashboard.py  # 看板可视化
│       │   └── report.py     # 质量报告
│       │
│       └── cli.py            # CLI 入口
│
├── tests/
│   ├── test_board.py
│   ├── test_sandbox.py
│   ├── test_git.py
│   ├── test_agents.py
│   └── test_integration.py
│
├── examples/
│   ├── todo_app.yaml         # 示例需求：Todo 应用
│   ├── blog_api.yaml         # 示例需求：博客 API
│   └── chat_app.yaml         # 示例需求：聊天应用
│
└── output/                   # 运行产出
    ├── projects/             # 每次运行的项目产物
    │   └── {project_id}/
    │       ├── prd.md
    │       ├── design.md
    │       ├── src/           # 最终代码
    │       ├── tests/
    │       ├── Dockerfile
    │       └── report.md
    ├── logs/
    └── snapshots/
```

### 5.3 LLM 调用策略

| 角色 | 任务 | 模型 | 理由 |
|------|------|------|------|
| PM | 需求分析、PRD | GPT-4o | 需理解力 |
| Architect | 技术设计 | GPT-4o | 需推理深度 |
| Dev | 代码生成 | GPT-4o | 代码质量关键 |
| QA | 测试用例 | GPT-4o-mini | 可降级 |
| DevOps | 部署配置 | GPT-4o-mini | 模板化 |

- **并行调用**：多个 Dev 的独立任务可并行编码
- **缓存**：相同 prompt 缓存（如重复的项目配置生成）
- **重试**：代码执行失败时自动反馈给 Agent 重试（最多 3 次）

---

## 六、协作流程详细设计

### 6.1 完整开发流程

```
Phase 1: 需求分析 (PM)
  ├─ 读取用户需求
  ├─ 生成 PRD（功能列表、用户故事、验收标准）
  ├─ 创建 Issue 到看板
  └─ 输出：PRD 文档 + Issue 列表

Phase 2: 技术设计 (Architect)
  ├─ 阅读 PRD
  ├─ 技术选型（语言、框架、数据库）
  ├─ 设计架构（模块划分、接口定义、数据模型）
  ├─ 拆解为开发任务（每个任务有明确的输入/输出/验收标准）
  ├─ 创建开发 Issue 到看板
  └─ 输出：技术设计文档 + 任务 Issue

Phase 3: 开发 (Devs)
  ├─ 认领任务
  ├─ 阅读设计文档
  ├─ 编写代码 + 单元测试
  ├─ 在沙箱中运行测试验证
  ├─ 测试通过 → 提交 PR
  ├─ 等待 Review
  ├─ 修复 Review 意见
  └─ 合并到主分支

Phase 4: 集成测试 (QA)
  ├─ 阅读需求 + 设计
  ├─ 编写集成测试 / E2E 测试
  ├─ 在沙箱中运行全部测试
  ├─ Bug → 创建 Bug Issue
  ├─ 通知 Dev 修复
  └─ 回归测试

Phase 5: 部署 (DevOps)
  ├─ 编写 Dockerfile
  ├─ 编写 docker-compose（如需多服务）
  ├─ 配置启动脚本
  ├─ 验证构建 + 运行
  └─ 输出：可运行产物

Phase 6: 交付
  ├─ 整理最终代码
  ├─ 生成 README + 文档
  ├─ 生成质量报告（测试覆盖率、Issue 完成率）
  └─ 用户验收
```

### 6.2 迭代修复循环

```
QA 发现 Bug
    │
    ▼
创建 Bug Issue（含错误信息 + 复现步骤）
    │
    ▼
Dev 认领 Bug Issue
    │
    ▼
分析错误 → 修复代码 → 运行测试
    │
    ├─ 测试通过 → 提交 PR → Review → 合并
    │
    └─ 测试仍失败 → 继续修复（最多 3 轮）
         │
         └─ 3 轮失败 → 标记为 blocked，通知用户
```

### 6.3 Orchestrator — 协调器

```python
class Orchestrator:
    """驱动整个开发流程"""
    
    def run(self, requirement: str):
        # 1. PM 分析需求
        prd = self.pm.analyze_requirement(requirement)
        self.board.create_issues_from_prd(prd)
        
        # 2. Architect 设计
        design = self.architect.design(prd)
        self.board.create_tasks_from_design(design)
        
        # 3. Devs 并行开发
        while self.board.has_todo_tasks():
            tasks = self.board.get_available_tasks()
            # 并行分配给 Devs
            for task, dev in self.assign_tasks(tasks):
                pr = dev.work_on(task)
                # Review
                reviewer = self.get_reviewer(dev)
                review = reviewer.review_pr(pr)
                if review.approved:
                    self.git.merge_pr(pr)
                else:
                    dev.fix_review_comments(pr, review)
        
        # 4. QA 测试
        test_result = self.qa.run_integration_tests()
        while test_result.has_bugs():
            self.fix_bugs(test_result.bugs)
            test_result = self.qa.run_integration_tests()
        
        # 5. DevOps 部署
        self.devops.build_and_deploy()
        
        # 6. 交付
        return self.collect_deliverables()
```

---

## 七、开发路线图

### Phase 1: 引擎核心 (1 周)
- [ ] 看板系统（Issue CRUD + 看板视图）
- [ ] 代码沙箱（文件读写 + 命令执行 + 测试运行）
- [ ] Git 模拟（commit + PR + Review + merge）
- [ ] 制品管理
- [ ] LLM 客户端封装
- **里程碑：** 引擎核心可独立运行，手动创建 Issue 和执行代码

### Phase 2: 单角色 Agent (1 周)
- [ ] Agent 基类（LLM 调用 + 记忆 + 任务执行）
- [ ] PM Agent（需求 → PRD → Issue）
- [ ] Architect Agent（PRD → 设计 → 任务）
- [ ] CLI 实时日志输出
- **里程碑：** PM + Architect 协作，从需求生成设计文档和任务列表

### Phase 3: 开发闭环 (1-2 周)
- [ ] Developer Agent（认领任务 → 编码 → 测试 → PR）
- [ ] Code Review 流程
- [ ] 代码沙箱真实执行
- [ ] 迭代修复循环
- **里程碑：** Dev 能写代码、跑测试、提交 PR、修复 Review 意见

### Phase 4: 完整团队 (1 周)
- [ ] QA Agent（集成测试 + Bug 报告）
- [ ] DevOps Agent（Dockerfile + 部署）
- [ ] Orchestrator 完整流程串联
- **里程碑：** 完整团队协作，从需求到可运行产物

### Phase 5: 优化与体验 (1 周)
- [ ] Web Dashboard（看板 + 日志流 + Git 历史）
- [ ] 用户交互（调整需求、审查产出）
- [ ] 质量报告生成
- [ ] 示例项目库
- **里程碑：** 可交互的 Agent 软件公司 Demo

---

## 八、成功标准

### 功能验证
- [ ] 输入一个需求（如"做一个 Todo 应用"），输出可运行的代码
- [ ] 代码能在沙箱中通过测试
- [ ] 有完整的 PRD + 设计文档 + 代码 + 测试 + 部署配置
- [ ] Bug 能被自动发现和修复

### 协作验证
- [ ] Agent 间通过 Issue/PR 协作，非人工干预
- [ ] Code Review 有实质内容（非 rubber stamp）
- [ ] Bug 修复闭环：发现 → 修复 → 验证

### 工程质量
- [ ] 最终产物可 `docker build` + `docker run` 成功运行
- [ ] 测试覆盖率 > 60%
- [ ] 单元测试 + 集成测试通过

### 示例项目
- [ ] Todo App（CRUD + 简单 UI）
- [ ] 博客 API（REST + 数据库）
- [ ] 实时聊天应用（WebSocket）

---

## 九、设计决策（已确定）

| # | 问题 | 决策 | 说明 |
|---|------|------|------|
| 1 | 代码沙箱 | subprocess + 临时目录 | 轻量起步，后续可选 Docker |
| 2 | 目标软件架构 | 前后端分离 | Agent 生成的软件采用前后端分离架构 |
| 3 | 目标软件语言 | Python (后端) + TypeScript (前端) | 后端 FastAPI，前端 React/Vite |
| 4 | LLM API 配置 | 用户自行配置 | 从 .env / config 读取，不硬编码 |
| 5 | 示例项目 | 暂不包含 | 用户自行提供需求 |
| 6 | Agent 通信 | Issue 评论 + PR Review | 工程化协作，非自由对话 |
