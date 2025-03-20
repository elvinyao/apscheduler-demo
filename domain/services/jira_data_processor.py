import logging
import os
import time
import concurrent.futures
import threading

import pandas as pd
from integration.external_clients.jira_service import JiraService

class JiraDataProcessor:
    """
    Contains business logic to interpret and respond to JIRA data.
    Delegates real JIRA calls to JiraService (integration).
    """
    def __init__(self, jira_service: JiraService):
        self.jira_service = jira_service
        # 添加线程锁，用于保护共享资源在多线程环境下的访问
        self._lock = threading.Lock()

    def check_and_process_tickets(self, jql: str) -> bool:
        """
        Example domain logic: run a JQL, parse results,
        and decide if further action is needed.
        """
        logging.info("Checking JIRA tickets with JQL: %s", jql)
        issues = self.jira_service.search_issues(jql, fetch_all=True)

        if not issues:
            logging.info("No matching issues for JQL: %s", jql)
            return False

        logging.info("Found %d issues. Checking last comments...", len(issues))
        time.sleep(0.5)  # domain-level logic or transformations

        # Suppose we find we need post-processing if any issue has a special marker
        need_post_process = any("SPECIAL_MARKER" in i.get('fields', {}).get('description', '')
                                for i in issues)
        return need_post_process

    
    def process_jira_task_exp(self, task_params):
        """
        处理JIRA_TASK_EXP标签的任务
        
        :param task_params: 包含任务参数的字典，需要有以下字段：
            - jira_envs: JIRA环境列表，如["env1.jira.com", "env2.jira.com"]
            - key_type: "root_ticket" 或 "project"
            - key_value: 根据key_type，可能是root-ticket key或project key
            - user: 用户名，用于权限检查
            - is_scheduled: 是否为定时任务
        :return: 包含处理结果的字典，包括success标志和可能的excel文件路径
        """
        logging.info(f"Processing JIRA_TASK_EXP task with params: {task_params}")
        
        try:
            # 1. 提取任务参数
            jira_envs = task_params.get('jira_envs', [])
            key_type = task_params.get('key_type')
            key_value = task_params.get('key_value')
            user = task_params.get('user')
            is_scheduled = task_params.get('is_scheduled', False)
            
            if not jira_envs or not key_type or not key_value:
                return {"success": False, "error": "Missing required parameters"}
            
            # 2. 检查用户权限
            if key_type == "root_ticket":
                has_permission = self.jira_service.check_project_permission_mock(
                    key_value.split('-')[0], user
                )
            else:  # project key
                has_permission = self.jira_service.check_project_permission_mock(
                    key_value, user
                )
                
            if not has_permission:
                return {"success": False, "error": f"User {user} does not have permission"}
            
            # 3. 获取JIRA数据
            all_issues = []
            for jira_env in jira_envs:
                if key_type == "root_ticket":
                    issues_data = self.jira_service.get_issues_by_root_ticket(
                        jira_env, key_value
                    )
                else:  # project key
                    issues_data = self.jira_service.get_issues_by_project(
                        jira_env, key_value
                    )
                
                # 将环境信息添加到每个issue
                for issue in issues_data.get('issues', []):
                    issue['jira_environment'] = jira_env
                    all_issues.append(issue)
            
            # 4. 生成Excel
            excel_data = self._generate_excel_data(all_issues)
            excel_path = self._save_excel(excel_data, key_value, is_scheduled)
            
            return {
                "success": True, 
                "excel_path": excel_path,
                "issue_count": len(all_issues)
            }
            
        except Exception as e:
            logging.error(f"Error processing JIRA_TASK_EXP task: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_excel_data(self, issues):
        """
        根据JIRA issues数据生成Excel数据，按照亲子关系组织
        
        :param issues: JIRA issues列表
        :return: 包含DataFrame的字典，用于生成Excel工作簿
        """
        # 创建根issue的DataFrame
        root_issues = [i for i in issues if 'parent' not in i['fields'] or not i['fields']['parent']]
        child_issues = [i for i in issues if 'parent' in i['fields'] and i['fields']['parent']]
        
        # 转换成DataFrame格式
        root_data = []
        for issue in root_issues:
            root_data.append({
                'Key': issue['key'],
                'Summary': issue['fields']['summary'],
                'Status': issue['fields']['status']['name'],
                'Type': issue['fields']['issuetype']['name'],
                'Environment': issue.get('jira_environment', '')
            })
        
        child_data = []
        for issue in child_issues:
            child_data.append({
                'Key': issue['key'],
                'Parent Key': issue['fields']['parent']['key'],
                'Summary': issue['fields']['summary'],
                'Status': issue['fields']['status']['name'],
                'Type': issue['fields']['issuetype']['name'],
                'Environment': issue.get('jira_environment', '')
            })
        
        root_df = pd.DataFrame(root_data) if root_data else pd.DataFrame()
        child_df = pd.DataFrame(child_data) if child_data else pd.DataFrame()
        
        return {
            'Root Issues': root_df,
            'Child Issues': child_df
        }
    
    def _save_excel(self, excel_data, key_value, is_scheduled):
        """
        将数据保存为Excel文件
        
        :param excel_data: 包含DataFrame的字典
        :param key_value: 用于生成文件名的键值
        :param is_scheduled: 是否为定时任务
        :return: 保存的Excel文件路径
        """
        # 创建输出目录
        output_dir = "jira_reports"
        os.makedirs(output_dir, exist_ok=True)
        
        # 文件名逻辑：如果是定时任务，加上时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if is_scheduled:
            filename = f"{key_value}_{timestamp}.xlsx"
        else:
            filename = f"{key_value}.xlsx"
        
        filepath = os.path.join(output_dir, filename)
        
        # 创建Excel writer
        with pd.ExcelWriter(filepath) as writer:
            for sheet_name, df in excel_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logging.info(f"Excel report saved to {filepath}")
        return filepath

    def process_bulk_jira_operations(self, tickets_data, operation_type="create", max_workers=5):
        """
        使用多线程处理批量Jira tickets创建或更新操作
        
        :param tickets_data: 要创建或更新的tickets数据列表，每个元素是一个包含ticket数据的字典
        :param operation_type: 操作类型，"create"或"update"
        :param max_workers: 最大并发工作线程数
        :return: 包含处理结果的字典，包括成功和失败的ticket信息
        """
        logging.info(f"开始批量{operation_type} {len(tickets_data)}个Jira tickets，使用{max_workers}个线程")
        
        # 初始化结果收集器
        results = {
            "success": [],
            "failed": [],
            "total": len(tickets_data),
            "success_count": 0,
            "failed_count": 0
        }
        
        # 选择合适的操作方法
        if operation_type.lower() == "create":
            operation_method = self.jira_service.create_issue
        elif operation_type.lower() == "update":
            operation_method = self.jira_service.update_issue
        else:
            return {"success": False, "error": f"不支持的操作类型: {operation_type}"}
        
        # 定义线程工作函数
        def process_ticket(ticket_data):
            try:
                ticket_id = ticket_data.get('key') if operation_type.lower() == "update" else None
                response = operation_method(ticket_data, ticket_id)
                
                # 使用锁保护共享资源的访问
                with self._lock:
                    results["success"].append({
                        "key": response.get("key", ticket_id),
                        "data": ticket_data
                    })
                    results["success_count"] += 1
                    
                logging.info(f"成功{operation_type} ticket: {response.get('key', ticket_id)}")
                return response
            except Exception as e:
                error_msg = str(e)
                
                # 使用锁保护共享资源的访问
                with self._lock:
                    results["failed"].append({
                        "data": ticket_data,
                        "error": error_msg
                    })
                    results["failed_count"] += 1
                    
                logging.error(f"执行{operation_type}操作失败: {error_msg}")
                return {"error": error_msg, "data": ticket_data}
        
        # 使用线程池执行多线程操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务到线程池
            futures = [executor.submit(process_ticket, ticket_data) for ticket_data in tickets_data]
            
            # 等待所有任务完成（可选：添加超时机制）
            concurrent.futures.wait(futures)
            
        logging.info(f"批量{operation_type}操作完成: 成功={results['success_count']}, 失败={results['failed_count']}")
        return results

    def process_linked_jira_operations(self, tickets_hierarchy, operation_type="create", max_workers=5):
        """
        使用多线程处理具有层级关系的Jira tickets批量创建或更新操作
        
        :param tickets_hierarchy: 包含层级结构的ticket数据，例如：
                                 {"root": root_ticket, "children": [child1, child2, ...]}
        :param operation_type: 操作类型，"create"或"update"
        :param max_workers: 最大并发工作线程数
        :return: 包含处理结果的字典，包括层级信息
        """
        logging.info(f"开始处理层级{operation_type} Jira tickets")
        
        results = {
            "root": None,
            "children": [],
            "failed": [],
            "success_count": 0,
            "failed_count": 0
        }
        
        # 首先处理根ticket
        root_ticket = tickets_hierarchy.get("root")
        if not root_ticket:
            return {"success": False, "error": "缺少根ticket数据"}
        
        try:
            # 直接处理根ticket，不使用多线程
            if operation_type.lower() == "create":
                root_response = self.jira_service.create_issue(root_ticket)
            else:
                root_id = root_ticket.get('key')
                if not root_id:
                    return {"success": False, "error": "更新根ticket时缺少key"}
                root_response = self.jira_service.update_issue(root_ticket, root_id)
            
            results["root"] = root_response
            results["success_count"] += 1
            root_key = root_response.get("key")
            logging.info(f"成功{operation_type}根ticket: {root_key}")
            
            # 准备子ticket数据，添加父ticket引用
            children = tickets_hierarchy.get("children", [])
            for child in children:
                if operation_type.lower() == "create":
                    # 添加父ticket引用
                    if "fields" not in child:
                        child["fields"] = {}
                    child["fields"]["parent"] = {"key": root_key}
            
            # 如果有子tickets，使用多线程处理
            if children:
                child_results = self.process_bulk_jira_operations(
                    children, operation_type, max_workers
                )
                
                results["children"] = child_results["success"]
                results["failed"] = child_results["failed"]
                results["success_count"] += child_results["success_count"]
                results["failed_count"] = child_results["failed_count"]
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"处理根ticket时出错: {error_msg}")
            return {"success": False, "error": error_msg, "data": root_ticket}
