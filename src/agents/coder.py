from __future__ import annotations
import re
from typing import List, Dict, Any
from .protocols import CoderOutput, CodeChange, CommandSpec
from ..core.llm import client
from ..core.logger import info, warn
from ..core.config import runtime
from ..tools import fs, shell

SYSTEM = (
    "You are a Code Generation Agent. You generate pure code for a given file based on a task description. "
    "Output ONLY the raw code for the file. Do not include any explanation, comments, or markdown fences (e.g., ```html)."
)

PROMPT_TMPL = (
    "Project Goal:\n{goal}\n\n"
    "Your task is to generate the full content for the file: `{file_path}`.\n\n"
    "Task Description:\n{task_desc}\n\n"
    "{mode_instruction}\n\n"
    "Current file content (if any):\n---\n{current_content}\n---\n\n"
    "Now, generate the complete and updated code for the file `{file_path}`."
)

# Heuristic to find the target file path from a task description
_RE_FILE_PATH = re.compile(r"(?:create|modify|generate|write|implement|update) `?([\w\./\-_]+(?:\.py|\.html|\.css|\.js|\.json))`?", re.IGNORECASE)

def _extract_path_from_desc(desc: str) -> str | None:
    match = _RE_FILE_PATH.search(desc)
    if match:
        return match.group(1)
    return None

def apply_coder_output(out: CoderOutput) -> None:
    for ch in out.changes:
        if ch.content is None:
            warn(f"Skipping write (no content): {ch.path}")
            continue
        
        path_norm = ch.path.replace("\\", "/").lstrip("/")
        prefix = f"{runtime.output_dir}/"
        if not path_norm.startswith(prefix):
            path_norm = prefix + path_norm
        
        fs.write_file(path_norm, ch.content, overwrite=ch.overwrite)
    
    for cmd in out.commands:
        shell.run(cmd.cmd, cwd=cmd.cwd)

def implement(goal: str, task_desc: str, mode: str = "full") -> CoderOutput:
    file_path = _extract_path_from_desc(task_desc)
    if not file_path:
        warn(f"Could not extract file path from task description: {task_desc}")
        return CoderOutput()

    prefix = f"{runtime.output_dir}/"
    full_path = file_path
    if not full_path.startswith(prefix):
        full_path = prefix + full_path

    current_content = fs.read_file(full_path) or ""

    mode_instruction = ""
    if mode == "skeleton":
        mode_instruction = "IMPORTANT: Generate a minimal, runnable skeleton version of the file, NOT the full content. For Python, just import statements and empty functions/classes. For HTML, just the basic structure with placeholders."
    elif mode == "full":
        mode_instruction = "IMPORTANT: Generate the complete and final implementation based on the task description and the existing skeleton."

    msg = PROMPT_TMPL.format(
        goal=goal, 
        task_desc=task_desc, 
        file_path=file_path,
        current_content=current_content,
        mode_instruction=mode_instruction
    )
    
    generated_code = client.simple_text(msg, system=SYSTEM)
    
    # The LLM is now supposed to return pure code, so we don't parse JSON.
    # We manually construct the CoderOutput.
    change = CodeChange(path=file_path, content=generated_code, overwrite=True)
    out = CoderOutput(changes=[change], commands=[])
    
    apply_coder_output(out)
    info(f"Coder applied changes to: {file_path}")
    return out
