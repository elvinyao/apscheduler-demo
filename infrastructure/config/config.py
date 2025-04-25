# scheduler/config.py

import os
import yaml
import logging
from logging.handlers import RotatingFileHandler

# 默认的config.yaml路径，可根据需要修改
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # scheduler目录
    "..",               # 上一级目录
    "config.yaml"       # 配置文件名
)

def load_config(config_path: str = None) -> dict:
    """
    从YAML文件加载配置并返回一个dict。
    如果config_path为None，使用DEFAULT_CONFIG_PATH。
    """
    if not config_path:
        config_path = DEFAULT_CONFIG_PATH

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config

def setup_logging(log_config: dict) -> None:
    """
    基于log_config配置日志:
      - 级别
      - 文件输出(带滚动)
      - 控制台输出
    """
    level_str = log_config.get("level", "INFO")
    log_level = getattr(logging, level_str.upper(), logging.INFO)

    # 日志记录器的格式
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    formatter = logging.Formatter(log_format)

    # 获取 root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers.clear()  # 清除可能已存在的默认处理器

    # 1) 文件滚动日志处理器
    filename = log_config.get("filename", "app.log")
    max_bytes = log_config.get("max_bytes", 10485760)   # 10MB
    backup_count = log_config.get("backup_count", 5)

    # 确保日志目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    file_handler = RotatingFileHandler(
        filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 2) 控制台（stdout）处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 打印一条初始消息
    logger.info("Logging is set up. Level: %s, log file: %s", level_str, filename)

