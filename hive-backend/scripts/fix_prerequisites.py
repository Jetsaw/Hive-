"""
Fix course catalog prerequisites - remove self-referencing prerequisites
"""
import json
from pathlib import Path

# Load course catalog
catalog_path = Path("./data/kb/course_catalog.json")
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

# Fix self-referencing prerequisites
fixed_count = 0
for code, course in catalog.items():
    prereqs = course.get("prereq", [])
    
    # Remove self-references
    if code in prereqs:
        prereqs.remove(code)
        fixed_count += 1
        print(f"Fixed {code}: removed self-reference")
    
    # Update course
    course["prereq"] = prereqs

# Save fixed catalog
catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n✅ Fixed {fixed_count} courses with self-referencing prerequisites")
print(f"📝 Saved to {catalog_path}")
