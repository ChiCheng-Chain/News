# backend/app/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=("settings_",),
    )

    mysql_url: str = "sqlite:///:memory:"
    volc_api_key: str = "test"
    volc_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model_doubao_lite: str = "test-model"
    model_doubao_pro: str = "test-model"
    model_deepseek_r1: str = "test-model"
    model_deepseek_v3: str = "test-model"

settings = Settings()
