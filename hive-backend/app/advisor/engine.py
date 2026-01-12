import json
import re
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

COURSE_CODE_RE = re.compile(r"\b[A-Z]{3}\d{4}\b")

# ---------- Normalization ----------
def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------- Common student aliases ----------
ALIASES = {
    "math 1": "AMT6113",
    "math 2": "AMT6123",
    "engineering math 1": "AMT6113",
    "engineering math 2": "AMT6123",

    "data communication": "ACE6143",
    "data communications": "ACE6143",
    "networking": "ACE6143",
    "computer networking": "ACE6143",

    "industrial training": "ITT",
    "internship": "ITT",
}


# ---------- Load FAIE KB ----------
def load_faie_kb() -> Tuple[Dict, Dict, Dict]:
    """
    Returns (kb_raw, code_map, name_map)

    Priority:
    1) Try hive_kb_mmu_faie.json if it is truly course-based
    2) Otherwise fall back to data/kb/course_catalog.json (reliable)
    """
    def build_maps_from_courses(courses: List[dict]) -> Tuple[Dict[str, dict], Dict[str, str]]:
        code_map: Dict[str, dict] = {}
        name_map: Dict[str, str] = {}
        for c in courses:
            if not isinstance(c, dict):
                continue
            code = (c.get("code") or "").upper().strip()
            name = c.get("name") or c.get("course_name") or ""
            if not code or not name:
                continue
            code_map[code] = c
            name_map[_norm(name)] = code
        return code_map, name_map

    # --- 1) Try hive_kb_mmu_faie.json ---
    path = Path("data/kb/hive_kb_mmu_faie.json")
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        courses: List[dict] = []

        if isinstance(raw, list):
            courses = [c for c in raw if isinstance(c, dict)]

        elif isinstance(raw, dict):
            if "courses" in raw and isinstance(raw["courses"], list):
                courses = [c for c in raw["courses"] if isinstance(c, dict)]
            else:
                for code, val in raw.items():
                    if isinstance(val, dict):
                        c = dict(val)
                        c.setdefault("code", code)
                        courses.append(c)
                    elif isinstance(val, str):
                        courses.append({"code": code, "name": val})

        code_map, name_map = build_maps_from_courses(courses)

        # ✅ If it looks like a real catalog (many courses), use it
        if len(code_map) >= 20:
            return raw, code_map, name_map

        # Otherwise: fall through to course_catalog.json

    # --- 2) Fallback to course_catalog.json ---
    cat_path = Path("data/kb/course_catalog.json")
    catalog = json.loads(cat_path.read_text(encoding="utf-8"))

    # catalog schema: { "ACE6143": {"code": "...", "name": "...", ...}, ... }
    courses = []
    if isinstance(catalog, dict):
        for code, obj in catalog.items():
            if isinstance(obj, dict):
                c = dict(obj)
                c.setdefault("code", code)
                courses.append(c)

    code_map, name_map = build_maps_from_courses(courses)
    return catalog, code_map, name_map



# ---------- Resolve course from student text ----------
def resolve_course_from_text(
    text: str, code_map: Dict, name_map: Dict
) -> Optional[str]:
    raw = text or ""

    # 1) Explicit course code
    m = COURSE_CODE_RE.search(raw.upper())
    if m:
        code = m.group(0)
        if code in code_map:
            return code

    q = _norm(raw)
    if not q:
        return None

    # 2) Alias contains
    for k, v in ALIASES.items():
        if k in q:
            if v == "ITT":
                for nm, cc in name_map.items():
                    if "industrial training" in nm:
                        return cc
            if v in code_map:
                return v

    # 3) Exact name
    if q in name_map:
        return name_map[q]

    # 4) Token overlap scoring (BEST for "data communication")
    tokens = [t for t in q.split() if len(t) >= 3]
    best = (0, None)
    for nm, cc in name_map.items():
        score = sum(1 for t in tokens if t in nm)
        if score > best[0]:
            best = (score, cc)
    if best[0] >= 1:
        return best[1]

    # 5) Fuzzy fallback (typos)
    names = list(name_map.keys())
    hit = difflib.get_close_matches(q, names, n=1, cutoff=0.72)
    if hit:
        return name_map[hit[0]]

    return None



def resolve_course_mentions(text: str, code_map: Dict, name_map: Dict) -> List[str]:
    t = text or ""
    nt = _norm(t)

    found: List[str] = []

    # 1) Explicit course codes
    for m in COURSE_CODE_RE.findall(t.upper()):
        if m not in found:
            found.append(m)

    # 2) Strong math alias patterns (handles math1/math 1/math2/math 2)
    alias_patterns = [
        (r"\bmath\s*1\b", "AMT6113"),
        (r"\bmath\s*2\b", "AMT6123"),
        (r"\bengineering\s*math\s*1\b", "AMT6113"),
        (r"\bengineering\s*math\s*2\b", "AMT6123"),
    ]
    for pat, code in alias_patterns:
        if re.search(pat, nt) and code not in found:
            found.append(code)

    # 3) Name substring matches (general courses)
    # longer names first
    for nm, cc in sorted(name_map.items(), key=lambda x: len(x[0]), reverse=True):
        if nm and nm in nt and cc not in found:
            found.append(cc)

    return found




# ---------- Adviser Logic (unchanged) ----------
def load_kb() -> Tuple[dict, dict, dict]:
    kb = Path("./data/kb")
    course_catalog = json.loads((kb / "course_catalog.json").read_text(encoding="utf-8"))
    programme_plan = json.loads((kb / "programme_plan.json").read_text(encoding="utf-8"))
    prereq_graph = json.loads((kb / "prereq_graph.json").read_text(encoding="utf-8"))
    return course_catalog, programme_plan, prereq_graph


def extract_course_codes(text: str) -> List[str]:
    return COURSE_CODE_RE.findall((text or "").upper())


def eligibility_check(course: str, passed: List[str], catalog: dict) -> Tuple[bool, List[str]]:
    course = course.upper()
    passed_set = set([c.upper() for c in passed])
    prereq = catalog.get(course, {}).get("prereq", [])
    missing = [p for p in prereq if p.upper() not in passed_set]
    return (len(missing) == 0), missing


def recommend_for_trimester(trimester_key: str, passed: List[str], failed: List[str], plan: dict, catalog: dict) -> dict:
    passed = [c.upper() for c in passed]
    failed = [c.upper() for c in failed]
    plan_courses = plan.get(trimester_key, [])

    recommended, blocked, notes = [], [], []

    for c in plan_courses:
        ok, missing = eligibility_check(c, passed, catalog)
        if ok and c not in passed:
            recommended.append(c)
        else:
            blocked.append(c)
            if missing:
                notes.append(f"{c} blocked (missing prereq: {', '.join(missing)})")

    for f in failed:
        if f not in recommended and f not in passed:
            for c in plan_courses:
                if f in catalog.get(c, {}).get("prereq", []):
                    recommended.insert(0, f)
                    notes.append(f"Retake recommended: {f}")
                    break

    return {"trimester": trimester_key, "recommended": recommended, "blocked": blocked, "notes": notes}


def parse_trimester(text: str) -> Optional[str]:
    t = (text or "").lower()
    year_map = {"first": "1", "second": "2", "third": "3", "fourth": "4"}
    for w, n in year_map.items():
        t = t.replace(w, n)

    patterns = [
        r"year\s*(\d)\s*(?:sem|semester)\s*(\d)",
        r"y\s*(\d)\s*s\s*(\d)",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            return f"Year{m.group(1)}_T{m.group(2)}"
    return None


def answer_fail_question(question: str, passed: List[str], failed: List[str], catalog: dict) -> str:
    codes = extract_course_codes(question)
    if not codes:
        return "Tell me the course name or code so I can check eligibility."

    target = codes[-1]
    ok, missing = eligibility_check(target, passed, catalog)

    if ok:
        return f"Yes, you can take {target}. Its prerequisites are satisfied."
    return f"No. You must complete {', '.join(missing)} before taking {target}."
