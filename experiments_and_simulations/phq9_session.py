"""
PHQ-9 Session Manager
Handles PHQ-9 screening logic, scoring, and state management
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid


@dataclass
class PHQ9Question:
    """PHQ-9 Question structure"""
    id: int
    question: str
    options: List[str]
    scores: List[int]


# PHQ-9 Questions (standardized)
PHQ9_QUESTIONS = [
    PHQ9Question(1, "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(2, "Over the last 2 weeks, how often have you felt down, depressed, or hopeless?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(3, "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(4, "Over the last 2 weeks, how often have you felt tired or had little energy?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(5, "Over the last 2 weeks, how often have you had poor appetite or overeating?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(6, "Over the last 2 weeks, how often have you felt bad about yourself, or that you are a failure, or have let yourself or your family down?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(7, "Over the last 2 weeks, how often have you had trouble concentrating on things, such as reading the newspaper or watching television?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(8, "Over the last 2 weeks, how often have you been moving or speaking slowly enough that other people could have noticed?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3]),
    PHQ9Question(9, "Over the last 2 weeks, how often have you had thoughts that you would be better off dead or of hurting yourself in some way?",
                 ["Not at all", "Several days", "More than half the days", "Nearly every day"], [0, 1, 2, 3])
]


@dataclass
class PHQ9Session:
    """
    PHQ-9 Screening Session
    Manages state, scoring, and validation for a single PHQ-9 screening session
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    
    # Scoring state
    current_question_index: int = 0
    final_scores: List[Optional[int]] = field(default_factory=lambda: [None] * 9)
    attempts_per_question: Dict[int, List[int]] = field(default_factory=lambda: {i: [] for i in range(9)})
    retry_counts: Dict[int, int] = field(default_factory=lambda: {i: 0 for i in range(9)})
    
    # Configuration
    MAX_RETRIES_PER_QUESTION: int = 3
    
    # Status
    is_active: bool = False
    waiting_for_confirmation: bool = False
    pending_score: Optional[int] = None
    pending_confirmation: Optional[str] = None
    
    def start_session(self) -> None:
        """Initialize a new screening session"""
        self.is_active = True
        self.current_question_index = 0
        self.final_scores = [None] * 9
        self.attempts_per_question = {i: [] for i in range(9)}
        self.retry_counts = {i: 0 for i in range(9)}
        self.start_time = datetime.now()
    
    def get_current_question(self) -> Optional[PHQ9Question]:
        """Get the current question"""
        if 0 <= self.current_question_index < len(PHQ9_QUESTIONS):
            return PHQ9_QUESTIONS[self.current_question_index]
        return None
    
    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return self.current_question_index >= 9
    
    def record_attempt(self, score: int) -> None:
        """Record a score attempt for current question"""
        if 0 <= score <= 3:
            self.attempts_per_question[self.current_question_index].append(score)
    
    def confirm_answer(self, score: int) -> None:
        """Confirm and finalize the answer for current question"""
        self.final_scores[self.current_question_index] = score
        self.waiting_for_confirmation = False
        self.pending_score = None
        self.pending_confirmation = None
    
    def increment_retry(self) -> bool:
        """
        Increment retry counter for current question
        Returns True if max retries reached
        """
        self.retry_counts[self.current_question_index] += 1
        return self.retry_counts[self.current_question_index] >= self.MAX_RETRIES_PER_QUESTION
    
    def apply_fallback_score(self) -> int:
        """Apply fallback score when max retries reached"""
        attempts = self.attempts_per_question[self.current_question_index]
        fallback = attempts[-1] if attempts else 0
        self.final_scores[self.current_question_index] = fallback
        return fallback
    
    def move_to_next_question(self) -> bool:
        """
        Move to next question
        Returns True if more questions remain, False if complete
        """
        self.current_question_index += 1
        return not self.is_complete()
    
    def calculate_total_score(self) -> int:
        """Calculate total PHQ-9 score (0-27)"""
        # Fill any missing scores with 0
        scores = [s if s is not None else 0 for s in self.final_scores]
        total = sum(scores)
        
        # Safety clamp
        if total < 0:
            return 0
        elif total > 27:
            return 27
        return total
    
    def get_severity(self) -> str:
        """Get severity classification based on total score"""
        total = self.calculate_total_score()
        
        if total <= 4:
            return "minimal"
        elif total <= 9:
            return "mild"
        elif total <= 14:
            return "moderate"
        elif total <= 19:
            return "moderately_severe"
        else:
            return "severe"
    
    def get_severity_description(self) -> str:
        """Get detailed severity description"""
        severity = self.get_severity()
        descriptions = {
            "minimal": "Minimal depression symptoms. Scores in this range (0-4) typically suggest little to no depressive symptoms.",
            "mild": "Mild depression symptoms. Scores in this range (5-9) may indicate mild depressive symptoms that might benefit from monitoring.",
            "moderate": "Moderate depression symptoms. Scores in this range (10-14) suggest moderate depressive symptoms that may warrant professional evaluation.",
            "moderately_severe": "Moderately severe depression symptoms. Scores in this range (15-19) indicate significant symptoms that would benefit from professional care.",
            "severe": "Severe depression symptoms. Scores in this range (20-27) suggest severe depressive symptoms requiring immediate professional attention."
        }
        return descriptions.get(severity, "Unknown severity level.")
    
    def requires_crisis_protocol(self) -> bool:
        """Check if Q9 (suicidality) requires crisis intervention"""
        if self.current_question_index == 8:  # Q9 is index 8
            score = self.final_scores[8]
            return score is not None and score > 0
        return False
    
    def get_summary(self) -> Dict:
        """Get complete session summary"""
        total = self.calculate_total_score()
        severity = self.get_severity()
        
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "final_scores": self.final_scores,
            "total_score": total,
            "severity": severity,
            "severity_description": self.get_severity_description(),
            "retry_counts": list(self.retry_counts.values()),
            "total_retries": sum(self.retry_counts.values())
        }
    
    def validate_scores(self) -> List[str]:
        """Validate final scores and return any warnings"""
        warnings = []
        
        for i in range(9):
            if self.final_scores[i] is None:
                warnings.append(f"Q{i+1} has no final score, will default to 0")
            elif not (0 <= self.final_scores[i] <= 3):
                warnings.append(f"Q{i+1} score {self.final_scores[i]} is invalid (must be 0-3)")
        
        total = self.calculate_total_score()
        if total > 27:
            warnings.append(f"Total score {total} exceeds maximum 27")
        
        return warnings

