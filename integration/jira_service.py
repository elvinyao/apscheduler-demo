import logging
from atlassian import Jira


class JiraService:
    """
    使用 atlassian-python-api 封装对 Jira 的常用操作。

    功能：
    1. 初始化并登录 Jira
    2. 判断某个用户名在某 Jira Project 是否有相应的权限（简单示例）
    3. 按照 JQL 搜索 Issue，支持分页或一次性获取全量
    4. 更新 Issue 指定字段（通过字段名字找到真正的字段 ID）
    5. 删除 Issue 前，检查某些字段是否有值或无值，以及检查状态是否符合要求再执行删除
    """

    def __init__(self, url: str, username: str, password: str):
        """
        初始化 Jira Helper，并登录 Jira。
        :param url: Jira 的 URL，例如 "https://your-jira.com"
        :param username: Jira 用户名
        :param password: Jira 密码或 API Token
        """
        self.jira = Jira(
            url=url,
            username=username,
            password=password
        )
    def check_project_permission_mock(self, project_key: str, check_username: str) -> bool:
        """
        Mock

        :param project_key: Jira 项目的 Key
        :param check_username: 要检查权限的用户名
        :return: 如果用户在项目角色中出现，则返回 True，否则 False
        """
        

        return True

    def check_project_permission(self, project_key: str, check_username: str) -> bool:
        """
        检查指定用户在对应的 Jira Project 是否具有某些权限。
        这里以项目中是否配置到某些角色(actors)中为例进行判断（简单示例）。
        根据实际业务需要，可以进一步细化权限判断逻辑。

        :param project_key: Jira 项目的 Key
        :param check_username: 要检查权限的用户名
        :return: 如果用户在项目角色中出现，则返回 True，否则 False
        """
        try:
            # 获取该项目下所有角色对应的链接
            project_roles = self.jira.project_role(project_key)
            # project_roles 形如 {"Administrators": "https://xxx", "Developers": "https://xxx"} 等

            for role_name, role_link in project_roles.items():
                # role_link 形如 "https://xxx/rest/api/2/project/PROJ/role/10002"
                role_id = role_link.split('/')[-1]
                # 获取该角色的详细信息
                role_details = self.jira.get_project_role_details_by_id(project_key, role_id)
                # role_details 中包含 actors 列表，可用来判断用户是否在此角色下
                actors = role_details.get('actors', [])
                for actor in actors:
                    if actor['type'] == 'atlassian-user-role-actor':
                        # 不同 Jira 版本里 actorUser 字段可能不同，这里以 name 或 accountId 等字段做判断
                        # 假设兼容老版 Jira username 以及新版 accountId
                        actor_name = actor['actorUser'].get('name') or actor['actorUser'].get('accountId')
                        if actor_name == check_username:
                            return True
        except Exception as e:
            print(f"获取项目权限时出现异常: {e}")

        return False

    def search_issues(self,
                      jql: str,
                      fields: str = "*all",
                      start: int = 0,
                      limit: int = None,
                      expand: str = None,
                      validate_query: bool = None,
                      fetch_all: bool = False) -> list:
        """
        根据 JQL 搜索 Issue，支持单次指定 limit 查询或自动翻页查询全部。

        :param jql: JQL 查询语句
        :param fields: 要返回的字段，默认 "*all"
        :param start: 起始位置，默认从 0 开始
        :param limit: 每次查询的数量，默认不指定则由 Jira 的默认限制决定
        :param expand: 扩展字段
        :param validate_query: 是否验证 query
        :param fetch_all: 是否自动翻页获取全部 Issue，默认 False
        :return: Issue 列表（每个元素都是字典对象）
        """
        if not fetch_all:
            # 不获取全部，仅单次调用
            return self.jira.jql(
                jql=jql,
                start=start,
                limit=limit,
                fields=fields,
                expand=expand,
                validate_query=validate_query
            ).get('issues', [])

        # 如果需要获取全部，循环翻页
        all_issues = []
        current_start = start
        per_page = limit if limit else 50  # 如果没指定 limit，就用一个默认值做分页

        while True:
            result = self.jira.jql(
                jql=jql,
                start=current_start,
                limit=per_page,
                fields=fields,
                expand=expand,
                validate_query=validate_query
            )
            issues = result.get('issues', [])
            all_issues.extend(issues)

            total = result.get('total', 0)
            current_start += len(issues)
            if current_start >= total:
                break

        return all_issues

    def update_issue(self, issue_key: str, field_name: str, value) -> bool:
        """
        更新 Issue 指定字段的值。此处通过字段名字获取到真正的字段 ID。

        :param issue_key: Issue Key, 如 "PROJ-123"
        :param field_name: Jira 中显示的字段名称，比如 "自定义字段 A"
        :param value: 要更新的值，可以是字符串、数字、或符合 Jira API 要求的对象
        :return: 是否更新成功
        """
        try:
            # 获取所有字段信息，然后根据 field_name 匹配真正的 field_id
            all_fields = self.jira.get_all_fields()
            field_id = None
            for f in all_fields:
                if f.get('name') == field_name:
                    field_id = f.get('id')
                    break
            if not field_id:
                print(f"未找到字段 '{field_name}' 对应的 field id，更新失败。")
                return False

            # 拼装要更新的数据
            update_data = {field_id: value}
            self.jira.issue_update(issue_key, fields=update_data)
            return True
        except Exception as e:
            print(f"更新 Issue [{issue_key}] 字段 [{field_name}] 失败: {e}")
            return False

    def delete_issue(self,
                     issue_key: str,
                     must_have_fields: dict = None,
                     must_not_have_fields: list = None,
                     must_status_in: list = None) -> bool:
        """
        删除 Issue 前，可根据要求判断：
        - 某些字段是否必须有值 (must_have_fields)
        - 某些字段是否必须为空 (must_not_have_fields)
        - Issue 的状态是否在允许删除的状态列表内 (must_status_in)

        :param issue_key: 要删除的 Issue Key
        :param must_have_fields: {field_name: expected_value}，如果期望值是非空即可，可写 None 做判断
        :param must_not_have_fields: 需要为空的字段名称列表
        :param must_status_in: 允许删除的状态名称列表（可选）
        :return: 是否删除成功
        """
        must_have_fields = must_have_fields or {}
        must_not_have_fields = must_not_have_fields or []
        must_status_in = must_status_in or []

        try:
            issue = self.jira.issue(issue_key)

            # 1. 检查状态
            status_name = issue['fields'].get('status', {}).get('name')
            if must_status_in:
                if status_name not in must_status_in:
                    print(f"Issue [{issue_key}] 当前状态 [{status_name}] 不在允许删除的状态 {must_status_in} 内，无法删除。")
                    return False

            # 2. 检查 must_have_fields
            for f_name, expected_value in must_have_fields.items():
                actual_value = issue['fields'].get(f_name)
                if expected_value is None:
                    # 仅要求非空
                    if not actual_value:
                        print(f"Issue [{issue_key}] 字段 [{f_name}] 为空，无法删除。")
                        return False
                else:
                    if actual_value != expected_value:
                        print(f"Issue [{issue_key}] 字段 [{f_name}] 值 [{actual_value}] != 期望值 [{expected_value}]，无法删除。")
                        return False

            # 3. 检查 must_not_have_fields
            for f_name in must_not_have_fields:
                actual_value = issue['fields'].get(f_name)
                if actual_value:
                    print(f"Issue [{issue_key}] 字段 [{f_name}] 要求为空，但实际值 [{actual_value}]，无法删除。")
                    return False

            # 条件均符合，则执行删除
            self.jira.delete_issue(issue_key)
            print(f"Issue [{issue_key}] 已删除。")
            return True
        except Exception as e:
            print(f"删除 Issue [{issue_key}] 失败: {e}")
            return False
    def get_issues_by_root_ticket(self, jira_env_url: str, root_ticket_key: str, fields: list = None):
        """
        根据root-ticket key获取相关的JIRA issues数据
        
        :param jira_env_url: JIRA环境URL，如env1.jira.com
        :param root_ticket_key: 根ticket的key，如"PROJ-123"
        :param fields: 需要获取的字段列表
        :return: 包含相关issues及其亲子关系的数据
        """
        # 模拟API调用，实际项目中应替换为真实的JIRA API调用
        # 构造模拟数据 - 包含层级结构
        mock_data = {
            "issues": [
                {
                    "id": "10001",
                    "key": root_ticket_key,
                    "fields": {
                        "summary": f"Root Ticket for {root_ticket_key}",
                        "description": "This is a root ticket",
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Epic"},
                        "parent": None  # 根ticket没有父级
                    }
                },
                {
                    "id": "10002",
                    "key": f"{root_ticket_key.split('-')[0]}-124",
                    "fields": {
                        "summary": "Child Ticket 1",
                        "description": "This is a child ticket",
                        "status": {"name": "In Progress"},
                        "issuetype": {"name": "Task"},
                        "parent": {"key": root_ticket_key}
                    }
                },
                {
                    "id": "10003",
                    "key": f"{root_ticket_key.split('-')[0]}-125",
                    "fields": {
                        "summary": "Child Ticket 2",
                        "description": "Another child ticket",
                        "status": {"name": "Done"},
                        "issuetype": {"name": "Bug"},
                        "parent": {"key": root_ticket_key}
                    }
                }
            ]
        }
        
        # 记录API调用日志
        logging.info(f"Retrieved {len(mock_data['issues'])} issues from {jira_env_url} for root ticket {root_ticket_key}")
        
        return mock_data

    def get_issues_by_project(self, jira_env_url: str, project_key: str, fields: list = None):
        """
        根据project key获取相关的JIRA issues数据
        
        :param jira_env_url: JIRA环境URL，如env1.jira.com
        :param project_key: 项目的key，如"PROJ"
        :param fields: 需要获取的字段列表
        :return: 该项目下的issues数据
        """
        # 模拟API调用
        mock_data = {
            "issues": [
                {
                    "id": "20001",
                    "key": f"{project_key}-100",
                    "fields": {
                        "summary": "Project Task 1",
                        "description": "First task in project",
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Task"}
                    }
                },
                {
                    "id": "20002",
                    "key": f"{project_key}-101",
                    "fields": {
                        "summary": "Project Task 2",
                        "description": "Second task in project",
                        "status": {"name": "In Progress"},
                        "issuetype": {"name": "Task"}
                    }
                }
            ]
        }
        
        logging.info(f"Retrieved {len(mock_data['issues'])} issues from {jira_env_url} for project {project_key}")
        
        return mock_data