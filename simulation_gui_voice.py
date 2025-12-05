#!/usr/bin/env python3
"""
PHQ-9 Health Screening Simulation - GUI with VOICE INPUT
Uses sounddevice (easier to install than PyAudio on Windows)
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import uuid
import csv
import random
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os

# Load configuration
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GPT_ENABLED = os.getenv("GPT_ENABLED", "True").lower() == "true"

# Try importing speech libraries
try:
    import pyttsx3
    TTS_AVAILABLE = True
except:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    import openai
    import tempfile
    import wave
    ASR_AVAILABLE = True
except:
    ASR_AVAILABLE = False

# Import simulation components
from simulation import PHQ9_QUESTIONS, LanguageDetector

# Interaction logger (embedded)
class SimpleLogger:
    def __init__(self, session_id):
        self.session_id = session_id
        self.entries = []
        self.turn_index = 0
    
    def log_turn(self, **kwargs):
        entry = {
            "timestamp": int(time.time() * 1000),
            "sessionId": self.session_id,
            "turnIndex": self.turn_index,
            **{k: v if v is not None else "" for k, v in kwargs.items()}
        }
        self.entries.append(entry)
        self.turn_index += 1
    
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
        self.root.title("🤖 PHQ-9 Pepper Simulation - VOICE ENABLED")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # State
        self.session_id = str(uuid.uuid4())
        self.logger = SimpleLogger(self.session_id)
        self.current_question = 0
        self.responses = []
        self.session_active = False
        self.is_listening = False
        self.waiting_for_crisis_ack = False
        self.waiting_for_consent = False
        self.waiting_for_answer_confirmation = False
        self.pending_score = None
        self.pending_confirmation = None
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 160)
                self.tts_engine.setProperty('volume', 1.0)
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    self.tts_engine.setProperty('voice', voices[0].id)
                self.tts_ready = True
                print("TTS initialized successfully")
            except Exception as e:
                print(f"TTS initialization failed: {e}")
                self.tts_ready = False
        else:
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
                self.mic_available = True
            except Exception as e:
                print(f"Microphone initialization error: {e}")
                self.mic_available = False
        
        # Create GUI
        self.create_widgets()
        
        # Welcome
        self.add_robot_message("Hello! I'm Pepper, ready to conduct a health screening with you.")
        self.speak("Hello! I'm Pepper, ready to conduct a health screening with you.")
    
    def create_widgets(self):
        """Create the GUI interface"""
        # Header
        header = tk.Frame(self.root, bg="#4CAF50", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🤖 PHQ-9 HEALTH SCREENING SIMULATION",
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
            text=f"🔊 Voice Mode: {'ON' if ASR_AVAILABLE else 'OFF'} | GPT: {'ON' if GPT_ENABLED else 'OFF'} | Status: Ready",
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
            text="🎤 PRESS TO SPEAK",
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
            text="▶ START SCREENING",
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
            text="📊 Export Logs",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            width=15,
            height=3,
            command=self.export_logs,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text="💡 Use the BIG RED BUTTON to speak your answer, or type in the text field",
            font=("Arial", 10),
            bg="#FFF3E0",
            fg="#E65100",
            pady=10
        )
        instructions.pack(fill=tk.X, padx=25, pady=(0, 15))
    
    def speak(self, text, wait=True):
        """Robot speaks using TTS"""
        if not self.tts_ready:
            print(f"TTS not ready. Text: {text[:50]}")
            return
        
        try:
            print(f"SPEAKING: {text[:50]}...")
            # Create new engine instance for thread safety
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            if wait:
                time.sleep(0.3)
        except Exception as e:
            print(f"TTS Error: {e}")
    
    def add_robot_message(self, text):
        """Add robot message"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "🤖 Pepper: ", "robot")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def add_user_message(self, text):
        """Add user message"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "👤 You: ", "user")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
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
        self.responses = []
        self.start_button.config(state=tk.DISABLED)
        self.text_input.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        if ASR_AVAILABLE and self.mic_available:
            self.mic_button.config(state=tk.NORMAL, text="🎤 PRESS TO SPEAK")
        
        # Run consent sequentially
        def consent_thread():
            # First disclaimer
            consent = "Hello! Before we begin, I want to inform you that this is a technical demonstration for research purposes only. This is NOT a psychological evaluation or medical diagnosis."
            self.root.after(0, lambda: self.add_robot_message(consent))
            self.speak(consent)
            time.sleep(1)
            
            # Second disclaimer
            consent2 = "The information collected will be used solely for technical testing. If you have real health concerns, please consult a qualified healthcare professional."
            self.root.after(0, lambda: self.add_robot_message(consent2))
            self.speak(consent2)
            time.sleep(1)
            
            # Ask for consent
            consent_question = "Do you consent to participate in this screening? Please say 'yes' to continue or 'no' to decline."
            self.root.after(0, lambda: self.add_robot_message(consent_question))
            self.speak(consent_question)
            
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
        
        question_text = f"Question {self.current_question + 1}: {q['question']}"
        
        # Display and speak question
        def question_thread():
            self.root.after(0, lambda: self.add_robot_message(question_text))
            self.speak(question_text)
            time.sleep(0.5)
            
            self.logger.log_turn(
                userRawSpeech="", asrTranscript="", languageDetected="EN",
                phqQuestionId=f"Q{q['id']}", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
                gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
                gptResponse="", finalRobotOutput=question_text, notes=f"Question {self.current_question + 1}"
            )
        
        threading.Thread(target=question_thread, daemon=True).start()
        self.status_label.config(text=f"Question {self.current_question + 1}/9 - 🎤 Press microphone or type answer")
    
    def start_voice_input(self):
        """Start listening via microphone using Whisper"""
        if not self.mic_available or self.is_listening:
            self.add_system_message("❌ Microphone not available. Please use text input.")
            return
        
        self.is_listening = True
        self.mic_button.config(text="🔴 LISTENING...", bg="#D32F2F")
        self.status_label.config(text="🎤 LISTENING... Speak your answer now!")
        
        def listen_thread():
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    self.root.after(0, lambda: self.add_system_message("🎤 Speak now!"))
                    audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
                
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
                    self.root.after(0, lambda: self.add_system_message("❌ No clear speech detected. Please speak your answer clearly."))
                    return
                
                self.root.after(0, lambda: self.process_response(text, is_voice=True))
                
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: self.add_system_message("⏰ No speech detected. Try again or type."))
            except Exception as e:
                error_msg = str(e)
                print(f"Voice input error: {error_msg}")
                if "PyAudio" in error_msg or "portaudio" in error_msg:
                    self.root.after(0, lambda: self.add_system_message("❌ Microphone error. Please use text input."))
                    self.mic_available = False
                    self.root.after(0, lambda: self.mic_button.config(state=tk.DISABLED, text="🎤 N/A"))
                else:
                    self.root.after(0, lambda: self.add_system_message(f"Error: {error_msg[:50]}. Use text input."))
            finally:
                self.root.after(0, self.stop_listening)
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self.mic_button.config(text="🎤 PRESS TO SPEAK", bg="#FF5722")
    
    def send_text(self):
        """Send text input"""
        text = self.text_input.get().strip()
        if text and self.session_active:
            self.text_input.delete(0, tk.END)
            self.process_response(text, is_voice=False)
    
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
        for idx, option in enumerate(q['options']):
            if option.lower() in resp_lower:
                return (q['scores'][idx], option)
        
        return (-1, None)
    
    def handle_crisis_protocol(self, score: int):
        """Handle Q9 safety protocol when self-harm risk is detected"""
        if self.current_question == 8 and score > 0:  # Q9 is index 8
            # Pause conversation
            self.text_input.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.mic_button.config(state=tk.DISABLED)
            
            # Add crisis warning to chat
            self.add_system_message("⚠️ SAFETY PROTOCOL ACTIVATED ⚠️")
            
            # Display supportive message
            crisis_msg = "I want to acknowledge your response. Your safety is very important. Please know that help is available."
            self.add_robot_message(crisis_msg)
            self.speak(crisis_msg)
            time.sleep(4)
            
            # Show crisis resources
            resources_title = "CRISIS RESOURCES - Please take note of these:"
            self.add_robot_message(resources_title)
            self.speak(resources_title)
            time.sleep(2)
            
            # Display hotlines in chat (visible on screen)
            crisis_info = """
EMERGENCY HOTLINES:
• Germany Crisis Hotline: 0800 111 0 111 or 0800 111 0 222
• International Crisis Line: 116 123
• Emergency Services: 112

You are not alone. Professional help is available 24/7.
Please consider reaching out to a mental health professional or counselor."""
            
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.insert(tk.END, crisis_info + "\n\n", "system")
            self.chat_area.see(tk.END)
            self.chat_area.config(state=tk.DISABLED)
            
            # Speak resources
            resources_msg = "Germany Crisis Hotline: 0800 111 0 111. International Crisis Line: 116 123. Emergency Services: 112. Please consider reaching out to a mental health professional. You are not alone, and help is available."
            self.speak(resources_msg)
            time.sleep(8)
            
            # Important reminder
            reminder = "This screening is not a diagnosis. Please contact a healthcare professional for proper evaluation and support."
            self.add_robot_message(reminder)
            self.speak(reminder)
            time.sleep(5)
            
            # Ask for acknowledgment
            self.add_robot_message("Have you noted these resources? Type 'yes' or press the microphone to continue.")
            self.speak("Have you noted these resources? Please confirm to continue.")
            
            # Re-enable input for acknowledgment
            self.text_input.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            if ASR_AVAILABLE:
                self.mic_button.config(state=tk.NORMAL)
            
            # Set flag to wait for acknowledgment
            self.waiting_for_crisis_ack = True
            
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
        """Use GPT to parse unclear response into PHQ-9 score"""
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            q = PHQ9_QUESTIONS[self.current_question]
            
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Question: {q['question']}\n0=Not at all, 1=Several days, 2=More than half, 3=Nearly every day\nRespond: NUMBER|PHRASE"},
                    {"role": "user", "content": f"{response}"}
                ],
                temperature=0,
                max_tokens=10
            )
            result = resp.choices[0].message.content.strip()
            parts = result.split('|')
            if len(parts) >= 2:
                score = int(parts[0].strip())
                confirm = parts[1].strip()
                return (score, confirm)
            else:
                return (-1, None)
        except:
            return (-1, None)
    
    def check_confirmation_with_gpt(self, response: str) -> bool:
        """Use GPT to understand if user confirmed"""
        if not OPENAI_API_KEY:
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['yes', 'correct', 'right', 'yeah', 'yep', 'ok', 'okay'])
        
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Reply YES if confirming, NO if not."},
                    {"role": "user", "content": f"Is '{response}' a confirmation?"}
                ],
                temperature=0,
                max_tokens=3
            )
            result = resp.choices[0].message.content.strip().upper()
            return "YES" in result
        except:
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
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Reply YES if agrees/consents, NO if declines."},
                    {"role": "user", "content": f"Does '{response}' mean consent?"}
                ],
                temperature=0,
                max_tokens=3
            )
            result = resp.choices[0].message.content.strip().upper()
            return "YES" in result
        except:
            # Fallback
            resp_lower = response.lower().strip()
            return any(word in resp_lower for word in ['yes', 'yeah', 'yep', 'accept', 'agree', 'consent', 'ok', 'okay', 'sure', 'fine', 'alright'])
    
    def call_gpt_fallback(self, response: str) -> tuple:
        """Call GPT for unclear responses"""
        q = PHQ9_QUESTIONS[self.current_question]
        prompt = f"""The user is answering PHQ-9: {q['question']}
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
            score = int(gpt_text[0]) if gpt_text[0] in "0123" else 1
            return score, gpt_text
        except:
            return 1, "GPT_ERROR"
    
    def process_response(self, response: str, is_voice: bool):
        """Process user response"""
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
                    self.speak(thanks)
                    time.sleep(1)
                    
                    instructions = "I will now ask you 9 questions about how you've been feeling over the last 2 weeks. Please answer with: not at all, several days, more than half the days, or nearly every day."
                    self.root.after(0, lambda: self.add_robot_message(instructions))
                    self.speak(instructions)
                    time.sleep(1)
                    
                    # Start questions
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=proceed_thread, daemon=True).start()
                return
            else:
                # User declined
                self.add_system_message("✗ Consent declined")
                decline_msg = "I understand. Thank you for your time. The screening will not proceed."
                self.add_robot_message(decline_msg)
                self.speak(decline_msg)
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
                
                # Log
                q = PHQ9_QUESTIONS[self.current_question]
                self.logger.log_turn(
                    userRawSpeech="", asrTranscript=confirmation,
                    languageDetected="EN",
                    phqQuestionId=f"Q{q['id']}",
                    handlingModule="PEPPER_LOCAL",
                    pepperLocalNlpSuccess=True,
                    gptUsed=False,
                    gptReason="",
                    gptModel="",
                    gptPromptSnippet="",
                    gptResponse="",
                    finalRobotOutput="Confirmed",
                    notes=f"Q{self.current_question + 1} response, score={score}"
                )
                
                # CHECK FOR CRISIS PROTOCOL (Q9 with score > 0)
                if self.handle_crisis_protocol(score):
                    return
                
                # Move directly to next question
                def continue_thread():
                    if self.current_question < 8:
                        next_msg = "Let me ask you the next question."
                        self.root.after(0, lambda: self.add_robot_message(next_msg))
                        self.speak(next_msg)
                        time.sleep(0.5)
                    
                    self.current_question += 1
                    self.root.after(500, self.ask_question)
                
                threading.Thread(target=continue_thread, daemon=True).start()
                return
            else:
                # User says no, ask again
                retry_msg = "I see. Let me ask the question again. Please answer with: not at all, several days, more than half the days, or nearly every day."
                self.add_robot_message(retry_msg)
                self.speak(retry_msg)
                self.waiting_for_answer_confirmation = False
                
                # Re-ask question
                def reask():
                    q = PHQ9_QUESTIONS[self.current_question]
                    question_text = f"Question {self.current_question + 1}: {q['question']}"
                    self.root.after(0, lambda: self.add_robot_message(question_text))
                    self.speak(question_text)
                
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
        module = "PEPPER_LOCAL"
        
        if not local_success and OPENAI_API_KEY:
            # Use GPT to understand response
            self.add_system_message("Using GPT to understand response...")
            gpt_score, gpt_confirmation = self.parse_with_gpt(response)
            if 0 <= gpt_score <= 3:
                score = gpt_score
                confirmation = gpt_confirmation
                local_success = False
                self.add_system_message(f"GPT understood: score={score}, as: {confirmation}")
            else:
                # Ask for clarification
                clarify_msg = f"I heard '{response}', but I'm not sure I understood correctly. Could you please repeat using: not at all, several days, more than half the days, or nearly every day?"
                self.add_robot_message(clarify_msg)
                self.speak(clarify_msg)
                self.add_system_message("Asked for clarification")
                return
        elif not local_success:
            # Ask for clarification
            clarify_msg = f"I heard '{response}', but I'm not sure I understood correctly. Could you please repeat using: not at all, several days, more than half the days, or nearly every day?"
            self.add_robot_message(clarify_msg)
            self.speak(clarify_msg)
            self.add_system_message("Asked for clarification")
            return
        else:
            self.add_system_message(f"Local NLP: score={score}, understood as: {confirmation}")
        
        self.responses.append(score)
        
        # Confirm what was understood
        confirm_msg = f"I understood: {confirmation}. Is that correct?"
        self.add_robot_message(confirm_msg)
        self.speak(confirm_msg)
        
        # Set flag waiting for confirmation
        self.waiting_for_answer_confirmation = True
        self.pending_score = score
        self.pending_confirmation = confirmation
        return
    
    def complete_screening(self):
        """Finish screening"""
        self.session_active = False
        self.text_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.mic_button.config(state=tk.DISABLED)
        
        total = sum(self.responses)
        severity = self.get_severity(total)
        severity_description = self.get_severity_description(severity)
        
        # Display score breakdown
        self.add_system_message(f"COMPLETED | Total Score: {total} out of 27 | Severity: {severity.upper()}")
        self.add_system_message(f"Your responses: {self.responses}")
        
        # Speak summary in background thread
        def summary_thread():
            # First message - score
            intro = f"Thank you for completing all 9 questions. Let me share your results."
            self.root.after(0, lambda: self.add_robot_message(intro))
            self.speak(intro)
            
            # Second message - score breakdown
            score_msg = f"Your total score is {total} out of a maximum of 27 points. This indicates {severity} level symptoms."
            self.root.after(0, lambda: self.add_robot_message(score_msg))
            self.speak(score_msg)
            
            # Third message - severity description
            self.root.after(0, lambda: self.add_robot_message(severity_description))
            self.speak(severity_description)
            
            # Fourth message - disclaimer
            disclaimer = "Please remember: This is a technical demonstration only, not a medical diagnosis. This data is collected for research purposes. If you have real health concerns, please consult a qualified healthcare professional."
            self.root.after(0, lambda: self.add_robot_message(disclaimer))
            self.speak(disclaimer)
            
            self.root.after(0, lambda: self.export_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text=f"✅ Completed! Total score: {total}/27 - {severity}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Screening Complete", 
                f"PHQ-9 Screening Complete!\n\n"
                f"Total Score: {total} / 27\n"
                f"Severity Level: {severity.upper()}\n\n"
                f"{severity_description}\n\n"
                f"⚠️ This is for technical demonstration only.\n"
                f"Click 'Export Logs' to save the session data."))
        
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
        """Export to CSV"""
        filename = self.logger.export_to_csv()
        messagebox.showinfo("Exported", f"Logs saved to:\n{filename}\n\nOpening folder...")
        os.startfile(os.getcwd())
    
    def update_status(self, text):
        """Update status"""
        self.status_label.config(text=text)


def main():
    """Launch GUI"""
    print("\n" + "="*70)
    print("🎤 PHQ-9 VOICE SIMULATION")
    print("="*70)
    
    if not ASR_AVAILABLE:
        print("\n⚠️  Speech recognition not fully available")
        print("   Microphone button will be disabled")
        print("   You can use text input + hear robot speak via TTS\n")
    
    if not TTS_AVAILABLE:
        print("\n⚠️  Text-to-speech not available")
        print("   You can still see robot messages in the window\n")
    
    print("🚀 Launching GUI window...")
    print("   - Green 'START SCREENING' button to begin")
    print("   - Red 'PRESS TO SPEAK' for voice input")
    print("   - Or type in text field\n")
    
    root = tk.Tk()
    app = VoicePHQ9GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

