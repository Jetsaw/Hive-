import json
from pathlib import Path

from app.preprocess.extractors import (
    extract_course_blocks_from_syllabus_pdf,
    extract_plan_from_structure_pdf,
)

def build_prereq_graph(course_catalog: dict) -> dict:
    graph = {}
    for code, obj in course_catalog.items():
        for prereq in obj.get("prereq", []):
            graph.setdefault(prereq, [])
            if code not in graph[prereq]:
                graph[prereq].append(code)
    # sort lists
    for k in graph:
        graph[k] = sorted(graph[k])
    return graph

def main():
    base = Path("./data")
    kb_dir = base / "kb"
    kb_dir.mkdir(parents=True, exist_ok=True)

    # Your preloaded PDFs (place in data/global_docs/)
    syllabus_pdf = base / "global_docs" / "mmu faie all course.pdf"
    structure_pdf = base / "global_docs" / "BSc-October-2025-T2530.pdf"

    if not syllabus_pdf.exists():
        raise FileNotFoundError(f"Missing: {syllabus_pdf}")
    if not structure_pdf.exists():
        raise FileNotFoundError(f"Missing: {structure_pdf}")

    course_catalog = extract_course_blocks_from_syllabus_pdf(str(syllabus_pdf))
    programme_plan = {
        "Intelligent Robotics": extract_plan_from_structure_pdf(str(structure_pdf))
    }
    prereq_graph = build_prereq_graph(course_catalog)

    (kb_dir / "course_catalog.json").write_text(json.dumps(course_catalog, indent=2), encoding="utf-8")
    (kb_dir / "programme_plan.json").write_text(json.dumps(programme_plan, indent=2), encoding="utf-8")
    (kb_dir / "prereq_graph.json").write_text(json.dumps(prereq_graph, indent=2), encoding="utf-8")

    print(" KB built:")
    print(" - data/kb/course_catalog.json")
    print(" - data/kb/programme_plan.json")
    print(" - data/kb/prereq_graph.json")
    print(f"Courses extracted: {len(course_catalog)}")
    print(f"Plan buckets: {len(programme_plan['Intelligent Robotics'])}")

if __name__ == "__main__":
    main()
