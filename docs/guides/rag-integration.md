# RAG Architecture Integration Guide

This document explains how to use the new dual-layer RAG system with programme detection, alias resolution, and deterministic routing.

## Quick Start

### 1. Build Indices

```python
from app.rag.indexer import build_or_load_structure_index, build_or_load_details_index

# Build/load programme structure index
structure_index, structure_metas = build_or_load_structure_index()

# Build/load subject details index
details_index, details_metas = build_or_load_details_index()
```

### 2. Process a Query

```python
from app.advisor.alias_resolver import resolve_aliases
from app.advisor.programme_detection import detect_programme
from app.advisor.session_manager import get_session_manager
from app.rag.query_router import route_query
from app.rag.retriever import search_structure_layer, search_details_layer

# Initialize session
session_manager = get_session_manager()
session = session_manager.get_session("user_session_123")

# User query
query = "What subjects are in Year 2 Trimester 1 and what is AI ethics about?"

# Step 1: Detect programme
detection = detect_programme(query, session_manager.get_context(session.session_id))
if detection.programme and detection.confidence > 0.7:
    session_manager.set_programme(session.session_id, detection.programme)

# Step 2: Route query
route = route_query(query, session)

# Step 3: Resolve aliases if needed
resolved_courses = []
if route.requires_course_code and not route.detected_course_codes:
    resolved = resolve_aliases(query, session.programme)
    resolved_courses = [r['course_code'] for r in resolved]
else:
    resolved_courses = route.detected_course_codes

# Step 4: Search appropriate layer(s)
results = []

if route.should_query_structure:
    structure_results = search_structure_layer(
        structure_index, 
        structure_metas, 
        query,
        programme=session.programme
    )
    results.extend(structure_results)

if route.should_query_details and resolved_courses:
    details_results = search_details_layer(
        details_index,
        details_metas,
        query,
        course_codes=resolved_courses
    )
    results.extend(details_results)

# Step 5: Build response
for result in results:
    print(f"Layer: {result['layer']}")
    print(f"Score: {result['score']}")
    print(f"Text: {result['text'][:200]}...")
    print("---")
```

## Example Queries

### Structure Query
```python
query = "What courses are in Year 2 Trimester 1?"
# Routes to: structure layer only
# No course code needed
```

### Details Query with Explicit Code
```python
query = "Tell me about ACE6313"
# Routes to: details layer
# Course code: ACE6313 (detected)
```

### Details Query with Alias
```python
query = "What is machine learning about?"
# Routes to: details layer
# Alias "machine learning" → ACE6313
```

### Mixed Query
```python
query = "What subjects in Year 3 and what is deep learning?"
# Routes to: both layers
# Structure: Year 3 courses
# Details: "deep learning" → ACE6323
```

## Hallucination Prevention

The system enforces strict rules:

1. **No subject details without course code**
   ```python
   # This will NOT access details layer
   query = "Tell me about some course"
   # Reason: No course code detected or resolved
   ```

2. **Structure first for planning**
   ```python
   # This queries structure layer first
   query = "When can I take Project I?"
   # Returns: Eligibility rules from structure layer
   ```

3. **Programme filtering**
   ```python
   # Only returns Applied AI courses
   session.programme = "Applied AI"
   query = "What's in Year 3?"
   # Filters: Applied AI Year 3 courses only
   ```

## Session Management

```python
from app.advisor.session_manager import get_session_manager

manager = get_session_manager()
session = manager.get_session("user_123")

# Set programme
manager.set_programme("user_123", "Applied AI")

# Set current term
manager.set_current_term("user_123", "Year2_T1")

# Add to history
manager.add_to_history("user_123", "user", "What's in Year 2?")
manager.add_to_history("user_123", "assistant", "Year 2 Trimester 1 courses are...")

# Get context for detection
context = manager.get_context("user_123")
```

## Alias Resolution

```python
from app.advisor.alias_resolver import resolve_aliases

# Resolve natural language
resolved = resolve_aliases("machine learning and deep learning", "Applied AI")

for course in resolved:
    print(f"{course['matched_pattern']} → {course['course_code']} ({course['course_name']})")

# Output:
# machine learning → ACE6313 (Machine Learning Fundamentals)
# deep learning → ACE6323 (Deep Learning)
```

## Programme Detection

```python
from app.advisor.programme_detection import detect_programme

# High confidence (course code)
result = detect_programme("Tell me about ACE6313")
# programme: Applied AI, confidence: 0.95

# Medium confidence (keywords)
result = detect_programme("I want to learn about robots and drones")
# programme: Intelligent Robotics, confidence: 0.70

# With context
context = {'programme': 'Applied AI', 'history': [...]}
result = detect_programme("What's in Year 3?", context)
# programme: Applied AI, confidence: 0.95 (from context)
```

## Query Routing

```python
from app.rag.query_router import route_query

# Structure query
route = route_query("What subjects in Year 2?")
# query_type: STRUCTURE_ONLY
# target_layer: STRUCTURE
# requires_course_code: False

# Details query
route = route_query("What is ACE6313 about?")
# query_type: DETAILS_ONLY
# target_layer: DETAILS
# requires_course_code: True
# detected_course_codes: ['ACE6313']

# Mixed query
route = route_query("What's in Year 3 and what is AI ethics?")
# query_type: MIXED
# target_layer: BOTH
```

## Integration with Chat API

See `app/api/chat.py` for full integration example. Key points:

1. Initialize indices at startup
2. Get/create session for each request
3. Detect programme if not set
4. Route query to appropriate layer(s)
5. Resolve aliases as needed
6. Search with proper filters
7. Update session state

## Testing

```bash
# Test alias resolution
python -c "from app.advisor.alias_resolver import resolve_aliases; print(resolve_aliases('machine learning'))"

# Test programme detection
python -c "from app.advisor.programme_detection import detect_programme; print(detect_programme('Tell me about ACE6313'))"

# Test query routing
python -c "from app.rag.query_router import route_query; print(route_query('What subjects in Year 2?'))"
```

## Troubleshooting

### Issue: Empty results from details layer
**Cause**: No course code provided
**Solution**: Ensure alias resolution or explicit course code

### Issue: Wrong programme courses returned
**Cause**: Programme not set in session
**Solution**: Detect and set programme first

### Issue: Structure queries returning details
**Cause**: Query routing misconfigured
**Solution**: Check `rules.yaml` patterns

## Next Steps

1. Populate `faie_ai_robotics_combined_qa.jsonl` with full 1270 Q&A pairs
2. Expand `alias_mapping.yaml` with more natural language patterns
3. Add more programme structure rules to `programme_structure.jsonl`
4. Integrate with chat API
5. Add logging and monitoring
