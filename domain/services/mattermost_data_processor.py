# scheduler/mattermost_data_processor.py

import logging
import time

class MattermostDataProcessor:
    """
    负责与Mattermost的发送消息操作，这里仅模拟日志输出和延时。
    """
    def send_notification(self):
        logging.info("Simulating sending notification to Mattermost user...")
        time.sleep(1)  # 模拟网络
        logging.info("Mattermost notification sent successfully.")

    def send_custom_message(self,text: str):
        logging.info(f"Sending custom Mattermost message: {text}")
        time.sleep(1) # 模拟网络发送
        logging.info("Custom message sent to Mattermost successfully.")
