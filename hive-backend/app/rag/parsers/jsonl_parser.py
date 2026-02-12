import json
from typing import Iterator, Tuple, Dict


def extract_jsonl(path: str) -> Iterator[Tuple[str, Dict]]:
    """
    Parse JSONL file and yield (text, metadata) tuples.
    
    Expected format: {"text": "...", "metadata": {...}}
    If no "text" field, uses entire JSON as text.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON at line {line_no} in {path}: {e}")
                continue
            
            # Extract text field
            if isinstance(obj, dict) and "text" in obj:
                text = obj["text"]
                metadata = obj.get("metadata", {})
            else:
                # Fallback: use entire JSON dump as text
                text = json.dumps(obj, ensure_ascii=False)
                metadata = {}
            
            # Ensure metadata is a dict
            if not isinstance(metadata, dict):
                metadata = {}
            
            yield text, metadata
