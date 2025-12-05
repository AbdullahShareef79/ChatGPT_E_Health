#!/usr/bin/env python3
"""
PHQ-9 Health Screening Simulation
Replicates the Android app logic without needing Android/emulator
WITH SPEECH INPUT AND OUTPUT - just like Pepper!
"""

import csv
import json
import re
import time
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
GPT_ENABLED = os.getenv("GPT_ENABLED", "True").lower() == "true"
SIMULATION_MODE = True  # Always True for Python simulation

# Try to import speech libraries (optional)
try:
    import speech_recognition as sr
    import pyttsx3
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("⚠️  Speech libraries not available. Running in text-only mode.")
    print("   To enable speech: pip install SpeechRecognition pyttsx3")
    print("   On Windows: pip install pipwin && pipwin install pyaudio\n")

# PHQ-9 Questions
PHQ9_QUESTIONS = [
    {
        "id": 1,
        "question": "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 2,
        "question": "Over the last 2 weeks, how often have you felt down, depressed, or hopeless?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 3,
        "question": "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 4,
        "question": "Over the last 2 weeks, how often have you felt tired or had little energy?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 5,
        "question": "Over the last 2 weeks, how often have you had poor appetite or overeating?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 6,
        "question": "Over the last 2 weeks, how often have you felt bad about yourself, or that you are a failure, or have let yourself or your family down?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 7,
        "question": "Over the last 2 weeks, how often have you had trouble concentrating on things, such as reading the newspaper or watching television?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 8,
        "question": "Over the last 2 weeks, how often have you been moving or speaking slowly enough that other people could have noticed?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    },
    {
        "id": 9,
        "question": "Over the last 2 weeks, how often have you had thoughts that you would be better off dead or of hurting yourself in some way?",
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3]
    }
]


class InteractionLogger:
    """Logs all interactions to CSV - identical to Android app"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries = []
        self.turn_index = 0
    
    def log_turn(self, user_raw_speech: Optional[str], asr_transcript: str,
                 language_detected: str, phq_question_id: Optional[str],
                 handling_module: str, pepper_local_nlp_success: bool,
                 gpt_used: bool, gpt_reason: Optional[str],
                 gpt_model: Optional[str], gpt_prompt_snippet: Optional[str],
                 gpt_response: Optional[str], final_robot_output: str,
                 notes: Optional[str]):
        """Log a single interaction turn"""
        entry = {
            "timestamp": int(time.time() * 1000),
            "sessionId": self.session_id,
            "turnIndex": self.turn_index,
            "userRawSpeech": user_raw_speech or "",
            "asrTranscript": asr_transcript,
            "languageDetected": language_detected,
            "phqQuestionId": phq_question_id or "",
            "handlingModule": handling_module,
            "pepperLocalNlpSuccess": pepper_local_nlp_success,
            "gptUsed": gpt_used,
            "gptReason": gpt_reason or "",
            "gptModel": gpt_model or "",
            "gptPromptSnippet": gpt_prompt_snippet or "",
            "gptResponse": gpt_response or "",
            "finalRobotOutput": final_robot_output,
            "notes": notes or ""
        }
        self.entries.append(entry)
        self.turn_index += 1
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export logs to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interaction_logs_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "sessionId", "turnIndex", "userRawSpeech", "asrTranscript",
                "languageDetected", "phqQuestionId", "handlingModule", "pepperLocalNlpSuccess",
                "gptUsed", "gptReason", "gptModel", "gptPromptSnippet", "gptResponse",
                "finalRobotOutput", "notes"
            ])
            writer.writeheader()
            writer.writerows(self.entries)
        
        return filename


class LanguageDetector:
    """Simple language detection - identical to Android app"""
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect if text is EN or DE"""
        text_lower = text.lower()
        german_indicators = [
            "nicht", "sch", "der", "die", "das", "und", "ist", "zu", "für",
            "auf", "mit", "über", "ä", "ö", "ü", "ß"
        ]
        
        german_count = sum(1 for indicator in german_indicators if indicator in text_lower)
        return "DE" if german_count >= 2 else "EN"


class PHQ9Simulator:
    """Main PHQ-9 simulation class - identical logic to Android app"""
    
    def __init__(self, api_key: str, gpt_enabled: bool = True, use_speech: bool = True):
        self.api_key = api_key
        self.gpt_enabled = gpt_enabled
        self.use_speech = use_speech and SPEECH_AVAILABLE
        self.session_id = str(uuid.uuid4())
        self.logger = InteractionLogger(self.session_id)
        self.responses = []
        
        # Initialize speech components (if available)
        if self.use_speech:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.tts_engine = pyttsx3.init()
                
                # Configure TTS
                self.tts_engine.setProperty('rate', 150)  # Speed
                self.tts_engine.setProperty('volume', 0.9)  # Volume
                
                # Adjust for ambient noise
                print("🎤 Calibrating microphone for ambient noise... Please wait.")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("✅ Microphone ready!\n")
            except Exception as e:
                print(f"⚠️  Could not initialize speech: {e}")
                print("   Running in text-only mode.\n")
                self.use_speech = False
        
        if self.api_key and self.api_key != "YOUR_OPENAI_API_KEY_HERE":
            openai.api_key = self.api_key
    
    def speak(self, text: str):
        """Speak text using TTS - just like Pepper!"""
        if self.use_speech:
            print(f"🤖 Robot: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            print(f"🤖 Robot: {text}")
    
    def listen(self) -> Optional[str]:
        """Listen to user speech and transcribe - just like Pepper ASR!"""
        if not self.use_speech:
            return input("\n👤 You: ").strip()
        
        print("\n🎤 Listening... (speak now)")
        
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            print("🔄 Processing speech...")
            
            # Use Google Speech Recognition (free)
            transcript = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {transcript}")
            return transcript
            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected. Please try again.")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            print("💡 Falling back to text input...")
            return input("\n👤 You (text): ").strip()
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def parse_response_to_score(self, response: str, question_index: int) -> int:
        """
        Local NLP parsing - identical to Android app
        Returns -1 if parsing fails (triggers GPT fallback)
        """
        response_lower = response.lower()
        
        # Check for explicit scores
        if "not at all" in response_lower or "never" in response_lower:
            return 0
        elif "several days" in response_lower or "sometimes" in response_lower:
            return 1
        elif "more than half" in response_lower or "often" in response_lower:
            return 2
        elif "nearly every day" in response_lower or "always" in response_lower:
            return 3
        else:
            # Try to match with question options
            question = PHQ9_QUESTIONS[question_index]
            for idx, option in enumerate(question["options"]):
                if option.lower() in response_lower:
                    return question["scores"][idx]
            
            # Parsing failed
            return -1
    
    def call_gpt_for_response_parsing(self, response: str, question_index: int) -> Tuple[int, str]:
        """
        GPT fallback for parsing unclear responses
        Returns: (score, gpt_response)
        """
        question = PHQ9_QUESTIONS[question_index]
        prompt = f"""The user is answering a PHQ-9 mental health screening question.
Question: {question['question']}
User response: "{response}"

Determine which option best matches the user's response:
- "Not at all" (score 0)
- "Several days" (score 1)
- "More than half the days" (score 2)
- "Nearly every day" (score 3)

Respond with ONLY the score number (0, 1, 2, or 3). If unclear, respond with "1"."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0
            )
            gpt_response = response.choices[0].message.content.strip()
            
            # Extract score
            for char in gpt_response:
                if char in "0123":
                    return int(char), gpt_response
            
            return 1, gpt_response  # Default
        except Exception as e:
            print(f"GPT API error: {e}")
            return 1, f"Error: {str(e)}"
    
    def generate_summary(self, total_score: int, severity: str) -> str:
        """Generate empathetic summary using GPT"""
        severity_text = {
            "minimal": "minimal symptoms",
            "mild": "mild symptoms",
            "moderate": "moderate symptoms",
            "moderately_severe": "moderately severe symptoms",
            "severe": "severe symptoms"
        }.get(severity, "some symptoms")
        
        if not self.gpt_enabled:
            return f"Thank you for completing the screening. Your total score is {total_score}, which indicates {severity_text}. Remember, this is just a tool to help you reflect on your emotions. If you have concerns, please talk to a healthcare provider."
        
        prompt = f"""You are Pepper, a friendly robot conducting a mental health screening. 
The person's total PHQ-9 score is {total_score}, which indicates {severity_text} of depression.

Please provide a gentle, supportive, and empathetic response that:
1. Acknowledges their participation
2. Provides context about what the score means (without being clinical)
3. Offers encouragement and support
4. Reminds them this is not a diagnosis
5. Suggests talking to a healthcare provider if they're concerned
6. Maintains a warm, caring tone

Keep the response conversational and under 3 sentences."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"GPT API error: {e}")
            return f"Thank you for completing the screening. Your responses help us understand how you've been feeling. Remember, this is just a tool to help you reflect on your emotions. If you have concerns, please talk to a healthcare provider."
    
    def get_severity_level(self, score: int) -> str:
        """Calculate severity level from total score"""
        if score <= 4:
            return "minimal"
        elif score <= 9:
            return "mild"
        elif score <= 14:
            return "moderate"
        elif score <= 19:
            return "moderately_severe"
        else:
            return "severe"
    
    def run_screening(self):
        """Run the complete PHQ-9 screening"""
        print("\n" + "="*70)
        print("🤖 PHQ-9 HEALTH SCREENING SIMULATION")
        print("="*70)
        print(f"Session ID: {self.session_id}")
        print(f"GPT Mode: {'ENABLED' if self.gpt_enabled else 'DISABLED'}")
        print(f"Speech Mode: {'ENABLED' if self.use_speech else 'TEXT ONLY'}")
        print("="*70 + "\n")
        
        # Welcome message
        welcome_msg = "I will ask you a few questions to check how you've been feeling recently. This is not a diagnosis, but it helps you understand your emotions better. Please answer honestly based on the last 2 weeks."
        
        self.speak(welcome_msg)
        
        self.logger.log_turn(
            user_raw_speech=None,
            asr_transcript="",
            language_detected="EN",
            phq_question_id=None,
            handling_module="PEPPER_LOCAL",
            pepper_local_nlp_success=True,
            gpt_used=False,
            gpt_reason=None,
            gpt_model=None,
            gpt_prompt_snippet=None,
            gpt_response=None,
            final_robot_output=welcome_msg,
            notes="Screening started"
        )
        
        # Ask each question
        for idx, question in enumerate(PHQ9_QUESTIONS):
            print(f"\n{'='*70}")
            print(f"📋 Question {idx + 1} of {len(PHQ9_QUESTIONS)}")
            print(f"{'='*70}")
            
            question_text = question['question']
            self.speak(question_text)
            
            if self.use_speech:
                print(f"   💡 Options: {', '.join(question['options'])}")
            
            # Log question
            self.logger.log_turn(
                user_raw_speech=None,
                asr_transcript="",
                language_detected="EN",
                phq_question_id=f"Q{question['id']}",
                handling_module="PEPPER_LOCAL",
                pepper_local_nlp_success=True,
                gpt_used=False,
                gpt_reason=None,
                gpt_model=None,
                gpt_prompt_snippet=None,
                gpt_response=None,
                final_robot_output=question_text,
                notes=f"Asking PHQ-9 question {idx + 1}"
            )
            
            # Get user response (with retry)
            user_response = None
            retry_count = 0
            max_retries = 3
            
            while user_response is None and retry_count < max_retries:
                user_response = self.listen()
                if user_response is None:
                    retry_count += 1
                    if retry_count < max_retries:
                        self.speak("I didn't catch that. Could you please repeat?")
            
            if user_response is None:
                self.speak("Let's use text input for this question.")
                user_response = input("\n👤 You (text): ").strip()
            
            # Detect language
            language_detected = LanguageDetector.detect_language(user_response)
            print(f"   [Language detected: {language_detected}]")
            
            # Try local NLP parsing
            score = self.parse_response_to_score(user_response, idx)
            local_nlp_success = score >= 0 and score <= 3
            
            gpt_used = False
            gpt_reason = None
            gpt_model = None
            gpt_prompt_snippet = None
            gpt_response = None
            handling_module = "PEPPER_LOCAL"
            
            if not local_nlp_success and self.gpt_enabled:
                # GPT fallback
                print("   [Local NLP failed, using GPT fallback...]")
                handling_module = "GPT_FALLBACK"
                gpt_reason = "intent_not_found"
                gpt_model = "gpt-4o-mini"
                gpt_prompt_snippet = f"Parse PHQ-9 response: {user_response}"
                
                score, gpt_response = self.call_gpt_for_response_parsing(user_response, idx)
                gpt_used = True
                print(f"   [GPT returned: {gpt_response}]")
            
            elif not local_nlp_success:
                # GPT disabled, use default
                gpt_reason = "gpt_disabled_experiment"
                score = 1
                print("   [Local NLP failed, GPT disabled - using default score 1]")
            else:
                print(f"   [Local NLP success: score = {score}]")
            
            self.responses.append(score)
            
            robot_response = "Thank you. Moving to the next question."
            self.speak(robot_response)
            print(f"   [Module: {handling_module}]")
            
            # Log response
            self.logger.log_turn(
                user_raw_speech=None,
                asr_transcript=user_response,
                language_detected=language_detected,
                phq_question_id=f"Q{question['id']}",
                handling_module=handling_module,
                pepper_local_nlp_success=local_nlp_success,
                gpt_used=gpt_used,
                gpt_reason=gpt_reason,
                gpt_model=gpt_model,
                gpt_prompt_snippet=gpt_prompt_snippet,
                gpt_response=gpt_response,
                final_robot_output=robot_response,
                notes=f"Response to question {idx + 1}"
            )
        
        # Calculate results
        total_score = sum(self.responses)
        severity = self.get_severity_level(total_score)
        
        print("\n" + "="*70)
        print("📊 SCREENING COMPLETE")
        print("="*70)
        print(f"Total Score: {total_score}")
        print(f"Severity: {severity}")
        print("="*70 + "\n")
        
        # Generate summary
        print("\n💭 Generating summary...")
        summary = self.generate_summary(total_score, severity)
        self.speak(summary)
        
        # Log summary
        self.logger.log_turn(
            user_raw_speech=None,
            asr_transcript="",
            language_detected="EN",
            phq_question_id="COMPLETE",
            handling_module="GPT_FALLBACK" if self.gpt_enabled else "PEPPER_LOCAL",
            pepper_local_nlp_success=True,
            gpt_used=self.gpt_enabled,
            gpt_reason="summary_generation" if self.gpt_enabled else "gpt_disabled_experiment",
            gpt_model="gpt-4o-mini" if self.gpt_enabled else None,
            gpt_prompt_snippet=f"Generate empathetic summary for PHQ-9 score {total_score}" if self.gpt_enabled else None,
            gpt_response=summary if self.gpt_enabled else None,
            final_robot_output=summary,
            notes=f"Screening completed. Score: {total_score}, Severity: {severity}"
        )
        
        # Export logs
        filename = self.logger.export_to_csv()
        print("="*70)
        print(f"✅ Logs exported to: {filename}")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("🎯 PHQ-9 HEALTH SCREENING SIMULATION")
    print("   WITH SPEECH INPUT/OUTPUT - Just like Pepper!")
    print("="*70)
    
    # Configuration from .env
    api_key = OPENAI_API_KEY
    gpt_enabled = GPT_ENABLED
    use_speech = SPEECH_AVAILABLE  # Use speech if libraries available
    
    # Check for text-only mode
    import sys
    if "--text-only" in sys.argv:
        use_speech = False
        print("\n📝 Running in TEXT-ONLY mode (no speech)")
    
    # Check API key
    if api_key == "YOUR_OPENAI_API_KEY_HERE" or not api_key:
        print("\n⚠️  Warning: OpenAI API key not set in .env file!")
        print("   GPT fallback and summary generation will use defaults.")
        print("   To fix: Create .env file with OPENAI_API_KEY=your_key")
    else:
        print(f"\n✅ OpenAI API key loaded from .env")
    
    print(f"\nConfiguration:")
    print(f"  - GPT Mode: {'ENABLED' if gpt_enabled else 'DISABLED'}")
    print(f"  - Speech Mode: {'ENABLED' if use_speech else 'TEXT ONLY'}")
    print(f"  - Simulation Mode: ACTIVE")
    
    if use_speech:
        print("\n🎤 IMPORTANT:")
        print("  - Make sure your microphone is connected")
        print("  - Find a quiet environment")
        print("  - Speak clearly when prompted")
        print("  - You'll hear the robot speak its questions")
    
    print("\n" + "="*70)
    input("Press Enter to start the screening...")
    
    # Run screening
    simulator = PHQ9Simulator(api_key, gpt_enabled, use_speech)
    simulator.run_screening()
    
    print("\n" + "="*70)
    print("✨ Thank you for participating!")
    print("You can now analyze the CSV file in Excel, Python, or R.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

