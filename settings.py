from functools import cached_property, lru_cache
from pathlib import Path
from pydantic import Field
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_FILE_NAME="config.yaml"

def _default_config_path() -> Path:
    return Path(__file__).resolve().with_name(CONFIG_FILE_NAME)

class Settings(BaseSettings):
    # ── 简单字段，直接通过 env or secret 文件注入 ───────────
    log_level: str = "INFO"

    # ── 复杂 / 大体积配置：先得到文件路径，再自己去读 ─────────
    config_path: Path = Field(
        default_factory=_default_config_path,
        validation_alias="APP_CONFIG_PATH",   # 指定 env 名（或用 env_prefix）
    )

    # Pydantic settings 配置
    model_config = SettingsConfigDict(
        env_prefix="APP_",              # APP_LOG_LEVEL、APP_DB_URL…
        secrets_dir="/var/run/secrets",  # k8s Secret 挂载目录（可自定义）
        extra="ignore"                  # 允许有未用到的 env
    )

    # 读取并缓存 YAML（大文件避免重复解析）
    @cached_property
    def config_file(self) -> dict:
        return yaml.safe_load(self.config_path.read_text())


# 单例获取函数，便于依赖注入 / FastAPI Depends
@lru_cache
def get_settings() -> Settings:
    return Settings()
