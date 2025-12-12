from __future__ import annotations
from typing import List
from pathlib import Path
from .protocols import EvalIssue, EvalResult
from ..core.logger import info, warn
from ..core.config import runtime


class BaseAcceptance:
    def evaluate(self, goal: str) -> EvalResult:
        return EvalResult(success=True, issues=[], suggestions="")


class ArxivDailyAcceptance(BaseAcceptance):
    base = Path(runtime.workspace_root) / runtime.output_dir / "arxiv_cs_daily"

    def evaluate(self, goal: str) -> EvalResult:
        issues: List[EvalIssue] = []
        # 关键文件
        expected = [
            self.base / "index.html",
            self.base / "assets" / "style.css",
            self.base / "src" / "fetch_arxiv.py",
            self.base / "src" / "build_site.py",
        ]
        for p in expected:
            if not p.exists():
                issues.append(EvalIssue(severity="error", file=str(p), message="缺少必需文件"))
        success = len([i for i in issues if i.severity == "error"]) == 0
        suggestions = "确保包含主页、样式表与数据抓取/构建脚本；主页需有按领域导航、每日论文列表、详情页链接。"
        return EvalResult(success=success, issues=issues, suggestions=suggestions)


def get_acceptance(goal: str) -> BaseAcceptance:
    g = goal.lower()
    if "arxiv" in g and "daily" in g:
        return ArxivDailyAcceptance()
    return BaseAcceptance()

