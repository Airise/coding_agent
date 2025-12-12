from __future__ import annotations
import argparse
from pathlib import Path
from .orchestrator import Orchestrator
from .core.logger import info, success, warn

DEFAULT_GOAL_FILE = "prompts/arxiv_cs_daily_testcase_en.txt"
PRESET_FILES = {
    "skeleton": "prompts/arxiv_cs_daily_skeleton_en.txt",
    "fetcher": "prompts/arxiv_cs_daily_fetcher_en.txt",
    "builder": "prompts/arxiv_cs_daily_builder_en.txt",
}
DEFAULT_FALLBACK_GOAL = (
    "Build an 'arXiv CS Daily' website with domain navigation, daily paper list, and a paper detail page "
    "(PDF link, metadata, BibTeX with one-click copy). All outputs must be placed under project/arxiv_cs_daily. "
    "No heavy JS scaffolding."
)


def load_text_file(path: Path) -> str | None:
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8").strip()
            return text if text else None
    except Exception as e:
        warn(f"读取目标文件失败：{e}")
    return None


def resolve_goal(positional_goal: str | None, goal_file: str | None, preset: str | None) -> str:
    # 优先级：命令行 goal > goal-file > preset > 默认 Test Case
    if positional_goal:
        return positional_goal

    # goal-file
    if goal_file:
        gf = Path(goal_file)
        text = load_text_file(gf)
        if text:
            info(f"已从文件读取目标: {gf}")
            return text
        else:
            warn(f"指定的目标文件不可用：{gf}，将尝试 preset/默认")

    # preset（可选使用；如未指定则忽略）
    if preset:
        pf = PRESET_FILES.get(preset)
        if pf:
            text = load_text_file(Path(pf))
            if text:
                info(f"已从预设加载目标: {preset} -> {pf}")
                return text
            else:
                warn(f"预设文件不可用：{pf}，将回退默认 Test Case")
        else:
            warn(f"未知预设：{preset}，将回退默认 Test Case")

    # 默认 Test Case 文件
    text = load_text_file(Path(DEFAULT_GOAL_FILE))
    if text:
        info(f"已从默认 Test Case 读取目标: {DEFAULT_GOAL_FILE}")
        return text

    warn("未找到可用目标，使用内置默认目标。")
    return DEFAULT_FALLBACK_GOAL


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent 编排器：从自然语言自动完成开发任务")
    parser.add_argument("goal", nargs="?", default=None, help="高层自然语言目标（若提供，将覆盖其它来源）")
    parser.add_argument("--goal-file", "-f", default=None, help="从文件读取目标（高优先级于 preset）")
    parser.add_argument("--preset", choices=["skeleton", "fetcher", "builder"], default=None,
                        help="使用内置预设指令（skeleton/fetcher/builder），便于分步由 LLM 生成（可选）")
    parser.add_argument("--phased", action="store_true", help="启用编排分步模式（skeleton → fetcher → builder）")
    parser.add_argument("--auto-fix", action="store_true", help="启用自我纠错（阶段后运行校验与 Fixer 自动重写，最多2轮）")
    args = parser.parse_args()

    goal = resolve_goal(args.goal, args.goal_file, args.preset)
    orch = Orchestrator(phased=args.phased, auto_fix=args.auto_fix)
    state = orch.run(goal)
    success(f"完成。已执行任务: {len(state.completed_tasks)}，迭代次数: {state.iteration}")


if __name__ == "__main__":
    main()
