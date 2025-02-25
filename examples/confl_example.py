# 初始化
confluence_helper = ConfluenceHelper(
    url="https://your-confluence.com",
    username="confluence_user",
    password="confluence_password_or_token"
)

# 1. 获取页面的 XHTML 数据
page_info = confluence_helper.get_page_xhtml(page_id="123456")
print("页面标题:", page_info['title'])
print("页面版本:", page_info['version']['number'])

# 2. 获取页面表格数据
table_data = confluence_helper.get_table_data(page_id="123456", table_index=0)
for row in table_data:
    print(row)

# 3. 更新页面中的表格数据
# 假设我们想要写回新的表格数据
new_table_data = [
    {"列1": "新值1-1", "列2": "新值1-2"},
    {"列1": "新值2-1", "列2": "新值2-2"}
]
update_ok = confluence_helper.update_table_data(page_id="123456", new_data=new_table_data)
print(f"更新表格成功? {update_ok}")
