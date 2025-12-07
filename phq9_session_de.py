"""
PHQ-9 Session Manager - GERMAN VERSION
Handles PHQ-9 screening logic, scoring, and state management
Deutsche Version des PHQ-9 Fragebogens
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


# PHQ-9 Questions (German - standardized translation)
PHQ9_QUESTIONS_DE = [
    PHQ9Question(1, "Wie oft hatten Sie in den letzten 2 Wochen wenig Interesse oder Freude an Ihren Tätigkeiten?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(2, "Wie oft fühlten Sie sich in den letzten 2 Wochen niedergeschlagen, schwermütig oder hoffnungslos?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(3, "Wie oft hatten Sie in den letzten 2 Wochen Schwierigkeiten ein- oder durchzuschlafen oder haben Sie zu viel geschlafen?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(4, "Wie oft fühlten Sie sich in den letzten 2 Wochen müde oder hatten wenig Energie?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(5, "Wie oft hatten Sie in den letzten 2 Wochen wenig Appetit oder haben Sie zu viel gegessen?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(6, "Wie oft hatten Sie in den letzten 2 Wochen das Gefühl, ein Versager zu sein, sich selbst oder Ihre Familie enttäuscht zu haben?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(7, "Wie oft hatten Sie in den letzten 2 Wochen Schwierigkeiten, sich auf etwas zu konzentrieren, zum Beispiel beim Zeitunglesen oder Fernsehen?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(8, "Wie oft waren Sie in den letzten 2 Wochen so unruhig, dass Sie nicht still sitzen konnten, oder das Gegenteil davon: Sie waren so antriebslos, dass Sie sich deutlich weniger bewegt haben als sonst?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3]),
    PHQ9Question(9, "Wie oft hatten Sie in den letzten 2 Wochen Gedanken, dass Sie lieber tot wären oder sich Leid zufügen möchten?",
                 ["Überhaupt nicht", "An einzelnen Tagen", "An mehr als der Hälfte der Tage", "Beinahe jeden Tag"], [0, 1, 2, 3])
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
        if 0 <= self.current_question_index < len(PHQ9_QUESTIONS_DE):
            return PHQ9_QUESTIONS_DE[self.current_question_index]
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
            return "leicht"
        elif total <= 14:
            return "mittelgradig"
        elif total <= 19:
            return "mittelschwer"
        else:
            return "schwer"
    
    def get_severity_description(self) -> str:
        """Get detailed severity description (German)"""
        severity = self.get_severity()
        descriptions = {
            "minimal": "Minimale Depressionssymptome. Werte in diesem Bereich (0-4) deuten typischerweise auf wenige oder keine depressiven Symptome hin.",
            "leicht": "Leichte Depressionssymptome. Werte in diesem Bereich (5-9) können auf leichte depressive Symptome hinweisen, die eine Beobachtung erfordern könnten.",
            "mittelgradig": "Mittelgradige Depressionssymptome. Werte in diesem Bereich (10-14) deuten auf mittelgradige depressive Symptome hin, die möglicherweise eine professionelle Bewertung erfordern.",
            "mittelschwer": "Mittelschwere Depressionssymptome. Werte in diesem Bereich (15-19) weisen auf signifikante Symptome hin, die von professioneller Betreuung profitieren würden.",
            "schwer": "Schwere Depressionssymptome. Werte in diesem Bereich (20-27) deuten auf schwere depressive Symptome hin, die sofortige professionelle Aufmerksamkeit erfordern."
        }
        return descriptions.get(severity, "Unbekannter Schweregrad.")
    
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
            "total_retries": sum(self.retry_counts.values()),
            "language": "DE"
        }
    
    def validate_scores(self) -> List[str]:
        """Validate final scores and return any warnings"""
        warnings = []
        
        for i in range(9):
            if self.final_scores[i] is None:
                warnings.append(f"F{i+1} hat keine finale Bewertung, wird auf 0 gesetzt")
            elif not (0 <= self.final_scores[i] <= 3):
                warnings.append(f"F{i+1} Bewertung {self.final_scores[i]} ist ungültig (muss 0-3 sein)")
        
        total = self.calculate_total_score()
        if total > 27:
            warnings.append(f"Gesamtpunktzahl {total} überschreitet Maximum 27")
        
        return warnings

