        })
    
    def save_session_data(self, responses, total_score, severity):
        """Save complete session data"""
        session_data = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "phq9_responses": responses,
            "total_score": total_score,
            "severity": severity,
            "transcript": self.transcript,
            "gpt_calls": self.gpt_calls,
            "total_gpt_calls": len(self.gpt_calls),
            "interaction_logs": self.ent