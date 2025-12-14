from __future__ import annotations
from typing import List, Dict, Any
from .protocols import Plan, TaskItem
from ..core.llm import client
from ..core.config import runtime
from ..utils.json_utils import extract_json
from ..core.logger import info, warn

SYSTEM = (
  "你是Project Planning Agent。你接收一个软件开发高层目标，输出严格JSON，键为 tasks: TaskItem[]。"
  "TaskItem包含: "
  "id(短小唯一字符串), "
  "desc(可执行开发任务，带文件路径/语言/框架等具体信息), "
  "deps(前置任务id列表), "
  "target_files(该任务需要创建/修改的文件路径列表), "
  "test_command(可选：用于验证该任务的命令或断言，如 py_compile:... / assert_contains:... / assert_exists:...)。"
  "务必细化为可直接由代码代理实现的任务，避免含糊。"
)

PROMPT_TMPL = (
    "目标: \n{goal}\n\n"
    "严格遵循以下Test Case约束：\n"
    "- 所有生成路径必须位于 {prefix}arxiv_cs_daily/ 下（与源码隔离）。\n"
    "- 必须产出以下关键文件：\n"
    "  1) {prefix}arxiv_cs_daily/index.html（含按arXiv CS领域导航：cs.AI/cs.CV/cs.LG/cs.CL/cs.RO/cs.NE/cs.IR/cs.DB/cs.DS/cs.SE/cs.DL/cs.SY/cs.TH）\n"
    "  2) {prefix}arxiv_cs_daily/assets/style.css\n"
    "  3) {prefix}arxiv_cs_daily/src/fetch_arxiv.py（从RSS抓取每日论文）\n"
    "  4) {prefix}arxiv_cs_daily/src/build_site.py（生成每日列表与详情页，详情页需含PDF链接、元数据、BibTeX与一键复制）\n"
    "- 在 index.html 中需包含占位容器：<div id=\"daily-container\">...</div>，build_site.py 负责将每日列表注入此处。\n"
    "- 任务需细化为可直接由代码代理实现的开发任务（明确具体路径与文件内容主题），并声明依赖顺序。\n"
    "仅返回JSON，例如: {{\"tasks\":[{{\"id\":\"t1\",\"desc\":\"创建 {prefix}arxiv_cs_daily/index.html\",\"deps\":[]}}]}}"
)


def create_plan(goal: str) -> Plan:
    prefix = f"{runtime.output_dir}/"
    msg = PROMPT_TMPL.format(goal=goal, prefix=prefix)
    data = client.simple_text(msg, system=SYSTEM)
    try:
        obj = extract_json(data)
        tasks = [TaskItem(**t) for t in obj.get("tasks", [])]
        info(f"规划生成 {len(tasks)} 个任务")
        return Plan(tasks=tasks)
    except Exception as e:
        warn(f"规划解析失败，回退默认计划: {e}")
        fallback = Plan(tasks=[
            TaskItem(id="init", desc="创建项目目录 project/ 与 README 占位", deps=[]),
        ])
        return fallback

