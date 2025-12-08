# ChatGPT E-Health: Pepper Robot PHQ-9 Health Screening

Master's Thesis Project - Natural Language Processing Integration with Social Robots for Mental Health Screening

## Overview

This project implements a GPT-powered conversational AI system integrated with the Pepper Robot to conduct PHQ-9 (Patient Health Questionnaire-9) depression screening. The system supports natural voice and text interaction in both English and German, with comprehensive logging capabilities for research evaluation.

## Key Features

### PHQ-9 Health Screening
- Complete 9-question PHQ-9 assessment
- Voice and text input support
- Real-time progress tracking
- GPT-4o-mini powered natural language understanding
- Automated severity assessment
- Safety protocol for Question 9 (self-harm)
- Session data persistence

### Robot Integration
- Pepper Robot (SoftBank Robotics) integration
- QiSDK voice recognition and text-to-speech
- Multimodal interaction (voice, text, touch)
- Simulation mode for research without physical robot
- Ethical design with clear disclaimers

### Research Features
- Turn-level interaction logging
- GPT usage tracking and analysis
- Language detection (EN/DE)
- CSV export for data analysis
- Session transcripts and metadata
- Configurable evaluation parameters

## Technology Stack

- **Android Studio Bumblebee 2021.1.1**
- **Kotlin** - Primary language
- **QiSDK** - Pepper robot integration
- **Room Database** - Local data persistence
- **OpenAI API** - GPT-4o-mini for natural language understanding
- **OkHttp** - Network communication
- **Python** - Simulation environment
- **OpenAI Whisper API** - Speech recognition in simulation

## Project Structure

- **`app/`** - Android application for Pepper Robot
- **`experiments_and_simulations/`** - Experimental code, simulation tools, data, and results
  - Session management scripts (English and German)
  - GUI simulation with voice input
  - Session analysis and visualization tools
  - `data/` - Session data and logs
  - `results/` - Analysis results and figures
  - See `experiments_and_simulations/README.md` for details
- **`docs/`** - Documentation and implementation guides
- **`WRITTENPART/`** - Master's thesis LaTeX documents

## PHQ-9 Implementation

### Questions
1. Little interest or pleasure in doing things
2. Feeling down, depressed, or hopeless
3. Trouble falling/staying asleep or sleeping too much
4. Feeling tired or having little energy
5. Poor appetite or overeating
6. Feeling bad about self or failure
7. Trouble concentrating
8. Moving or speaking slowly
9. Thoughts of self-harm

### Severity Categories
- 0-4: Minimal symptoms
- 5-9: Mild symptoms
- 10-14: Moderate symptoms
- 15-19: Moderately severe symptoms
- 20-27: Severe symptoms

## Installation

### Android Application (Pepper Robot)

1. Clone the repository:
   ```bash
   git clone https://github.com/AbdullahShareef79/ChatGPT_E_Health.git
   cd ChatGPT_E_Health
   ```

2. Configure OpenAI API key:
   - Open `app/src/main/java/com/example/pepperapp/ui/Fragments/ChatFragment.kt`
   - Replace `YOUR_OPENAI_API_KEY_HERE` with your API key

3. Connect to Pepper Robot:
   ```bash
   adb connect <PEPPER_IP>:5555
   ```

4. Build and deploy:
   - Open project in Android Studio
   - Select Pepper as target device
   - Build and run

### Python Simulation

1. Install dependencies:
   ```bash
   cd ChatGPT_E_Health
   pip install -r requirements.txt
   ```

2. Create `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_key_here
   GPT_ENABLED=True
   ```

3. Run simulation (from project root):
   ```bash
   python experiments_and_simulations/simulation_gui_voice.py
   ```
   
   Or navigate to the experiments folder first:
   ```bash
   cd experiments_and_simulations
   python simulation_gui_voice.py
   ```

## Usage

### Pepper Robot Mode
1. Launch application on Pepper
2. Navigate to "Health Screening"
3. Complete 9 PHQ-9 questions using voice or text
4. Receive automated severity assessment
5. View supportive feedback

### Simulation Mode
1. Set `RobotMode.SIMULATION` in `app/src/main/java/com/example/pepperapp/config/RobotMode.kt`
2. Build and install on Android device or emulator
3. Use Android SpeechRecognizer and TTS instead of Pepper hardware

### Python Simulation
1. Run `python experiments_and_simulations/simulation_gui_voice.py`
2. Speak into microphone or type responses
3. Complete PHQ-9 screening
4. Review results and logs in `experiments_and_simulations/data/sessions/`

## Data Collection

Each session logs:
- ASR transcripts with language detection
- Local NLP parsing results
- GPT API calls (prompts and responses)
- Token usage
- Retry counts per question
- Final PHQ-9 scores
- Severity classification
- Complete interaction transcript

### Exporting Logs

Android:
```bash
adb pull /storage/emulated/0/Android/data/com.example.pepperapp/files/interaction_logs_*.csv
```

Python:
Logs automatically saved to `data/sessions/session_[ID]_[timestamp]/`

## Research Applications

This implementation supports research on:
- Human-robot interaction in healthcare
- Mental health screening through social robots
- Natural language processing for clinical applications
- Multilingual conversational AI systems
- GPT-assisted response interpretation

## Security and Privacy

- All data stored locally on device
- No cloud storage of personal information
- OpenAI API used only for response interpretation
- Secure API key management via environment variables
- Clear ethical disclaimers throughout interaction
- Anonymized session IDs
