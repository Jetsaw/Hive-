import re
from typing import Dict, List, Tuple, Optional
from pypdf import PdfReader

COURSE_CODE_RE = re.compile(r"\b[A-Z]{3}\d{4}\b")
CREDITS_RE = re.compile(r"(?:Credit(?:s)?|Credit Hours|CH)\s*[:\-]?\s*(\d+)", re.IGNORECASE)
PREREQ_RE = re.compile(r"(?:Pre[-\s]?Requisite(?:\(s\))?|Prerequisite(?:\(s\))?)\s*[:\-]\s*(.+)", re.IGNORECASE)

def read_pdf_pages(path: str) -> List[Tuple[int, str]]:
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        pages.append((i + 1, txt))
    return pages

def normalize_spaces(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "")).strip()

def extract_course_blocks_from_syllabus_pdf(path: str) -> Dict[str, dict]:
    """
    Heuristic parser for the FAIE course syllabus PDF.
    It tries to detect course sections by course code and grab:
      - name
      - credits
      - prerequisites
    Returns { course_code: {..., source_page} }
    """
    pages = read_pdf_pages(path)

    # Join pages but keep page mapping by injecting markers
    big = []
    for pno, txt in pages:
        big.append(f"\n\n<<PAGE:{pno}>>\n{txt}")
    text = "\n".join(big)

    # Find occurrences of course codes
    matches = list(COURSE_CODE_RE.finditer(text))
    catalog: Dict[str, dict] = {}

    for idx, m in enumerate(matches):
        code = m.group(0)
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]

        # Find source page from nearest marker before start
        page_marker = text.rfind("<<PAGE:", 0, start)
        source_page = None
        if page_marker != -1:
            m2 = re.search(r"<<PAGE:(\d+)>>", text[page_marker:page_marker+30])
            if m2:
                source_page = int(m2.group(1))

        # Extract a likely course name: look at first ~3 lines after code
        lines = [normalize_spaces(x) for x in block.splitlines() if normalize_spaces(x)]
        name = None
        if lines:
            # common patterns:
            # "AMT6113 Engineering Mathematics 1"
            # or code on its own then name next
            if lines[0].startswith(code) and len(lines[0]) > len(code) + 2:
                name = lines[0].replace(code, "").strip(" -:")
            else:
                for j in range(min(5, len(lines))):
                    if code in lines[j]:
                        candidate = lines[j].replace(code, "").strip(" -:")
                        if candidate:
                            name = candidate
                            break
                if not name and len(lines) > 1:
                    name = lines[1]

        # Credits
        credits = None
        mcred = CREDITS_RE.search(block)
        if mcred:
            credits = int(mcred.group(1))

        # Prerequisites (extract all course codes in prereq line)
        prereq: List[str] = []
        mpre = PREREQ_RE.search(block)
        if mpre:
            prereq_text = mpre.group(1)
            prereq = sorted(set(COURSE_CODE_RE.findall(prereq_text.upper())))
        else:
            # Some syllabi embed prereq as codes near "Pre-Requisite"
            if "pre" in block.lower() and "requisite" in block.lower():
                # fallback: search around that phrase
                pos = block.lower().find("requisite")
                window = block[max(0, pos-200):pos+400]
                prereq = sorted(set(COURSE_CODE_RE.findall(window.upper())))

        # Basic validation: avoid overwriting real entries with empty ones
        if code not in catalog:
            catalog[code] = {
                "code": code,
                "name": name or code,
                "credits": credits,
                "prereq": prereq,
                "source": {
                    "file": path.split("/")[-1].split("\\")[-1],
                    "page": source_page
                }
            }
        else:
            # Prefer the one with name/credits/prereq populated
            old = catalog[code]
            if (old.get("name") == old["code"]) and name:
                old["name"] = name
            if old.get("credits") is None and credits is not None:
                old["credits"] = credits
            if not old.get("prereq") and prereq:
                old["prereq"] = prereq

    return catalog

def extract_plan_from_structure_pdf(path: str) -> Dict[str, List[str]]:
    """
    Heuristic parser for programme structure PDF.
    We extract trimester buckets based on headings like Year/Trimester and collect course codes under them.
    Output: { "Year1_T1": [...], "Year1_T2": [...], ... }
    """
    pages = read_pdf_pages(path)
    full_text = "\n".join([t for _, t in pages])
    lines = [normalize_spaces(x) for x in full_text.splitlines()]
    lines = [x for x in lines if x]

    # Accept many heading variants
    year_re = re.compile(r"\bYear\s*(\d)\b", re.IGNORECASE)
    tri_re = re.compile(r"\bTrimester\s*(\d)\b", re.IGNORECASE)

    plan: Dict[str, List[str]] = {}
    cur_key: Optional[str] = None
    cur_year: Optional[str] = None
    cur_tri: Optional[str] = None

    def set_bucket(y: str, t: str):
        nonlocal cur_key, cur_year, cur_tri
        cur_year, cur_tri = y, t
        cur_key = f"Year{y}_T{t}"
        plan.setdefault(cur_key, [])

    # Strategy:
    # when we see Year X -> remember
    # when we see Trimester Y -> bucket = YearX_TY
    # add any course codes found in nearby lines until next trimester/year
    for line in lines:
        ym = year_re.search(line)
        tm = tri_re.search(line)

        if ym:
            cur_year = ym.group(1)
            # don't create key until trimester appears

        if tm and cur_year:
            set_bucket(cur_year, tm.group(1))
            continue

        if cur_key:
            codes = COURSE_CODE_RE.findall(line.upper())
            if codes:
                for c in codes:
                    if c not in plan[cur_key]:
                        plan[cur_key].append(c)

    # remove empty buckets
    plan = {k:v for k,v in plan.items() if v}
    return plan
