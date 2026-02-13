"""
Alias Resolver Module
Resolves natural language course references to official course codes.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import yaml

from app.core.config import settings


class AliasResolver:
    """Resolves student natural language to deterministic course codes."""
    
    def __init__(self):
        self.aliases: List[Dict] = []
        self._load_aliases()
    
    def _load_aliases(self):
        """Load aliases from JSONL file for fast lookup."""
        alias_path = Path(settings.KB_DIR) / "alias_mapping.jsonl"
        
        if not alias_path.exists():
            # Fallback to YAML if JSONL doesn't exist
            yaml_path = Path(settings.KB_DIR) / "alias_mapping.yaml"
            if yaml_path.exists():
                self._load_from_yaml(yaml_path)
            return
        
        with open(alias_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.aliases.append(json.loads(line))
    
    def _load_from_yaml(self, yaml_path: Path):
        """Load aliases from YAML file."""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.aliases = data.get('aliases', [])
    
    def resolve(
        self, 
        text: str, 
        programme: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Resolve natural language text to course codes.
        
        Args:
            text: Input text containing course references
            programme: Optional programme filter (Applied AI, Intelligent Robotics, ALL)
        
        Returns:
            List of resolved courses with metadata
        """
        text_lower = text.lower()
        resolved = []
        
        for alias in self.aliases:
            pattern = alias['pattern']
            match_type = alias['match_type']
            alias_programme = alias.get('programme', 'ALL')
            
            # Filter by programme if specified
            if programme and alias_programme != 'ALL' and alias_programme != programme:
                continue
            
            # Check if pattern matches
            if self._matches(text_lower, pattern, match_type):
                resolved.append({
                    'course_code': alias['course_code'],
                    'course_name': alias.get('course_name', ''),
                    'matched_pattern': pattern,
                    'match_type': match_type,
                    'programme': alias_programme
                })
        
        # Remove duplicates (keep first match)
        seen_codes = set()
        unique_resolved = []
        for item in resolved:
            code = item['course_code']
            if code not in seen_codes:
                seen_codes.add(code)
                unique_resolved.append(item)
        
        return unique_resolved
    
    def _matches(self, text: str, pattern: str, match_type: str) -> bool:
        """
        Check if text matches pattern based on match type.
        
        Args:
            text: Text to match (already lowercased)
            pattern: Pattern to match against
            match_type: Type of matching (contains, exact, regex)
        
        Returns:
            True if matches, False otherwise
        """
        if match_type == 'contains':
            return pattern.lower() in text
        
        elif match_type == 'exact':
            return pattern.lower() == text.strip()
        
        elif match_type == 'regex':
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except re.error:
                return False
        
        return False
    
    def resolve_single(
        self, 
        text: str, 
        programme: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolve to a single course code (returns first match).
        
        Args:
            text: Input text
            programme: Optional programme filter
        
        Returns:
            Course code or None
        """
        resolved = self.resolve(text, programme)
        return resolved[0]['course_code'] if resolved else None
    
    def get_all_aliases_for_code(self, course_code: str) -> List[str]:
        """
        Get all alias patterns for a given course code.
        
        Args:
            course_code: Course code to find aliases for
        
        Returns:
            List of alias patterns
        """
        patterns = []
        for alias in self.aliases:
            if alias['course_code'] == course_code:
                patterns.append(alias['pattern'])
        return patterns


# Singleton instance
_resolver_instance: Optional[AliasResolver] = None


def get_alias_resolver() -> AliasResolver:
    """Get singleton instance of AliasResolver."""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = AliasResolver()
    return _resolver_instance


def resolve_aliases(text: str, programme: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Convenience function to resolve aliases.
    
    Args:
        text: Input text
        programme: Optional programme filter
    
    Returns:
        List of resolved courses
    """
    resolver = get_alias_resolver()
    return resolver.resolve(text, programme)
