# 初始化
jira_helper = JiraHelper(
    url="https://your-jira.com",
    username="jira_user",
    password="jira_password_or_token"
)

# 1. 检查项目权限
has_permission = jira_helper.check_project_permission("PROJECT_KEY", "check_username")
print(f"用户是否具备权限: {has_permission}")

# 2. JQL 搜索
issues = jira_helper.search_issues(
    jql='project = PROJECT_KEY AND status = "Open"',
    fields="key,summary,customfield_10011",  # 想要返回的字段
    fetch_all=True  # 一次性获取全部结果
)
print(f"共找到 {len(issues)} 个 issue。")

# 3. 更新 Issue 字段
res = jira_helper.update_issue(issue_key="PROJECT_KEY-123", field_name="自定义字段 A", value="测试写入值")
print(f"更新结果：{res}")

# 4. 删除 Issue 前检查字段
deleted = jira_helper.delete_issue(
    issue_key="PROJECT_KEY-456",
    must_have_fields={"customfield_10011": None},  # 该字段必须非空
    must_not_have_fields=["customfield_10012"],    # 该字段必须为空
    must_status_in=["To Do", "Open"]              # 仅在状态为 To Do 或 Open 时可删
)
print(f"删除结果：{deleted}")
