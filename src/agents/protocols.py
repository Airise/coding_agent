from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskItem(BaseModel):
    id: str
    desc: str
    deps: List[str] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    test_command: str = ""


class Plan(BaseModel):
    tasks: List[TaskItem]


class CodeChange(BaseModel):
    path: str
    content: Optional[str] = None
    overwrite: bool = True


class CommandSpec(BaseModel):
    cmd: str
    cwd: Optional[str] = None


class CoderOutput(BaseModel):
    changes: List[CodeChange] = Field(default_factory=list)
    commands: List[CommandSpec] = Field(default_factory=list)
    notes: str = ""


class EvalIssue(BaseModel):
    severity: str  # info|warn|error
    file: Optional[str] = None
    message: str


class EvalResult(BaseModel):
    success: bool
    issues: List[EvalIssue] = Field(default_factory=list)
    suggestions: str = ""


class OrchestratorState(BaseModel):
    goal: str
    plan: Optional[Plan] = None
    completed_tasks: List[str] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 5
