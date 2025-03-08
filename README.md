以下是一份示例的 README 文档，介绍该代码库的功能、交互方式与技术规范，帮助开发者或使用者快速上手并理解项目的整体结构和工作流程。

-------------------------------------------------------------------------------
README
-------------------------------------------------------------------------------

目录：
1. 项目简介  
2. 功能概述  
   2.1 核心功能  
   2.2 交互流程总览  
3. 代码结构及模块说明  
4. 配置说明  
   4.1 config.yaml  
   4.2 .gitignore  
5. 安装与运行  
   5.1 环境依赖  
   5.2 快速运行(本地)  
   5.3 API接口使用说明  
6. 主要逻辑说明  
   6.1 Scheduler (任务调度)  
   6.2 Task 流程与重试机制  
   6.3 Confluence 集成  
   6.4 Jira 集成  
   6.5 Mattermost 集成  
7. 示例与测试  
8. 后续扩展与注意事项  

-------------------------------------------------------------------------------
1. 项目简介
-------------------------------------------------------------------------------

本项目是一个基于 FastAPI 与 APScheduler 的任务调度与管理平台，主要功能包含：
• 通过定时或手动方式创建并执行 Task  
• 集成 Confluence、Jira 等系统的自动化处理逻辑  
• 支持任务结果的统一汇总和写回 (如写回到 Confluence 页面)  
• 支持处理复杂业务规则 (如检查 JIRA issue、根据特性导出 Excel 报表等)  

该项目还采用了领域分层 (domain / integration / scheduler / core 等)，并使用了简单的 DI 容器 (Dependency Injection) 管理对外部系统服务的依赖，方便维护和扩展。

-------------------------------------------------------------------------------
2. 功能概述
-------------------------------------------------------------------------------

2.1 核心功能：
• 任务调度：使用 APScheduler 外加自定义的优先级队列机制，实现对定时任务与即时任务 (IMMEDIATE) 的综合调度  
• JIRA_TASK_EXP 任务：针对带有标签 "JIRA_TASK_EXP" 的任务进行特殊逻辑处理，如导出包含根问题 (root ticket) 或项目 (project) 的相关所有 Issues，最终生成 Excel 报表  
• 并行处理：对需要进一步后续并发执行的子任务（如更新 Mattermost、Confluence）采用多线程并行处理  
• 结果汇总：将任务执行结果暂存在内存中 (TaskResultRepository)，再定期统一写回 Confluence (ConfluenceUpdater)  
• 任务依赖与重试：支持任务依赖管理，且在任务失败或超时后可进行重试  

2.2 交互流程总览：
1) 创建 Task → 存储到 TaskRepository (内存或模拟 DB).  
2) SchedulerService 会周期性轮询待执行任务，或根据 cron 表达式执行定时任务。  
3) Executor (TaskExecutor) 拉起具体任务时，会根据标签（如 "JIRA_TASK_EXP"）调用对应的域逻辑 (domain 层里对 Jira 数据的处理)，并可在其中并行处理 Mattermost、Confluence 更新。  
4) 任务执行完毕后将执行结果写入 TaskResultRepository。  
5) SchedulerService 又会周期性触发 update_confl_page()，从 TaskResultRepository 中读取结果并更新到 Confluence 内。  
6) 整个过程的日志打印、错误处理、重试等机制都交由调度框架和域逻辑共同完成。  

-------------------------------------------------------------------------------
3. 代码结构及模块说明
-------------------------------------------------------------------------------

根目录：
• app.py：项目的启动入口，包含 FastAPI 应用的初始化、路由与事件钩子。  
• config.yaml：全局配置文件，包含 Confluence/Jira/scheduler/log 等配置信息。  
• requirements.txt：依赖包清单。  

核心目录和文件：
• core/  
  └─ di_container.py：一个简单的依赖注入容器，统一管理对外部系统的连接与 domain 层对象的实例化。  

• domain/  
  ├─ confluence_data_processor.py：Confluence 域逻辑，判断何时以及如何更新 Confluence。  
  ├─ jira_data_processor.py：JIRA 域逻辑，判断何时以及如何处理 JIRA 任务、是否需要后续或并行处理。  
  └─ mattermost_data_processor.py：Mattermost 的简易域逻辑 (模拟发送通知)。  

• integration/  
  ├─ confluence_service.py：面向 Confluence API 的封装类，提供页面获取、表格更新等接口。  
  └─ jira_service.py：面向 Jira API 的封装类，提供项目权限检查、Issue 搜索、Issue 更新、Issue 删除等接口。  

• scheduler/  
  ├─ __init__.py：标识该文件夹为 package。  
  ├─ config.py：日志与配置加载模块，包含 setup_logging() 函数。  
  ├─ executor.py：TaskExecutor，封装线程池执行逻辑并调用 domain 进行任务处理。  
  ├─ fetch_service.py：示例，演示如何从外部系统(如 Confluence)获取任务并存入本地存储。  
  ├─ models.py：定义 Task、TaskPriority、TaskType、TaskStatus 等核心数据模型，以及一个标识任务标签 "JIRA_TASK_EXP"。  
  ├─ persistence.py：模拟将任务持久化到本地 JSON 文件，用于应用重启时恢复任务状态。  
  ├─ repository.py：TaskRepository，内存中的任务存储及对外操作接口，同时会读取与写入持久化快照。  
  ├─ scheduler_service.py：整个调度核心类，封装了 APScheduler + PriorityQueue 的使用，用于定期扫描新任务、添加定时任务、处理队列中的任务、超时处理、重试逻辑等。  
  ├─ schemas.py：API返回的 Pydantic 模型 (TaskListResponse)。  
  └─ task_result_repo.py：包含 TaskResultRepository(将执行结果保存在内存) 和 ConfluenceUpdater(将结果统一写入 Confluence)。  

• examples/：一些对 Confluence 或 Jira 集成操作的简单演示(不在主流程内)。  

• .gitignore：对不需要纳入版本管理的文件进行过滤。  

-------------------------------------------------------------------------------
4. 配置说明
-------------------------------------------------------------------------------

4.1 config.yaml：
该文件包含与外部服务和日志、调度相关的所有配置：
• confluence/url/username/password：Confluence 连接所需信息。  
• jira/url/username/password：Jira 连接所需信息。  
• scheduler/poll_interval：轮询数据库(任务库)的周期(秒)。  
• scheduler/concurrency：最大并发执行的任务数(用于 APScheduler 线程池和自定义线程池)。  
• log/level、filename、max_bytes、backup_count、format：日志级别与日志文件滚动策略。  

在部署或本地运行前，需要根据自身环境改写真实的 url、用户名与密码等信息。

4.2 .gitignore：
已经忽略了大多数 Python 常见的缓存、编译产物文件，也包含日志目录、虚拟环境目录等。

-------------------------------------------------------------------------------
5. 安装与运行
-------------------------------------------------------------------------------

5.1 环境依赖：
• Python 3.8+ (建议 3.9 或 3.10)  
• requirements.txt 里的第三方库，主要包含：  
  - fastapi  
  - uvicorn  
  - APScheduler  
  - atlassian-python-api (用于与 Confluence、Jira 通信)  
  - pandas、openpyxl (处理 Excel 导出功能)  

5.2 快速运行(本地)：
1) 创建并激活虚拟环境(可选)：  
   python -m venv venv  
   source venv/bin/activate  (Windows 下为 venv\Scripts\activate)  

2) 安装依赖：  
   pip install -r requirements.txt  

3) 启动服务：  
   python app.py  
   # 默认监听 0.0.0.0:8000  

4) 浏览器或使用工具访问 http://localhost:8000/tasks  
   即可查看任务列表等接口返回。  

5.3 API接口使用说明：
• /tasks (GET)：返回所有已创建的任务列表  
• /tasks/status/{status} (GET)：根据状态过滤并返回对应任务  
• /task_history (GET)：返回已经结束(DONE 或 FAILED)的历史任务  

启动后，可以通过日常 HTTP 工具 (curl, Postman, etc.) 或浏览器调用此 FastAPI 应用接口。

-------------------------------------------------------------------------------
6. 主要逻辑说明
-------------------------------------------------------------------------------

6.1 Scheduler (任务调度)：
• poll_interval (config.yaml) 指定轮询任务仓库的时间间隔，SchedulerService 会按该周期拉取待执行任务。  
• 对于带 cron_expr 的调度任务 (TaskType.SCHEDULED)，SchedulerService 使用 APScheduler 创建对应的调度；对于 IMMEDIATE 任务，则采用自定义 PriorityQueue 进行并发控制。  

6.2 Task 流程与重试机制：
• 每个 Task 被放入队列前会检查依赖(dependencies)是否全部完成。若依赖未完成，则先放置到 waiting_on_dependencies 集合中。  
• 在学号(或 cron)触发后，如果队列有空闲并发容量，则真正执行该 Task；执行时调用 executor.py 中 TaskExecutor.execute_task()。  
• 若配置了超时(timeout_seconds)，在任务执行时会启动一个计时器，超时后会自动取消并更新状态为 TIMEOUT。  
• 若任务失败或超时且仍可重试 (task.retry_policy)，则会被重新调度并等待下一次重试时间。重试将任务状态置为 RETRY，然后在预定时间自动变回 PENDING→放入队列→再次执行。  

6.3 Confluence 集成：
• integration/confluence_service.py：基于 atlassian-python-api 提供的 Confluence 客户端封装。  
• domain/confluence_data_processor.py：根据业务需求，判断是否更新 Confluence (如表格内容已变化才更新等)。  
• scheduler/task_result_repo.py 中的 ConfluenceUpdater 负责汇总完所有任务结果后，在 update_confluence() 中执行写入操作 (此处仅作日志模拟，而真实环境可调用 integration/confluence_service.py 中写表逻辑)。  

6.4 Jira 集成：
• integration/jira_service.py：基于 atlassian-python-api 的 Jira 客户端封装，包含权限检查、Issue 搜索、Issue 更新、Issue 删除等功能。  
• domain/jira_data_processor.py：核心业务逻辑，例如检查 JIRA Issue 的状态是否需要特殊处理，或根据 root_ticket / project 自动导出子任务等。  
• 在处理带有 "JIRA_TASK_EXP" 标签的任务时，会执行 process_jira_task_exp()，导出结果并生成 Excel。  

6.5 Mattermost 集成：
• domain/mattermost_data_processor.py 仅演示用，把 send_notification() 做成一个模拟（打日志 + sleep），实际可改接 Mattermost API。  
• 在任务执行后，如果需要通知用户，会通过并行线程调用这里的send_notification()进行示例操作。  

-------------------------------------------------------------------------------
7. 示例与测试
-------------------------------------------------------------------------------

• examples/confl_example.py：演示如何从 Confluence 获取/更新表格。  
• examples/jira_example.py：演示如何检查 Jira 项目权限、搜索 Issue、更新字段、删除 Issue 等。  

如果需要快速测试：
1) 启动服务后，在 /tasks 路径可查看系统中已有的示例任务信息(在 app.py 中手动添加)。  
2) 若需要自定义新任务，可直接在 TaskRepository 中添加一个新的 Task 数据字典。  
3) 可通过在 domain/jira_data_processor.py、domain/confluence_data_processor.py 修改日志或断点调试，以验证处理逻辑是否符合预期。

-------------------------------------------------------------------------------
8. 后续扩展与注意事项
-------------------------------------------------------------------------------

1) 持久化：  
   目前仅使用 JSON 文件 (scheduler/persistence.py) 来保存任务信息，后续可改用数据库 (MySQL、PostgreSQL、MongoDB 等)，以满足更高并发和更安全的存储需求。  

2) 安全与访问控制：  
   代码示例中对 Jira/Confluence 登录的用户名密码是写在 config.yaml 中明文，实际生产需要使用安全的密钥管理或加密方式，并全面控制访问权限。  

3) 代码部署：  
   - 可使用 uvicorn + gunicorn 的方式部署到生产环境；  
   - APScheduler 建议以单节点、独立进程方式运行，或使用分布式调度框架 (如 Celery + Redis) 进行水平扩展。  

4) 日志监控：  
   - 日志配置可进一步对接 ELK 或云端监控。  
   - 对关键节点的监控（任务执行时长异常等）需要配合统计接口或事件上报系统。  

5) 任务依赖与分解：  
   - 如果依赖关系复杂 (超过简单的 "父-子" 定义)，可考虑引入更完整的队列系统或工作流引擎。  

感谢使用本项目！如有问题和改进建议，欢迎在仓库的 Issue 区或直接与作者联系。  

-------------------------------------------------------------------------------
(完)  
-------------------------------------------------------------------------------