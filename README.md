# APScheduler任务调度管理系统

## 1. 项目概述

APScheduler任务调度管理系统是一个基于FastAPI和Advanced Python Scheduler (APScheduler)构建的高效任务调度与管理平台。该系统采用领域驱动设计(DDD)架构，通过依赖注入(DI)实现模块间的低耦合，具备任务创建、调度、执行、结果处理与外部系统集成等完整功能。

### 核心特性

- **灵活的任务调度**：支持即时任务(IMMEDIATE)和基于cron表达式的定时任务(SCHEDULED)
- **强大的任务管理**：包含优先级队列、依赖管理、超时处理、重试机制
- **外部系统集成**：支持与Jira、Confluence等系统对接，实现数据处理自动化
- **结果汇总与报告**：任务执行结果可自动汇总并更新至Confluence页面
- **RESTful API接口**：提供完整的任务管理接口，支持查询、过滤、监控
- **高可扩展性**：模块化设计，便于扩展新的任务类型和外部系统集成

## 2. 系统架构

系统基于清晰的分层架构设计：

### 架构分层

1. **表示层**（FastAPI应用）
   - 提供RESTful API接口，处理用户交互

2. **应用层**（Application）
   - 编排核心业务流程
   - 协调领域服务与基础设施
   - 任务调度服务

3. **领域层**（Domain）
   - 核心业务规则与实体模型
   - 领域服务（Jira处理、Confluence处理等）

4. **基础设施层**（Infrastructure）
   - 外部系统集成（Jira API、Confluence API）
   - 配置管理、日志服务
   - 持久化实现

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        表示层 (Presentation)                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   任务管理API     │    │   状态查询API     │    │  结果查看API  │ │
│  └────────┬────────┘    └────────┬────────┘    └───────┬──────┘ │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
┌───────────┼─────────────────────┼─────────────────────┼─────────┐
│                         应用层 (Application)                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  调度服务        │    │  执行服务        │    │  报告服务     │ │
│  │SchedulerService │    │ TaskExecutor    │    │ReportService │ │
│  └────────┬────────┘    └────────┬────────┘    └───────┬──────┘ │
│           │                      │                     │        │
│  ┌────────┴──────────────────────┴─────────────────────┴──────┐ │
│  │                      依赖注入容器                          │ │
│  │                    DIContainer                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                         领域层 (Domain)                          │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   任务实体       │    │   领域服务       │    │  领域事件    │ │
│  │   Task          │    │  JiraService    │    │TaskCreated   │ │
│  │   TaskResult    │    │ConfluenceService│    │TaskCompleted │ │
│  └────────┬────────┘    └────────┬────────┘    └───────┬──────┘ │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
┌───────────┼─────────────────────┼─────────────────────┼─────────┐
│                      基础设施层 (Infrastructure)                  │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   任务仓储       │    │   外部系统集成   │    │  配置管理    │ │
│  │ TaskRepository  │    │   JiraClient    │    │ConfigManager │ │
│  │ResultRepository │    │ConfluenceClient │    │ LogService   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 业务架构图

```
┌───────────────────────────────────────────────────────────────────┐
│                           外部触发                                 │
│                                                                   │
│    ┌─────────┐         ┌─────────┐         ┌─────────────┐        │
│    │ API请求  │         │定时触发  │         │手动创建任务 │        │
│    └────┬────┘         └────┬────┘         └──────┬──────┘        │
└─────────┼───────────────────┼───────────────────┬───────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌───────────────────────────────────────────────────────────────────┐
│                           任务生命周期                             │
│                                                                   │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│    │ 创建任务 │───▶│任务排队 │───▶│任务执行 │───▶│结果处理 │       │
│    └─────────┘    └────┬────┘    └────┬────┘    └────┬────┘       │
│                       │               │               │           │
│                       │               │               │           │
│                       ▼               ▼               ▼           │
│                  ┌─────────┐     ┌─────────┐     ┌─────────┐      │
│                  │优先级排序│     │任务超时 │     │结果汇总 │      │
│                  └─────────┘     └────┬────┘     └────┬────┘      │
│                                      │               │           │
│                                      ▼               ▼           │
│                                 ┌─────────┐     ┌─────────┐      │
│                                 │重试机制 │     │报告生成 │      │
│                                 └─────────┘     └────┬────┘      │
└───────────────────────────────────────────────────────┼────────────┘
                                                        │
                                                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                           外部系统集成                             │
│                                                                   │
│    ┌─────────────┐         ┌─────────────┐      ┌─────────────┐   │
│    │Jira数据处理 │         │Confluence更新│      │其他系统集成 │   │
│    └─────────────┘         └─────────────┘      └─────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### 核心组件

- **任务调度器**（SchedulerService）：系统核心，协调各管理器完成任务调度
- **任务执行器**（TaskExecutor）：执行具体任务，调用相应领域服务
- **任务仓库**（TaskRepository）：管理任务的存储和检索
- **结果报告服务**（ResultReportingService）：处理任务结果并生成报告

## 3. 功能详解

### 3.1 任务调度与执行

#### 任务类型

- **定时任务（SCHEDULED）**：通过cron表达式配置执行时间
- **即时任务（IMMEDIATE）**：创建后立即加入执行队列

#### 任务状态流转

```
PENDING -> QUEUED -> RUNNING -> DONE/FAILED
             ^                    |
             |                    v
             +---- RETRY <---- TIMEOUT
```

#### 任务优先级

- HIGH：高优先级任务，优先执行
- MEDIUM：中等优先级（默认）
- LOW：低优先级任务

#### 任务依赖管理

- 支持任务间依赖关系配置
- 依赖任务完成后，才会执行后续任务

#### 任务超时与重试

- 支持配置任务执行超时时间
- 支持自定义重试策略（最大重试次数、重试延迟、退避因子）

### 3.2 外部系统集成

#### Jira集成

- 支持根据项目或根问题提取Issue信息
- 支持Issue状态更新、字段修改
- 支持生成Excel格式报表导出

#### Confluence集成

- 支持任务结果汇总至Confluence页面
- 支持表格形式更新与展示
- 支持自动创建/更新内容页面

#### 未来可扩展集成

- Mattermost通知（已有基础实现）
- 邮件通知
- 其他第三方系统API

### 3.3 API接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/tasks` | GET | 获取所有任务列表 |
| `/tasks/status/{status}` | GET | 根据状态过滤任务 |
| `/task_history` | GET | 获取已执行完成的任务历史 |

## 4. 技术规范

### 4.1 开发环境

- **Python版本**：3.8+（推荐3.9或3.10）
- **主要依赖**：
  - FastAPI 0.115.8+：Web框架
  - Uvicorn 0.34.0+：ASGI服务器
  - APScheduler 3.11.0+：任务调度库
  - atlassian-python-api 3.41.19+：Atlassian API客户端
  - SQLAlchemy 2.0.37+：ORM框架
  - Pandas 2.2.3+：数据处理
  - PyYAML 6.0.2+：配置文件处理

### 4.2 代码组织结构

```
/
├── app.py                  # 应用入口
├── config.yaml             # 全局配置
├── requirements.txt        # 依赖清单
├── domain/                 # 领域层
│   ├── entities/           # 领域实体
│   │   ├── models.py       # 数据模型定义
│   │   └── repositories.py # 仓库接口
│   ├── services/           # 领域服务
│   └── exceptions.py       # 领域异常
├── application/            # 应用层
│   ├── di_container.py     # 依赖注入容器
│   ├── schedulers/         # 调度器组件
│   │   ├── scheduler_service.py  # 调度服务
│   │   └── managers/       # 各类任务管理器
│   ├── services/           # 应用服务
│   └── use_cases/          # 用例实现
├── infrastructure/         # 基础设施层
│   ├── config/             # 配置管理
│   ├── persistence/        # 持久化实现
│   └── integration/        # 外部系统集成
├── interface_adapters/     # 接口适配层
│   └── api/                # API模块
├── logs/                   # 日志目录
├── task_storage/           # 任务存储目录
└── examples/               # 示例代码
```

### 4.3 数据模型

#### Task模型

```python
class Task(BaseModel):
    id: UUID                            # 任务唯一标识
    name: str                           # 任务名称
    task_type: TaskType                 # 任务类型(SCHEDULED/IMMEDIATE)
    cron_expr: Optional[str]            # cron表达式(定时任务)
    status: TaskStatus                  # 当前状态
    created_at: datetime                # 创建时间
    updated_at: datetime                # 更新时间
    priority: TaskPriority              # 优先级(HIGH/MEDIUM/LOW)
    metadata: Dict[str, Any]            # 元数据
    tags: List[str]                     # 标签列表
    owner: Optional[str]                # 创建者
    dependencies: List[UUID]            # 依赖任务ID列表
    timeout_seconds: Optional[int]      # 超时时间(秒)
    retry_policy: Optional[RetryPolicy] # 重试策略
    parameters: Dict[str, Any]          # 任务参数
```

### 4.4 配置项说明

config.yaml文件包含以下配置项：

#### Confluence配置

```yaml
confluence:
  url: "https://confluence.example.com"
  username: "confluence_user"
  password: "confluence_password"
  main_page_id: "123456"
  task_result_page_id: "789012"
```

#### Jira配置

```yaml
jira:
  url: "https://jira.example.com"
  username: "jira_user"
  password: "jira_password"
```

#### 调度器配置

```yaml
scheduler:
  poll_interval: 30        # 轮询间隔(秒)
  concurrency: 5           # 最大并发任务数
  coalesce: false          # 是否合并延迟任务
  max_instances: 5         # 最大实例数
```

#### 日志配置

```yaml
log:
  level: INFO              # 日志级别
  filename: logs/app.log   # 日志文件路径
  max_bytes: 10485760      # 单个日志文件大小上限(10MB)
  backup_count: 5          # 保留日志文件数量
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### 存储配置

```yaml
storage:
  path: "task_storage"     # 任务存储路径
```

#### 报告配置

```yaml
reporting:
  interval: 30             # 报告生成间隔(秒)
  report_types:
    - "confluence"
    - "mattermost"
  confluence:
    page_id: "789012"
    template: "task_results_template"
```

## 5. 安装与部署

### 5.1 环境准备

1. 确保已安装Python 3.8+
2. 克隆代码仓库
   ```bash
   git clone https://github.com/yourusername/apscheduler-demo.git
   cd apscheduler-demo
   ```

3. 创建并激活虚拟环境
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

4. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

### 5.2 配置修改

1. 复制并修改配置文件
   ```bash
   cp config.yaml.example config.yaml
   # 编辑config.yaml，填入实际环境的配置信息
   ```

2. 创建必要的目录
   ```bash
   mkdir -p logs task_storage jira_reports
   ```

### 5.3 运行应用

#### 开发环境

```bash
python app.py
```

#### 生产环境

使用Gunicorn部署(Linux/macOS)：

```bash
gunicorn -w 1 -k uvicorn.workers.UvicornWorker app:create_app()
```

Windows可使用waitress：

```bash
waitress-serve --port=8000 app:create_app()
```

### 5.4 访问API

应用启动后，可通过以下URL访问：

- API文档：http://localhost:8000/docs
- 任务列表：http://localhost:8000/tasks
- 任务历史：http://localhost:8000/task_history

## 6. 使用指南

### 6.1 创建任务示例

在app.py中已包含两个示例任务：

```python
# JIRA根问题提取任务
root_ticket_task = {
    "name": "JIRA Extraction - Root Ticket",
    "task_type": TaskType.IMMEDIATE,
    "tags": ["JIRA_TASK_EXP"],
    "parameters": {
        "jira_envs": ["env1.jira.com", "env2.jira.com"],
        "key_type": "root_ticket",
        "key_value": "PROJ-123",
        "user": "johndoe"
    }
}

# JIRA项目提取任务(每日执行)
project_task = {
    "name": "JIRA Extraction - Project",
    "task_type": TaskType.IMMEDIATE,
    "cron_expr": "0 0 * * *",  # 每天午夜执行
    "tags": ["JIRA_TASK_EXP"],
    "parameters": {
        "jira_envs": ["env1.jira.com"],
        "key_type": "project",
        "key_value": "PROJ",
        "user": "johndoe"
    }
}
```

### 6.2 任务执行流程

1. 任务创建并存入TaskRepository
2. SchedulerService周期性轮询待执行任务
3. 根据任务类型(即时/定时)加入执行队列或创建定时作业
4. TaskExecutor执行任务，调用相应的领域服务
5. 执行结果存入TaskResultRepository
6. ResultReportingService定期汇总结果并更新到Confluence

### 6.3 任务参数说明

任务参数(parameters)根据任务标签和类型而异：

#### JIRA_TASK_EXP标签任务

```json
{
  "jira_envs": ["jira环境URL列表"],
  "key_type": "root_ticket或project",
  "key_value": "问题键值或项目键值",
  "user": "执行用户"
}
```

## 7. 如何开发和使用本框架

### 7.1 开发新的任务类型

1. **定义任务标签常量**
   
   在`domain/entities/models.py`中添加新的任务标签常量：
   ```python
   # 示例：添加一个处理数据同步的任务标签
   class TaskTags:
       JIRA_TASK_EXP = "JIRA_TASK_EXP"
       DATA_SYNC_TASK = "DATA_SYNC_TASK"  # 新添加的任务标签
   ```

2. **创建领域服务**
   
   在`domain/services/`目录下创建新的领域服务类：
   ```python
   # 示例：data_sync_service.py
   from domain.entities.models import TaskResult
   
   class DataSyncService:
       def __init__(self, config):
           self.config = config
       
       def sync_data(self, parameters):
           # 实现数据同步逻辑
           # ...
           return TaskResult(
               success=True,
               result_data={"synced_records": 100}
           )
   ```

3. **注册到依赖注入容器**
   
   在`application/di_container.py`中添加服务注册：
   ```python
   def get_data_sync_service(self):
       if not hasattr(self, '_data_sync_service'):
           self._data_sync_service = DataSyncService(self.config)
       return self._data_sync_service
   ```

4. **添加任务执行器处理逻辑**
   
   在`application/use_cases/executor.py`中的`TaskExecutor`类中添加处理方法：
   ```python
   def _execute_data_sync_task(self, task):
       data_sync_service = self.di_container.get_data_sync_service()
       result = data_sync_service.sync_data(task.parameters)
       return result
   ```

5. **修改任务执行流程**
   
   在`TaskExecutor.execute`方法中添加标签处理分支：
   ```python
   def execute(self, task):
       # ...现有代码...
       if TaskTags.JIRA_TASK_EXP in task.tags:
           result = self._execute_jira_task(task)
       elif TaskTags.DATA_SYNC_TASK in task.tags:  # 添加新的处理分支
           result = self._execute_data_sync_task(task)
       else:
           raise UnsupportedTaskTypeError(f"不支持的任务标签: {task.tags}")
       # ...现有代码...
   ```

### 7.2 使用框架创建和执行任务

1. **创建任务配置**

   ```python
   # 示例：创建数据同步任务
   data_sync_task = {
       "name": "每日数据同步任务",
       "task_type": TaskType.SCHEDULED,
       "cron_expr": "0 1 * * *",  # 每天凌晨1点执行
       "tags": ["DATA_SYNC_TASK"],
       "parameters": {
           "source_db": "production",
           "target_db": "analytics",
           "tables": ["users", "orders", "products"]
       }
   }
   
   # 使用任务仓库添加任务
   task_repo.add_from_dict(data_sync_task)
   ```

2. **通过API创建任务**

   可以扩展API接口，支持通过HTTP请求创建任务：
   ```python
   @app.post("/tasks", response_model=TaskResponse)
   def create_task(task_data: TaskCreate):
       task = task_repo.add_from_dict(task_data.dict())
       return TaskResponse(
           message="任务创建成功",
           task_id=str(task.id)
       )
   ```

3. **查看任务执行状态**

   ```bash
   # 查看所有任务
   curl http://localhost:8000/tasks
   
   # 查看特定状态任务
   curl http://localhost:8000/tasks/status/RUNNING
   
   # 查看任务执行历史
   curl http://localhost:8000/task_history
   ```

### 7.3 扩展框架功能

1. **添加新的外部系统集成**

   1. 在`infrastructure/integration/`下创建新的客户端类
   2. 在`domain/services/`下创建对应的领域服务
   3. 在依赖注入容器中注册新服务

2. **扩展结果报告方式**

   1. 在`application/services/result_reporting_service.py`中添加新的报告方法
   2. 在配置文件中添加对应的报告渠道配置

3. **添加自定义任务状态和生命周期钩子**

   1. 在`domain/entities/models.py`中扩展TaskStatus枚举
   2. 在任务执行流程中添加状态转换和钩子调用

### 7.4 最佳实践

1. **任务设计原则**
   
   - 保持任务功能单一，遵循单一职责原则
   - 将复杂业务流程拆分为多个小任务，通过依赖关系串联
   - 合理设置任务优先级和超时策略

2. **错误处理**
   
   - 为任务添加适当的重试策略，特别是涉及网络请求的任务
   - 使用领域异常表达业务规则违反，避免使用通用异常
   - 在日志中记录足够的上下文信息，便于问题排查

3. **性能优化**
   
   - 合理设置并发任务数量，避免资源竞争
   - 对于资源密集型任务，考虑使用异步执行
   - 定期清理历史任务数据，避免存储爆炸

4. **安全性考虑**
   
   - 敏感配置（如密码、API密钥）应使用环境变量或配置文件替换
   - 添加API访问认证机制，避免未授权使用
   - 对任务参数进行校验，防止注入攻击

## 8. 常见问题与解决方案

### 8.1 任务执行超时

- 检查任务timeout_seconds配置是否合理
- 确认外部系统(如Jira)响应是否正常
- 检查日志中的具体错误信息

### 8.2 定时任务未执行

- 验证cron表达式是否正确
- 检查系统时区设置
- 查看scheduler启动日志是否正常

### 8.3 结果未更新到Confluence

- 检查Confluence配置(URL、用户名、密码)
- 验证page_id是否正确
- 检查用户权限是否足够

## 9. 开发规范

### 9.1 代码风格

- 遵循PEP 8规范
- 使用类型注解
- 关键函数添加文档注释

### 9.2 异常处理

- 所有异常继承自BaseAppException
- 领域层异常应当有明确的业务含义
- 避免在领域层捕获基础设施异常

### 9.3 日志规范

- ERROR级别：影响系统运行的错误
- WARNING级别：需要注意但不影响主流程的问题
- INFO级别：重要操作节点信息
- DEBUG级别：详细调试信息

## 10. 未来规划

### 10.1 功能增强

- 支持更多外部系统集成
- 添加Web管理界面
- 实现分布式调度

### 10.2 性能优化

- 使用Redis存储任务状态
- 实现任务执行结果的异步处理
- 优化大量任务场景下的性能

### 10.3 安全增强

- API认证与授权
- 敏感信息加密存储
- 完善的审计日志

## 11. 贡献指南

1. Fork项目仓库
2. 创建特性分支
3. 提交变更
4. 提交Pull Request

## 12. 许可证

本项目采用MIT许可证。

---

*文档更新日期: 2024-03-16*