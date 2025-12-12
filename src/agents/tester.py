from __future__ import annotations
from typing import Tuple
import py_compile
from pathlib import Path

from ..tools import shell
from ..core.config import runtime


def run_test(test_command: str) -> Tuple[bool, str]:
    """
    Runs a test command and returns a tuple of (success, output).
    Supports special command prefixes like 'py_compile:', 'run_and_assert:', 'run_and_assert_file:', and 'assert_contains:'.
    """
    if not test_command:
        return True, "No test command provided."

    # Syntax check via py_compile
    if test_command.startswith("py_compile:"):
        file_path_str = test_command.replace("py_compile:", "").strip()
        file_path = Path(runtime.workspace_root) / file_path_str
        if not file_path.exists():
            return False, f"Compilation failed: File not found at {file_path}"
        try:
            py_compile.compile(str(file_path), doraise=True)
            return True, f"Compilation successful for {file_path}"
        except py_compile.PyCompileError as e:
            error_details = f"Syntax Error: {e.msg}"
            if hasattr(e, 'lineno') and e.lineno:
                error_details += f" on line {e.lineno}"
            if hasattr(e, 'text') and e.text:
                error_details += f"\n> {e.text.strip()}"
            return False, error_details
        except Exception as e:
            return False, f"Unknown compilation error: {e}"

    # Run command and assert that stdout contains a specific string
    if test_command.startswith("run_and_assert:"):
        parts = test_command.replace("run_and_assert:", "").split(":", 1)
        if len(parts) != 2:
            return False, "Invalid format for run_and_assert."
        command, expected_string = parts
        return_code, stdout, stderr = shell.run(command)
        output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        if return_code != 0:
            return False, f"Command failed with exit code {return_code}.\n{output}"
        if expected_string not in stdout:
            return False, f"Assertion failed: Expected string '{expected_string}' not found in stdout.\n{output}"
        return True, f"Assertion passed! Found '{expected_string}' in stdout."

    # Run command and assert that a file or directory is created
    if test_command.startswith("run_and_assert_file:"):
        parts = test_command.replace("run_and_assert_file:", "").split(":", 1)
        if len(parts) != 2:
            return False, "Invalid format for run_and_assert_file."
        command, expected_path_str = parts
        expected_path = Path(runtime.workspace_root) / expected_path_str
        return_code, stdout, stderr = shell.run(command)
        output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        if return_code != 0:
            return False, f"Command failed with exit code {return_code}.\n{output}"
        if not expected_path.exists():
            return False, f"Assertion failed: Expected file or directory '{expected_path}' was not created.\n{output}"
        return True, f"Assertion passed! Found created file/directory at '{expected_path}'."

    # Assert that a file contains a specific string
    if test_command.startswith("assert_contains:"):
        parts = test_command.replace("assert_contains:", "").split(":", 1)
        if len(parts) != 2:
            return False, "Invalid format for assert_contains."
        file_path_str, expected_string = parts
        file_path = Path(runtime.workspace_root) / file_path_str
        if not file_path.exists():
            return False, f"Assertion failed: File not found at {file_path}"
        try:
            content = file_path.read_text(encoding="utf-8")
            if expected_string not in content:
                return False, f"Assertion failed: Expected string '{expected_string}' not found in {file_path}."
            return True, f"Assertion passed! Found '{expected_string}' in {file_path}."
        except Exception as e:
            return False, f"Failed to read file {file_path}: {e}"

    # For all other commands, just run them via the shell
    return_code, stdout, stderr = shell.run(test_command)
    success = return_code == 0
    output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
    return success, output
