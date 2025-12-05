# Python PHQ-9 Simulation

## Overview

This Python script provides a **lightweight simulation** of the Android PHQ-9 app that runs entirely on your laptop - **no Android emulator needed!**

## Features

✅ **Identical Logic** - Same conversation flow as Android app  
✅ **GPT Integration** - Same fallback behavior  
✅ **Turn Logging** - Same CSV format for analysis  
✅ **Language Detection** - Same EN/DE detection  
✅ **Runs Anywhere** - Just Python 3.7+  
✅ **Very Lightweight** - Uses minimal resources  
✅ **Fast** - No emulator overhead  

## Installation

### Step 1: Install Python

If you don't have Python installed:
- Windows: Download from https://www.python.org/downloads/
- Already installed on most Linux/Mac systems

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install openai==0.28.1
```

### Step 3: Configure API Key (Optional)

Edit `simulation.py` and replace:
```python
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
```

With your actual OpenAI API key.

**Note**: If you don't have an API key, the simulation will still work but use default responses instead of GPT.

## Usage

### Basic Usage

```bash
python simulation.py
```

Then answer the 9 PHQ-9 questions when prompted.

### Toggle GPT Mode

Edit `simulation.py`:

```python
GPT_ENABLED = True   # Normal mode with GPT fallback
# or
GPT_ENABLED = False  # Experiment mode without GPT
```

## Example Session

```
🎯 PHQ-9 Health Screening Simulation
This Python script simulates the Android app without needing an emulator.

Configuration:
  - GPT Mode: ENABLED
  - Simulation Mode: ACTIVE

Press Enter to start the screening...

======================================================================
🤖 PHQ-9 HEALTH SCREENING SIMULATION
======================================================================
Session ID: 3f7a4b2c-8d9e-4f3a-b1c2-5e6f7a8b9c0d
GPT Mode: ENABLED
======================================================================

🤖 Robot: I will ask you a few questions to check how you've been feeling recently.
This is not a diagnosis, but it helps you understand your emotions better.
Please answer honestly based on the last 2 weeks.

📋 Question 1 of 9
🤖 Robot: Over the last 2 weeks, how often have you had little interest or pleasure in doing things?
   Options: Not at all, Several days, More than half the days, Nearly every day

👤 You: not at all
   [Language detected: EN]
   [Local NLP success: score = 0]
🤖 Robot: Thank you. Moving to the next question.
   [Module: PEPPER_LOCAL]

📋 Question 2 of 9
🤖 Robot: Over the last 2 weeks, how often have you felt down, depressed, or hopeless?
   Options: Not at all, Several days, More than half the days, Nearly every day

👤 You: sometimes I guess
   [Language detected: EN]
   [Local NLP failed, using GPT fallback...]
   [GPT returned: 1]
🤖 Robot: Thank you. Moving to the next question.
   [Module: GPT_FALLBACK]

...

======================================================================
📊 SCREENING COMPLETE
======================================================================
Total Score: 8
Severity: mild
======================================================================

🤖 Robot: Generating summary...

🤖 Robot: Thank you for completing the screening. Your responses show mild symptoms, which suggests you might be experiencing some challenges lately. Remember, this is just a tool to help you reflect on your well-being, not a diagnosis. If you're concerned, talking to a healthcare provider could be helpful.

======================================================================
✅ Logs exported to: interaction_logs_20231205_143022.csv
======================================================================

✨ Thank you for participating!
You can now analyze the CSV file in Excel, Python, or R.
```

## Output

The script generates a CSV file with the same format as the Android app:

**`interaction_logs_YYYYMMDD_HHMMSS.csv`**

Contains:
- timestamp
- sessionId
- turnIndex
- userRawSpeech
- asrTranscript
- languageDetected
- phqQuestionId
- handlingModule (PEPPER_LOCAL or GPT_FALLBACK)
- pepperLocalNlpSuccess
- gptUsed
- gptReason
- gptModel
- gptPromptSnippet
- gptResponse
- finalRobotOutput
- notes

## Advantages Over Android Emulator

| Feature | Python Simulation | Android Emulator |
|---------|------------------|------------------|
| **Setup Time** | 2 minutes | 30+ minutes |
| **Resource Usage** | Minimal (~50MB RAM) | Heavy (4-8GB RAM) |
| **Speed** | Instant | Slow startup |
| **Reliability** | Always works | May crash |
| **Portability** | Runs anywhere | Needs specific setup |
| **Multiple Sessions** | Easy to script | Manual each time |

## Use Cases

### 1. Quick Testing

Test the screening logic without waiting for emulator:
```bash
python simulation.py
```

### 2. Multiple Participants

Run multiple sessions easily:
```bash
for i in {1..10}; do python simulation.py; done
```

### 3. GPT Comparison Study

**Session 1**: GPT Enabled
```python
GPT_ENABLED = True
```

**Session 2**: GPT Disabled
```python
GPT_ENABLED = False
```

Compare the resulting CSV files.

### 4. Batch Processing

Create a script to simulate multiple participants:

```python
for participant_id in range(10):
    simulator = PHQ9Simulator(api_key, gpt_enabled=True)
    # ... provide automated responses for testing
```

### 5. Research Data Collection

- Send Python script to participants
- They run it on their own computers
- They email back the CSV file
- No phone/Android needed!

## Analysis

Same as Android app - open CSV in:

**Python:**
```python
import pandas as pd
df = pd.read_csv('interaction_logs_20231205_143022.csv')
print(df['gptUsed'].value_counts())
```

**R:**
```r
library(tidyverse)
logs <- read_csv('interaction_logs_20231205_143022.csv')
table(logs$gptUsed)
```

**Excel:**
- Open CSV file
- Create pivot tables
- Analyze GPT usage, language distribution, etc.

## Limitations

Compared to full Android app:
- ❌ No voice input (text only)
- ❌ No Android TTS (robot just prints text)
- ❌ No visual UI (command line only)

But these don't matter for:
- ✅ Testing conversation logic
- ✅ Collecting research data
- ✅ Generating logs for analysis
- ✅ GPT evaluation studies

## Troubleshooting

### Issue: OpenAI API error

**Solution**: Check your API key is correct, or set `GPT_ENABLED = False` to test without GPT.

### Issue: Module not found

**Solution**: Install dependencies:
```bash
pip install openai==0.28.1
```

### Issue: CSV file not found

**Solution**: CSV is created in the same directory as the script. Check current directory.

## Quick Start

```bash
# 1. Install Python (if needed)
# 2. Install dependencies
pip install openai==0.28.1

# 3. (Optional) Add your OpenAI API key to simulation.py

# 4. Run the simulation
python simulation.py

# 5. Answer the 9 questions

# 6. Get your CSV file!
```

## Summary

This Python simulation gives you **all the research benefits** of the Android app without needing:
- Pepper robot ❌
- Android device ❌
- Emulator ❌
- Strong laptop ❌

Just Python and your keyboard! ✅

Perfect for:
- Testing on any laptop
- Remote data collection
- Multiple participants
- GPT comparison studies
- Quick iterations

**Ready to run your first simulation?** Just: `python simulation.py`

