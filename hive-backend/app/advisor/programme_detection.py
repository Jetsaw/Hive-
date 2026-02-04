"""
Programme Detection Module
Auto-detects student's programme from query context and course codes.
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class Programme(str, Enum):
    """Programme enumeration."""
    APPLIED_AI = "Applied AI"
    INTELLIGENT_ROBOTICS = "Intelligent Robotics"
    FAIE = "FAIE"


@dataclass
class DetectionResult:
    """Result of programme detection."""
    programme: Optional[str]
    confidence: float  # 0.0 to 1.0
    reasons: List[str]
    detected_course_code: Optional[str] = None


class ProgrammeDetector:
    """Detects student's programme from context."""
    
    # Course code prefixes for each programme
    APPLIED_AI_PREFIXES = {'AAC', 'AAM', 'AAT', 'AAE'}
    ROBOTICS_PREFIXES = {'ARC', 'ARR', 'ARE', 'ARL', 'ARM', 'ARA'}
    FAIE_PREFIXES = {'AMT', 'ACE', 'ALE', 'AEE', 'AHS', 'AAP'}
    
    # Specialization course codes
    APPLIED_AI_COURSES = {
        'ACE6313', 'ACE6283', 'ACE6323', 'ACE6333', 
        'ACE6343', 'ACE6253', 'ACE6263'
    }
    
    ROBOTICS_COURSES = {
        'ACE6163', 'ACE6173', 'ACE6183', 'ACE6193',
        'ACE6203', 'ACE6213', 'ACE6223', 'ACE6233'
    }
    
    # Keywords for programme detection
    APPLIED_AI_KEYWORDS = {
        'applied ai', 'machine learning', 'deep learning', 'nlp',
        'natural language', 'computer vision', 'generative ai',
        'gen ai', 'ai ethics', 'neural network', 'transformer'
    }
    
    ROBOTICS_KEYWORDS = {
        'robot', 'robotics', 'drone', 'uav', 'autonomous',
        'mechatronics', 'actuator', 'sensor', 'control system',
        'human-robot', 'hri', 'manipulation'
    }
    
    COURSE_CODE_PATTERN = re.compile(r'\b([A-Z]{3})(\d{4})\b')
    
    def detect(
        self, 
        query: str, 
        context: Optional[Dict] = None
    ) -> DetectionResult:
        """
        Detect programme from query and context.
        
        Args:
            query: User query text
            context: Optional context dict with history, mentioned courses, etc.
        
        Returns:
            DetectionResult with programme, confidence, and reasons
        """
        reasons = []
        confidence = 0.0
        programme = None
        detected_code = None
        
        # 1. Check explicit programme mention with natural language patterns
        query_lower = query.lower()
        print(f"[PROG DETECT] Query: '{query}'")
        print(f"[PROG DETECT] Lower: '{query_lower}'")
        
        # Applied AI detection patterns
        applied_ai_patterns = [
            'applied ai',
            'applied artificial intelligence',
            'study applied ai',
            'studying applied ai',
            'interested in applied ai',
            'want to study applied ai',
            'take applied ai',
            'enroll in applied ai',
            'enrolled in applied ai',
            'apply for applied ai',
            'applying for applied ai'
        ]
        
        for pattern in applied_ai_patterns:
            if pattern in query_lower:
                return DetectionResult(
                    programme=Programme.APPLIED_AI,
                    confidence=1.0,
                    reasons=[f"Explicit programme mention: '{pattern}'"],
                    detected_course_code=None
                )
        
        # Intelligent Robotics detection patterns
        robotics_patterns = [
            'intelligent robotics',
            'robotics programme',
            'robotics program',
            'study intelligent robotics',
            'studying intelligent robotics',
            'study robotics',
            'studying robotics',
            'interested in intelligent robotics',
            'interested in robotics',
            'interested in studying intelligent robotics',
            'interested in studying robotics',
            'want to study intelligent robotics',
            'want to study robotics',
            'take intelligent robotics',
            'take robotics',
            'enroll in intelligent robotics',
            'enroll in robotics',
            'enrolled in intelligent robotics',
            'enrolled in robotics',
            'apply for intelligent robotics',
            'apply for robotics',
            'applying for intelligent robotics',
            'applying for robotics'
        ]
        
        for pattern in robotics_patterns:
            if pattern in query_lower:
                print(f"[PROG DETECT] MATCH! Pattern: '{pattern}'")
                return DetectionResult(
                    programme=Programme.INTELLIGENT_ROBOTICS,
                    confidence=1.0,
                    reasons=[f"Explicit programme mention: '{pattern}'"],
                    detected_course_code=None
                )
        
        # 2. Check context for stored programme
        if context and context.get('programme'):
            return DetectionResult(
                programme=context['programme'],
                confidence=0.95,
                reasons=["Programme from session context"],
                detected_course_code=None
            )
        
        # 3. Detect by course code (HIGH CONFIDENCE)
        course_codes = self.COURSE_CODE_PATTERN.findall(query.upper())
        for prefix, number in course_codes:
            full_code = f"{prefix}{number}"
            
            # Check specialization courses first
            if full_code in self.APPLIED_AI_COURSES:
                return DetectionResult(
                    programme=Programme.APPLIED_AI,
                    confidence=0.95,
                    reasons=[f"Applied AI specialization course: {full_code}"],
                    detected_course_code=full_code
                )
            
            if full_code in self.ROBOTICS_COURSES:
                return DetectionResult(
                    programme=Programme.INTELLIGENT_ROBOTICS,
                    confidence=0.95,
                    reasons=[f"Robotics specialization course: {full_code}"],
                    detected_course_code=full_code
                )
            
            # Check by prefix
            if prefix in self.APPLIED_AI_PREFIXES:
                programme = Programme.APPLIED_AI
                confidence = 0.90
                reasons.append(f"Course code prefix: {prefix} (Applied AI)")
                detected_code = full_code
                break
            
            if prefix in self.ROBOTICS_PREFIXES:
                programme = Programme.INTELLIGENT_ROBOTICS
                confidence = 0.90
                reasons.append(f"Course code prefix: {prefix} (Robotics)")
                detected_code = full_code
                break
            
            if prefix in self.FAIE_PREFIXES:
                programme = Programme.FAIE
                confidence = 0.70
                reasons.append(f"Foundation course prefix: {prefix}")
                detected_code = full_code
        
        # 4. Detect by keywords (MEDIUM CONFIDENCE)
        if not programme:
            ai_score = sum(1 for kw in self.APPLIED_AI_KEYWORDS if kw in query_lower)
            robotics_score = sum(1 for kw in self.ROBOTICS_KEYWORDS if kw in query_lower)
            
            if ai_score > robotics_score and ai_score > 0:
                programme = Programme.APPLIED_AI
                confidence = min(0.60 + (ai_score * 0.1), 0.85)
                reasons.append(f"Keyword signals: {ai_score} Applied AI keywords")
            
            elif robotics_score > ai_score and robotics_score > 0:
                programme = Programme.INTELLIGENT_ROBOTICS
                confidence = min(0.60 + (robotics_score * 0.1), 0.85)
                reasons.append(f"Keyword signals: {robotics_score} Robotics keywords")
        
        # 5. Check context history
        if not programme and context and context.get('history'):
            # Analyze recent conversation history
            history_text = ' '.join([
                msg.get('content', '') 
                for msg in context['history'][-5:]  # Last 5 messages
            ]).lower()
            
            ai_hist_score = sum(1 for kw in self.APPLIED_AI_KEYWORDS if kw in history_text)
            robotics_hist_score = sum(1 for kw in self.ROBOTICS_KEYWORDS if kw in history_text)
            
            if ai_hist_score > robotics_hist_score and ai_hist_score > 0:
                programme = Programme.APPLIED_AI
                confidence = 0.50
                reasons.append(f"Conversation history suggests Applied AI")
            
            elif robotics_hist_score > ai_hist_score and robotics_hist_score > 0:
                programme = Programme.INTELLIGENT_ROBOTICS
                confidence = 0.50
                reasons.append(f"Conversation history suggests Robotics")
        
        return DetectionResult(
            programme=programme,
            confidence=confidence,
            reasons=reasons if reasons else ["Unable to detect programme"],
            detected_course_code=detected_code
        )
    
    def detect_by_course_code(self, course_code: str) -> Optional[str]:
        """
        Quick detection by course code only.
        
        Args:
            course_code: Course code (e.g., ACE6313)
        
        Returns:
            Programme name or None
        """
        course_code = course_code.upper()
        
        # Check specialization courses
        if course_code in self.APPLIED_AI_COURSES:
            return Programme.APPLIED_AI
        
        if course_code in self.ROBOTICS_COURSES:
            return Programme.INTELLIGENT_ROBOTICS
        
        # Check by prefix
        if len(course_code) >= 3:
            prefix = course_code[:3]
            
            if prefix in self.APPLIED_AI_PREFIXES:
                return Programme.APPLIED_AI
            
            if prefix in self.ROBOTICS_PREFIXES:
                return Programme.INTELLIGENT_ROBOTICS
            
            if prefix in self.FAIE_PREFIXES:
                return Programme.FAIE
        
        return None


# Singleton instance
_detector_instance: Optional[ProgrammeDetector] = None


def get_programme_detector() -> ProgrammeDetector:
    """Get singleton instance of ProgrammeDetector."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ProgrammeDetector()
    return _detector_instance


def detect_programme(query: str, context: Optional[Dict] = None) -> DetectionResult:
    """
    Convenience function to detect programme.
    
    Args:
        query: User query
        context: Optional context
    
    Returns:
        DetectionResult
    """
    detector = get_programme_detector()
    return detector.detect(query, context)
