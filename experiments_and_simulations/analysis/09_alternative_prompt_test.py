"""
Test alternative GPT prompts on the 29 unique fallback turns.

This script reruns GPT fallback with two alternative prompt variants:
- Prompt A: "Classifier framing"
- Prompt B: "Strict rejection"

Keeps: temperature=0, max_tokens small, same transcript input
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Check for OpenAI API key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    print("=" * 80)
    print("OpenAI API Key Required")
    print("=" * 80)
    print(f"ERROR: OPENAI_API_KEY not found in .env file at: {env_path}")
    print("Please ensure the .env file exists and contains OPENAI_API_KEY=your_key")
    exit(1)

import openai
openai.api_key = OPENAI_API_KEY

# Paths
SCRIPT_DIR = Path(__file__).parent
TABLES_DIR = SCRIPT_DIR.parent / "analysis_tables"
OUTPUT_DIR = TABLES_DIR

# PHQ-9 Questions (English and German)
PHQ9_QUESTIONS_EN = {
    'Q1': "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
    'Q2': "Over the last 2 weeks, how often have you felt down, depressed, or hopeless?",
    'Q3': "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
    'Q4': "Over the last 2 weeks, how often have you felt tired or had little energy?",
    'Q5': "Over the last 2 weeks, how often have you had poor appetite or overeating?",
    'Q6': "Over the last 2 weeks, how often have you felt bad about yourself, or that you are a failure, or have let yourself or your family down?",
    'Q7': "Over the last 2 weeks, how often have you had trouble concentrating on things, such as reading the newspaper or watching television?",
    'Q8': "Over the last 2 weeks, how often have you been moving or speaking slowly enough that other people could have noticed?",
    'Q9': "Over the last 2 weeks, how often have you had thoughts that you would be better off dead or of hurting yourself in some way?"
}

PHQ9_QUESTIONS_DE = {
    'F1': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Wenig Interesse oder Freude an Ihren Tätigkeiten",
    'F2': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Niedergeschlagenheit, Schwermut oder Hoffnungslosigkeit",
    'F3': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Schwierigkeiten, ein- oder durchzuschlafen oder vermehrter Schlaf",
    'F4': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Müdigkeit oder Gefühl, keine Energie zu haben",
    'F5': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Verminderter Appetit oder übermäßiges Bedürfnis zu essen",
    'F6': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Schlechte Meinung von sich selbst; Gefühl, ein Versager zu sein oder die Familie enttäuscht zu haben",
    'F7': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Schwierigkeiten, sich auf etwas zu konzentrieren, z. B. beim Zeitunglesen oder Fernsehen",
    'F8': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Waren Ihre Bewegungen oder Ihre Sprache so verlangsamt, dass es auch anderen auffallen würde? Oder waren Sie im Gegenteil 'zappelig' oder ruhelos und hatten dadurch einen stärkeren Bewegungsdrang als sonst?",
    'F9': "Wie oft fühlten Sie sich im Verlauf der letzten 2 Wochen durch die folgenden Beschwerden beeinträchtigt? Gedanken, dass Sie lieber tot wären oder sich Leid zufügen möchten"
}

# Response options
RESPONSE_OPTIONS_EN = "0=Not at all, 1=Several days, 2=More than half, 3=Nearly every day"
RESPONSE_OPTIONS_DE = "0=Überhaupt nicht, 1=An einzelnen Tagen, 2=An mehr als der Hälfte der Tage, 3=Beinahe jeden Tag"


def get_question_text(question_id):
    """Get the full question text based on question ID"""
    if question_id.startswith('Q'):
        return PHQ9_QUESTIONS_EN.get(question_id, "")
    elif question_id.startswith('F'):
        return PHQ9_QUESTIONS_DE.get(question_id, "")
    return ""


def get_response_options(question_id):
    """Get response options based on language"""
    if question_id.startswith('Q'):
        return RESPONSE_OPTIONS_EN
    elif question_id.startswith('F'):
        return RESPONSE_OPTIONS_DE
    return ""


def test_original_prompt(question_id, transcript):
    """Test with the original prompt format used in the simulation"""
    question = get_question_text(question_id)
    options = get_response_options(question_id)
    
    prompt = f"Question: {question}\n{options}\nRespond: NUMBER|PHRASE"
    
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript}
            ],
            temperature=0,
            max_tokens=10
        )
        
        result = resp.choices[0].message.content.strip()
        tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
        
        return result, tokens
    except Exception as e:
        return f"ERROR: {str(e)}", 0


def test_prompt_a_classifier(question_id, transcript):
    """
    Prompt A — "Classifier framing"
    Your task is to classify the user response into one of the PHQ-9 options.
    If the response does not provide sufficient information, output −1.
    Respond ONLY as NUMBER|PHRASE.
    """
    question = get_question_text(question_id)
    options = get_response_options(question_id)
    
    prompt = f"""Your task is to classify the user response into one of the PHQ-9 options.
Question: {question}
Options: {options}

If the response does not provide sufficient information, output -1|INSUFFICIENT.
Respond ONLY as NUMBER|PHRASE."""
    
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript}
            ],
            temperature=0,
            max_tokens=15
        )
        
        result = resp.choices[0].message.content.strip()
        tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
        
        return result, tokens
    except Exception as e:
        return f"ERROR: {str(e)}", 0


def test_prompt_b_strict(question_id, transcript):
    """
    Prompt B — "Strict rejection"
    Classify the response ONLY if a frequency is explicitly stated or clearly inferable.
    Otherwise output −1|INSUFFICIENT.
    """
    question = get_question_text(question_id)
    options = get_response_options(question_id)
    
    prompt = f"""Classify the user response ONLY if a frequency is explicitly stated or clearly inferable.
Question: {question}
Options: {options}

If the frequency is not clearly stated or inferable, output -1|INSUFFICIENT.
Respond ONLY as NUMBER|PHRASE."""
    
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript}
            ],
            temperature=0,
            max_tokens=15
        )
        
        result = resp.choices[0].message.content.strip()
        tokens = resp.usage.total_tokens if hasattr(resp, 'usage') else None
        
        return result, tokens
    except Exception as e:
        return f"ERROR: {str(e)}", 0


def main():
    print("=" * 80)
    print("ALTERNATIVE PROMPT TEST: Testing Prompt A and Prompt B")
    print("=" * 80)
    print()
    
    # Load the 29 unique fallback cases
    input_file = TABLES_DIR / "qualitative_17_fallback_cases.csv"
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run 07_qualitative_fallback_derivation.py first.")
        return
    
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} unique fallback turns from {input_file.name}")
    print(f"  English: {len(df[df['language'] == 'EN'])}")
    print(f"  German:  {len(df[df['language'] == 'DE'])}")
    print()
    
    # Prepare results storage
    results = []
    
    print("Testing prompts on all fallback turns...")
    print("-" * 80)
    
    for idx, row in df.iterrows():
        session_id = row['session_id']
        language = row['language']
        question_id = row['question_id']
        transcript = row['transcript']
        original_output = row['gpt_output']
        
        print(f"\n[{idx+1}/{len(df)}] {session_id} | {question_id} | {language}")
        print(f"Transcript: {transcript[:80]}..." if len(transcript) > 80 else f"Transcript: {transcript}")
        print(f"Original:   {original_output}")
        
        # Test Original (for verification - should match)
        original_result, original_tokens = test_original_prompt(question_id, transcript)
        print(f"Original*:  {original_result} ({original_tokens} tokens)")
        
        # Test Prompt A - Classifier
        prompt_a_result, prompt_a_tokens = test_prompt_a_classifier(question_id, transcript)
        print(f"Prompt A:   {prompt_a_result} ({prompt_a_tokens} tokens)")
        
        # Test Prompt B - Strict
        prompt_b_result, prompt_b_tokens = test_prompt_b_strict(question_id, transcript)
        print(f"Prompt B:   {prompt_b_result} ({prompt_b_tokens} tokens)")
        
        # Store results
        results.append({
            'session_id': session_id,
            'language': language,
            'question_id': question_id,
            'transcript': transcript,
            'original_gpt_output': original_output,
            'original_retest': original_result,
            'original_tokens': original_tokens,
            'prompt_a_output': prompt_a_result,
            'prompt_a_tokens': prompt_a_tokens,
            'prompt_b_output': prompt_b_result,
            'prompt_b_tokens': prompt_b_tokens
        })
    
    # Create DataFrame and save
    results_df = pd.DataFrame(results)
    output_file = OUTPUT_DIR / "alternative_prompt_comparison.csv"
    results_df.to_csv(output_file, index=False)
    
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    # Compare outputs
    def extract_score(output):
        """Extract numeric score from output"""
        if pd.isna(output) or 'ERROR' in str(output):
            return None
        try:
            return int(str(output).split('|')[0].strip())
        except:
            return None
    
    results_df['original_score'] = results_df['original_gpt_output'].apply(extract_score)
    results_df['original_retest_score'] = results_df['original_retest'].apply(extract_score)
    results_df['prompt_a_score'] = results_df['prompt_a_output'].apply(extract_score)
    results_df['prompt_b_score'] = results_df['prompt_b_output'].apply(extract_score)
    
    # Agreement analysis
    original_match = (results_df['original_score'] == results_df['original_retest_score']).sum()
    prompt_a_match = (results_df['original_score'] == results_df['prompt_a_score']).sum()
    prompt_b_match = (results_df['original_score'] == results_df['prompt_b_score']).sum()
    
    # Count -1 (insufficient) responses
    prompt_a_insufficient = (results_df['prompt_a_score'] == -1).sum()
    prompt_b_insufficient = (results_df['prompt_b_score'] == -1).sum()
    
    print(f"\nTotal test cases: {len(results_df)}")
    print(f"\nAgreement with original GPT output:")
    print(f"  Original retest:  {original_match}/{len(results_df)} ({100*original_match/len(results_df):.1f}%)")
    print(f"  Prompt A:         {prompt_a_match}/{len(results_df)} ({100*prompt_a_match/len(results_df):.1f}%)")
    print(f"  Prompt B:         {prompt_b_match}/{len(results_df)} ({100*prompt_b_match/len(results_df):.1f}%)")
    
    print(f"\nRejection rate (output -1|INSUFFICIENT):")
    print(f"  Prompt A:         {prompt_a_insufficient}/{len(results_df)} ({100*prompt_a_insufficient/len(results_df):.1f}%)")
    print(f"  Prompt B:         {prompt_b_insufficient}/{len(results_df)} ({100*prompt_b_insufficient/len(results_df):.1f}%)")
    
    # Token usage
    total_original_tokens = results_df['original_tokens'].sum()
    total_prompt_a_tokens = results_df['prompt_a_tokens'].sum()
    total_prompt_b_tokens = results_df['prompt_b_tokens'].sum()
    
    print(f"\nTotal token usage:")
    print(f"  Original retest:  {total_original_tokens} tokens")
    print(f"  Prompt A:         {total_prompt_a_tokens} tokens")
    print(f"  Prompt B:         {total_prompt_b_tokens} tokens")
    
    print(f"\nOutput file saved to: {output_file}")
    print()
    
    return results_df


if __name__ == "__main__":
    result = main()
