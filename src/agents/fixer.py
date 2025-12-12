from __future__ import annotations
from pathlib import Path
from typing import Optional

from .protocols import CodeChange, CoderOutput
from ..core.llm import client
from ..core.logger import info, warn
from ..core.config import runtime
from ..tools import fs

SYSTEM = (
    "You are a Code Fixer Agent. You will be given a file path, its current content, and the exact error logs (e.g., SyntaxError, ImportError, NameError, or 'Assertion failed: script produced no output'). "
    "Your task is to analyze the error and generate the complete, corrected, and pure code for the file. "
    "For an ImportError, check if the function/class name is misspelled and correct it. "
    "If the error is 'Assertion failed' or indicates the script ran without doing anything, you MUST add a main execution block (e.g., `if __name__ == '__main__': main()`) to call the core functions. "
    "Output ONLY the raw code. Do not include any explanation, comments, or markdown fences (e.g., ```python)."
)

PROMPT_TMPL = (
    "Project Goal:\n{goal}\n\n"
    "Your task is to fix the file `{path}` to be valid and runnable.\n\n"
    "{fix_instruction}\n\n"
    "Current content of `{path}` (may be empty if file is missing):\n---\n{content}\n---\n\n"
    "Error logs to fix:\n{error}\n\n"
    "Now, generate the complete and corrected code for the file `{path}`."
)

def apply_fixer_output(out: CoderOutput) -> None:
    # Simplified apply logic, as Fixer now only produces one change.
    if not out.changes:
        warn("Fixer did not produce any changes.")
        return

    ch = out.changes[0]
    if ch.content is None:
        warn(f"Skipping write (no content): {ch.path}")
        return

    path_norm = ch.path.replace("\\", "/").lstrip("/")
    prefix = f"{runtime.output_dir}/"
    if not path_norm.startswith(prefix):
        path_norm = prefix + path_norm
    
    fs.write_file(path_norm, ch.content, overwrite=True)

def fix_file(goal: str, path: str, error_message: str, minimal_fix: bool = False) -> bool:
    p = Path(runtime.workspace_root) / path
    try:
        current_content = p.read_text(encoding="utf-8") if p.exists() else ""
    except Exception:
        current_content = ""

    fix_instruction = (
        "IMPORTANT: The file is too long and causes issues. Return a minimal, runnable skeleton version of the file, NOT the full content. "
        "For HTML, just the basic structure with placeholders. For Python, just import statements and empty functions/classes."
        if minimal_fix
        else "Provide the full, corrected content for the file."
    )

    prompt = PROMPT_TMPL.format(
        goal=goal, 
        path=path, 
        content=current_content, 
        error=error_message, 
        fix_instruction=fix_instruction
    )
    
    fixed_code = client.simple_text(prompt, system=SYSTEM)

    if not fixed_code or fixed_code.isspace():
        warn(f"Fixer returned empty content for {path}. Skipping.")
        return False

    # Manually construct the CoderOutput, ensuring no JSON parsing is needed.
    change = CodeChange(path=path, content=fixed_code, overwrite=True)
    out = CoderOutput(changes=[change], commands=[])
    
    apply_fixer_output(out)
    info(f"Fixer applied changes to: {path}")
    return True
