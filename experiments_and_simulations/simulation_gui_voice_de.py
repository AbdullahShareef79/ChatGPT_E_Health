#!/usr/bin/env python3
"""
PHQ-9 Health Screening Simulation - GERMAN VERSION
GUI with VOICE INPUT
Deutsche Version mit Sprachunterstützung
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
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
if not env_path.exists():
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
    print(f"  Fehler bei der Spracherkennung: {e}")
    ASR_AVAILABLE = False

# Import German PHQ-9 questions from session manager
from phq9_session_de import PHQ9_QUESTIONS_DE

# Simple language detector
class LanguageDetector:
    @staticmethod
    def detect_language(text):
        """Simple language detection - DE for German"""
        return "DE"

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
        
        # Create session folder in German language subfolder
        self.session_folder = Path("data") / "sessions" / "german" / f"session_{session_id[:8]}_{self.session_start.strftime('%Y%m%d_%H%M%S')}"
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
            print(f"⚠️ Error appending to CSV: {e}")
    
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
            "language": "DE",
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
            f.write(f"PHQ-9 Screening Session (DEUTSCH)\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Datum: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n\n")
            
            for msg in self.transcript:
                f.write(f"[{msg['timestamp'].split('T')[1][:8]}] {msg['speaker']}: {msg['text']}\n")
            
            f.write(f"\n{'='*70}\n")
            f.write(f"ERGEBNISSE:\n")
            f.write(f"Gesamtpunktzahl: {total_score}/27\n")
            f.write(f"Schweregrad: {severity}\n")
            f.write(f"Antworten: {responses}\n")
        
        # Save CSV for analysis
        csv_file = self.session_folder / "interaction_logs.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "sessionId", "turnIndex", "userRawSpeech", "asrTranscript",
                "languageDetected", "phqQuestionId", "handlingModule", "pepperLocalNlpSuccess",
                "gptUsed", "gptReason", "gptModel", "gptPromptSnippet", "gptResponse",
                "finalRobotOutput", "notes"
            ])
            writer.writeheader()
            writer.writerows(self.entries)
        
        # Save GPT calls log
        if self.gpt_calls:
            gpt_log_file = self.session_folder / "gpt_api_calls.json"
            with open(gpt_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.gpt_calls, f, indent=2, ensure_ascii=False)
            
            # Also save as readable text
            gpt_txt_file = self.session_folder / "gpt_api_calls.txt"
            with open(gpt_txt_file, 'w', encoding='utf-8') as f:
                f.write(f"GPT API Calls Log (DEUTSCH)\n")
                f.write(f"Session: {self.session_id}\n")
                f.write(f"Gesamt Aufrufe: {len(self.gpt_calls)}\n")
                f.write(f"{'='*70}\n\n")
                
                for i, call in enumerate(self.gpt_calls, 1):
                    f.write(f"AUFRUF #{i} - {call['purpose']}\n")
                    f.write(f"Zeit: {call['timestamp']}\n")
                    f.write(f"Modell: {call['model']}\n")
                    f.write(f"Tokens: {call.get('tokens_used', 'N/A')}\n")
                    f.write(f"\nPrompt:\n{call['prompt']}\n")
                    f.write(f"\nAntwort:\n{call['response']}\n")
                    f.write(f"{'-'*70}\n\n")
        
        return self.session_folder
    
    def export_to_csv(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interaction_logs_de_{timestamp}.csv"
        
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
        self.root.title("PHQ-9 Pepper Simulation - Deutsche Version")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Ensure window is visible before asking for input
        self.root.update()
        
        # Ask for participant metadata at startup (German)
        self.participant_id = simpledialog.askstring("Teilnehmer Info", "Teilnehmer ID eingeben:", parent=root) or str(uuid.uuid4())[:8]
        self.proficiency = simpledialog.askstring("Teilnehmer Info", "Sprachkenntnisse (Muttersprache/B1/etc):", parent=root) or "Unbekannt"
        
        # State
        self.session_id = str(uuid.uuid4())
        self.logger = SimpleLogger(self.session_id, {"id": self.participant_id, "proficiency": self.proficiency})
        self.current_question = 0
        self.final_scores = [None] * 9  # Exactly 9 final confirmed scores
        self.attempts_per_question = {i: [] for i in range(9)}  # Track all attempts
        self.retry_counts = {i: 0 for i in range(9)}  # Track retries per question
        self.MAX_RETRIES = 3
        self.session_active = False
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
        self.processing_lock = threading.Lock()
        
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
                
                # Try to set German voice
                voices = self.tts_engine.getProperty('voices')
                german_voice = None
                for voice in voices:
                    if 'german' in voice.name.lower() or 'de' in voice.languages:
                        german_voice = voice.id
                        break
                
                if german_voice:
                    self.tts_engine.setProperty('voice', german_voice)
                elif voices:
                    self.tts_engine.setProperty('voice', voices[0].id)
                
                self.tts_ready = True
                print("TTS initialisiert")
                
                # Start TTS worker thread
                self.tts_worker_running = True
                self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
                self.tts_thread.start()
            except Exception as e:
                print(f"  TTS Fehler: {e}")
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
                print(f"  Mikrofon Fehler: {e}")
                self.mic_available = False
        
        # Create GUI
        self.create_widgets()
        
        # Welcome - don't wait for speech to complete so GUI can show
        self.add_robot_message("Hallo! Ich bin Pepper, bereit für ein Gesundheits-Screening mit Ihnen.")
        self.speak("Hallo! Ich bin Pepper, bereit für ein Gesundheits-Screening mit Ihnen.", wait=False)
    
    def create_widgets(self):
        """Create the GUI interface"""
        # Header
        header = tk.Frame(self.root, bg="#4CAF50", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="PHQ-9 GESUNDHEITS-SCREENING SIMULATION",
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
            text=f" Sprache: {'AN' if ASR_AVAILABLE else 'AUS'} | GPT: {'AN' if GPT_ENABLED else 'AUS'} | Status: Bereit",
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
            text="Frage 0 / 9",
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
            text="Senden",
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
            text="ZUM SPRECHEN DRÜCKEN",
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
            text=" SCREENING STARTEN",
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
            text=" Logs Exportieren",
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
            text=" Neustart",
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
            text="Ist das richtig?",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=10)
        
        self.yes_button = tk.Button(
            self.confirm_frame,
            text="✓ JA",
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
            text="✗ NEIN",
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
            text="Stimmen Sie der Teilnahme zu?",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=10)
        
        self.consent_yes_button = tk.Button(
            self.consent_frame,
            text="✓ ICH STIMME ZU",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=16,
            height=2,
            command=self.consent_yes
        )
        self.consent_yes_button.pack(side=tk.LEFT, padx=5)
        
        self.consent_no_button = tk.Button(
            self.consent_frame,
            text="✗ ICH LEHNE AB",
            font=("Arial", 14, "bold"),
            bg="#f44336",
            fg="white",
            width=16,
            height=2,
            command=self.consent_no
        )
        self.consent_no_button.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text="💡 Verwenden Sie die ROTE TASTE zum Sprechen oder das Textfeld zum Tippen",
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
                        print(f"  TTS Fehler: {e}")
                
                self.tts_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"  TTS Worker Fehler: {e}")
    
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
        self.chat_area.insert(tk.END, "[Sie]: ", "user")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        # Log to transcript
        if hasattr(self, 'logger'):
            self.logger.add_to_transcript("Benutzer", text)
    
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
            self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN")
        
        # Run consent sequentially but non-blocking
        def consent_thread():
            # First disclaimer
            consent = "Hallo! Bevor wir beginnen, möchte ich Sie informieren, dass dies eine technische Demonstration nur zu Forschungszwecken ist. Dies ist KEINE psychologische Bewertung oder medizinische Diagnose."
            self.root.after(0, lambda: self.add_robot_message(consent))
            self.speak(consent, wait=True)
            time.sleep(1)
            
            # Second disclaimer
            consent2 = "Die gesammelten Informationen werden ausschließlich für technische Tests verwendet. Wenn Sie echte gesundheitliche Bedenken haben, wenden Sie sich bitte an einen qualifizierten Gesundheitsexperten."
            self.root.after(0, lambda: self.add_robot_message(consent2))
            self.speak(consent2, wait=True)
            time.sleep(1)
            
            # Ask for consent
            consent_question = "Stimmen Sie der Teilnahme an diesem Screening zu?"
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
                userRawSpeech="", asrTranscript="", languageDetected="DE",
                phqQuestionId="", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
                gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
                gptResponse="", finalRobotOutput=consent + " " + consent2 + " " + consent_question, notes="Einwilligung angefordert"
            )
        
        threading.Thread(target=consent_thread, daemon=True).start()
    
    def ask_question(self):
        """Ask current PHQ-9 question"""
        if self.current_question >= 9:
            self.complete_screening()
            return
        
        q = PHQ9_QUESTIONS_DE[self.current_question]
        self.progress_label.config(text=f"Frage {self.current_question + 1} / 9")
        self.progress_bar['value'] = self.current_question + 1
        
        question_text = f"Frage {self.current_question + 1}: {q.question}"
        
        # Display and speak question
        def question_thread():
            self.root.after(0, lambda: self.add_robot_message(question_text))
            self.speak(question_text, wait=True)  # Wait for speech to finish
            time.sleep(0.5)
            
            # Enable mic button AFTER speaking finishes
            if ASR_AVAILABLE and self.mic_available and not self.is_listening:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
            
            self.logger.log_turn(
                userRawSpeech="", asrTranscript="", languageDetected="DE",
                phqQuestionId=f"F{q.id}", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
                gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
                gptResponse="", finalRobotOutput=question_text, notes=f"Frage {self.current_question + 1}"
            )
        
        threading.Thread(target=question_thread, daemon=True).start()
        self.status_label.config(text=f"Frage {self.current_question + 1}/9 - Mikrofon drücken oder Antwort tippen")
    
    def start_voice_input(self):
        """Start listening via microphone using Whisper"""
        if not self.mic_available or self.is_listening:
            self.add_system_message("[Fehler] Mikrofon nicht verfügbar. Bitte Texteingabe verwenden.")
            return
        
        self.is_listening = True
        # Debounce mic button during listen
        self.mic_button.config(text="HÖRE ZU...", bg="#D32F2F", state=tk.DISABLED)
        self.status_label.config(text="HÖRE ZU... Sprechen Sie jetzt!")
        # Make ASR snappier
        self.recognizer.pause_threshold = LISTEN_PAUSE_THRESHOLD
        
        def listen_thread():
            failures = 0
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=LISTEN_AMBIENT_DURATION)
                    self.root.after(0, lambda: self.add_system_message("[Höre zu] Sprechen Sie jetzt!"))
                    audio = self.recognizer.listen(
                        source,
                        timeout=LISTEN_TIMEOUT,
                        phrase_time_limit=LISTEN_PHRASE_LIMIT
                    )
                
                self.root.after(0, lambda: self.status_label.config(text="🔄 Transkribiere..."))
                
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
                        language="de"  # German language
                    )
                
                # Clean up temp file
                import os
                os.unlink(temp_filename)
                
                text = transcript.text.strip()
                
                # Check if transcription is meaningful
                if len(text) < 2 or text.lower() in ['oh', 'uh', 'um', 'ah', 'ähm']:
                    self.root.after(0, lambda: self.add_system_message("[Fehler] Keine klare Sprache erkannt. Bitte antworten Sie deutlich."))
                    return
                
                self.root.after(0, lambda: self.process_response(text, is_voice=True))
                
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError) as e:
                failures += 1
                if isinstance(e, sr.WaitTimeoutError):
                    msg = "⏰ Keine Sprache erkannt. Erneut versuchen oder tippen."
                elif isinstance(e, sr.UnknownValueError):
                    msg = "[Fehler] Sprache nicht verstanden. Bitte erneut versuchen."
                else:
                    msg = "[Fehler] Sprachdienst-Problem. Bitte erneut versuchen oder tippen."

                if failures >= 2:
                    self.root.after(0, lambda: self.add_system_message("Spracheingabe zweimal fehlgeschlagen, bitte Antwort tippen."))
                    return
                else:
                    self.root.after(0, lambda: self.add_system_message(msg))
                    return
            except Exception as e:
                error_msg = str(e)
                print(f"Spracheingabe Fehler: {error_msg}")
                if "PyAudio" in error_msg or "portaudio" in error_msg:
                    self.root.after(0, lambda: self.add_system_message("[Fehler] Mikrofonfehler. Bitte Texteingabe verwenden."))
                    self.mic_available = False
                    self.root.after(0, lambda: self.mic_button.config(state=tk.DISABLED, text="MIK N/V"))
                else:
                    self.root.after(0, lambda: self.add_system_message(f"Fehler: {error_msg[:50]}. Texteingabe verwenden."))
            finally:
                self.root.after(0, self.stop_listening)
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self.mic_button.config(text="ZUM SPRECHEN DRÜCKEN", bg="#FF5722", state=tk.NORMAL)
    
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
        self.add_system_message(f"✓ Bestätigt: {confirmation}")
        
        # Log
        q = PHQ9_QUESTIONS_DE[self.current_question]
        self.logger.log_turn(
            userRawSpeech="[BUTTON: JA]", asrTranscript=confirmation,
            languageDetected="DE",
            phqQuestionId=f"F{q.id}",
            handlingModule=self.pending_module,
            pepperLocalNlpSuccess=(self.pending_module == "PEPPER_LOCAL"),
            gptUsed=self.pending_gpt_used,
            gptReason=self.pending_gpt_reason if self.pending_gpt_reason else "",
            gptModel="gpt-4o-mini" if self.pending_gpt_used else "",
            gptPromptSnippet=self.pending_gpt_prompt_snippet if self.pending_gpt_used else "",
            gptResponse=self.pending_gpt_response if self.pending_gpt_used else "",
            finalRobotOutput="Bestätigt per Button",
            notes=f"F{self.current_question + 1} FINALE Punktzahl={score}, Wiederholungen={self.retry_counts[self.current_question]}"
        )
        
        # CHECK FOR CRISIS PROTOCOL (Q9 with score > 0)
        if self.handle_crisis_protocol(score):
            return
        
        # Move directly to next question
        def continue_thread():
            if self.current_question < 8:
                next_msg = "Lassen Sie mich die nächste Frage stellen."
                self.root.after(0, lambda: self.add_robot_message(next_msg))
                self.speak(next_msg, wait=True)
                time.sleep(0.5)
            
            self.current_question += 1
            # Re-enable input before next question
            self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            if ASR_AVAILABLE and self.mic_available:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
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
        self.add_system_message(f"✗ Nicht bestätigt. Wiederholung {self.retry_counts[self.current_question]}/{self.MAX_RETRIES}")
        
        # Check if max retries reached
        if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
            # Use last attempted score or default to 0
            fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
            self.final_scores[self.current_question] = fallback_score
            
            self.add_system_message(f"Max. Wiederholungen erreicht. Verwende Fallback-Punktzahl: {fallback_score}")
            
            fallback_msg = "Ich verstehe, das ist schwierig. Lassen Sie uns zur nächsten Frage übergehen."
            self.add_robot_message(fallback_msg)
            self.speak(fallback_msg, wait=True)
            
            # Move to next question
            def continue_after_retry():
                time.sleep(0.5)
                self.current_question += 1
                self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
                if ASR_AVAILABLE and self.mic_available:
                    self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                self.root.after(500, self.ask_question)
            
            threading.Thread(target=continue_after_retry, daemon=True).start()
            return
        
        # Ask again
        def reask_thread():
            retry_msg = "Ich verstehe. Lassen Sie mich die Frage erneut stellen. Bitte antworten Sie mit: überhaupt nicht, an einzelnen Tagen, an mehr als der Hälfte der Tage, oder beinahe jeden Tag."
            self.root.after(0, lambda: self.add_robot_message(retry_msg))
            self.speak(retry_msg, wait=True)
            
            # Re-ask question
            q = PHQ9_QUESTIONS_DE[self.current_question]
            question_text = f"Frage {self.current_question + 1}: {q.question}"
            self.root.after(0, lambda: self.add_robot_message(question_text))
            self.speak(question_text, wait=True)
            
            # Re-enable input after re-asking
            self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            if ASR_AVAILABLE and self.mic_available:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
        
        threading.Thread(target=reask_thread, daemon=True).start()
    
    def consent_yes(self):
        """Handle consent YES button click"""
        if not self.waiting_for_consent:
            return
        
        self.waiting_for_consent = False
        self.consent_frame.pack_forget()  # Hide consent buttons
        
        self.add_system_message("✓ Zustimmung per Button gegeben")
        
        # Log consent
        self.logger.log_turn(
            userRawSpeech="[BUTTON: ICH STIMME ZU]", asrTranscript="Zustimmung gegeben",
            languageDetected="DE", phqQuestionId="",
            handlingModule="BUTTON", pepperLocalNlpSuccess=True,
            gptUsed=False, finalRobotOutput="Danke für Ihre Zustimmung",
            notes="Zustimmung per Button-Klick gegeben"
        )
        
        # Continue with screening
        def continue_screening():
            thank_msg = "Danke für Ihre Zustimmung."
            self.root.after(0, lambda: self.add_robot_message(thank_msg))
            self.speak(thank_msg, wait=True)
            
            explain_msg = "Ich werde Ihnen nun 9 Fragen stellen, wie Sie sich in den letzten 2 Wochen gefühlt haben. Bitte antworten Sie mit: überhaupt nicht, an einzelnen Tagen, an mehr als der Hälfte der Tage, oder beinahe jeden Tag."
            self.root.after(0, lambda: self.add_robot_message(explain_msg))
            self.speak(explain_msg, wait=True)
            
            # Re-enable input
            self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            if ASR_AVAILABLE and self.mic_available:
                self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
            
            # Ask first question
            self.root.after(500, self.ask_question)
        
        threading.Thread(target=continue_screening, daemon=True).start()
    
    def consent_no(self):
        """Handle consent NO button click"""
        if not self.waiting_for_consent:
            return
        
        self.waiting_for_consent = False
        self.consent_frame.pack_forget()  # Hide consent buttons
        
        self.add_system_message("✗ Zustimmung per Button abgelehnt")
        
        # Log declined consent
        self.logger.log_turn(
            userRawSpeech="[BUTTON: ICH LEHNE AB]", asrTranscript="Zustimmung abgelehnt",
            languageDetected="DE", phqQuestionId="",
            handlingModule="BUTTON", pepperLocalNlpSuccess=True,
            gptUsed=False, finalRobotOutput="Sitzung beendet - Zustimmung abgelehnt",
            notes="Zustimmung per Button-Klick abgelehnt"
        )
        
        # End session
        def end_session():
            decline_msg = "Ich verstehe. Vielen Dank für Ihre Zeit. Die Sitzung wird nun beendet."
            self.root.after(0, lambda: self.add_robot_message(decline_msg))
            self.speak(decline_msg, wait=True)
            
            self.session_active = False
            self.root.after(0, lambda: self.restart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.add_system_message("Sitzung beendet - Zustimmung abgelehnt"))
        
        threading.Thread(target=end_session, daemon=True).start()
    
    def parse_response(self, response: str) -> tuple:
        """Parse response locally - returns (score, user_friendly_confirmation)"""
        resp_lower = response.lower().strip()
        
        # Score 0 - "Überhaupt nicht"
        if "überhaupt nicht" in resp_lower or "gar nicht" in resp_lower or "nie" in resp_lower:
            return (0, "überhaupt nicht")
        elif resp_lower == "0":
            return (0, "überhaupt nicht")
        
        # Score 1 - "An einzelnen Tagen"
        elif "einzelnen tagen" in resp_lower or "einzelne tage" in resp_lower:
            return (1, "an einzelnen Tagen")
        elif "manchmal" in resp_lower or "selten" in resp_lower:
            return (1, "an einzelnen Tagen")
        elif resp_lower == "1":
            return (1, "an einzelnen Tagen")
        
        # Score 2 - "An mehr als der Hälfte der Tage"
        elif "mehr als" in resp_lower and ("hälfte" in resp_lower or "halfte" in resp_lower):
            return (2, "an mehr als der Hälfte der Tage")
        elif "meiste zeit" in resp_lower or "oft" in resp_lower:
            return (2, "an mehr als der Hälfte der Tage")
        elif resp_lower == "2":
            return (2, "an mehr als der Hälfte der Tage")
        
        # Score 3 - "Beinahe jeden Tag"
        elif "beinahe jeden tag" in resp_lower or "fast jeden tag" in resp_lower:
            return (3, "beinahe jeden Tag")
        elif "jeden tag" in resp_lower or "immer" in resp_lower or "ständig" in resp_lower:
            return (3, "beinahe jeden Tag")
        elif resp_lower == "3":
            return (3, "beinahe jeden Tag")
        
        # Try matching PHQ-9 options
        q = PHQ9_QUESTIONS_DE[self.current_question]
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
            self.add_system_message(" SICHERHEITSPROTOKOLL AKTIVIERT ")
            
            # Run crisis protocol in background thread
            def crisis_thread():
                # Display supportive message
                crisis_msg = "Ich möchte Ihre Antwort anerkennen. Ihre Sicherheit ist sehr wichtig. Bitte wissen Sie, dass Hilfe verfügbar ist."
                self.root.after(0, lambda: self.add_robot_message(crisis_msg))
                self.speak(crisis_msg, wait=True)
                time.sleep(4)
                
                # Show crisis resources
                resources_title = "KRISEN-RESSOURCEN - Bitte notieren Sie diese:"
                self.root.after(0, lambda: self.add_robot_message(resources_title))
                self.speak(resources_title, wait=True)
                time.sleep(2)
                
                # Display hotlines in chat (visible on screen)
                crisis_info = """
NOTFALL-HOTLINES:
• Telefonseelsorge Deutschland: 0800 111 0 111 oder 0800 111 0 222
• Internationale Krisenlinie: 116 123
• Notdienst: 112

Sie sind nicht allein. Professionelle Hilfe ist rund um die Uhr verfügbar.
Bitte ziehen Sie in Betracht, sich an einen Fachmann für psychische Gesundheit oder einen Berater zu wenden."""
                
                def add_crisis_info():
                    self.chat_area.config(state=tk.NORMAL)
                    self.chat_area.insert(tk.END, crisis_info + "\n\n", "system")
                    self.chat_area.see(tk.END)
                    self.chat_area.config(state=tk.DISABLED)
                
                self.root.after(0, add_crisis_info)
                
                # Speak resources
                resources_msg = "Telefonseelsorge Deutschland: 0800 111 0 111. Internationale Krisenlinie: 116 123. Notdienst: 112. Bitte ziehen Sie in Betracht, sich an einen Fachmann für psychische Gesundheit zu wenden. Sie sind nicht allein, und Hilfe ist verfügbar."
                self.speak(resources_msg, wait=True)
                time.sleep(8)
                
                # Important reminder
                reminder = "Dieses Screening ist keine Diagnose. Bitte kontaktieren Sie einen Gesundheitsexperten für eine ordnungsgemäße Bewertung und Unterstützung."
                self.root.after(0, lambda: self.add_robot_message(reminder))
                self.speak(reminder, wait=True)
                time.sleep(5)
                
                # Ask for acknowledgment
                ack_msg = "Haben Sie diese Ressourcen notiert? Tippen Sie 'ja' oder drücken Sie das Mikrofon um fortzufahren."
                self.root.after(0, lambda: self.add_robot_message(ack_msg))
                self.speak("Haben Sie diese Ressourcen notiert? Bitte bestätigen Sie um fortzufahren.", wait=True)
                
                # Re-enable input for acknowledgment AFTER speaking finishes
                self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
                if ASR_AVAILABLE and self.mic_available:
                    self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                
                # Set flag to wait for acknowledgment
                self.waiting_for_crisis_ack = True
            
            threading.Thread(target=crisis_thread, daemon=True).start()
            
            return True
        return False
    
    def get_acknowledgment(self, score: int) -> str:
        """Get varied acknowledgment based on score (without mentioning numbers)"""
        acknowledgments = {
            0: [
                "Ich verstehe, überhaupt nicht.",
                "Okay, überhaupt nicht.",
                "Verstanden, Sie haben das nicht erlebt.",
                "Danke, überhaupt nicht."
            ],
            1: [
                "Ich verstehe, an einzelnen Tagen.",
                "Verstanden, an einzelnen Tagen.",
                "Okay, an einzelnen Tagen.",
                "Danke, an einzelnen Tagen."
            ],
            2: [
                "Ich höre Sie, an mehr als der Hälfte der Tage.",
                "Verstanden, an mehr als der Hälfte der Tage.",
                "Okay, an mehr als der Hälfte der Tage.",
                "Danke, an mehr als der Hälfte der Tage."
            ],
            3: [
                "Ich verstehe, beinahe jeden Tag.",
                "Okay, beinahe jeden Tag.",
                "Verstanden, beinahe jeden Tag.",
                "Danke, beinahe jeden Tag."
            ]
        }
        if score in acknowledgments:
            return random.choice(acknowledgments[score])
        return "Danke, ich habe Ihre Antwort notiert."
    
    def parse_with_gpt(self, response: str) -> tuple:
        """Use GPT to parse unclear response into PHQ-9 score
        Returns: (score, confirmation, prompt_snippet, gpt_response)
        """
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            q = PHQ9_QUESTIONS_DE[self.current_question]
            
            prompt = f"Frage: {q.question}\n0=Überhaupt nicht, 1=An einzelnen Tagen, 2=An mehr als der Hälfte der Tage, 3=Beinahe jeden Tag\nAntworte: ZAHL|PHRASE"
            
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
                purpose=f"Parse PHQ-9 F{self.current_question + 1} Antwort",
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
            print(f"GPT Parse Fehler: {e}")
            return (-1, None, "", str(e))
    
    def check_confirmation_with_gpt(self, response: str) -> bool:
        """Use GPT to understand if user confirmed"""
        if not OPENAI_API_KEY:
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['ja', 'richtig', 'korrekt', 'stimmt', 'genau', 'ok', 'okay'])
        
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            prompt = "Antworte JA wenn Bestätigung, NEIN wenn nicht."
            user_msg = f"Ist '{response}' eine Bestätigung?"
            
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
                purpose="Prüfe Antwort Bestätigung",
                prompt=f"System: {prompt}\nUser: {user_msg}",
                response=result,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            return "JA" in result or "YES" in result
        except Exception as e:
            print(f"GPT Bestätigung Fehler: {e}")
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['ja', 'richtig', 'korrekt', 'stimmt', 'genau', 'ok', 'okay'])
    
    def check_consent_with_gpt(self, response: str) -> bool:
        """Use GPT to understand if user consented"""
        if not OPENAI_API_KEY:
            # Fallback to keywords
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['ja', 'stimme zu', 'einverstanden', 'ok', 'okay', 'sicher', 'gut', 'einwilligung'])
        
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            
            prompt = "Antworte JA wenn zustimmt/einwilligt, NEIN wenn ablehnt."
            user_msg = f"Bedeutet '{response}' Einwilligung?"
            
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
                purpose="Prüfe Einwilligung",
                prompt=f"System: {prompt}\nUser: {user_msg}",
                response=result,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            return "JA" in result or "YES" in result
        except Exception as e:
            print(f"GPT Einwilligung Fehler: {e}")
            # Fallback
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['ja', 'stimme zu', 'einverstanden', 'ok', 'okay', 'sicher', 'gut', 'einwilligung'])
    
    def call_gpt_fallback(self, response: str) -> tuple:
        """Call GPT for unclear responses"""
        q = PHQ9_QUESTIONS_DE[self.current_question]
        prompt = f"""Der Benutzer beantwortet PHQ-9: {q.question}
Benutzer sagte: "{response}"

Optionen: Überhaupt nicht (0), An einzelnen Tagen (1), An mehr als der Hälfte der Tage (2), Beinahe jeden Tag (3)
Antworte mit NUR der Zahl 0, 1, 2, oder 3."""

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
                purpose=f"Fallback Parse PHQ-9 F{self.current_question + 1}",
                prompt=prompt,
                response=gpt_text,
                model="gpt-4o-mini",
                tokens_used=tokens
            )
            
            return score, gpt_text
        except Exception as e:
            print(f"GPT Fallback Fehler: {e}")
            return 1, "GPT_ERROR"
    
    def process_response(self, response: str, is_voice: bool):
        """Process user response in a background thread to prevent GUI freeze"""
        # Prevent double triggering (thread safety)
        if getattr(self, 'is_processing', False):
            print("Ignoriere gleichzeitige Eingabe")
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
                self.add_system_message("✓ Einwilligung erteilt")
                
                # Thank and explain
                def proceed_thread():
                    thanks = "Vielen Dank für Ihre Einwilligung."
                    self.root.after(0, lambda: self.add_robot_message(thanks))
                    self.speak(thanks, wait=True)
                    time.sleep(1)
                    
                    instructions = "Ich werde Ihnen jetzt 9 Fragen stellen, wie Sie sich in den letzten 2 Wochen gefühlt haben. Bitte antworten Sie mit: überhaupt nicht, an einzelnen Tagen, an mehr als der Hälfte der Tage, oder beinahe jeden Tag."
                    self.root.after(0, lambda: self.add_robot_message(instructions))
                    self.speak(instructions, wait=True)
                    time.sleep(1)
                    
                    # Enable mic button before starting questions
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                    
                    # Start questions
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=proceed_thread, daemon=True).start()
                return
            else:
                # User declined
                self.add_system_message("[Einwilligung abgelehnt]")
                decline_msg = "Ich verstehe. Vielen Dank für Ihre Zeit. Das Screening wird nicht fortgesetzt."
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
                q = PHQ9_QUESTIONS_DE[self.current_question]
                self.logger.log_turn(
                    userRawSpeech="", asrTranscript=confirmation,
                    languageDetected="DE",
                    phqQuestionId=f"F{q.id}",
                    handlingModule=self.pending_module,
                    pepperLocalNlpSuccess=(self.pending_module == "PEPPER_LOCAL"),
                    gptUsed=self.pending_gpt_used,
                    gptReason=self.pending_gpt_reason,
                    gptModel="gpt-4o-mini" if self.pending_gpt_used else "",
                    gptPromptSnippet="",
                    gptResponse="",
                    finalRobotOutput="Bestätigt",
                    notes=f"F{self.current_question + 1} FINALE Punktzahl={score}, Wiederholungen={self.retry_counts[self.current_question]}"
                )
                
                # CHECK FOR CRISIS PROTOCOL (Q9 with score > 0)
                if self.handle_crisis_protocol(score):
                    return
                
                # Move directly to next question
                def continue_thread():
                    if self.current_question < 8:
                        next_msg = "Lassen Sie mich die nächste Frage stellen."
                        self.root.after(0, lambda: self.add_robot_message(next_msg))
                        self.speak(next_msg, wait=True)
                        time.sleep(0.5)
                    
                    self.current_question += 1
                    # Re-enable mic button before next question
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
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
                    
                    self.add_system_message(f" Maximale Wiederholungen erreicht für F{self.current_question + 1}. Verwende Fallback-Punktzahl: {fallback_score}")
                    
                    fallback_msg = "Ich verstehe, dass dies schwierig ist. Lassen Sie uns zur nächsten Frage übergehen."
                    self.add_robot_message(fallback_msg)
                    self.speak(fallback_msg, wait=True)
                    
                    # Move to next question
                    def continue_after_retry():
                        time.sleep(0.5)
                        self.current_question += 1
                        # Re-enable mic button before next question
                        if ASR_AVAILABLE and self.mic_available:
                            self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                        self.root.after(500, self.ask_question)
                    
                    threading.Thread(target=continue_after_retry, daemon=True).start()
                    return
                
                # Ask again
                retry_msg = "Ich verstehe. Lassen Sie mich die Frage erneut stellen. Bitte antworten Sie mit: überhaupt nicht, an einzelnen Tagen, an mehr als der Hälfte der Tage, oder beinahe jeden Tag."
                self.add_robot_message(retry_msg)
                self.speak(retry_msg, wait=True)
                
                # Re-ask question
                def reask():
                    q = PHQ9_QUESTIONS_DE[self.current_question]
                    question_text = f"Frage {self.current_question + 1}: {q.question}"
                    self.root.after(0, lambda: self.add_robot_message(question_text))
                    self.speak(question_text, wait=True)
                    
                    # Enable mic button after re-asking
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                
                threading.Thread(target=reask, daemon=True).start()
                return
        
        # Handle crisis acknowledgment
        if self.waiting_for_crisis_ack:
            resp_lower = response.lower().strip()
            if any(word in resp_lower for word in ['ja', 'ok', 'okay', 'notiert', 'verstanden', 'weiter', 'fortfahren']):
                self.waiting_for_crisis_ack = False
                self.add_user_message(response)
                self.add_system_message("Krisen-Ressourcen bestätigt. Screening wird fortgesetzt...")
                
                # Move to next question or complete
                self.current_question += 1
                # Re-enable mic button before next question
                if ASR_AVAILABLE and self.mic_available:
                    self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN")
                self.root.after(2000, self.ask_question)
                return
            else:
                self.add_system_message("Bitte bestätigen Sie, dass Sie die Krisen-Ressourcen notiert haben, indem Sie 'ja' sagen oder tippen.")
                return
        
        self.add_user_message(response)
        
        # Detect language
        lang = LanguageDetector.detect_language(response)
        self.add_system_message(f"Sprache: {lang}")
        
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
            self.add_system_message("Verwende GPT um Antwort zu verstehen...")
            gpt_score, gpt_confirmation, gpt_prompt_snippet, gpt_response_text = self.parse_with_gpt(response)
            if 0 <= gpt_score <= 3:
                score = gpt_score
                confirmation = gpt_confirmation
                local_success = False
                gpt_used = True
                gpt_reason = "parse_answer"
                module = "GPT_FALLBACK"
                self.add_system_message(f"GPT verstanden: Punktzahl={score}, als: {confirmation}")
            else:
                # Increment retry and ask for clarification
                self.retry_counts[self.current_question] += 1
                
                # --- START ADDED LOGGING ---
                q = PHQ9_QUESTIONS_DE[self.current_question]
                self.logger.log_turn(
                    userRawSpeech=response, asrTranscript=response, languageDetected=lang,
                    phqQuestionId=f"F{q.id}", handlingModule="GPT_FALLBACK", pepperLocalNlpSuccess=False,
                    gptUsed=True, gptReason="parse_answer", gptModel="gpt-4o-mini",
                    gptPromptSnippet=gpt_prompt_snippet, gptResponse=gpt_response_text,
                    finalRobotOutput="Clarification asked", 
                    notes=f"Failed attempt (GPT failed). Retry {self.retry_counts[self.current_question]}/{self.MAX_RETRIES}"
                )
                # --- END ADDED LOGGING ---
                
                if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
                    # Max retries - use fallback
                    fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
                    self.final_scores[self.current_question] = fallback_score
                    self.add_system_message(f" Max. Wiederholungen. Verwende Fallback: {fallback_score}")
                    
                    fallback_msg = "Ich habe Schwierigkeiten zu verstehen. Lassen Sie uns zur nächsten Frage übergehen."
                    self.add_robot_message(fallback_msg)
                    self.speak(fallback_msg, wait=True)
                    
                    def skip_question():
                        time.sleep(0.5)
                        self.current_question += 1
                        # Re-enable mic button before next question
                        if ASR_AVAILABLE and self.mic_available:
                            self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                        self.root.after(500, self.ask_question)
                    
                    threading.Thread(target=skip_question, daemon=True).start()
                    return
                
                clarify_msg = f"Ich habe '{response}' gehört, aber ich bin mir nicht sicher, ob ich es richtig verstanden habe. Könnten Sie bitte wiederholen mit: überhaupt nicht, an einzelnen Tagen, an mehr als der Hälfte der Tage, oder beinahe jeden Tag?"
                self.add_robot_message(clarify_msg)
                self.speak(clarify_msg, wait=True)
                self.add_system_message("Um Klarstellung gebeten")
                
                # Re-enable mic button after clarification
                if ASR_AVAILABLE and self.mic_available:
                    self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN")
                
                return
        elif not local_success:
            # Increment retry
            self.retry_counts[self.current_question] += 1
            
            # --- START ADDED LOGGING ---
            q = PHQ9_QUESTIONS_DE[self.current_question]
            self.logger.log_turn(
                userRawSpeech=response, asrTranscript=response, languageDetected=lang,
                phqQuestionId=f"Q{q.id}", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=False,
                gptUsed=False, finalRobotOutput="Clarification asked", 
                notes=f"Failed attempt. Retry {self.retry_counts[self.current_question]}/{self.MAX_RETRIES}"
            )
            # --- END ADDED LOGGING ---
            
            if self.retry_counts[self.current_question] >= self.MAX_RETRIES:
                fallback_score = self.attempts_per_question[self.current_question][-1] if self.attempts_per_question[self.current_question] else 0
                self.final_scores[self.current_question] = fallback_score
                self.add_system_message(f" Max. Wiederholungen. Verwende Fallback: {fallback_score}")
                
                fallback_msg = "Lassen Sie uns zur nächsten Frage übergehen."
                self.add_robot_message(fallback_msg)
                self.speak(fallback_msg, wait=True)
                
                def skip_question():
                    time.sleep(0.5)
                    self.current_question += 1
                    # Re-enable mic button before next question
                    if ASR_AVAILABLE and self.mic_available:
                        self.root.after(0, lambda: self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN"))
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=skip_question, daemon=True).start()
                return
            
            clarify_msg = f"Ich habe '{response}' gehört, aber ich bin mir nicht sicher, ob ich es richtig verstanden habe. Könnten Sie bitte wiederholen mit: überhaupt nicht, an einzelnen Tagen, an mehr als der Hälfte der Tage, oder beinahe jeden Tag?"
            self.add_robot_message(clarify_msg)
            self.speak(clarify_msg, wait=True)
            self.add_system_message("Um Klarstellung gebeten")
            
            # Re-enable mic button after clarification
            if ASR_AVAILABLE and self.mic_available:
                self.mic_button.config(state=tk.NORMAL, text="ZUM SPRECHEN DRÜCKEN")
            
            return
        else:
            self.add_system_message(f"Lokales NLP: Punktzahl={score}, verstanden als: {confirmation}")
        
        # Store as attempt (not final yet)
        self.attempts_per_question[self.current_question].append(score)
        
        # Confirm what was understood
        confirm_msg = f"Ich habe verstanden: {confirmation}. Ist das richtig?"
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
                self.add_system_message(f" Warnung: F{i+1} hat keine finale Punktzahl, Standardwert 0")
        
        # Calculate total (must be 0-27)
        total = sum(self.final_scores)
        
        # Safety clamp
        if total > 27:
            self.add_system_message(f"[FEHLER] Punktzahl {total} überschreitet Maximum 27! Begrenzung.")
            total = 27
        elif total < 0:
            self.add_system_message(f"[FEHLER] Punktzahl {total} ist negativ! Begrenzung.")
            total = 0
        
        severity = self.get_severity(total)
        severity_description = self.get_severity_description(severity)
        
        # Save session data
        session_folder = self.logger.save_session_data(self.final_scores, total, severity, self.retry_counts)
        
        # Display score breakdown
        self.add_system_message(f"ABGESCHLOSSEN | Gesamtpunktzahl: {total} von 27 | Schweregrad: {severity.upper()}")
        self.add_system_message(f"Finale Antworten (F1-F9): {self.final_scores}")
        self.add_system_message(f"Wiederholungen: {list(self.retry_counts.values())}")
        self.add_system_message(f"Session gespeichert: {session_folder}")
        
        # Speak summary in background thread
        def summary_thread():
            # First message - score
            intro = f"Vielen Dank für das Ausfüllen aller 9 Fragen. Lassen Sie mich Ihre Ergebnisse mitteilen."
            self.root.after(0, lambda: self.add_robot_message(intro))
            self.speak(intro, wait=True)
            
            # Second message - score breakdown
            score_msg = f"Ihre Gesamtpunktzahl beträgt {total} von maximal 27 Punkten. Dies deutet auf {severity} Symptome hin."
            self.root.after(0, lambda: self.add_robot_message(score_msg))
            self.speak(score_msg, wait=True)
            
            # Third message - severity description
            self.root.after(0, lambda: self.add_robot_message(severity_description))
            self.speak(severity_description, wait=True)
            
            # Fourth message - disclaimer
            disclaimer = "Bitte denken Sie daran: Dies ist nur eine technische Demonstration, keine medizinische Diagnose. Diese Daten werden zu Forschungszwecken gesammelt. Wenn Sie echte gesundheitliche Bedenken haben, wenden Sie sich bitte an einen qualifizierten Gesundheitsexperten."
            self.root.after(0, lambda: self.add_robot_message(disclaimer))
            self.speak(disclaimer, wait=True)
            
            self.root.after(0, lambda: self.export_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.restart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text=f"Abgeschlossen! Gesamtpunktzahl: {total}/27 - {severity}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Screening Abgeschlossen", 
                f"PHQ-9 Screening Abgeschlossen!\n\n"
                f"Gesamtpunktzahl: {total} / 27\n"
                f"Schweregrad: {severity.upper()}\n\n"
                f"{severity_description}\n\n"
                f" Dies ist nur für technische Demonstrationszwecke.\n\n"
                f"Session-Daten gespeichert in:\n{session_folder}"))
        
        threading.Thread(target=summary_thread, daemon=True).start()
    
    def get_severity(self, score):
        """Get severity level"""
        if score <= 4: return "minimal"
        elif score <= 9: return "leicht"
        elif score <= 14: return "mittelgradig"
        elif score <= 19: return "mittelschwer"
        else: return "schwer"
    
    def get_severity_description(self, severity):
        """Get detailed description for each severity level"""
        descriptions = {
            "minimal": "Minimale Depressionssymptome. Werte in diesem Bereich (0-4) deuten typischerweise auf wenige oder keine depressiven Symptome hin.",
            "leicht": "Leichte Depressionssymptome. Werte in diesem Bereich (5-9) können auf leichte depressive Symptome hinweisen, die eine Beobachtung erfordern könnten.",
            "mittelgradig": "Mittelgradige Depressionssymptome. Werte in diesem Bereich (10-14) deuten auf mittelgradige depressive Symptome hin, die möglicherweise eine professionelle Bewertung erfordern.",
            "mittelschwer": "Mittelschwere Depressionssymptome. Werte in diesem Bereich (15-19) weisen auf signifikante Symptome hin, die von professioneller Betreuung profitieren würden.",
            "schwer": "Schwere Depressionssymptome. Werte in diesem Bereich (20-27) deuten auf schwere depressive Symptome hin, die sofortige professionelle Aufmerksamkeit erfordern."
        }
        return descriptions.get(severity, "Unbekannter Schweregrad.")
    
    def export_logs(self):
        """Export to CSV and open folder"""
        if hasattr(self, 'logger') and hasattr(self.logger, 'session_folder'):
            os.startfile(str(self.logger.session_folder))
            messagebox.showinfo("Session-Daten", f"Öffne Session-Ordner:\n{self.logger.session_folder}")
        else:
            filename = self.logger.export_to_csv()
            messagebox.showinfo("Exportiert", f"Logs gespeichert in:\n{filename}")
            os.startfile(os.getcwd())
    
    def restart_screening(self):
        """Restart the screening"""
        response = messagebox.askyesno("Neustart", "Eine neue Screening-Session starten?\n\nAktuelle Session-Daten sind bereits gespeichert.")
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
            self.progress_label.config(text="Frage 0 / 9")
            self.start_button.config(state=tk.NORMAL)
            self.text_input.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.mic_button.config(state=tk.DISABLED)
            self.export_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.status_label.config(text="Bereit für neue Session")
            
            # Welcome message
            self.add_robot_message("Bereit für eine neue Screening-Session. Klicken Sie SCREENING STARTEN wenn bereit.")
            self.speak("Bereit für eine neue Screening-Session.")
    
    def update_status(self, text):
        """Update status"""
        self.status_label.config(text=text)


def main():
    """Launch GUI"""
    print("\n" + "="*70)
    print("PHQ-9 SPRACH-SIMULATION (DEUTSCH)")
    print("="*70)
    
    if not ASR_AVAILABLE:
        print("\n  Spracherkennung nicht vollständig verfügbar")
        print("   Mikrofon-Taste wird deaktiviert")
        print("   Sie können Texteingabe verwenden + Roboter hören via TTS\n")
    
    if not TTS_AVAILABLE:
        print("\n  Text-zu-Sprache nicht verfügbar")
        print("   Sie können dennoch Roboter-Nachrichten im Fenster sehen\n")
    
    print(" GUI-Fenster wird gestartet...")
    print("   - Grüne 'SCREENING STARTEN' Taste zum Beginnen")
    print("   - Rote 'ZUM SPRECHEN DRÜCKEN' für Spracheingabe")
    print("   - Oder tippen Sie im Textfeld\n")
    
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

