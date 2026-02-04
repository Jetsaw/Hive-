"""
Year Level and Programme Filtering Utilities
Provides context-aware filtering for course recommendations
"""

import re
from typing import Optional, List, Dict, Any


def parse_year_level(query: str) -> Optional[str]:
    """
    Extract year level from natural language query.
    
    Args:
        query: User's natural language query
        
    Returns:
        Year level identifier (year_1, year_2, etc.) or None
    """
    year_patterns = {
        r"\bfirst year\b|\byear 1\b|\by1\b": "year_1",
        r"\bsecond year\b|\byear 2\b|\by2\b": "year_2",
        r"\bthird year\b|\byear 3\b|\by3\b": "year_3",
        r"\bfinal year\b|\byear 4\b|\by4\b|\bfyp\b": "year_4",
        r"\by1s1\b|\byear 1 semester 1\b": "year_1_sem_1",
        r"\by1s2\b|\byear 1 semester 2\b": "year_1_sem_2",
        r"\by2s1\b|\byear 2 semester 1\b": "year_2_sem_1",
        r"\by2s2\b|\byear 2 semester 2\b": "year_2_sem_2",
        r"\by3s1\b|\byear 3 semester 1\b": "year_3_sem_1",
        r"\by3s2\b|\byear 3 semester 2\b": "year_3_sem_2",
        r"\by4s1\b|\byear 4 semester 1\b": "year_4_sem_1",
        r"\by4s2\b|\byear 4 semester 2\b": "year_4_sem_2",
    }
    
    query_lower = query.lower()
    for pattern, level in year_patterns.items():
        if re.search(pattern, query_lower):
            print(f"[YEAR FILTER] Detected year level: {level} from query: {query}")
            return level
    
    return None


def filter_by_programme(results: List[Dict[str, Any]], programme: str) -> List[Dict[str, Any]]:
    """
    Filter RAG results to match user's programme.
    
    Args:
        results: List of RAG retrieval results
        programme: User's programme (e.g., "INTELLIGENT_ROBOTICS")
        
    Returns:
        Filtered results matching the programme
    """
    if not programme or not results:
        return results
    
    # Normalize programme name for matching
    programme_normalized = str(programme).upper().replace(' ', '_')
    
    filtered = []
    for result in results:
        # Check metadata for programme information
        metadata = result.get('metadata', {})
        
        # Check if this result is associated with the programme
        if 'programmes' in metadata:
            result_programmes = metadata['programmes']
            if isinstance(result_programmes, str):
                result_programmes = [result_programmes]
            
            # Check if user's programme matches
            for prog in result_programmes:
                prog_normalized = str(prog).upper().replace(' ', '_')
                if programme_normalized in prog_normalized or prog_normalized in programme_normalized:
                    filtered.append(result)
                    break
        elif 'programme' in metadata:
            # Single programme field
            prog_normalized = str(metadata['programme']).upper().replace(' ', '_')
            if programme_normalized in prog_normalized or prog_normalized in programme_normalized:
                filtered.append(result)
        else:
            # No programme metadata - include by default
            filtered.append(result)
    
    # If filtering removed everything, return original results as fallback
    if not filtered:
        print(f"[PROG FILTER] No results matched programme {programme}, using all results")
        return results
    
    print(f"[PROG FILTER] Filtered from {len(results)} to {len(filtered)} results for programme {programme}")
    return filtered


def filter_by_year_level(results: List[Dict[str, Any]], year_level: str) -> List[Dict[str, Any]]:
    """
    Filter RAG results by academic year level.
    
    Args:
        results: List of RAG retrieval results
        year_level: Year level identifier (e.g., "year_1", "year_1_sem_1")
        
    Returns:
        Filtered results matching the year level
    """
    if not year_level or not results:
        return results
    
    # Extract base year (year_1, year_2, etc.)
    base_year = year_level.split('_sem')[0] if '_sem' in year_level else year_level
    
    filtered = []
    for result in results:
        metadata = result.get('metadata', {})
        
        # Check for year information in metadata
        result_year = metadata.get('year') or metadata.get('year_level') or metadata.get('level')
        
        if result_year:
            result_year_str = str(result_year).lower()
            # Match exact year or semester
            if year_level in result_year_str or base_year in result_year_str:
                filtered.append(result)
        else:
            # If no year metadata, include by default
            filtered.append(result)
    
    # Fallback to original if filtering removed everything
    if not filtered:
        print(f"[YEAR FILTER] No results matched year {year_level}, using all results")
        return results
    
    print(f"[YEAR FILTER] Filtered from {len(results)} to {len(filtered)} results for year {year_level}")
    return filtered


def apply_context_filters(
    results: List[Dict[str, Any]], 
    programme: Optional[str] = None,
    year_level: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Apply all context-aware filters to RAG results.
    
    Args:
        results: List of RAG retrieval results
        programme: User's programme
        year_level: Detected year level from query
        
    Returns:
        Filtered results matching all applicable filters
    """
    filtered_results = results
    
    # Apply programme filter
    if programme:
        filtered_results = filter_by_programme(filtered_results, programme)
    
    # Apply year level filter
    if year_level:
        filtered_results = filter_by_year_level(filtered_results, year_level)
    
    return filtered_results
