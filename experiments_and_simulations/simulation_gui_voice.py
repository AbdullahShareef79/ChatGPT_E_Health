#!/usr/bin/env python3
"""
PHQ-9 Health Screening Simulation - GUI with VOICE INPUT
Uses sounddevice (easier to install than PyAudio on Windows)
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, simpledialog
import threading
import time
import uuid
import csv
import random
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os
from pathlib import Path
import queue

# Load configuration
# Look for .env in the script's directory first, then current directory
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
if not env_path.exists():
    # Try parent directory
    env_path = script_dir.parent / '.env'
    
load_dotenv(dotenv_path=env_path if env_path.exists() else None)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GPT_ENABLED = os.getenv("GPT_ENABLED", "True").lower() == "true"

# Try importing speech libraries
try:
    import pyttsx3
    TTS_AVAILABLE = True
except:
    TTS_AVAILABLE = False

ASR_AVAILABLE = False
try:
    import speech_recognition as sr
    import openai
    import tempfile
    import wave
    import pyaudio
    
    ASR_AVAILABLE = True

    # Listening tunables (safe defaults, easy to adjust)
    LISTEN_TIMEOUT = 5           # seconds to wait for speech start
    LISTEN_PHRASE_LIMIT = 8      # max seconds per utterance
    LISTEN_AMBIENT_DURATION = 0.3  # seconds for ambient noise calibration
    LISTEN_PAUSE_THRESHOLD = 0.7   # seconds of silence to end phrase
except Exception as e:
    print(f"  Speech recognition initialization error: {e}")
    ASR_AVAILABLE = False

# Import PHQ-9 questions from session manager
from phq9_session import PHQ9_QUESTIONS

# Simple language detector
class LanguageDetector:
    @staticmethod
    def detect_language(text):
        """Simple language detection - EN for now"""
        # Could be enhanced with langdetect library if needed
        return "EN"

# Interaction logger (embedded)
class SimpleLogger:
    def __init__(self, session_id, participant_info=None):
        self.session_id = session_id
        self.participant_info = participant_info or {}
        self.entries = []
        self.turn_index = 0
        self.transcript = []
        self.gpt_calls = []  # Track all GPT API calls
        self.session_start = datetime.now()
        
        # Create session folder in English language subfolder
        self.session_folder = Path("data") / "sessions" / "english" / f"session_{session_id[:8]}_{self.session_start.strftime('%Y%m%d_%H%M%S')}"
        self.session_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV immediately for real-time logging
        self.csv_file = self.session_folder / "interaction_logs.csv"
        self.csv_fields = [
            "timestamp", "sessionId", "turnIndex", "userRawSpeech", "asrTranscript",
            "languageDetected", "phqQuestionId", "handlingModule", "pepperLocalNlpSuccess",
            "gptUsed", "gptReason", "gptModel", "gptPromptSnippet", "gptResponse",
            "finalRobotOutput", "notes"
        ]
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fields)
            writer.writeheader()
    
    def log_gpt_call(self, purpose, prompt, response, model="gpt-4o-mini", tokens_used=None):
        """Log GPT API call with input/output"""
        self.gpt_calls.append({
            "timestamp": datetime.now().isoformat(),
            "purpose": purpose,
            "model": model,
            "prompt": prompt,
            "response": response,
            "tokens_used": tokens_used
        })
    
    def log_turn(self, **kwargs):
        entry = {
            "timestamp": int(time.time() * 1000),
            "sessionId": self.session_id,
            "turnIndex": self.turn_index,
            **{k: v if v is not None else "" for k, v in kwargs.items()}
        }
        self.entries.append(entry)
        self.turn_index += 1
        
        # Real-time append to CSV (Instant updates for Demo)
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_fields)
                writer.writerow(entry)
        except Exception as e:
            print(f" Error appending to CSV: {e}")
    
    def add_to_transcript(self, speaker, text):
        """Add message to conversation transcript"""
        self.transcript.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "text": text
        })
    
    def save_session_data(self, responses, total_score, severity, retry_counts):
        """Save complete session data"""
        session_data = {
            "session_id": self.session_id,
            "language": "EN",
            "participant_info": self.participant_info,
            "start_time": self.session_start.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "phq9_responses": responses,
            "total_score": total_score,
            "severity": severity,
            "retry_counts": retry_counts,
            "transcript": self.transcript,
            "gpt_calls": self.gpt_calls,
            "total_gpt_calls": len(self.gpt_calls),
            "interaction_logs": self.entries
        }
        
        # Save as JSON
        json_file = self.session_folder / "session_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Save transcript as readable text
        transcript_file = self.session_folder / "transcript.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(f"PHQ-9 Screening Session\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Date: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n\n")
            
            for msg in self.transcript:
                f.write(f"[{msg['timestamp'].split('T')[1][:8]}] {msg['speaker']}: {msg['text']}\n")
            
            f.write(f"\n{'='*70}\n")
            f.write(f"RESULTS:\n")
            f.write(f"Total Score: {total_score}/27\n")
            f.write(f"Severity: {severity}\n")
            f.write(f"Responses: {responses}\n")
        
        # CSV is already saved in real-time, no need to rewrite it here
        
        # Save GPT calls log
        if self.gpt_calls:
            gpt_log_file = self.session_folder / "gpt_api_calls.json"
            with open(gpt_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.gpt_calls, f, indent=2, ensure_ascii=False)
            
            # Also save as readable text
            gpt_txt_file = self.session_folder / "gpt_api_calls.txt"
            with open(gpt_txt_file, 'w', encoding='utf-8') as f:
                f.write(f"GPT API Calls Log\n")
                f.write(f"Session: {self.session_id}\n")
                f.write(f"Total Calls: {len(self.gpt_calls)}\n")
                f.write(f"{'='*70}\n\n")
                
                for i, call in enumerate(self.gpt_calls, 1):
                    f.write(f"CALL #{i} - {call['purpose']}\n")
                    f.write(f"Time: {call['timestamp']}\n")
                    f.write(f"Model: {call['model']}\n")
                    f.write(f"Tokens: {call.get('tokens_used', 'N/A')}\n")
                    f.write(f"\nPrompt:\n{call['prompt']}\n")
                    f.write(f"\nResponse:\n{call['response']}\n")
                    f.write(f"{'-'*70}\n\n")
        
        return self.session_folder
    
    def export_to_csv(self):
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


class VoicePHQ9GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PHQ-9 Pepper Simulation - Voice Enabled")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Ensure window is visible before asking for input
        self.root.update()
        
        # Ask for participant metadata at startup (essential demographics only)
        self.participant_id = simpledialog.askstring(
            "Participant ID", 
            "Enter Participant ID or pseudonym:", 
            parent=root
        ) or str(uuid.uuid4())[:8]
        
        self.age_group = simpledialog.askstring(
            "Demographics", 
            "Age group (18-25 / 26-35 / 36-45 / 46+):", 
            parent=root
        ) or "Not specified"
        
        self.proficiency = simpledialog.askstring(
            "Language Proficiency", 
            "English level (Native / C2 / C1 / B2 / B1 / A2):", 
            parent=root
        ) or "Not specified"
        
        self.native_speaker = simpledialog.askstring(
            "Language Background", 
            "Native English speaker? (Yes / No):", 
            parent=root
        ) or "Not specified"
        
        # State
        self.session_id = str(uuid.uuid4())
        self.logger = SimpleLogger(self.session_id, {
            "id": self.participant_id, 
            "age_group": self.age_group,
            "proficiency": self.proficiency,
            "native_speaker": self.native_speaker
        })
        self.current_question = 0
        self.final_scores = [None] * 9  # Exactly 9 final confirmed scores
        self.attempts_per_question = {i: [] for i in range(9)}  # Track all attempts
        self.retry_counts = {i: 0 for i in range(9)}  # Track retries per question
        self.MAX_RETRIES = 3
        self.session_active = False
        self.is_processing = False
        self.is_listening = False
        self.is_speaking = False  # Track if TTS is currently speaking
        self.waiting_for_crisis_ack = False
        self.waiting_for_consent = False
        self.waiting_for_answer_confirmation = False
        self.pending_score = None
        self.pending_confirmation = None
        self.pending_gpt_used = False
        self.pending_gpt_reason = ""
        self.pending_gpt_prompt_snippet = ""
        self.pending_gpt_response = ""
        self.pending_module = "PEPPER_LOCAL"
        
        # Initialize TTS
        self.tts_queue = queue.Queue()
        self.tts_lock = threading.Lock()
        self.tts_engine = None
        self.tts_ready = False
        
        if TTS_AVAILABLE:
            try:
                # Initialize TTS engine
                self.tts_engine = pyttsx3.init('sapi5')  # Explicitly use SAPI5 on Windows
                self.tts_engine.setProperty('rate', 160)
                self.tts_engine.setProperty('volume', 1.0)
                
                # Select English voice (not German)
                voices = self.tts_engine.getProperty('voices')
                english_voice = None
                for voice in voices:
                    # Look for English voice (US or GB)
                    if 'english' in voice.name.lower() or 'david' in voice.name.lower() or 'zira' in voice.name.lower():
                        english_voice = voice.id
                        print(f"  Selected English voice: {voice.name}")
                        break
                
                if english_voice:
                    self.tts_engine.setProperty('voice', english_voice)
                elif voices:
                    # Fallback to first voice
                    self.tts_engine.setProperty('voice', voices[0].id)
                    print(f"  Warning: Using default voice: {voices[0].name}")
                
                self.tts_ready = True
                print("✓ TTS initialized successfully")
                
                # Start TTS worker thread
                self.tts_worker_running = True
                self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
                self.tts_thread.start()
            except Exception as e:
                print(f"  TTS initialization failed: {e}")
                self.tts_ready = False
        
        # Initialize Speech Recognition
        self.mic_available = False
        if ASR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 3000
                self.recognizer.dynamic_energy_threshold = True
                
                # Test microphone
                test_mic = sr.Microphone()
                with test_mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                
                self.mic_available = True
            except Exception as e:
                print(f"  Microphone initialization error: {e}")
                self.mic_available = False
        
        # Create GUI
        self.create_widgets()
        
        # Welcome - don't wait for speech to complete so GUI can show
        self.add_robot_message("Hello! I'm Pepper, ready to conduct a health screening with you.")
        self.speak("Hello! I'm Pepper, ready to conduct a health screening with you.", wait=False)
    
    def create_widgets(self):
        """Create the GUI interface"""
        # Header
        header = tk.Frame(self.root, bg="#4CAF50", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="PHQ-9 HEALTH SCREENING SIMULATION",
            font=("Arial", 20, "bold"),
            bg="#4CAF50",
            fg="white"
        ).pack(pady=20)
        
        # Status
        status_frame = tk.Frame(self.root, bg="#2196F3", height=45)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text=f" Voice Mode: {'ON' if ASR_AVAILABLE else 'OFF'} | GPT: {'ON' if GPT_ENABLED else 'OFF'} | Status: Ready",
            font=("Arial", 11),
            bg="#2196F3",
            fg="white"
        )
        self.status_label.pack(pady=12)
        
        # Progress
        progress_frame = tk.Frame(self.root, bg="#f0f0f0")
        progress_frame.pack(fill=tk.X, padx=25, pady=10)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Question 0 / 9",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            length=850,
            mode='determinate',
            maximum=9
        )
        self.progress_bar.pack(pady=5)
        
        # Chat area
        chat_frame = tk.Frame(self.root, bg="#f0f0f0")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)
        
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 12),
            bg="#ffffff",
            state=tk.DISABLED,
            height=18
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Tags for styling
        self.chat_area.tag_config("robot", foreground="#1565C0", font=("Arial", 12, "bold"))
        self.chat_area.tag_config("user", foreground="#2E7D32", font=("Arial", 12, "bold"))
        self.chat_area.tag_config("system", foreground="#E65100", font=("Arial", 10, "italic"))
        
        # Input controls
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=25, pady=15)
        
        # Text input
        input_frame = tk.Frame(control_frame, bg="#f0f0f0")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.text_input = tk.Entry(
            input_frame,
            font=("Arial", 13),
            state=tk.DISABLED
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.text_input.bind("<Return>", lambda e: self.send_text())
        
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            width=10,
            height=2,
            command=self.send_text,
            state=tk.DISABLED
        )
        self.send_button.pack(side=tk.LEFT)
        
        # Main action buttons
        button_frame = tk.Frame(control_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X)
        
        # Big microphone button
        self.mic_button = tk.Button(
            button_frame,
            text="PRESS TO SPEAK",
            font=("Arial", 16, "bold"),
            bg="#FF5722",
            fg="white",
            width=25,
            height=3,
            command=self.start_voice_input,
            state=tk.DISABLED
        )
        self.mic_button.pack(side=tk.LEFT, padx=5)
        
        # Start button
        self.start_button = tk.Button(
            button_frame,
            text=" START SCREENING",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=3,
            command=self.start_screening
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Export button
        self.export_button = tk.Button(
            button_frame,
            text=" Export Logs",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            width=15,
            height=3,
            command=self.export_logs,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Restart button
        self.restart_button = tk.Button(
            button_frame,
            text=" Restart",
            font=("Arial", 12, "bold"),
            bg="#9C27B0",
            fg="white",
            width=12,
            height=3,
            command=self.restart_screening,
            state=tk.DISABLED
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # Confirmation buttons frame (hidden by default)
        self.confirm_frame = tk.Frame(control_frame, bg="#f0f0f0")
        self.confirm_frame.pack(fill=tk.X, pady=(10, 0))
        self.confirm_frame.pack_forget()  # Hide initially
        
        tk.Label(
            self.confirm_frame,
            text="Is that correct?",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=10)
        
        self.yes_button = tk.Button(
            self.confirm_frame,
            text="✓ YES",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
            height=2,
            command=self.confirm_yes
        )
        self.yes_button.pack(side=tk.LEFT, padx=5)
        
        self.no_button = tk.Button(
            self.confirm_frame,
            text="✗ NO",
            font=("Arial", 14, "bold"),
            bg="#f44336",
            fg="white",
            width=12,
            height=2,
            command=self.confirm_no
        )
        self.no_button.pack(side=tk.LEFT, padx=5)
        
        # Consent buttons frame (hidden by default)
        self.consent_frame = tk.Frame(control_frame, bg="#f0f0f0")
        self.consent_frame.pack(fill=tk.X, pady=(10, 0))
        self.consent_frame.pack_forget()  # Hide initially
        
        tk.Label(
            self.consent_frame,
            text="Do you consent to participate?",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=10)
        
        self.consent_yes_button = tk.Button(
            self.consent_frame,
            text="✓ I CONSENT",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=14,
            height=2,
            command=self.consent_yes
        )
        self.consent_yes_button.pack(side=tk.LEFT, padx=5)
        
        self.consent_no_button = tk.Button(
            self.consent_frame,
            text="✗ I DECLINE",
            font=("Arial", 14, "bold"),
            bg="#f44336",
            fg="white",
            width=14,
            height=2,
            command=self.consent_no
        )
        self.consent_no_button.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text=" Use the BIG RED BUTTON to speak your answer, or type in the text field",
            font=("Arial", 10),
            bg="#FFF3E0",
            fg="#E65100",
            pady=10
        )
        instructions.pack(fill=tk.X, padx=25, pady=(0, 15))
    
    def _tts_worker(self):
        """Background worker thread for TTS - prevents threading issues"""
        while self.tts_worker_running:
            try:
                text = self.tts_queue.get(timeout=0.5)
                if text is None:  # Poison pill to stop worker
                    break
                
                with self.tts_lock:
                    try:
                        # Use the shared engine instance
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"  TTS Error: {e}")
                
                self.tts_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"  TTS Worker Error: {e}")
    
    def speak(self, text, wait=True, blocking=False):
        """Robot speaks using TTS - uses queue-based system to prevent threading issues"""
        if not self.tts_ready:
            return
        
        # Add to queue
        self.tts_queue.put(text)
        
        # Wait for it to complete if requested
        if wait or blocking:
            self.tts_queue.join()
    
    def add_robot_message(self, text):
        """Add robot message"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "[Pepper]: ", "robot")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        # Log to transcript
        if hasattr(self, 'logger'):
            self.logger.add_to_transcript("Pepper", text)
    
    def add_user_message(self, text):
        """Add user message"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "[You]: ", "user")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        # Log to transcript
        if hasattr(self, 'logger'):
            self.logger.add_to_transcript("User", text)
    
    def add_system_message(self, text):
        """Add system info"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"   [{text}]\n", "system")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def start_screening(self):
        """Start PHQ-9 screening"""
        self.session_active = True
        self.current_question = 0
        self.final_scores = [None] * 9
        self.attempts_per_question = {i: [] for i in range(9)}
        self.retry_counts = {i: 0 for i in range(9)}
        self.start_button.config(state=tk.DISABLED)
        self.text_input.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        
        if ASR_AVAILABLE and self.mic_available:
            self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK")
        
        # Run consent sequentially but non-blocking
        def consent_thread():
            # First disclaimer
            consent = "Hello! Before we begin, I want to inform you that this is a technical demonstration for research purposes only. This is NOT a psychological evaluation or medical diagnosis."
            self.root.after(0, lambda: self.add_robot_message(consent))
            self.speak(consent, wait=True)
            time.sleep(1)
            
            # Second disclaimer
            consent2 = "The information collected will be used solely for technical testing. If you have real health concerns, please consult a qualified healthcare professional."
            self.root.after(0, lambda: self.add_robot_message(consent2))
            self.speak(consent2, wait=True)
            time.sleep(1)
            
            # Ask for consent
            consent_question = "Do you consent to participate in this screening?"
            self.root.after(0, lambda: self.add_robot_message(consent_question))
            self.speak(consent_question, wait=True)
            
            # Disable voice/text input and show consent buttons
            self.mic_button.config(state=tk.DISABLED)
            self.text_input.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.root.after(0, lambda: self.consent_frame.pack(fill=tk.X, pady=(10, 0)))
            
            # Set waiting for consent flag
            self.waiting_for_consent = True
            
            self.logger.log_turn(
                userRawSpeech="", asrTranscript="", languageDetected="EN",
                phqQuestionId="", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
                gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
                gptResponse="", finalRobotOutput=consent + " " + consent2 + " " + consent_question, notes="Consent requested"
            )
        
        threading.Thread(target=consent_thread, daemon=True).start()
    
    def ask_question(self):
        """Ask current PHQ-9 question"""
        if self.current_question >= 9:
            self.complete_screening()
            return
        
        q = PHQ9_QUESTIONS[self.current_question]
        self.progress_label.config(text=f"Question {self.current_question + 1} / 9")
        self.progress_bar['value'] = self.current_question + 1
        
        question_text = f"Question {self.current_question + 1}: {q.question}"
        
        # Display and speak question
        def question_thread():
            self.root.after(0, lambda: self.add_robot_message(question_text))
            self.speak(question_text, wait=True)  # Wait for speech to finish
            time.sleep(0.5)
            
            # Enable mic button AFTER speaking finishes
            if ASR_AVAILABLE and self.mic_available and not self.is_listening:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
            
            self.logger.log_turn(
                userRawSpeech="", asrTranscript="", languageDetected="EN",
                phqQuestionId=f"Q{q.id}", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
                gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
                gptResponse="", finalRobotOutput=question_text, notes=f"Question {self.current_question + 1}"
            )
        
        threading.Thread(target=question_thread, daemon=True).start()
        self.status_label.config(text=f"Question {self.current_question + 1}/9 - Press microphone or type answer")
    
    def start_voice_input(self):
        """Start listening via microphone using Whisper"""
        if not self.mic_available or self.is_listening:
            self.add_system_message("[Error] Microphone not available. Please use text input.")
            return
        
        self.is_listening = True
        # Debounce mic button during listen
        self.mic_button.config(text="LISTENING...", bg="#D32F2F", state=tk.DISABLED)
        self.status_label.config(text="LISTENING... Speak your answer now!")
        # Make ASR snappier
        self.recognizer.pause_threshold = LISTEN_PAUSE_THRESHOLD
        
        def listen_thread():
            failures = 0
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=LISTEN_AMBIENT_DURATION)
                    self.root.after(0, lambda: self.add_system_message("[Listening] Speak now!"))
                    audio = self.recognizer.listen(
                        source,
                        timeout=LISTEN_TIMEOUT,
                        phrase_time_limit=LISTEN_PHRASE_LIMIT
                    )
                
                self.root.after(0, lambda: self.status_label.config(text="🔄 Transcribing..."))
                
                # Save audio to temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    temp_filename = temp_audio.name
                    with wave.open(temp_filename, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio.get_wav_data(convert_rate=16000))
                
                # Use OpenAI Whisper for transcription
                openai.api_key = OPENAI_API_KEY
                with open(temp_filename, 'rb') as audio_file:
                    transcript = openai.Audio.transcribe(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                
                # Clean up temp file
                import os
                os.unlink(temp_filename)
                
                text = transcript.text.strip()
                
                # Check if transcription is meaningful
                if len(text) < 2 or text.lower() in ['oh', 'uh', 'um', 'ah']:
                    self.root.after(0, lambda: self.add_system_message("[Error] No clear speech detected. Please speak your answer clearly."))
                    return
                
                self.root.after(0, lambda: self.process_response(text, is_voice=True))
                
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError) as e:
                failures += 1
                if isinstance(e, sr.WaitTimeoutError):
                    msg = " No speech detected. Try again or type."
                elif isinstance(e, sr.UnknownValueError):
                    msg = "[Error] Speech not understood. Please try again."
                else:
                    msg = "[Error] Speech service issue. Please try again or type."

                if failures >= 2:
                    self.root.after(0, lambda: self.add_system_message("Speech input failed twice, please type your answer instead."))
                    return
                else:
                    self.root.after(0, lambda: self.add_system_message(msg))
                    return
            except Exception as e:
                error_msg = str(e)
                print(f"Voice input error: {error_msg}")
                if "PyAudio" in error_msg or "portaudio" in error_msg:
                    self.root.after(0, lambda: self.add_system_message("[Error] Microphone error. Please use text input."))
                    self.mic_available = False
                    self.root.after(0, lambda: self.mic_button.config(state=tk.DISABLED, text="MIC N/A"))
                else:
                    self.root.after(0, lambda: self.add_system_message(f"Error: {error_msg[:50]}. Use text input."))
            finally:
                self.root.after(0, self.stop_listening)
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self.mic_button.config(text="PRESS TO SPEAK", bg="#FF5722", state=tk.NORMAL)
    
    def send_text(self):
        """Send text input"""
        text = self.text_input.get().strip()
        if text and self.session_active:
            self.text_input.delete(0, tk.END)
            self.process_response(text, is_voice=False)
    
    def confirm_yes(self):
        """Handle YES confirmation button click"""
        if not self.waiting_for_answer_confirmation:
            return
        
        self.waiting_for_answer_confirmation = False
        self.confirm_frame.pack_forget()  # Hide confirmation buttons
        
        score = self.pending_score
        confirmation = self.pending_confirmation
        
        # Store as FINAL confirmed score
        self.final_scores[self.current_question] = score
        self.add_system_message(f"✓ Confirmed: {confirmation}")
        
        # Log
        q = PHQ9_QUESTIONS[self.current_question]
        self.logger.log_turn(
            userRawSpeech="[BUTTON: YES]", asrTranscript=confirmation,
            languageDetected="EN",
            phqQuestionId=f"Q{q.id}",
            handlingModule=self.pending_module,
            pepperLocalNlpSuccess=(self.pending_module == "PEPPER_LOCAL"),
            gptUsed=self.pending_gpt_used,
            gptReason=self.pending_gpt_reason if self.pending_gpt_reason else "",
            gptModel="gpt-4o-mini" if self.pending_gpt_used else "",
            gptPromptSnippet=self.pending_gpt_prompt_snippet if self.pending_gpt_used else "",
            gptResponse=self.pending_gpt_response if self.pending_gpt_used else "",
            finalRobotOutput="Confirmed via button",
            notes=f"Q{self.current_question + 1} FINAL score={score}, retries={self.retry_counts[self.current_question]}"
        )
        
        # CHECK FOR CRISIS PROTOCOL (Q9 with score > 0)
        if self.handle_crisis_protocol(score):
            return
        
        # Move directly to next question
        def continue_thread():
            if self.current_question < 8:
                next_msg = "Let me ask you the next question."
                self.root.after(0, lambda: self.add_robot_message(next_msg))
                self.speak(next_msg, wait=True)
                time.sleep(0.5)
            
            self.current_question += 1
            # Re-enable input before next question
            self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            if ASR_AVAILABLE and self.mic_available:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
            self.root.after(500, self.ask_question)
        
        threading.Thread(target=continue_thread, daemon=True).start()
    
    def confirm_no(self):
        """Handle NO confirmation button click"""
        if not self.waiting_for_answer_confirmation:
            return
        
        self.waiting_for_answer_confirmation = False
        self.confirm_frame.pack_forget()  # Hide confirmation buttons
        
        # User says no - increment retry count
        self.retry_counts[self.current_question] += 1
        self.add_system_message(f"✗ Not confirmed. Retry {self.retry_counts[self.current_question]}/{self.MAX_RETRIES}")
        
        # Check if max retries reached
        if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
            # Use last attempted score or default to 0
            fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
            self.final_scores[self.current_question] = fallback_score
            
            self.add_system_message(f"Max retries reached. Using fallback score: {fallback_score}")
            
            fallback_msg = "I understand this is difficult. Let's move to the next question."
            self.add_robot_message(fallback_msg)
            self.speak(fallback_msg, wait=True)
            
            # Move to next question
            def continue_after_retry():
                time.sleep(0.5)
                self.current_question += 1
                self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
                if ASR_AVAILABLE and self.mic_available:
                    self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                self.root.after(500, self.ask_question)
            
            threading.Thread(target=continue_after_retry, daemon=True).start()
            return
        
        # Ask again
        def reask_thread():
            retry_msg = "I see. Let me ask the question again. Please answer with: not at all, several days, more than half the days, or nearly every day."
            self.root.after(0, lambda: self.add_robot_message(retry_msg))
            self.speak(retry_msg, wait=True)
            
            # Re-ask question
            q = PHQ9_QUESTIONS[self.current_question]
            question_text = f"Question {self.current_question + 1}: {q.question}"
            self.root.after(0, lambda: self.add_robot_message(question_text))
            self.speak(question_text, wait=True)
            
            # Re-enable input after re-asking
            self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            if ASR_AVAILABLE and self.mic_available:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
        
        threading.Thread(target=reask_thread, daemon=True).start()
    
    def consent_yes(self):
        """Handle consent YES button click"""
        if not self.waiting_for_consent:
            return
        
        self.waiting_for_consent = False
        self.consent_frame.pack_forget()  # Hide consent buttons
        
        self.add_system_message("✓ Consent given via button")
        
        # Log consent
        self.logger.log_turn(
            userRawSpeech="[BUTTON: I CONSENT]", asrTranscript="Consent given",
            languageDetected="EN", phqQuestionId="",
            handlingModule="BUTTON", pepperLocalNlpSuccess=True,
            gptUsed=False, finalRobotOutput="Thank you for consenting",
            notes="Consent given via button click"
        )
        
        # Continue with screening
        def continue_screening():
            thank_msg = "Thank you for consenting."
            self.root.after(0, lambda: self.add_robot_message(thank_msg))
            self.speak(thank_msg, wait=True)
            
            explain_msg = "I will now ask you 9 questions about how you've been feeling over the last 2 weeks. Please answer with: not at all, several days, more than half the days, or nearly every day."
            self.root.after(0, lambda: self.add_robot_message(explain_msg))
            self.speak(explain_msg, wait=True)
            
            # Re-enable input
            self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            if ASR_AVAILABLE and self.mic_available:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
            
            # Ask first question
            self.root.after(500, self.ask_question)
        
        threading.Thread(target=continue_screening, daemon=True).start()
    
    def consent_no(self):
        """Handle consent NO button click"""
        if not self.waiting_for_consent:
            return
        
        self.waiting_for_consent = False
        self.consent_frame.pack_forget()  # Hide consent buttons
        
        self.add_system_message("✗ Consent declined via button")
        
        # Log declined consent
        self.logger.log_turn(
            userRawSpeech="[BUTTON: I DECLINE]", asrTranscript="Consent declined",
            languageDetected="EN", phqQuestionId="",
            handlingModule="BUTTON", pepperLocalNlpSuccess=True,
            gptUsed=False, finalRobotOutput="Session ended - consent declined",
            notes="Consent declined via button click"
        )
        
        # End session
        def end_session():
            decline_msg = "I understand. Thank you for your time. The session will now end."
            self.root.after(0, lambda: self.add_robot_message(decline_msg))
            self.speak(decline_msg, wait=True)
            
            self.session_active = False
            self.root.after(0, lambda: self.restart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.add_system_message("Session ended - consent declined"))
        
        threading.Thread(target=end_session, daemon=True).start()
    
    def parse_response(self, response: str) -> tuple:
        """Parse response locally - returns (score, user_friendly_confirmation)"""
        resp_lower = response.lower().strip()
        
        # Score 0
        if "not at all" in resp_lower or "never" in resp_lower:
            return (0, "not at all")
        elif resp_lower == "0":
            return (0, "not at all")
        
        # Score 1
        elif "several days" in resp_lower:
            return (1, "several days")
        elif "sometimes" in resp_lower or "few days" in resp_lower:
            return (1, "sometimes")
        elif resp_lower == "1":
            return (1, "several days")
        
        # Score 2
        elif "more than half" in resp_lower:
            return (2, "more than half the days")
        elif "most days" in resp_lower or "often" in resp_lower:
            return (2, "often")
        elif resp_lower == "2":
            return (2, "more than half the days")
        
        # Score 3
        elif "nearly every day" in resp_lower:
            return (3, "nearly every day")
        elif "every day" in resp_lower or "always" in resp_lower or "all the time" in resp_lower:
            return (3, "every day")
        elif resp_lower == "3":
            return (3, "nearly every day")
        
        # Try matching PHQ-9 options
        q = PHQ9_QUESTIONS[self.current_question]
        for idx, option in enumerate(q.options):
            if option.lower() in resp_lower:
                return (q.scores[idx], option)
        
        return (-1, None)
    
    def handle_crisis_protocol(self, score: int):
        """Handle Q9 safety protocol when self-harm risk is detected"""
        if self.current_question == 8 and score > 0:  # Q9 is index 8
            # Pause conversation
            self.text_input.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.mic_button.config(state=tk.DISABLED)
            
            # Add crisis warning to chat
            self.add_system_message(" SAFETY PROTOCOL ACTIVATED ")
            
            # Run crisis protocol in background thread
            def crisis_thread():
                # Display supportive message
                crisis_msg = "I want to acknowledge your response. Your safety is very important. Please know that help is available."
                self.root.after(0, lambda: self.add_robot_message(crisis_msg))
                self.speak(crisis_msg, wait=True)
                time.sleep(4)
                
                # Show crisis resources
                resources_title = "CRISIS RESOURCES - Please take note of these:"
                self.root.after(0, lambda: self.add_robot_message(resources_title))
                self.speak(resources_title, wait=True)
                time.sleep(2)
                
                # Display hotlines in chat (visible on screen)
                crisis_info = """
EMERGENCY HOTLINES:
• Germany Crisis Hotline: 0800 111 0 111 or 0800 111 0 222
• International Crisis Line: 116 123
• Emergency Services: 112

You are not alone. Professional help is available 24/7.
Please consider reaching out to a mental health professional or counselor."""
                
                def add_crisis_info():
                    self.chat_area.config(state=tk.NORMAL)
                    self.chat_area.insert(tk.END, crisis_info + "\n\n", "system")
                    self.chat_area.see(tk.END)
                    self.chat_area.config(state=tk.DISABLED)
                
                self.root.after(0, add_crisis_info)
                
                # Speak resources
                resources_msg = "Germany Crisis Hotline: 0800 111 0 111. International Crisis Line: 116 123. Emergency Services: 112. Please consider reaching out to a mental health professional. You are not alone, and help is available."
                self.speak(resources_msg, wait=True)
                time.sleep(8)
                
                # Important reminder
                reminder = "This screening is not a diagnosis. Please contact a healthcare professional for proper evaluation and support."
                self.root.after(0, lambda: self.add_robot_message(reminder))
                self.speak(reminder, wait=True)
                time.sleep(5)
                
                # Ask for acknowledgment
                ack_msg = "Have you noted these resources? Type 'yes' or press the microphone to continue."
                self.root.after(0, lambda: self.add_robot_message(ack_msg))
                self.speak("Have you noted these resources? Please confirm to continue.", wait=True)
                
                # Re-enable input for acknowledgment AFTER speaking finishes
                self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
                if ASR_AVAILABLE and self.mic_available:
                    self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                
                # Set flag to wait for acknowledgment
                self.waiting_for_crisis_ack = True
            
            threading.Thread(target=crisis_thread, daemon=True).start()
            
            return True
        return False
    
    def get_acknowledgment(self, score: int) -> str:
        """Get varied acknowledgment based on score (without mentioning numbers)"""
        acknowledgments = {
            0: [
                "I understand, not at all.",
                "Okay, not at all.",
                "Got it, you haven't experienced that.",
                "Thank you, not at all."
            ],
            1: [
                "I see, several days.",
                "Understood, several days.",
                "Okay, on several days.",
                "Thank you, several days."
            ],
            2: [
                "I hear you, more than half the days.",
                "Understood, more than half the days.",
                "Okay, more than half the days.",
                "Thank you, more than half the days."
            ],
            3: [
                "I understand, nearly every day.",
                "Okay, nearly every day.",
                "Got it, nearly every day.",
                "Thank you, nearly every day."
            ]
        }
        if score in acknowledgments:
            return random.choice(acknowledgments[score])
        return "Thank you, I've noted your response."
    
    def parse_with_gpt(self, response: str) -> tuple:
        """Use GPT to parse unclear response into PHQ-9 score
        Returns: (score, confirmation, prompt_snippet, gpt_response)
        """
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            q = PHQ9_QUESTIONS[self.current_question]
            
            prompt = f"Question: {q.question}\n0=Not at all, 1=Several days, 2=More than half, 3=Nearly every day\nRespond: NUMBER|PHRASE"
            
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"{response}"}
                ],
                temperature=0,
                max_tokens=10
            )
            
            result = resp.choices[0].message.content.strip()
            tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            
            full_prompt = f"System: {prompt}\nUser: {response}"
            
            # Log GPT call
            self.logger.log_gpt_call(
                purpose=f"Parse PHQ-9 Q{self.current_question + 1} response",
                prompt=full_prompt,
                response=result,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            parts = result.split('|')
            if len(parts) >= 2:
                score = int(parts[0].strip())
                confirm = parts[1].strip()
                # Return prompt snippet (first 100 chars) and response
                prompt_snippet = full_prompt[:100] + "..." if len(full_prompt) > 100 else full_prompt
                return (score, confirm, prompt_snippet, result)
            else:
                return (-1, None, full_prompt[:100], result)
        except Exception as e:
            print(f"GPT parse error: {e}")
            return (-1, None, "", str(e))
    
    def check_confirmation_with_gpt(self, response: str) -> bool:
        """Use GPT to understand if user confirmed"""
        if not OPENAI_API_KEY:
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['yes', 'correct', 'right', 'yeah', 'yep', 'ok', 'okay'])
        
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            prompt = "Reply YES if confirming, NO if not."
            user_msg = f"Is '{response}' a confirmation?"
            
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0,
                max_tokens=3
            )
            
            result = resp.choices[0].message.content.strip().upper()
            tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            
            # Log GPT call
            self.logger.log_gpt_call(
                purpose="Check answer confirmation",
                prompt=f"System: {prompt}\nUser: {user_msg}",
                response=result,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            return "YES" in result
        except Exception as e:
            print(f"GPT confirmation error: {e}")
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['yes', 'correct', 'right', 'yeah', 'yep', 'ok', 'okay'])
    
    def check_consent_with_gpt(self, response: str) -> bool:
        """Use GPT to understand if user consented"""
        if not OPENAI_API_KEY:
            # Fallback to keywords
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['yes', 'yeah', 'yep', 'accept', 'agree', 'consent', 'ok', 'okay', 'sure', 'fine', 'alright'])
        
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            prompt = "Reply YES if agrees/consents, NO if declines."
            user_msg = f"Does '{response}' mean consent?"
            
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0,
                max_tokens=3
            )
            
            result = resp.choices[0].message.content.strip().upper()
            tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            
            # Log GPT call
            self.logger.log_gpt_call(
                purpose="Check consent",
                prompt=f"System: {prompt}\nUser: {user_msg}",
                response=result,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            return "YES" in result
        except Exception as e:
            print(f"GPT consent error: {e}")
            # Fallback
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['yes', 'yeah', 'yep', 'accept', 'agree', 'consent', 'ok', 'okay', 'sure', 'fine', 'alright'])
    
    def call_gpt_fallback(self, response: str) -> tuple:
        """Call GPT for unclear responses"""
        q = PHQ9_QUESTIONS[self.current_question]
        prompt = f"""The user is answering PHQ-9: {q.question}
User said: "{response}"

Options: Not at all (0), Several days (1), More than half (2), Nearly every day (3)
Respond with ONLY the number 0, 1, 2, or 3."""

        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0,
                max_tokens=5
            )
            gpt_text = resp.choices[0].message.content.strip()
            tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            score = int(gpt_text[0]) if gpt_text[0] in "0123" else 1
            
            # Log GPT call
            self.logger.log_gpt_call(
                purpose=f"Fallback parse PHQ-9 Q{self.current_question + 1}",
                prompt=prompt,
                response=gpt_text,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            return score, gpt_text
        except Exception as e:
            print(f"GPT fallback error: {e}")
            return 1, "GPT_ERROR"
    
    def process_response(self, response: str, is_voice: bool):
        """Process user response in a background thread to prevent GUI freeze"""
        if getattr(self, 'is_processing', False):
            print(" Input ignored - already processing")
            return
            
        self.is_processing = True
        threading.Thread(target=self._process_response_wrapper, args=(response, is_voice), daemon=True).start()

    def _process_response_wrapper(self, response, is_voice):
        """Wrapper to ensure processing flag is reset"""
        try:
            self._process_response_logic(response, is_voice)
        finally:
            self.is_processing = False

    def _process_response_logic(self, response: str, is_voice: bool):
        """Worker method containing the actual logic"""
        if not self.session_active:
            return
            
            # Handle consent response
        if self.waiting_for_consent:
            self.add_user_message(response)
            
            # Use GPT to understand consent
            consent_given = self.check_consent_with_gpt(response)
            
            if consent_given:
                self.waiting_for_consent = False
                self.add_system_message("✓ Consent given")
                
                # Thank and explain
                def proceed_thread():
                    thanks = "Thank you for consenting."
                    self.root.after(0, lambda: self.add_robot_message(thanks))
                    self.speak(thanks, wait=True)
                    time.sleep(1)
                    
                    instructions = "I will now ask you 9 questions about how you've been feeling over the last 2 weeks. Please answer with: not at all, several days, more than half the days, or nearly every day."
                    self.root.after(0, lambda: self.add_robot_message(instructions))
                    self.speak(instructions, wait=True)
                    time.sleep(1)
                    
                    # Enable mic button before starting questions
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                    
                    # Start questions
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=proceed_thread, daemon=True).start()
                return
            else:
                # User declined
                self.add_system_message("[Consent declined]")
                decline_msg = "I understand. Thank you for your time. The screening will not proceed."
                self.add_robot_message(decline_msg)
                self.speak(decline_msg, wait=True)
                self.session_active = False
                self.text_input.config(state=tk.DISABLED)
                self.send_button.config(state=tk.DISABLED)
                self.mic_button.config(state=tk.DISABLED)
                return
        
        # Handle answer confirmation
        if self.waiting_for_answer_confirmation:
            self.add_user_message(response)
            
            # Use GPT to check confirmation
            confirmed = self.check_confirmation_with_gpt(response)
            
            if confirmed:
                self.waiting_for_answer_confirmation = False
                score = self.pending_score
                confirmation = self.pending_confirmation
                
                # Store as FINAL confirmed score
                self.final_scores[self.current_question] = score
                
                # Log
                q = PHQ9_QUESTIONS[self.current_question]
                self.logger.log_turn(
                    userRawSpeech="", asrTranscript=confirmation,
                    languageDetected="EN",
                    phqQuestionId=f"Q{q.id}",
                    handlingModule=self.pending_module,
                    pepperLocalNlpSuccess=(self.pending_module == "PEPPER_LOCAL"),
                    gptUsed=self.pending_gpt_used,
                    gptReason=self.pending_gpt_reason,
                    gptModel="gpt-4o-mini" if self.pending_gpt_used else "",
                    gptPromptSnippet="",
                    gptResponse="",
                    finalRobotOutput="Confirmed",
                    notes=f"Q{self.current_question + 1} FINAL score={score}, retries={self.retry_counts[self.current_question]}"
                )
                
                # CHECK FOR CRISIS PROTOCOL (Q9 with score > 0)
                if self.handle_crisis_protocol(score):
                    return
                
                # Move directly to next question
                def continue_thread():
                    if self.current_question < 8:
                        next_msg = "Let me ask you the next question."
                        self.root.after(0, lambda: self.add_robot_message(next_msg))
                        self.speak(next_msg, wait=True)
                        time.sleep(0.5)
                    
                    self.current_question += 1
                    # Re-enable mic button before next question
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=continue_thread, daemon=True).start()
                return
            else:
                # User says no - increment retry count
                self.retry_counts[self.current_question] += 1
                self.waiting_for_answer_confirmation = False
                
                # Check if max retries reached
                if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
                    # Use last attempted score or default to 0
                    fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
                    self.final_scores[self.current_question] = fallback_score
                    
                    self.add_system_message(f" Max retries reached for Q{self.current_question + 1}. Using fallback score: {fallback_score}")
                    
                    fallback_msg = "I understand this is difficult. Let's move to the next question."
                    self.add_robot_message(fallback_msg)
                    self.speak(fallback_msg, wait=True)
                    
                    # Move to next question
                    def continue_after_retry():
                        time.sleep(0.5)
                        self.current_question += 1
                        # Re-enable mic button before next question
                        if ASR_AVAILABLE and self.mic_available:
                            self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                        self.root.after(500, self.ask_question)
                    
                    threading.Thread(target=continue_after_retry, daemon=True).start()
                    return
                
                # Ask again
                retry_msg = "I see. Let me ask the question again. Please answer with: not at all, several days, more than half the days, or nearly every day."
                self.add_robot_message(retry_msg)
                self.speak(retry_msg, wait=True)
                
                # Re-ask question
                def reask():
                    q = PHQ9_QUESTIONS[self.current_question]
                    question_text = f"Question {self.current_question + 1}: {q.question}"
                    self.root.after(0, lambda: self.add_robot_message(question_text))
                    self.speak(question_text, wait=True)
                    
                    # Enable mic button after re-asking
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                
                threading.Thread(target=reask, daemon=True).start()
                return
        
        # Handle crisis acknowledgment
        if self.waiting_for_crisis_ack:
            resp_lower = response.lower().strip()
            if any(word in resp_lower for word in ['yes', 'ok', 'okay', 'noted', 'understood', 'continue', 'proceed']):
                self.waiting_for_crisis_ack = False
                self.add_user_message(response)
                self.add_system_message("Crisis resources acknowledged. Continuing screening...")
                
                # Move to next question or complete
                self.current_question += 1
                # Re-enable mic button before next question
                if ASR_AVAILABLE and self.mic_available:
                    self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK")
                self.root.after(2000, self.ask_question)
                return
            else:
                self.add_system_message("Please confirm you have noted the crisis resources by saying 'yes' or typing 'yes'.")
                return
        
        self.add_user_message(response)
        
        # Detect language
        lang = LanguageDetector.detect_language(response)
        self.add_system_message(f"Language: {lang}")
        
        # Try local NLP
        score, confirmation = self.parse_response(response)
        local_success = 0 <= score <= 3
        
        gpt_used = False
        gpt_reason = None
        gpt_prompt_snippet = ""
        gpt_response_text = ""
        module = "PEPPER_LOCAL"
        
        if not local_success and OPENAI_API_KEY:
            # Use GPT to understand response
            self.add_system_message("Using GPT to understand response...")
            gpt_score, gpt_confirmation, gpt_prompt_snippet, gpt_response_text = self.parse_with_gpt(response)
            if 0 <= gpt_score <= 3:
                score = gpt_score
                confirmation = gpt_confirmation
                local_success = False
                gpt_used = True
                gpt_reason = "parse_answer"
                module = "GPT_FALLBACK"
                self.add_system_message(f"GPT understood: score={score}, as: {confirmation}")
            else:
                # Increment retry and ask for clarification
                self.retry_counts[self.current_question] += 1
                
                # --- ADDED LOGGING ---
                q = PHQ9_QUESTIONS[self.current_question]
                self.logger.log_turn(
                    userRawSpeech=response, asrTranscript=response, languageDetected=lang,
                    phqQuestionId=f"Q{q.id}", handlingModule="GPT_FALLBACK", pepperLocalNlpSuccess=False,
                    gptUsed=True, gptReason="parse_answer", gptModel="gpt-4o-mini",
                    gptPromptSnippet=gpt_prompt_snippet, gptResponse=gpt_response_text,
                    finalRobotOutput="Clarification asked", 
                    notes=f"Failed attempt (GPT failed). Retry {self.retry_counts[self.current_question]}/{self.MAX_RETRIES}"
                )
                # ---------------------
                
                if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
                    # Max retries - use fallback
                    fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
                    self.final_scores[self.current_question] = fallback_score
                    self.add_system_message(f" Max retries. Using fallback: {fallback_score}")
                    
                    fallback_msg = "I'm having trouble understanding. Let's move to the next question."
                    self.add_robot_message(fallback_msg)
                    self.speak(fallback_msg, wait=True)
                    
                    def skip_question():
                        time.sleep(0.5)
                        self.current_question += 1
                        # Re-enable mic button before next question
                        if ASR_AVAILABLE and self.mic_available:
                            self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                        self.root.after(500, self.ask_question)
                    
                    threading.Thread(target=skip_question, daemon=True).start()
                    return
                
                clarify_msg = f"I heard '{response}', but I'm not sure I understood correctly. Could you please repeat using: not at all, several days, more than half the days, or nearly every day?"
                self.add_robot_message(clarify_msg)
                self.speak(clarify_msg, wait=True)
                self.add_system_message("Asked for clarification")
                
                # Re-enable mic button after clarification
                if ASR_AVAILABLE and self.mic_available:
                    self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK")
                
                return
        elif not local_success:
            # Increment retry
            self.retry_counts[self.current_question] += 1
            
            # --- ADDED LOGGING ---
            q = PHQ9_QUESTIONS[self.current_question]
            self.logger.log_turn(
                userRawSpeech=response, asrTranscript=response, languageDetected=lang,
                phqQuestionId=f"Q{q.id}", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=False,
                gptUsed=False, finalRobotOutput="Clarification asked", 
                notes=f"Failed attempt. Retry {self.retry_counts[self.current_question]}/{self.MAX_RETRIES}"
            )
            # ---------------------
            
            if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
                fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
                self.final_scores[self.current_question] = fallback_score
                self.add_system_message(f" Max retries. Using fallback: {fallback_score}")
                
                fallback_msg = "Let's move to the next question."
                self.add_robot_message(fallback_msg)
                self.speak(fallback_msg, wait=True)
                
                def skip_question():
                    time.sleep(0.5)
                    self.current_question += 1
                    # Re-enable mic button before next question
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK"))
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=skip_question, daemon=True).start()
                return
            
            clarify_msg = f"I heard '{response}', but I'm not sure I understood correctly. Could you please repeat using: not at all, several days, more than half the days, or nearly every day?"
            self.add_robot_message(clarify_msg)
            self.speak(clarify_msg, wait=True)
            self.add_system_message("Asked for clarification")
            
            # Re-enable mic button after clarification
            if ASR_AVAILABLE and self.mic_available:
                self.mic_button.config(state=tk.NORMAL, text="PRESS TO SPEAK")
            
            return
        else:
            self.add_system_message(f"Local NLP: score={score}, understood as: {confirmation}")
        
        # Store as attempt (not final yet)
        self.attempts_per_question[self.current_question].append(score)
        
        # Confirm what was understood
        confirm_msg = f"I understood: {confirmation}. Is that correct?"
        self.add_robot_message(confirm_msg)
        self.speak(confirm_msg, wait=True)
        
        # Disable voice/text input and show confirmation buttons
        self.mic_button.config(state=tk.DISABLED)
        self.text_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.root.after(0, lambda: self.confirm_frame.pack(fill=tk.X, pady=(10, 0)))
        
        # Set flag waiting for confirmation
        self.waiting_for_answer_confirmation = True
        self.pending_score = score
        self.pending_confirmation = confirmation
        self.pending_gpt_used = gpt_used
        self.pending_gpt_reason = gpt_reason
        self.pending_gpt_prompt_snippet = gpt_prompt_snippet
        self.pending_gpt_response = gpt_response_text
        self.pending_module = module
        return
    
    def complete_screening(self):
        """Finish screening"""
        self.session_active = False
        self.text_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.mic_button.config(state=tk.DISABLED)
        
        # Fill any missing scores with 0 (shouldn't happen but safety check)
        for i in range(9):
            if self.final_scores[i] is None:
                self.final_scores[i] = 0
                self.add_system_message(f" Warning: Q{i+1} has no final score, defaulting to 0")
        
        # Calculate total (must be 0-27)
        total = sum(self.final_scores)
        
        # Safety clamp
        if total > 27:
            self.add_system_message(f"[ERROR] Score {total} exceeds maximum 27! Clamping.")
            total = 27
        elif total < 0:
            self.add_system_message(f"[ERROR] Score {total} is negative! Clamping.")
            total = 0
        
        severity = self.get_severity(total)
        severity_description = self.get_severity_description(severity)
        
        # Save session data
        session_folder = self.logger.save_session_data(self.final_scores, total, severity, self.retry_counts)
        
        # Display score breakdown
        self.add_system_message(f"COMPLETED | Total Score: {total} out of 27 | Severity: {severity.upper()}")
        self.add_system_message(f"Final responses (Q1-Q9): {self.final_scores}")
        self.add_system_message(f"Retry counts: {list(self.retry_counts.values())}")
        self.add_system_message(f"Session saved: {session_folder}")
        
        # Speak summary in background thread
        def summary_thread():
            # First message - score
            intro = f"Thank you for completing all 9 questions. Let me share your results."
            self.root.after(0, lambda: self.add_robot_message(intro))
            self.speak(intro, wait=True)
            
            # Second message - score breakdown
            score_msg = f"Your total score is {total} out of a maximum of 27 points. This indicates {severity} level symptoms."
            self.root.after(0, lambda: self.add_robot_message(score_msg))
            self.speak(score_msg, wait=True)
            
            # Third message - severity description
            self.root.after(0, lambda: self.add_robot_message(severity_description))
            self.speak(severity_description, wait=True)
            
            # Fourth message - disclaimer
            disclaimer = "Please remember: This is a technical demonstration only, not a medical diagnosis. This data is collected for research purposes. If you have real health concerns, please consult a qualified healthcare professional."
            self.root.after(0, lambda: self.add_robot_message(disclaimer))
            self.speak(disclaimer, wait=True)
            
            self.root.after(0, lambda: self.export_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.restart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text=f"Completed! Total score: {total}/27 - {severity}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Screening Complete", 
                f"PHQ-9 Screening Complete!\n\n"
                f"Total Score: {total} / 27\n"
                f"Severity Level: {severity.upper()}\n\n"
                f"{severity_description}\n\n"
                f" This is for technical demonstration only.\n\n"
                f"Session data saved to:\n{session_folder}"))
        
        threading.Thread(target=summary_thread, daemon=True).start()
    
    def get_severity(self, score):
        """Get severity level"""
        if score <= 4: return "minimal"
        elif score <= 9: return "mild"
        elif score <= 14: return "moderate"
        elif score <= 19: return "moderately severe"
        else: return "severe"
    
    def get_severity_description(self, severity):
        """Get detailed description for each severity level"""
        descriptions = {
            "minimal": "Minimal depression symptoms. Scores in this range (0-4) typically suggest little to no depressive symptoms.",
            "mild": "Mild depression symptoms. Scores in this range (5-9) may indicate mild depressive symptoms that might benefit from monitoring.",
            "moderate": "Moderate depression symptoms. Scores in this range (10-14) suggest moderate depressive symptoms that may warrant professional evaluation.",
            "moderately severe": "Moderately severe depression symptoms. Scores in this range (15-19) indicate significant symptoms that would benefit from professional care.",
            "severe": "Severe depression symptoms. Scores in this range (20-27) suggest severe depressive symptoms requiring immediate professional attention."
        }
        return descriptions.get(severity, "Unknown severity level.")
    
    def export_logs(self):
        """Export to CSV and open folder"""
        if hasattr(self, 'logger') and hasattr(self.logger, 'session_folder'):
            os.startfile(str(self.logger.session_folder))
            messagebox.showinfo("Session Data", f"Opening session folder:\n{self.logger.session_folder}")
        else:
            filename = self.logger.export_to_csv()
            messagebox.showinfo("Exported", f"Logs saved to:\n{filename}")
            os.startfile(os.getcwd())
    
    def restart_screening(self):
        """Restart the screening"""
        response = messagebox.askyesno("Restart", "Start a new screening session?\n\nCurrent session data is already saved.")
        if response:
            # Clear chat
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state=tk.DISABLED)
            
            # Reset state
            self.session_id = str(uuid.uuid4())
            self.logger = SimpleLogger(self.session_id)
            self.current_question = 0
            self.final_scores = [None] * 9
            self.attempts_per_question = {i: [] for i in range(9)}
            self.retry_counts = {i: 0 for i in range(9)}
            self.session_active = False
            self.waiting_for_consent = False
            self.waiting_for_answer_confirmation = False
            self.waiting_for_crisis_ack = False
            
            # Reset UI
            self.progress_bar['value'] = 0
            self.progress_label.config(text="Question 0 / 9")
            self.start_button.config(state=tk.NORMAL)
            self.text_input.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.mic_button.config(state=tk.DISABLED)
            self.export_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.status_label.config(text="Ready to start new session")
            
            # Welcome message
            self.add_robot_message("Ready for a new screening session. Click START SCREENING when ready.")
            self.speak("Ready for a new screening session.")
    
    def update_status(self, text):
        """Update status"""
        self.status_label.config(text=text)


def main():
    """Launch GUI"""
    print("\n" + "="*70)
    print("PHQ-9 VOICE SIMULATION")
    print("="*70)
    
    if not ASR_AVAILABLE:
        print("\n  Speech recognition not fully available")
        print("   Microphone button will be disabled")
        print("   You can use text input + hear robot speak via TTS\n")
    
    if not TTS_AVAILABLE:
        print("\n  Text-to-speech not available")
        print("   You can still see robot messages in the window\n")
    
    print(" Launching GUI window...")
    print("   - Green 'START SCREENING' button to begin")
    print("   - Red 'PRESS TO SPEAK' for voice input")
    print("   - Or type in text field\n")
    
    root = tk.Tk()
    app = VoicePHQ9GUI(root)
    
    # Force window to front
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    root.focus_force()
    
    root.mainloop()


if __name__ == "__main__":
    main()

