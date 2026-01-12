from pydantic import BaseModel
from typing import List, Optional

class EligibilityResult(BaseModel):
    course: str
    allowed: bool
    missing_prereq: List[str] = []
    reason: str
    suggested_alternatives: List[str] = []

class PlanResult(BaseModel):
    trimester: str
    recommended: List[str]
    blocked: List[str]
    notes: List[str]
