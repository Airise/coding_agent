import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(override=True)
# 额外加载非隐藏环境文件，便于在部分环境禁止 .env 时使用
load_dotenv("local.env", override=True)
load_dotenv("config/.env", override=True)

class LLMConfig(BaseModel):
    provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    api_key: str | None = os.getenv("LLM_API_KEY")
    model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    mock_mode: bool = os.getenv("MOCK_MODE", "false").lower() == "true"

class RuntimeConfig(BaseModel):
    workspace_root: str = os.getenv("WORKSPACE_ROOT", os.getcwd())
    step_limit: int = int(os.getenv("STEP_LIMIT", "12"))
    allow_shell: bool = os.getenv("ALLOW_SHELL", "true").lower() == "true"
    allow_write: bool = os.getenv("ALLOW_WRITE", "true").lower() == "true"
    # 所有生成产物的根目录名（相对 workspace_root），默认 'project'
    output_dir: str = os.getenv("OUTPUT_DIR", "project")

llm_config = LLMConfig()
runtime = RuntimeConfig()

