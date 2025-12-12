from __future__ import annotations
import os
import json
import time
from typing import List, Dict, Any
import requests
from requests import ReadTimeout
from .config import llm_config
from .logger import info, warn, error

OpenAICompatURL = "/v1/chat/completions"

class LLMClient:
    def __init__(self):
        self.base_url = llm_config.base_url.rstrip("/")
        self.api_key = llm_config.api_key
        self.model = llm_config.model
        self.temperature = llm_config.temperature
        self.max_tokens = llm_config.max_tokens
        self.mock = llm_config.mock_mode or not self.api_key
        self.force_json = os.getenv("FORCE_JSON", "false").lower() == "true"

    def chat(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] | None = None,
             tool_choice: str | None = None, system: str | None = None) -> Dict[str, Any]:
        if self.mock:
            warn("LLM 处于 mock 模式，将返回演示用的简化结果。配置 LLM_API_KEY 以启用真实调用。")
            return self._mock_response(messages)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Cascade-Agent/1.0 (+https://github.com/)"
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": ([] if system is None else [{"role": "system", "content": system}]) + messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        # 可选强制 JSON（仅在兼容端支持时开启）
        if self.force_json:
            payload["response_format"] = {"type": "json_object"}
        url = f"{self.base_url}{OpenAICompatURL}"

        # 稳健重试：3 次，指数退避
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=(30, 240))
                if resp.status_code >= 400:
                    txt = resp.text[:500]
                    error(f"LLM API 错误 {resp.status_code}: {txt}")
                    # 对于 400 类错误不重试
                    raise RuntimeError(f"LLM API error: {resp.status_code}")
                return resp.json()
            except ReadTimeout as e:
                last_err = e
                wait_s = 2 ** attempt
                warn(f"LLM 读取超时，{wait_s}s 后重试（第 {attempt+1}/3 次）")
                time.sleep(wait_s)
            except requests.RequestException as e:
                last_err = e
                # 网络类错误重试
                wait_s = 2 ** attempt
                warn(f"LLM 请求异常，{wait_s}s 后重试（第 {attempt+1}/3 次）：{e}")
                time.sleep(wait_s)
        # 最终失败
        error(f"LLM 请求失败：{last_err}")
        raise last_err if last_err else RuntimeError("LLM request failed")

    def simple_text(self, prompt: str, system: str | None = None) -> str:
        data = self.chat(messages=[{"role": "user", "content": prompt}], system=system)
        # OpenAI兼容返回
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return json.dumps(data)

    def _mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # 极简 mock：如果用户提到 plan，则返回一个固定 JSON 计划
        content = messages[-1]["content"].lower()
        if "plan" in content or "规划" in content:
            msg = {
                "role": "assistant",
                "content": json.dumps({
                    "plan": [
                        {"id": "t-pl-1", "desc": "创建项目结构", "deps": []},
                        {"id": "t-pl-2", "desc": "生成主页 index.html", "deps": ["t-pl-1"]},
                        {"id": "t-pl-3", "desc": "生成样式 assets/style.css", "deps": ["t-pl-1"]},
                    ]
                }, ensure_ascii=False)
            }
        else:
            msg = {"role": "assistant", "content": "{\"result\": \"ok\"}"}
        return {
            "choices": [
                {"index": 0, "message": msg}
            ]
        }

client = LLMClient()

