# PHQ-9 Voice Simulation - User Guide

## 🎤 Enhanced Features

### What's New
The voice simulation now includes:

1. **✅ Consent & Disclaimer**: 
   - Starts with a clear statement that this is for technical demonstration only
   - Explains it's NOT a psychological evaluation
   - Mentions data is for research purposes only

2. **✅ Intelligent Responses**:
   - Robot acknowledges each answer with varied responses
   - Clearly states the score recorded (0, 1, 2, or 3)
   - Makes the conversation feel more natural

3. **✅ Detailed Score Calculation**:
   - Shows your total score out of 27
   - Lists all your individual responses
   - Calculates severity level automatically

4. **✅ Comprehensive Severity Summary**:
   - **Minimal** (0-4): Little to no symptoms
   - **Mild** (5-9): Mild symptoms, may benefit from monitoring
   - **Moderate** (10-14): May warrant professional evaluation
   - **Moderately Severe** (15-19): Benefit from professional care
   - **Severe** (20-27): Requires immediate professional attention

## 🚀 How to Use

### Starting the Simulation

```bash
python simulation_gui_voice.py
```

### During the Screening

1. **Click "▶ START SCREENING"** - Listen to the consent and introduction

2. **For Each Question**, you can:
   - **🎤 Press the red "PRESS TO SPEAK" button** and say your answer
   - **⌨️ Type your answer** in the text field
   
3. **Valid Answers**:
   - "Not at all" (score 0)
   - "Several days" (score 1)
   - "More than half the days" (score 2)
   - "Nearly every day" (score 3)
   - Or simply say: "0", "1", "2", "3"

4. **Robot will**:
   - Acknowledge your answer
   - Tell you the score recorded
   - Move to the next question

### After Completion

The robot will:
1. Thank you for completing the screening
2. Tell you your total score (out of 27)
3. Explain your severity level
4. Provide detailed information about what that level means
5. Remind you this is for technical demonstration only

Then you can:
- **📊 Click "Export Logs"** to save all interaction data to CSV
- Review the conversation in the chat window

## 📋 Example Interaction

```
🤖 Robot: Hello! Before we begin, I want to inform you that this is 
         a technical demonstration for research purposes only...

🤖 Robot: Question 1: Over the last 2 weeks, how often have you been 
         bothered by little interest or pleasure in doing things?

👤 You: Several days

🤖 Robot: Understood, several days. I've noted that as 1.
🤖 Robot: Let me ask you the next question.

[... continues for all 9 questions ...]

🤖 Robot: Thank you for completing all 9 questions. Let me share your results.
🤖 Robot: Your total score is 7 out of a maximum of 27 points. 
         This indicates mild level symptoms.
🤖 Robot: Mild depression symptoms. Scores in this range (5-9) may indicate 
         mild depressive symptoms that might benefit from monitoring.
🤖 Robot: Please remember: This is a technical demonstration only...
```

## 🔧 Technical Details

### Requirements
- ✅ Python 3.12
- ✅ PyAudio (for microphone input)
- ✅ SpeechRecognition (for speech-to-text)
- ✅ pyttsx3 (for text-to-speech)
- ✅ tkinter (for GUI)

### Voice Recognition Tips
- Speak clearly and at a moderate pace
- Wait for the "LISTENING..." indicator
- If recognition fails, you can always type your answer
- Microphone automatically adjusts for ambient noise

### Data Logging
All interactions are automatically logged with:
- Timestamp
- Your responses (text and audio)
- Language detected
- Scores assigned
- Whether GPT was used for parsing
- Final robot output

Export creates a CSV file with complete session data for analysis.

## ⚠️ Important Reminders

1. **This is NOT medical advice**: This is purely a technical demonstration
2. **For research purposes**: Data collected is for technical testing only
3. **Seek professional help**: If you have real concerns, consult a healthcare provider
4. **Privacy**: Your voice data is processed locally and sent to Google Speech API for transcription

## 🐛 Troubleshooting

**Microphone not working?**
- Check that PyAudio is installed: `pip install PyAudio`
- Make sure your microphone is not muted
- Check Windows privacy settings allow microphone access
- Try the text input as an alternative

**Robot not speaking?**
- pyttsx3 may need initialization time on first run
- You can still read the robot's responses in the chat window

**Can't understand my speech?**
- Speak more clearly or slower
- Check your microphone quality
- Use the text input instead

---

**Enjoy the demonstration! 🎉**


