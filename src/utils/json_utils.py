from __future__ import annotations
import json
import re
from typing import Any

def extract_json(text: str) -> Any:
    """
    A simple JSON extractor. It finds the first JSON object within a string.
    It supports ```json ... ``` code fences.
    Since LLMs no longer generate complex JSON with code, this is kept minimal.
    """
    if not text:
        raise ValueError("Cannot parse JSON from empty string.")

    # For ```json ... ``` code fences
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        text = match.group(1)

    # Find the first '{' and the last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = text[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON: {e}\nSubstring: {json_str[:200]}...") from e

    raise ValueError("No valid JSON object found in the text.")
