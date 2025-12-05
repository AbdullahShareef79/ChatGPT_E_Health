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
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 160)
                self.tts_engine.setProperty('volume', 1.0)
                self.tts_ready = True
            except:
                self.tts_ready = False
        else:
            self.tts_ready = False
        
        # Initialize Speech Recognition
        if ASR_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
        
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
    
    def speak(self, text):
        """Robot speaks using TTS"""
        if self.tts_ready:
            def tts_thread():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except:
                    pass
            threading.Thread(target=tts_thread, daemon=True).start()
    
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
        if ASR_AVAILABLE:
            self.mic_button.config(state=tk.NORMAL, text="🎤 PRESS TO SPEAK")
        
        welcome = "I will ask you 9 questions about how you've been feeling over the last 2 weeks. This is not a diagnosis, but helps you understand your emotions. Please answer honestly."
        self.add_robot_message(welcome)
        self.speak(welcome)
        
        self.logger.log_turn(
            userRawSpeech="", asrTranscript="", languageDetected="EN",
            phqQuestionId="", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
            gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
            gptResponse="", finalRobotOutput=welcome, notes="Screening started"
        )
        
        time.sleep(1)
        self.ask_question()
    
    def ask_question(self):
        """Ask current PHQ-9 question"""
        if self.current_question >= 9:
            self.complete_screening()
            return
        
        q = PHQ9_QUESTIONS[self.current_question]
        self.progress_label.config(text=f"Question {self.current_question + 1} / 9")
        self.progress_bar['value'] = self.current_question + 1
        
        question_text = f"Question {self.current_question + 1}: {q['question']}"
        self.add_robot_message(question_text)
        self.speak(question_text)
        
        self.logger.log_turn(
            userRawSpeech="", asrTranscript="", languageDetected="EN",
            phqQuestionId=f"Q{q['id']}", handlingModule="PEPPER_LOCAL", pepperLocalNlpSuccess=True,
            gptUsed=False, gptReason="", gptModel="", gptPromptSnippet="",
            gptResponse="", finalRobotOutput=question_text, notes=f"Question {self.current_question + 1}"
        )
        
        self.status_label.config(text=f"Question {self.current_question + 1}/9 - 🎤 Press microphone or type answer")
    
    def start_voice_input(self):
        """Start listening via microphone"""
        if not ASR_AVAILABLE or self.is_listening:
            return
        
        self.is_listening = True
        self.mic_button.config(text="🔴 LISTENING...", bg="#D32F2F")
        self.status_label.config(text="🎤 LISTENING... Speak your answer now!")
        
        def listen_thread():
            try:
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    self.root.after(0, lambda: self.add_system_message("Microphone active - speak now!"))
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                self.root.after(0, lambda: self.status_label.config(text="Processing your speech..."))
                transcript = recognizer.recognize_google(audio)
                
                self.root.after(0, lambda: self.process_response(transcript, is_voice=True))
                
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: self.add_system_message("⏰ Timeout - no speech detected. Try again or type."))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.add_system_message("❌ Could not understand. Try again or type."))
            except Exception as e:
                self.root.after(0, lambda: self.add_system_message(f"Error: {str(e)[:50]}. Use text input."))
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
    
    def parse_response(self, response: str) -> int:
        """Parse response locally"""
        resp_lower = response.lower()
        if "not at all" in resp_lower or "never" in resp_lower:
            return 0
        elif "several days" in resp_lower or "sometimes" in resp_lower:
            return 1
        elif "more than half" in resp_lower or "often" in resp_lower:
            return 2
        elif "nearly every day" in resp_lower or "always" in resp_lower:
            return 3
        
        # Try matching options
        q = PHQ9_QUESTIONS[self.current_question]
        for idx, option in enumerate(q['options']):
            if option.lower() in resp_lower:
                return q['scores'][idx]
        return -1
    
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
                temperature=0
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
        
        self.add_user_message(response)
        
        # Detect language
        lang = LanguageDetector.detect_language(response)
        self.add_system_message(f"Language: {lang}")
        
        # Try local NLP
        score = self.parse_response(response)
        local_success = 0 <= score <= 3
        
        gpt_used = False
        gpt_reason = None
        module = "PEPPER_LOCAL"
        
        if not local_success and GPT_ENABLED:
            self.add_system_message("Using GPT fallback...")
            score, gpt_resp = self.call_gpt_fallback(response)
            gpt_used = True
            gpt_reason = "intent_not_found"
            module = "GPT_FALLBACK"
            self.add_system_message(f"GPT: {gpt_resp}")
        elif not local_success:
            self.add_system_message("Local NLP failed, GPT disabled - default score")
            score = 1
            gpt_reason = "gpt_disabled"
        else:
            self.add_system_message(f"Local NLP: score={score}")
        
        self.responses.append(score)
        
        # Log
        q = PHQ9_QUESTIONS[self.current_question]
        self.logger.log_turn(
            userRawSpeech=response if is_voice else "",
            asrTranscript=response,
            languageDetected=lang,
            phqQuestionId=f"Q{q['id']}",
            handlingModule=module,
            pepperLocalNlpSuccess=local_success,
            gptUsed=gpt_used,
            gptReason=gpt_reason or "",
            gptModel="gpt-4o-mini" if gpt_used else "",
            gptPromptSnippet=f"Parse: {response}" if gpt_used else "",
            gptResponse="",
            finalRobotOutput="Thank you",
            notes=f"Q{self.current_question + 1} response"
        )
        
        # Next
        ack = "Thank you. Moving to the next question."
        self.add_robot_message(ack)
        self.speak(ack)
        
        self.current_question += 1
        self.root.after(1500, self.ask_question)
    
    def complete_screening(self):
        """Finish screening"""
        self.session_active = False
        self.text_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.mic_button.config(state=tk.DISABLED)
        
        total = sum(self.responses)
        severity = self.get_severity(total)
        
        summary = f"Thank you for completing the screening. Your score is {total}, indicating {severity} symptoms. Remember, this is not a diagnosis. If concerned, please speak with a healthcare provider."
        
        self.add_system_message(f"COMPLETED | Score: {total} | Severity: {severity}")
        self.add_robot_message(summary)
        self.speak(summary)
        
        self.export_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"✅ Completed! Total score: {total}")
        
        messagebox.showinfo("Complete", f"Screening complete!\n\nScore: {total}\nSeverity: {severity}\n\nClick Export Logs to save.")
    
    def get_severity(self, score):
        """Get severity level"""
        if score <= 4: return "minimal"
        elif score <= 9: return "mild"
        elif score <= 14: return "moderate"
        elif score <= 19: return "moderately severe"
        else: return "severe"
    
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

