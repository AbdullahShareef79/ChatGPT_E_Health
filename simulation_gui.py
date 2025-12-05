#!/usr/bin/env python3
"""
PHQ-9 Health Screening Simulation - GUI Version
With speech input/output and visual interface
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
from datetime import datetime
from simulation import (
    PHQ9Simulator, InteractionLogger, LanguageDetector, 
    PHQ9_QUESTIONS, OPENAI_API_KEY, GPT_ENABLED, SPEECH_AVAILABLE
)

try:
    import speech_recognition as sr
    import pyttsx3
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False


class PHQ9GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 PHQ-9 Health Screening Simulation")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize simulator
        self.simulator = None
        self.current_question = 0
        self.session_active = False
        
        # Speech components
        self.has_microphone = False
        if SPEECH_AVAILABLE:
            try:
                # Try to initialize TTS (usually works)
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.9)
            except:
                self.tts_engine = None
            
            try:
                # Try to initialize microphone (requires PyAudio)
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.has_microphone = True
                self.is_listening = False
            except:
                self.has_microphone = False
                print("⚠️  Microphone not available (PyAudio not installed)")
                print("   You can still use text input and hear robot speak!")
        
        # Create GUI
        self.create_widgets()
        
        # Welcome message
        self.add_robot_message("Hello! I'm ready to conduct a PHQ-9 health screening.")
        self.add_robot_message("Click 'Start Screening' to begin.")
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#4CAF50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🤖 PHQ-9 HEALTH SCREENING",
            font=("Arial", 18, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#2196F3", height=40)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Status: Ready | GPT: " + ("ON" if GPT_ENABLED else "OFF"),
            font=("Arial", 10),
            bg="#2196F3",
            fg="white"
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Question 0 / 9",
            font=("Arial", 10),
            bg="#f0f0f0"
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            length=760,
            mode='determinate',
            maximum=9
        )
        self.progress_bar.pack()
        
        # Chat area
        chat_frame = tk.Frame(self.root, bg="#f0f0f0")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="#ffffff",
            state=tk.DISABLED,
            height=15
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for styling
        self.chat_area.tag_config("robot", foreground="#1976D2", font=("Arial", 11, "bold"))
        self.chat_area.tag_config("user", foreground="#388E3C", font=("Arial", 11, "bold"))
        self.chat_area.tag_config("system", foreground="#F57C00", font=("Arial", 10, "italic"))
        
        # Input area
        input_frame = tk.Frame(self.root, bg="#f0f0f0")
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Text input
        self.text_input = tk.Entry(
            input_frame,
            font=("Arial", 12),
            state=tk.DISABLED
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.text_input.bind("<Return>", lambda e: self.send_text_response())
        
        # Microphone button
        mic_state = tk.NORMAL if (SPEECH_AVAILABLE and hasattr(self, 'has_microphone') and self.has_microphone) else tk.DISABLED
        self.mic_button = tk.Button(
            input_frame,
            text="🎤 Speak" if mic_state == tk.NORMAL else "🎤 N/A",
            font=("Arial", 12, "bold"),
            bg="#FF5722" if mic_state == tk.NORMAL else "#999999",
            fg="white",
            width=10,
            height=2,
            command=self.start_listening,
            state=mic_state
        )
        self.mic_button.pack(side=tk.LEFT, padx=5)
        
        if mic_state == tk.DISABLED:
            # Add tooltip
            tk.Label(
                input_frame,
                text="(Mic disabled - use text input)",
                font=("Arial", 8),
                fg="#666666",
                bg="#f0f0f0"
            ).pack(side=tk.LEFT, padx=5)
        
        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            width=8,
            height=2,
            command=self.send_text_response,
            state=tk.DISABLED
        )
        self.send_button.pack(side=tk.LEFT)
        
        # Control buttons
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.start_button = tk.Button(
            control_frame,
            text="▶ Start Screening",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2,
            command=self.start_screening
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.export_button = tk.Button(
            control_frame,
            text="📊 Export Logs",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            width=20,
            height=2,
            command=self.export_logs,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
    
    def add_robot_message(self, text):
        """Add robot message to chat"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "🤖 Robot: ", "robot")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        # Speak if TTS available (in background thread)
        if SPEECH_AVAILABLE and hasattr(self, 'tts_engine') and self.tts_engine:
            def speak_async():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except:
                    pass  # Silently fail if TTS issues
            threading.Thread(target=speak_async, daemon=True).start()
    
    def add_user_message(self, text):
        """Add user message to chat"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "👤 You: ", "user")
        self.chat_area.insert(tk.END, text + "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def add_system_message(self, text):
        """Add system message to chat"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"[{text}]\n", "system")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def update_status(self, text):
        """Update status label"""
        self.status_label.config(text=text)
    
    def start_screening(self):
        """Start the PHQ-9 screening"""
        self.session_active = True
        self.current_question = 0
        self.start_button.config(state=tk.DISABLED)
        self.text_input.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        if SPEECH_AVAILABLE and self.has_microphone:
            self.mic_button.config(state=tk.NORMAL)
        
        # Initialize simulator
        from simulation import PHQ9Simulator
        self.simulator = PHQ9Simulator(OPENAI_API_KEY, GPT_ENABLED, use_speech=False)
        
        # Welcome message
        welcome = "I will ask you 9 questions about how you've been feeling. Please answer honestly based on the last 2 weeks."
        self.add_robot_message(welcome)
        
        # Start with first question
        self.ask_next_question()
    
    def ask_next_question(self):
        """Ask the next PHQ-9 question"""
        if self.current_question >= len(PHQ9_QUESTIONS):
            self.complete_screening()
            return
        
        question = PHQ9_QUESTIONS[self.current_question]
        self.progress_label.config(text=f"Question {self.current_question + 1} / 9")
        self.progress_bar['value'] = self.current_question + 1
        
        self.add_robot_message(question['question'])
        self.add_system_message(f"Options: {', '.join(question['options'])}")
        
        self.update_status(f"Question {self.current_question + 1}/9 | Waiting for response...")
    
    def process_response(self, response):
        """Process user response"""
        if not self.session_active:
            return
        
        self.add_user_message(response)
        
        # Detect language
        language = LanguageDetector.detect_language(response)
        self.add_system_message(f"Language detected: {language}")
        
        # Parse response
        score = self.simulator.parse_response_to_score(response, self.current_question)
        local_success = 0 <= score <= 3
        
        if not local_success and GPT_ENABLED:
            self.add_system_message("Using GPT fallback...")
            self.update_status("Processing with GPT...")
            score, gpt_response = self.simulator.call_gpt_for_response_parsing(response, self.current_question)
            self.add_system_message(f"GPT returned: {gpt_response}")
        elif not local_success:
            self.add_system_message("Local NLP failed, using default score")
            score = 1
        else:
            self.add_system_message(f"Local NLP success: score = {score}")
        
        self.simulator.responses.append(score)
        
        # Log the interaction
        question = PHQ9_QUESTIONS[self.current_question]
        self.simulator.logger.log_turn(
            user_raw_speech=None,
            asr_transcript=response,
            language_detected=language,
            phq_question_id=f"Q{question['id']}",
            handling_module="GPT_FALLBACK" if not local_success and GPT_ENABLED else "PEPPER_LOCAL",
            pepper_local_nlp_success=local_success,
            gpt_used=not local_success and GPT_ENABLED,
            gpt_reason="intent_not_found" if not local_success else None,
            gpt_model="gpt-4o-mini" if not local_success and GPT_ENABLED else None,
            gpt_prompt_snippet=f"Parse: {response}" if not local_success and GPT_ENABLED else None,
            gpt_response=None,
            final_robot_output="Thank you",
            notes=f"Response to Q{self.current_question + 1}"
        )
        
        # Move to next question
        self.add_robot_message("Thank you. Moving to the next question.")
        self.current_question += 1
        
        self.root.after(1000, self.ask_next_question)
    
    def complete_screening(self):
        """Complete the screening and show results"""
        self.session_active = False
        self.text_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.mic_button.config(state=tk.DISABLED)
        
        total_score = sum(self.simulator.responses)
        severity = self.simulator.get_severity_level(total_score)
        
        self.add_system_message(f"Total Score: {total_score} | Severity: {severity}")
        self.update_status(f"Completed! Score: {total_score}")
        
        # Generate summary
        self.add_system_message("Generating summary...")
        summary = self.simulator.generate_summary(total_score, severity)
        self.add_robot_message(summary)
        
        # Enable export
        self.export_button.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "Screening Complete",
            f"Thank you for completing the screening!\n\n"
            f"Total Score: {total_score}\n"
            f"Severity: {severity}\n\n"
            f"Click 'Export Logs' to save the results."
        )
    
    def send_text_response(self):
        """Send text response"""
        response = self.text_input.get().strip()
        if response and self.session_active:
            self.text_input.delete(0, tk.END)
            self.process_response(response)
    
    def start_listening(self):
        """Start speech recognition"""
        if not SPEECH_AVAILABLE or not self.has_microphone or self.is_listening:
            return
        
        self.is_listening = True
        self.mic_button.config(text="🔴 Listening...", bg="#D32F2F")
        self.update_status("🎤 Listening... Speak now!")
        
        def listen_thread():
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                self.root.after(0, lambda: self.update_status("Processing speech..."))
                transcript = self.recognizer.recognize_google(audio)
                
                self.root.after(0, lambda: self.process_response(transcript))
                
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: messagebox.showwarning("Timeout", "No speech detected. Please try again."))
            except sr.UnknownValueError:
                self.root.after(0, lambda: messagebox.showwarning("Error", "Could not understand audio. Please try again or type your response."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Speech recognition error: {e}"))
            finally:
                self.root.after(0, self.stop_listening)
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self.mic_button.config(text="🎤 Speak", bg="#FF5722")
        self.update_status(f"Question {self.current_question + 1}/9 | Ready")
    
    def export_logs(self):
        """Export logs to CSV"""
        if self.simulator:
            filename = self.simulator.logger.export_to_csv()
            messagebox.showinfo(
                "Logs Exported",
                f"Logs exported successfully!\n\nFile: {filename}\n\n"
                f"You can now analyze this CSV file in Excel, Python, or R."
            )
            
            # Show file location
            import os
            os.startfile(os.getcwd())


def main():
    """Main entry point for GUI"""
    if not SPEECH_AVAILABLE:
        print("⚠️  Warning: Speech libraries not fully available.")
        print("   TTS will work but microphone input may not work.")
        print("   You can still use text input!\n")
    
    root = tk.Tk()
    app = PHQ9GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

