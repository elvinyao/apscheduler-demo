import logging

class ResultReporter:
    """
    用于对任务执行结果进行进一步判断或处理，并发送到 Mattermost。
    示例：根据不同的 task.tags 生成不同消息内容。
    """
    def __init__(self, mattermost_processor):
        """
        :param mattermost_processor: 通过 DI 注入的 MattermostDataProcessor 实例
        """
        self.mattermost_processor = mattermost_processor

    def handle_task_result(self, task, result_item):
        """
        对最终执行结果进行检查或处理，并将结果发送到 Mattermost。
        
        :param task: Task 类型对象
        :param result_item: 存储了执行状态、success/错误信息等的字典
        :return: None 或者其他需要返回的数据
        """
        execution_details = result_item.get('execution_details', {})
        is_success = execution_details.get("success", False)
        
        # 根据标签决定不同的发送逻辑
        if "SPECIAL_TAG_A" in task.tags:
            message = f"[Tag A] Task {task.id} ended with success={is_success}. Info: {execution_details}"
        elif "SPECIAL_TAG_B" in task.tags:
            message = f"[Tag B] Task {task.id} -> {execution_details}"
        else:
            # 默认逻辑
            message = f"Task {task.id} finished. success={is_success}, details={execution_details}"

        # 在此处可做更多判断或格式化
        logging.info(f"ResultReporter is sending Mattermost message: {message}")

        # 通过注入进来的 mattermost_processor 发送消息
        self.mattermost_processor.send_custom_message(message)

        # 若需要返回更多信息或做其他处理，也可在这里进行
        # 例如 return {"message_sent": True, "task_id": str(task.id)}
        return