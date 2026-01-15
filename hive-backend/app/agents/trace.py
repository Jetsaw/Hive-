from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class TraceEntry:
    name: str
    input: dict[str, Any]
    output: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class Trace:
    request_id: str = field(default_factory=lambda: uuid4().hex)
    entries: list[TraceEntry] = field(default_factory=list)

    def add(
        self,
        name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = TraceEntry(
            name=name,
            input=input_data,
            output=output_data,
            metadata=metadata or {},
        )
        self.entries.append(entry)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "entries": [
                {
                    "name": entry.name,
                    "input": entry.input,
                    "output": entry.output,
                    "metadata": entry.metadata,
                    "timestamp": entry.timestamp,
                }
                for entry in self.entries
            ],
        }
