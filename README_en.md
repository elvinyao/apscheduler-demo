我很乐意帮您创建技术架构图和业务架构图，以可视化您提供的系统文档内容。

```mermaid
graph TD
    subgraph "FastAPI应用"
        APP[app.py] --> DI[core/di_container.py]
        APP --> CONFIG[scheduler/config.py]
        APP --> ROUTES[API路由]
    end

    subgraph "核心层 (core)"
        DI --> ERROR[error_handler.py]
        DI --> EXCEPTIONS[exceptions.py]
        DI --> REPOS_BASE[repositories.py]
    end

    subgraph "调度器层 (scheduler)"
        CONFIG --> SCHEDULER[scheduler_service.py]
        SCHEDULER --> EXECUTOR[executor.py]
        SCHEDULER --> MODELS[models.py]
        SCHEDULER --> FETCH[fetch_service.py]
        SCHEDULER --> PERSISTENCE[persistence.py]
        
        subgraph "存储仓库"
            TASK_REPO[task_repository.py]
            TASK_RESULT_REPO[task_result_repository.py]
            CONFL_REPO[confluence_repository.py]
        end
        
        SCHEDULER --> TASK_REPO
        EXECUTOR --> TASK_RESULT_REPO
        SCHEDULER --> CONFL_REPO
    end

    subgraph "领域层 (domain)"
        JIRA_PROC[jira_data_processor.py]
        CONFL_PROC[confluence_data_processor.py]
        MM_PROC[mattermost_data_processor.py]
        REPORTER[result_reporter.py]
        
        EXECUTOR --> JIRA_PROC
        EXECUTOR --> CONFL_PROC
        EXECUTOR --> MM_PROC
        EXECUTOR --> REPORTER
        REPORTER --> MM_PROC
    end

    subgraph "集成层 (integration)"
        JIRA_SVC[jira_service.py]
        CONFL_SVC[confluence_service.py]
        
        JIRA_PROC --> JIRA_SVC
        CONFL_PROC --> CONFL_SVC
        CONFL_REPO --> CONFL_SVC
    end

    subgraph "外部系统"
        JIRA[Jira服务器]
        CONFLUENCE[Confluence服务器]
        MATTERMOST[Mattermost服务器]
        
        JIRA_SVC --> JIRA
        CONFL_SVC --> CONFLUENCE
        MM_PROC -.-> MATTERMOST
    end
    
    subgraph "持久化"
        JSON[tasks_snapshot.json]
        PERSISTENCE --> JSON
    end

    style APP fill:#FF9900,stroke:#333,stroke-width:2px
    style SCHEDULER fill:#3498DB,stroke:#333,stroke-width:2px
    style EXECUTOR fill:#3498DB,stroke:#333,stroke-width:2px
    style JIRA fill:#E74C3C,stroke:#333,stroke-width:2px
    style CONFLUENCE fill:#E74C3C,stroke:#333,stroke-width:2px
    style MATTERMOST fill:#E74C3C,stroke:#333,stroke-width:2px

```

```mermaid
flowchart TD
    subgraph "用户交互"
        API[FastAPI接口] --> TASKS_API[任务管理API]
        TASKS_API --> VIEW_TASKS[查看任务列表]
        TASKS_API --> VIEW_STATUS[按状态查看任务]
        TASKS_API --> VIEW_HISTORY[查看历史任务]
    end

    subgraph "任务管理与调度"
        SCHEDULER[调度服务SchedulerService]
        SCHEDULER --> QUEUE[优先级任务队列]
        SCHEDULER --> CRON[定时任务]
        SCHEDULER --> RETRY[任务重试机制]
        SCHEDULER --> DEPENDENCY[任务依赖管理]
        
        QUEUE --> PRIORITY_H[高优先级]
        QUEUE --> PRIORITY_M[中优先级]
        QUEUE --> PRIORITY_L[低优先级]
        
        CRON --> POLL_DB[轮询数据库任务]
        CRON --> UPDATE_CONFL[更新Confluence页面]
        CRON --> READ_DATA[定时读取数据]
    end

    subgraph "任务执行"
        EXECUTOR[TaskExecutor]
        EXECUTOR --> THREADS[线程池]
        EXECUTOR --> TIMEOUT[超时管理]
        EXECUTOR --> STATUS_UPDATE[状态更新]
    end

    subgraph "业务处理"
        JIRA_PROC[Jira数据处理]
        CONFL_PROC[Confluence数据处理]
        MM_PROC[Mattermost消息处理]
        
        JIRA_PROC --> GET_ISSUES[获取Issue数据]
        JIRA_PROC --> GEN_EXCEL[生成Excel报表]
        
        CONFL_PROC --> READ_TABLE[读取表格数据]
        CONFL_PROC --> UPDATE_TABLE[更新表格数据]
    end

    subgraph "结果处理"
        RESULT_REPO[任务结果仓库]
        REPORTER[结果报告服务]
        
        RESULT_REPO --> STORE_RESULT[存储执行结果]
        REPORTER --> SEND_MM[发送Mattermost通知]
        REPORTER --> UPDATE_CONFL_RESULTS[更新Confluence结果]
    end

    %% 主要业务流程连接
    API --> SCHEDULER
    SCHEDULER --> EXECUTOR
    EXECUTOR --> JIRA_PROC
    EXECUTOR --> CONFL_PROC
    EXECUTOR --> MM_PROC
    EXECUTOR --> RESULT_REPO
    RESULT_REPO --> REPORTER
    
    %% 特定的业务场景流程
    JIRA_TASK[JIRA_TASK_EXP任务] --> EXECUTOR
    EXECUTOR --> JIRA_PROC
    JIRA_PROC --> GEN_EXCEL
    GEN_EXCEL --> RESULT_REPO
    RESULT_REPO --> REPORTER
    REPORTER --> SEND_MM
    UPDATE_CONFL --> RESULT_REPO
    
    style SCHEDULER fill:#3498DB,stroke:#333,stroke-width:2px
    style EXECUTOR fill:#2ECC71,stroke:#333,stroke-width:2px
    style JIRA_PROC fill:#9B59B6,stroke:#333,stroke-width:2px
    style CONFL_PROC fill:#9B59B6,stroke:#333,stroke-width:2px
    style MM_PROC fill:#9B59B6,stroke:#333,stroke-width:2px
    style REPORTER fill:#F1C40F,stroke:#333,stroke-width:2px

```

## 图表说明

### 系统技术架构图

技术架构图展示了系统的各个技术组件及其关系：

1. **FastAPI应用**：作为整个系统的入口点，包含配置加载、依赖注入和API路由
2. **核心层**：提供基础设施，包括依赖注入容器、错误处理和异常定义
3. **调度器层**：系统的核心，负责任务的调度、执行和管理
4. **领域层**：包含业务逻辑处理，处理Jira、Confluence和Mattermost数据
5. **集成层**：负责与外部系统交互，封装API调用细节
6. **外部系统**：系统需要与之交互的外部服务
7. **持久化**：通过JSON文件实现任务状态的持久化存储

### 系统业务架构图

业务架构图描述了系统的主要业务流程和功能模块：

1. **用户交互**：通过FastAPI提供的API接口查看任务信息
2. **任务管理与调度**：
   - 优先级队列管理（高、中、低）
   - 定时任务（轮询数据库、更新Confluence、读取数据）
   - 任务重试机制
   - 任务依赖管理
3. **任务执行**：通过线程池并发执行任务，管理任务状态和超时
4. **业务处理**：
   - Jira数据处理（获取Issue数据、生成Excel报表）
   - Confluence数据处理（读取和更新表格）
   - Mattermost消息处理
5. **结果处理**：存储执行结果、发送通知、更新到Confluence

这两张图直观地展示了系统的整体架构和业务流程，可以帮助团队更好地理解系统设计和实现。需要对任何部分进行调整或添加更多细节吗？