────────────────────────────────────────────────────────────────
1. 概览
────────────────────────────────────────────────────────────────

本项目是一个可执行的任务调度与集成处理系统，使用了 FastAPI 作为 Web 服务框架，并配合 APScheduler 实现定时任务调度；通过集成 Atlassian Confluence、Jira 的服务类（integration 层）与业务逻辑处理类（domain 层）来完成对外部系统的数据读取、写回、以及结果汇总和上报等流程。

代码结构基于以下主要分层与职责：
• core 层：提供全局错误处理、异常定义、依赖注入容器 (DIContainer) 等基础核心功能。  
• domain 层：实现业务逻辑，包括处理 Confluence 数据、Jira 数据，以及 Mattermost 消息发送和结果上报等。  
• integration 层：封装对外部系统 (Confluence、Jira 等) 的具体 API 调用逻辑，聚焦网络交互/认证等细节。  
• scheduler 层：包含任务调度核心逻辑、Task 及其存储仓库的实现、调度服务 (SchedulerService)、执行器 (executor)、数据持久化等。  
• examples 目录：使用示例，分别演示对 Confluence、Jira 的调用。  
• app.py：FastAPI 应用的入口点，包括启动调度器、定义路由、大致的服务周期管理 (startup/shutdown) 等。  
• config.yaml：全局配置文件 (如日志、Confluence/Jira 认证信息、调度器设置等)。  
• requirements.txt：Python 环境依赖清单。  

总体而言，该项目可执行以下核心场景：  
• 通过配置好的方式周期性或者即时地调度任务。  
• 读取、处理、更新 Confluence 上指定页面的表格数据（领域逻辑、Integration 层封装）。  
• 读取、处理、更新 Jira 上指定的 Issue 或 Project 相关信息，生成 Excel 报表。  
• 执行完任务后将结果发送到 Mattermost (模拟逻辑或实际调用)。  
• 将任务执行结果汇总更新到 Confluence (如生成新的表格条目)。  

────────────────────────────────────────────────────────────────
2. 功能模块与交互流程
────────────────────────────────────────────────────────────────

2.1 核心功能点概述
------------------------------------------------------------
1) 任务管理与调度 (SchedulerService + APScheduler)  
   - 提供任务的创建、查询、执行、定时触发等功能。  
   - 具备基于优先级 (HIGH/MEDIUM/LOW) 的任务队列执行机制。  
   - 支持任务依赖关系 (Task A 完成后才触发 Task B)。  
   - 具备任务超时、重试 (RetryPolicy) 等机制。  

2) 任务执行器 (TaskExecutor)  
   - 多线程 (ThreadPoolExecutor) 并发执行具体的任务逻辑。  
   - 可调用 domain 层的处理器 (JiraDataProcessor、ConfluenceDataProcessor 等)。  
   - 标记任务状态 (RUNNING / DONE / FAILED / RETRY / TIMEOUT)。  
   - 整合执行结果至 TaskResultRepository，触发后续结果上报 (ResultReporter)。  

3) Jira 相关功能 (JiraService + JiraDataProcessor)  
   - 封装了通过 atlassian-python-api 与 Jira 交互，并提供对项目权限、Issue 搜索、更新、删除的示例方法。  
   - domain 层中 JIRA_TASK_EXP 任务专门实现：可根据 root_ticket 或 project key 获取多级 Issue 并生成 Excel 报表。  

4) Confluence 相关功能 (ConfluenceService + ConfluenceDataProcessor)  
   - 封装了获取并解析 Confluence 页面、更新表格数据的逻辑 (通过 BeautifulSoup 处理 HTML)。  
   - domain 层中 ConfluenceDataProcessor 用于在真实调用前做业务判断，如是否有必要更新、以及更新前的检查或格式化操作。  

5) Mattermost 相关功能 (MattermostDataProcessor)  
   - 目前仅模拟了向 Mattermost 发送通知或自定义消息的操作。  
   - 用户可在 ResultReporter 中注入此处理器，实现任务执行完成后在 Mattermost 中发送结果汇报。  

6) 任务结果汇聚与上报 (result_reporter + confluence_repository)  
   - 任务执行后写入 TaskResultRepository。  
   - 可调用 ResultReporter 将结果发送到 Mattermost。  
   - scheduler_service 中有周期性作业 (update_confl_page) 将所有已收集的结果更新到 Confluence；更新完成后清空结果储存。  

7) 数据持久化 (scheduler/persistence.py)  
   - 采用简单的 JSON 文件快照 (tasks_snapshot.json)，在服务器重启后尽量恢复上次的未完成任务状态、或归档已完成的历史任务。  

2.2 系统主要交互流程 (示例)
------------------------------------------------------------
1) 启动流程：  
   - 运行 app.py，自动加载 config.yaml 做配置。  
   - 创建并启动 FastAPI 服务与 APScheduler 调度器 (scheduler_service.start())。  
   - 从存储快照中恢复上次任务状态，如果有 RUNNING 状态则重置为 PENDING。  

2) 新增任务：  
   - 在系统启动时或运行中，会自动添加一些示例任务 (JIRA_TASK_EXP)。也可以自行通过 FastAPI 接口或其他方式添加 (task_repo.add_from_dict)。  
   - 如果是 IMMEDIATE 类型，则会进入优先级队列；如果是 SCHEDULED 类型且有 cron 表达式，则由 APScheduler 自动添加定时 Job。  
   - 项目中 fetch_service.py 提供从外部接口抓取任务的可能性，并导入到本地仓库。  

3) 任务执行：  
   - 对于排队中的任务，scheduler_service.process_task_queue() 每秒检查一次，如果有空闲线程则弹出一个优先级最高的任务执行。  
   - 执行时，task_executor.execute_task() 会把状态置为 RUNNING 并执行对应的逻辑：  
     • 若任务带有 "JIRA_TASK_EXP" 标签，则调用 JiraDataProcessor.process_jira_task_exp()，生成并保存 Excel。  
     • 也可能在任务中进行 ConfluenceDataProcessor 或其他自定义处理。  
   - 执行完成后，状态更新为 DONE 或 FAILED 并将执行细节保存到 TaskResultRepository。  

4) 任务执行结果后续处理：  
   - TaskExecutor 在 finally 块中，将结果通过 ResultReporter 发送到 Mattermost；  
   - 同时 scheduler_service 会周期性地从 result_repo 获取最新执行结果列表并汇总写回 Confluence 页面；完成后清空 result_repo 中的记录。  

5) 重试与超时：  
   - 若任务设定了 RetryPolicy 并发生 FAILED 或 TIMEOUT，scheduler_service 会调度新的重试操作 (设置新时间点并重新加入队列)。  

6) 查询与管理：  
   - 提供若干 FastAPI 接口 (见 app.py) 以 GET /tasks 或 GET /tasks/status/{status} 的形式查看任务信息。  
   - 支持查看运行历史 (DONE/FAILED) 的任务列表 GET /task_history。  

────────────────────────────────────────────────────────────────
3. 项目目录与主要文件说明
────────────────────────────────────────────────────────────────

• app.py  
  - 主入口文件，初始化依赖与配置，创建 FastAPI 应用并启动 APScheduler。  
  - 提供示例路由 (例如 /tasks、/tasks/status/{status}、/task_history) 用于外部查看任务信息。  

• config.yaml  
  - 存放 Confluence、Jira 的认证信息，以及调度器 (scheduler) 和日志 (log) 的设置。  

• requirements.txt  
  - 列出了所需的第三方库，包括 APScheduler、fastapi、uvicorn、pandas、atlassian-python-api 等。  

• core/  
  1) di_container.py：Dependency Injection 容器，集中管理各种 service (ConfluenceService、JiraService 等) 及 repos 的创建。  
  2) error_handler.py：全局错误处理服务，可捕获并封装异常信息。  
  3) exceptions.py：定义多层 (IntegrationException、DomainException、RepositoryException、SchedulerException) 的通用异常类型。  
  4) repositories.py：抽象的 Repository 与 UnitOfWork 基类。  

• domain/  
  1) confluence_data_processor.py：封装对 Confluence 更新/校验逻辑，决定何时以及如何更新页面表格。  
  2) jira_data_processor.py：处理 JQL 搜索、检查满足特定条件以及生成 Excel 报表 (示例中针对 "JIRA_TASK_EXP" 的主要逻辑)。  
  3) mattermost_data_processor.py：模拟发送 Mattermost 消息。  
  4) result_reporter.py：任务执行完成后，依据任务标签等信息做结果处理，并调用 MattermostDataProcessor 发送通知。  

• integration/  
  1) confluence_service.py：基于 atlassian-python-api  等封装对 Confluence 的 CRUD，主要实现 get/update_page_xhtml, update_table_data 等方法。  
  2) jira_service.py：封装与 Jira 的交互，包括搜索、更新、删除 Issue，以及 get_issues_by_root_ticket / project 等方法 (带模拟数据)。  

• scheduler/  
  1) repositories/  
     - confluence_repository.py：示例将任务结果写回 Confluence 的 Repository 封装。  
     - task_repository.py & task_result_repository.py：对 任务(Task) 和 任务结果(TaskResult) 的增删改查操作。  
  2) config.py：加载全局配置、设置日志等；在 app.py 中被直接调用。  
  3) executor.py：核心是 TaskExecutor，包含多线程执行任务的逻辑 (execute_task)；可并行调用多个处理器 (Mattermost、Confluence 等)。  
  4) fetch_service.py：可选的外部接口抓取逻辑 (演示从 Confluence 或 REST API 读取任务到本地)。  
  5) models.py：定义 Task、TaskType、TaskStatus、RetryPolicy 等 Pydantic 数据模型；同时包含 "JIRA_TASK_EXP" 这类字符串常量。  
  6) persistence.py：使用 JSON 文件方式储存与加载任务快照 (任务信息持久化)。  
  7) scheduler_service.py：基于 APScheduler 实现具体的调度逻辑、队列管理 (PriorityQueue)、重试机制（_schedule_retry）等，并维护依赖图 (dependency_map)。  
  8) schemas.py：定义 API 返回的 TaskListResponse 等数据模型 (用于 FastAPI 序列化)。  

• examples/  
  1) confl_example.py：演示如何使用 ConfluenceHelper (注：这里的 ConfluenceHelper 仅在示例出现，概念与 integration/confluence_service 类似)。  
  2) jira_example.py：演示如何使用 JiraHelper 进行项目权限检查、issue 搜索、字段更新与删除。  

────────────────────────────────────────────────────────────────
4. 主要技术规范与使用要点
────────────────────────────────────────────────────────────────

1) 环境与依赖  
   - Python 版本建议 3.9+。  
   - pip install -r requirements.txt 安装依赖。  

2) 配置 (config.yaml)  
   - confluence、jira 块必须包含 url, username, password。  
   - scheduler 块中可设置轮询间隔 poll_interval、并发数 concurrency、是否合并 coalesce 等。  
   - 日志配置 (log) 提供日志级别和文件滚动策略。  

3) FastAPI 应用  
   - 默认启动命令：uvicorn app:app --host 0.0.0.0 --port 8000 (也可直接 python app.py)。  
   - 提供若干 GET 路由：  
     • /tasks (返回所有任务)  
     • /tasks/status/{status} (按状态查询任务)  
     • /task_history (查看已执行完成(含DONE/FAILED)的任务)  

4) 调度器 (APScheduler)  
   - 在 on_startup 事件中启动，包括：  
     • 定时轮询数据库任务 (poll_db_for_new_tasks)  
     • 定时更新 Confluence 页面 (update_confl_page)  
     • 定时执行 read_data() 演示方法 (cron)  
     • 处理重试 (process_retries) 等  
   - 可灵活添加更多调度任务（如自定义 cron 表达式）。  

5) 任务执行 (TaskExecutor + SchedulerService)  
   - 支持并发执行；默认 max_task_threads=3 (在executor.py中可改)。  
   - JIRA_TASK_EXP 标签的拾取：process_jira_task_exp()。  
   - 结果通过 ResultReporter.handle_task_result() 最终汇报到 Mattermost。  

6) 重试机制 (RetryPolicy)  
   - Task 中如启用 retry_policy，则在 FAILED 或 TIMEOUT 状态下会自动 schedule 下次重试时间 (带指数退避 backoff_factor)。  
   - 下次到达时间后，_retry_task() 将任务重新置为 PENDING 并进入队列。  

7) 数据持久化与恢复 (TaskPersistenceManager)  
   - 存在 scheduler/persistence.py，以 JSON 文件形式 (tasks_snapshot.json) 存储所有任务记录。  
   - 应用重启后，会自动 load_tasks_snapshot() 进行恢复；已完成的任务 (DONE/FAILED) 归入历史，不再激活。  

────────────────────────────────────────────────────────────────
5. 部署及本地运行示例
────────────────────────────────────────────────────────────────

下面是一个最简的本地部署步骤示例：

(1) 克隆或下载本项目文件。  
(2) 在项目根目录下执行安装命令：  
    pip install -r requirements.txt  
(3) 根据需要，修改 config.yaml 中所需的连接信息 (如 Confluence、Jira 的 url、凭证)。也可修改日志、调度器并发度等。  
(4) 启动服务：  
    python app.py  
    或  
    uvicorn app:app --host 0.0.0.0 --port 8000  
(5) 访问路由查看运行状态：  
    http://localhost:8000/tasks  
    http://localhost:8000/tasks/status/PENDING  
    http://localhost:8000/task_history  

注意：
• 如果想实际调用 Confluence、Jira，请在 config.yaml 正确配置 url、username、password，并在有网络的环境下使用。  
• 本项目内的一些对应方法 (比如 JIRA_SERVICE 中 get_issues_by_root_ticket) 目前是模拟返回数据，如需真实对接可自行替换为真实 API 调用。  

────────────────────────────────────────────────────────────────
6. 扩展与自定义
────────────────────────────────────────────────────────────────

• 添加自定义任务类型  
  - 在 models.py 中扩展 TaskType 枚举并在相关逻辑中处理。  

• 增加任务依赖关系  
  - 只需在创建 Task 时指定 dependencies 列表，并确保依赖对应的任务 ID 都存在；SchedulerService 会自动管理依赖图。  

• Excel 生成与格式需求  
  - 当前在 jira_data_processor.py 中示例写入了简单的 “Root Issues” 与 “Child Issues” 两个工作表，可根据业务需求自定义更多字段或表头规则。  

• 接入更多外部系统  
  - 可在 integration/ 目录下新增 *Service.py 并在 domain/ 中预留对应处理器进行业务逻辑封装，再由 executor 或调度器统一调度与运行。  

• 安全与错误处理  
  - core/exceptions.py 和 error_handler.py 中可对不同的异常进行差异化处理或记录。  
  - 在 DIContainer 中进一步注入自定义的安全验证逻辑 (本文未展示)。  

────────────────────────────────────────────────────────────────
7. 结语
────────────────────────────────────────────────────────────────

本 README 对整个代码仓库从架构、功能、流程、以及技术实现细节进行了比较全面的说明。通过该项目可快速上手一个带 APScheduler 调度、FastAPI 服务接口、以及与 Confluence/Jira 等外部系统交互的示例后端。若有更复杂的业务需求，可在现有框架基础上进行扩展，比如增加更多自定义任务类型、引入数据库、或将 JIRA 处理逻辑替换为真实对接接口等。

如需在生产环境中应用，建议考虑：
• 日志分级与监控告警；  
• 敏感信息(密码、连接 URL 等) 使用配置管理或安全存储方式；  
• 更稳健的异常重试策略(如消息队列、去中心化的工作流)；  
• 分布式环境下的任务队列（如 Celery、RQ）以及更高级的数据库持久化等。  

通过这一 README，希望读者能快速理解并使用该项目的核心功能，或基于此做后续定制开发。祝一切顺利，也欢迎在此基础上继续扩展改进！