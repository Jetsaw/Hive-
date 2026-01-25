"""
Query Router Module
Routes queries to the correct knowledge layer based on intent and rules.
"""

import re
import yaml
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.advisor.session_manager import SessionState


class QueryType(str, Enum):
    """Types of queries."""
    STRUCTURE_ONLY = "structure_only"
    DETAILS_ONLY = "details_only"
    MIXED = "mixed"
    CLARIFICATION_NEEDED = "clarification_needed"


class TargetLayer(str, Enum):
    """Target knowledge layers."""
    STRUCTURE = "structure"
    DETAILS = "details"
    BOTH = "both"
    NONE = "none"


@dataclass
class QueryRoute:
    """Result of query routing."""
    query_type: QueryType
    target_layer: TargetLayer
    should_query_structure: bool
    should_query_details: bool
    requires_course_code: bool
    detected_course_codes: List[str]
    reasons: List[str]
    priority: int


class QueryRouter:
    """Routes queries to appropriate knowledge layers."""
    
    # Regex patterns
    COURSE_CODE_PATTERN = re.compile(r'\b[A-Z]{3}\d{4}\b')
    TERM_PATTERN = re.compile(r'\b(year|term|trimester|semester)\s*\d+\b', re.IGNORECASE)
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict:
        """Load routing rules from YAML."""
        rules_path = Path(settings.KB_DIR) / "rules.yaml"
        
        if not rules_path.exists():
            return self._get_default_rules()
        
        with open(rules_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_default_rules(self) -> Dict:
        """Get default routing rules."""
        return {
            'routing_priority': [],
            'query_patterns': {
                'structure_queries': [
                    r'what (subjects|courses) (in|for)',
                    r'when can i take',
                    r'course (list|schedule|plan)'
                ],
                'details_queries': [
                    r'what (is|are) .+ about',
                    r'tell me about',
                    r'learning outcomes',
                    r'assessment'
                ],
                'eligibility_queries': [
                    r'can i take',
                    r'prerequisite',
                    r'requirement',
                    r'eligible'
                ]
            }
        }
    
    def route(
        self, 
        query: str, 
        session: Optional[SessionState] = None,
        detected_course_codes: Optional[List[str]] = None
    ) -> QueryRoute:
        """
        Route query to appropriate knowledge layer.
        
        Args:
            query: User query
            session: Optional session state
            detected_course_codes: Optional pre-detected course codes
        
        Returns:
            QueryRoute with routing decision
        """
        query_lower = query.lower()
        reasons = []
        
        # Extract course codes if not provided
        if detected_course_codes is None:
            detected_course_codes = self.COURSE_CODE_PATTERN.findall(query.upper())
        
        # 1. HIGHEST PRIORITY: Explicit course code
        if detected_course_codes:
            reasons.append(f"Explicit course code(s): {', '.join(detected_course_codes)}")
            
            # Check if also asking about structure
            if self._is_structure_query(query_lower):
                return QueryRoute(
                    query_type=QueryType.MIXED,
                    target_layer=TargetLayer.BOTH,
                    should_query_structure=True,
                    should_query_details=True,
                    requires_course_code=False,
                    detected_course_codes=detected_course_codes,
                    reasons=reasons + ["Mixed: structure + details query"],
                    priority=1
                )
            
            # Pure details query
            return QueryRoute(
                query_type=QueryType.DETAILS_ONLY,
                target_layer=TargetLayer.DETAILS,
                should_query_structure=False,
                should_query_details=True,
                requires_course_code=True,
                detected_course_codes=detected_course_codes,
                reasons=reasons + ["Details query with course code"],
                priority=1
            )
        
        # 2. Structure query (term planning, sequencing)
        if self._is_structure_query(query_lower):
            reasons.append("Structure query pattern matched")
            return QueryRoute(
                query_type=QueryType.STRUCTURE_ONLY,
                target_layer=TargetLayer.STRUCTURE,
                should_query_structure=True,
                should_query_details=False,
                requires_course_code=False,
                detected_course_codes=[],
                reasons=reasons,
                priority=3
            )
        
        # 3. Eligibility/prerequisite query
        if self._is_eligibility_query(query_lower):
            reasons.append("Eligibility/prerequisite query")
            return QueryRoute(
                query_type=QueryType.STRUCTURE_ONLY,
                target_layer=TargetLayer.STRUCTURE,
                should_query_structure=True,
                should_query_details=False,
                requires_course_code=False,
                detected_course_codes=[],
                reasons=reasons,
                priority=3
            )
        
        # 4. Details query without course code (needs alias resolution)
        if self._is_details_query(query_lower):
            reasons.append("Details query - requires course code resolution")
            return QueryRoute(
                query_type=QueryType.DETAILS_ONLY,
                target_layer=TargetLayer.DETAILS,
                should_query_structure=False,
                should_query_details=True,
                requires_course_code=True,
                detected_course_codes=[],
                reasons=reasons + ["Alias resolution needed"],
                priority=2
            )
        
        # 5. Check session context
        if session and session.selected_course_code:
            reasons.append(f"Using course from session: {session.selected_course_code}")
            return QueryRoute(
                query_type=QueryType.DETAILS_ONLY,
                target_layer=TargetLayer.DETAILS,
                should_query_structure=False,
                should_query_details=True,
                requires_course_code=True,
                detected_course_codes=[session.selected_course_code],
                reasons=reasons,
                priority=2
            )
        
        # 6. Ambiguous - need clarification
        reasons.append("Query intent unclear")
        return QueryRoute(
            query_type=QueryType.CLARIFICATION_NEEDED,
            target_layer=TargetLayer.NONE,
            should_query_structure=False,
            should_query_details=False,
            requires_course_code=False,
            detected_course_codes=[],
            reasons=reasons,
            priority=6
        )
    
    def _is_structure_query(self, query_lower: str) -> bool:
        """Check if query is about programme structure."""
        structure_patterns = self.rules.get('query_patterns', {}).get('structure_queries', [])
        
        # Check patterns from rules
        for pattern in structure_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check keywords
        structure_keywords = [
            'term', 'trimester', 'semester', 'year',
            'when can i take', 'what subjects', 'what courses',
            'course list', 'schedule', 'programme structure'
        ]
        
        return any(kw in query_lower for kw in structure_keywords)
    
    def _is_details_query(self, query_lower: str) -> bool:
        """Check if query is about course details."""
        details_patterns = self.rules.get('query_patterns', {}).get('details_queries', [])
        
        # Check patterns from rules
        for pattern in details_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check keywords
        details_keywords = [
            'about', 'learning outcomes', 'assessment', 'topics',
            'what will i learn', 'content', 'syllabus', 'objectives'
        ]
        
        return any(kw in query_lower for kw in details_keywords)
    
    def _is_eligibility_query(self, query_lower: str) -> bool:
        """Check if query is about eligibility/prerequisites."""
        eligibility_patterns = self.rules.get('query_patterns', {}).get('eligibility_queries', [])
        
        # Check patterns from rules
        for pattern in eligibility_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check keywords
        eligibility_keywords = [
            'can i take', 'prerequisite', 'requirement', 'eligible',
            'before taking', 'need to complete'
        ]
        
        return any(kw in query_lower for kw in eligibility_keywords)
    
    def should_use_alias_resolution(self, route: QueryRoute) -> bool:
        """Check if alias resolution should be attempted."""
        return (
            route.requires_course_code and 
            not route.detected_course_codes
        )


# Singleton instance
_router_instance: Optional[QueryRouter] = None


def get_query_router() -> QueryRouter:
    """Get singleton instance of QueryRouter."""
    global _router_instance
    if _router_instance is None:
        _router_instance = QueryRouter()
    return _router_instance


def route_query(
    query: str, 
    session: Optional[SessionState] = None,
    detected_course_codes: Optional[List[str]] = None
) -> QueryRoute:
    """
    Convenience function to route query.
    
    Args:
        query: User query
        session: Optional session state
        detected_course_codes: Optional pre-detected course codes
    
    Returns:
        QueryRoute
    """
    router = get_query_router()
    return router.route(query, session, detected_course_codes)
