# Experiments and Simulations

This folder contains all experimental code and simulation tools for the PHQ-9 E-Health screening system.

## Files Overview

### Core Session Management
- **`phq9_session.py`** - PHQ-9 session manager (English version)
  - Handles PHQ-9 screening logic, scoring, and state management
  - Manages question flow and validation
  
- **`phq9_session_de.py`** - PHQ-9 session manager (German version)
  - German language version of the session manager

### Simulation Tools
- **`simulation_gui_voice.py`** - Interactive GUI simulation with voice input (English)
  - Full GUI interface for testing PHQ-9 screening
  - Voice input/output support using speech recognition and TTS
  - GPT integration for conversational screening
  
- **`simulation_gui_voice_de.py`** - Interactive GUI simulation with voice input (German)
  - German language version of the GUI simulation

### Analysis and Visualization
- **`analyze_sessions.py`** - Session data analysis tool
  - Analyzes recorded session data from experiments
  - Generates statistics and metrics from simulation runs
  
- **`create_visualizations.py`** - Visualization generator
  - Creates charts and graphs from session data
  - Generates publication-ready figures

## Usage

**Important:** All scripts should be run from within the `experiments_and_simulations/` directory, or use the full path when running from the project root.

### Running Simulations

From the project root:
```bash
python experiments_and_simulations/simulation_gui_voice.py
```

Or from within this directory:
```bash
cd experiments_and_simulations
python simulation_gui_voice.py
```

For the German version:
```bash
python simulation_gui_voice_de.py
```

### Analyzing Results

To analyze session data:
```bash
python analyze_sessions.py
```

To create visualizations:
```bash
python create_visualizations.py
```

## Data Storage
Session data is stored in `data/sessions/` with each session in its own folder containing:
- `session_data.json` - Session metadata and scores
- `interaction_logs.csv` - Detailed interaction logs
- `gpt_api_calls.json` - GPT API call logs (if enabled)
- `transcript.txt` - Full conversation transcript

## Results
Analysis results and visualizations are stored in `results/figures/` including:
- Total score comparisons
- GPT usage statistics
- Duration analysis
- Per-question score breakdowns
- Severity distributions
- And more publication-ready figures

## Requirements
See `../requirements.txt` for dependencies. Key requirements:
- OpenAI API access (for GPT features)
- pyttsx3 (text-to-speech)
- speech_recognition (voice input)
- tkinter (GUI)
- Various data analysis libraries (pandas, matplotlib, seaborn)

