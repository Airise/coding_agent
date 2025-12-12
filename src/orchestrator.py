from __future__ import annotations
from typing import Dict, List
from .agents.protocols import OrchestratorState, TaskItem, Plan
from .agents import planner, coder
from .agents import fixer as fixer_agent
from .agents import tester
from .core.logger import info, warn
from .core.config import runtime

def topo_order(tasks: List[TaskItem]) -> List[str]:
    return [t.id for t in tasks]

def make_phased_plan() -> Plan:
    prefix = f"{runtime.output_dir}/arxiv_cs_daily"
    tasks = [
        TaskItem(
            id="phase-html-css",
            desc=f"Create `{prefix}/index.html` and `{prefix}/assets/style.css`.",
            target_files=[f"{prefix}/index.html", f"{prefix}/assets/style.css"],
        ),
        TaskItem(
            id="phase-js-logic",
            desc=f"Add JavaScript to `{prefix}/index.html` for client-side category filtering. The script should handle clicks on navigation links.",
            target_files=[f"{prefix}/index.html"],
            test_command=f"assert_contains:{prefix}/index.html:addEventListener"
        ),
        TaskItem(
            id="phase-fetcher",
            desc=f"Create `{prefix}/src/fetch_arxiv.py`.",
            target_files=[f"{prefix}/src/fetch_arxiv.py"],
            test_command=f"py_compile:{prefix}/src/fetch_arxiv.py"
        ),
        TaskItem(
            id="phase-builder",
            desc=f"Create `{prefix}/src/build_site.py`. The script MUST create the `{prefix}/papers` directory.",
            target_files=[f"{prefix}/src/build_site.py"],
            test_command=f"py_compile:{prefix}/src/build_site.py"
        ),
    ]
    return Plan(tasks=tasks)

class Orchestrator:
    def __init__(self, phased: bool = False, auto_fix: bool = False):
        self.state = OrchestratorState(goal="", iteration=0, max_iterations=3)
        self.phased = phased
        self.auto_fix = auto_fix

    def _test_and_fix(self, goal: str, file_to_test: str, test_command: str, max_rounds: int = 2) -> bool:
        for i in range(max_rounds):
            success, output = tester.run_test(test_command)
            if success:
                info(f"Test passed for {file_to_test}.")
                return True
            
            warn(f"Test failed for {file_to_test} (Round {i+1}/{max_rounds}). Error:\n{output}")
            fixer_agent.fix_file(goal, file_to_test, output, minimal_fix=(i == max_rounds - 1))
        
        success, final_output = tester.run_test(test_command)
        if not success:
            warn(f"Auto-fix failed for {file_to_test} after {max_rounds} rounds. Final error:\n{final_output}")
        return success

    def run(self, goal: str) -> OrchestratorState:
        self.state.goal = goal
        plan = make_phased_plan() if self.phased else planner.create_plan(goal)
        self.state.plan = plan
        order = topo_order(plan.tasks)
        info(f"Executing plan: {len(order)} tasks in order: {order}")

        for tid in order:
            t = next((task for task in plan.tasks if task.id == tid), None)
            if not t: continue

            info(f"--- Running Task: {tid} ---")
            
            info("Stage 1: Generating skeleton...")
            coder.implement(goal, t.desc, mode="skeleton")

            if self.auto_fix and t.test_command:
                self._test_and_fix(goal, t.target_files[0], t.test_command)

            info("Stage 2: Generating full implementation...")
            fill_desc = f"The skeleton for task '{t.desc}' has been created. Now, read the skeleton file(s) and fill in the complete implementation logic."
            coder.implement(goal, fill_desc, mode="full")

            if self.auto_fix and t.test_command:
                if not self._test_and_fix(goal, t.target_files[0], t.test_command):
                    warn(f"Final implementation for {t.target_files[0]} is still invalid.")

            self.state.completed_tasks.append(tid)

        info("--- Final Build and Test ---")
        build_script_path = f"{runtime.output_dir}/arxiv_cs_daily/src/build_site.py"
        papers_dir_path = f"{runtime.output_dir}/arxiv_cs_daily/papers"
        build_command = f"run_and_assert_file:py -3.12 {build_script_path}:{papers_dir_path}"
        
        success, output = tester.run_test(build_command)
        if not success:
            warn(f"Final build script failed to run or did not produce expected artifacts. Error:\n{output}")
            if self.auto_fix:
                info("Attempting to fix the build script based on functional test failure...")
                self._test_and_fix(goal, build_script_path, build_command)

        info("Orchestration finished. Please check the output in the 'project' directory.")
        return self.state
