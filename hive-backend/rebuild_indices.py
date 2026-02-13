"""
Rebuild FAISS indices with new knowledge base data.
"""
import sys
sys.path.insert(0, '.')

from app.rag.indexer import (
    build_or_load_structure_index,
    build_or_load_details_index,
    build_or_load_global_index
)

print("🔄 Rebuilding FAISS indices with new knowledge base...")
print()

# Rebuild structure index (programme structure)
print("1️⃣ Building structure index...")
try:
    structure_idx, structure_metas = build_or_load_structure_index()
    print(f"   ✅ Structure index: {structure_idx.ntotal} vectors, {len(structure_metas)} metadata entries")
except Exception as e:
    print(f"   ⚠️  Structure index failed: {e}")
    print(f"   Note: This is OK if you don't have programme_structure.jsonl yet")

print()

# Rebuild details index (course Q&A)
print("2️⃣ Building details index...")
try:
    details_idx, details_metas = build_or_load_details_index()
    print(f"   ✅ Details index: {details_idx.ntotal} vectors, {len(details_metas)} metadata entries")
except Exception as e:
    print(f"   ❌ Details index failed: {e}")
    sys.exit(1)

print()

# Rebuild global index (general docs)
print("3️⃣ Building global index...")
try:
    global_idx, global_metas = build_or_load_global_index()
    print(f"   ✅ Global index: {global_idx.ntotal} vectors, {len(global_metas)} metadata entries")
except Exception as e:
    print(f"   ⚠️  Global index failed: {e}")
    print(f"   Note: This is OK if you don't have global docs")

print()
print("✅ Index rebuild complete!")
print()
print("Summary:")
print(f"  - Structure layer: {structure_idx.ntotal if 'structure_idx' in locals() else 0} vectors")
print(f"  - Details layer: {details_idx.ntotal if 'details_idx' in locals() else 0} vectors")
print(f"  - Global docs: {global_idx.ntotal if 'global_idx' in locals() else 0} vectors")
