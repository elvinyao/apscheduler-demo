from atlassian import Confluence
from bs4 import BeautifulSoup
import copy


class ConfluenceService:
    """
    使用 atlassian-python-api 封装对 Confluence 的常用操作。

    功能：
    0. 初始化并登录 Confluence
    1. 获取指定页面的 XHTML 数据
    2. 获取页面中的表格数据，第一行为标题
    3. 更新页面表格内容，若遇到版本冲突，需要重新获取最新内容再更新
    """

    def __init__(self, url: str, username: str, password: str):
        """
        初始化 Confluence Helper，并登录 Confluence。
        :param url: Confluence 的 URL，例如 "https://your-confluence.com"
        :param username: Confluence 用户名
        :param password: Confluence 密码或 API Token
        """
        self.confluence = Confluence(
            url=url,
            username=username,
            password=password
        )

    def get_page_xhtml(self, page_id: str) -> dict:
        """
        获取 Confluence 页面信息（包含 xhtml 内容）。
        :param page_id: Confluence 页面 ID
        :return: 包含页面信息的字典，其中 body.storage.value 为 xhtml
        """
        page_info = self.confluence.get_page_by_id(
            page_id=page_id,
            expand='body.storage,version'
        )
        return page_info

    def parse_table_cell(self, cell_html: str) -> str:
        """
        对单元格的 HTML 做特殊解析的方法示例。可在此自定义更多规则。
        :param cell_html: 单元格的原始 HTML
        :return: 解析后的文本或需要的格式
        """
        # 简单示例：将 HTML 直接转成纯文本返回
        cell_soup = BeautifulSoup(cell_html, 'html.parser')
        return cell_soup.get_text(strip=True)

    def get_table_data(self, page_id: str, table_index: int = 0) -> list:
        """
        从指定的 page_id 中，解析并获取第 table_index 个表格的数据。
        默认取页面中的第一个表格。

        :param page_id: Confluence 页面 ID
        :param table_index: 指定取第几个表格（如果页面有多个表格）
        :return: 返回一个 list，每个元素是 dict，键是表头列名，值是对应单元格内容
        """
        page_info = self.get_page_xhtml(page_id)
        xhtml = page_info['body']['storage']['value']
        soup = BeautifulSoup(xhtml, 'html.parser')

        tables = soup.find_all('table')
        if not tables or table_index >= len(tables):
            print(f"页面 [{page_id}] 未找到第 {table_index+1} 个表格！")
            return []

        table = tables[table_index]
        rows = table.find_all('tr')

        # 第一行作为表头
        headers = []
        data_list = []

        for row_index, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])

            if row_index == 0:
                # 第一行视为表头
                for cell in cells:
                    headers.append(self.parse_table_cell(str(cell)))
            else:
                # 后续每行组成一条记录
                row_data = {}
                for i, cell in enumerate(cells):
                    header_name = headers[i] if i < len(headers) else f"col_{i}"
                    row_data[header_name] = self.parse_table_cell(str(cell))
                data_list.append(row_data)

        return data_list

    def update_table_data(self, page_id: str,
                          new_data: list,
                          table_index: int = 0,
                          retry_on_conflict: bool = True) -> bool:
        """
        更新页面中的指定表格数据。根据第一行列名进行写入。
        更新时需要进行版本检查。如果版本冲突则重新获取最新内容再更新。

        :param page_id: Confluence 页面 ID
        :param new_data: 要更新的表格数据，格式与 get_table_data 返回相同。
                         例如：[{"列1": "值11", "列2": "值12"}, {"列1": "值21", "列2": "值22"}]
        :param table_index: 指定更新第几个表格
        :param retry_on_conflict: 如果为 True，当检测到版本冲突时自动重试一次
        :return: 是否更新成功
        """
        try:
            page_info = self.get_page_xhtml(page_id)
            current_version = page_info['version']['number']
            xhtml = page_info['body']['storage']['value']
            title = page_info['title']

            soup = BeautifulSoup(xhtml, 'html.parser')
            tables = soup.find_all('table')
            if not tables or table_index >= len(tables):
                print(f"页面 [{page_id}] 不存在第 {table_index+1} 个表格，更新失败。")
                return False

            # 找到目标 table
            table = tables[table_index]

            # 清空原有的表格内容，重新生成
            # 注意：这里仅演示简单替换表格所有内容的方式，也可根据行数据做定向更新
            new_tbody = soup.new_tag('tbody')
            # 生成表头
            if len(new_data) > 0:
                headers = list(new_data[0].keys())
                header_tr = soup.new_tag('tr')
                for h in headers:
                    th = soup.new_tag('th')
                    th.string = h
                    header_tr.append(th)
                new_tbody.append(header_tr)

                # 生成数据行
                for row_item in new_data:
                    row_tr = soup.new_tag('tr')
                    for h in headers:
                        td = soup.new_tag('td')
                        # 这里可以根据需要插入 HTML 或纯文本
                        td.string = str(row_item.get(h, ""))
                        row_tr.append(td)
                    new_tbody.append(row_tr)
            # 用新的 tbody 替换旧的 tbody
            old_tbody = table.find('tbody')
            if old_tbody:
                old_tbody.replace_with(new_tbody)
            else:
                # 如果原本没有 tbody，就直接把 new_tbody 放进 table
                table.append(new_tbody)

            # 更新回 Confluence
            updated_body = str(soup)
            update_resp = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=updated_body,
                version=current_version + 1
            )
            if 'id' in update_resp:
                print(f"页面 [{page_id}] 表格更新成功，版本从 {current_version} -> {current_version+1}")
                return True
            else:
                print(f"页面 [{page_id}] 表格更新失败，Confluence 返回: {update_resp}")
                return False

        except Exception as e:
            # 如果出现版本冲突或其他异常情况，并且允许重试，则重新获取后再来一次
            if retry_on_conflict and "conflict" in str(e).lower():
                print("检测到版本冲突，尝试重新获取最新内容后再次更新...")
                return self.update_table_data(
                    page_id=page_id,
                    new_data=new_data,
                    table_index=table_index,
                    retry_on_conflict=False
                )
            else:
                print(f"更新页面 [{page_id}] 表格时出现异常: {e}")
                return False
