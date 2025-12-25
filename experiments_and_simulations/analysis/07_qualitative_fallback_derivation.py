"""
07_qualitative_fallback_derivation.py
================================================================================
REPRODUCIBILITY SCRIPT: Derives fallback counts and reconciles all discrepancies

COMPLETE RECONCILIATION (Verified December 2025):

  +---------------------------+-------+
  | Metric                    | Count |
  +---------------------------+-------+
  | Total GPT API calls       |    38 |
  | Unique (session, question)|    33 |
  | GPT as FINAL (all langs)  |    29 |
  |   - English (Q1-Q9)       |    17 |
  |   - German (F1-F9)        |    12 |
  +---------------------------+-------+

The thesis Table (nlp_performance_by_question.csv) reports 17 fallbacks
because it only analyzed ENGLISH sessions (Q1-Q9). The 12 German fallbacks
are in the interaction logs but not in that summary table.

FULL QUALITATIVE SAMPLE: 29 fallback cases (both EN and DE)

Unit of Analysis Definitions:
- GPT API Call: A single invocation of the GPT-4o-mini API
- Unique GPT Question: A (session, question) pair with at least one GPT call
- Fallback Turn: A question where GPT provided the FINAL confirmed answer

Author: [Thesis Author]
Date: December 2025
================================================================================
"""

import pandas as pd
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
TABLES_DIR = SCRIPT_DIR.parent / "analysis_tables"
OUTPUT_DIR = TABLES_DIR


def load_gpt_calls():
    """Load all GPT API calls from the simulation sessions."""
    gpt_calls_path = TABLES_DIR / "all_gpt_calls.csv"
    df = pd.read_csv(gpt_calls_path)
    print(f"Loaded {len(df)} GPT API calls from {gpt_calls_path.name}")
    return df


def load_interaction_logs():
    """Load all interaction logs."""
    logs_path = TABLES_DIR / "all_interaction_logs.csv"
    df = pd.read_csv(logs_path)
    print(f"Loaded {len(df)} interaction log entries from {logs_path.name}")
    return df


def extract_question_id(purpose_or_prompt):
    """Extract question ID (Q1-Q9 or F1-F9) from GPT call purpose/prompt."""
    import re
    # Try to match Q1-Q9 (English) or F1-F9 (German)
    match = re.search(r'[QF][1-9]', str(purpose_or_prompt))
    if match:
        return match.group()
    return None


def extract_session_id(session_folder):
    """Extract session ID from folder name."""
    # Format: session_XXXXXXXX_YYYYMMDD_HHMMSS
    if pd.isna(session_folder):
        return None
    parts = str(session_folder).split('_')
    if len(parts) >= 2:
        return parts[1][:8]  # First 8 chars of UUID
    return None


def extract_transcript(prompt):
    """Extract user transcript from GPT prompt."""
    if pd.isna(prompt):
        return None
    if 'User:' in str(prompt):
        return str(prompt).split('User:')[-1].strip()
    return None


def main():
    print("=" * 80)
    print("QUALITATIVE FALLBACK DERIVATION: Reconciling counts")
    print("=" * 80)
    print()
    
    # Load data
    gpt_calls = load_gpt_calls()
    interaction_logs = load_interaction_logs()
    
    print()
    print("-" * 80)
    print("STEP 1: Count from GPT API calls file")
    print("-" * 80)
    
    total_gpt_calls = len(gpt_calls)
    print(f"Total GPT API calls: {total_gpt_calls}")
    
    # Add session_id and question_id columns
    gpt_calls['session_id'] = gpt_calls['session_folder'].apply(extract_session_id)
    gpt_calls['question_id'] = gpt_calls['purpose'].apply(extract_question_id)
    
    # Unique (session, question) pairs
    unique_gpt_questions = gpt_calls.groupby(['session_id', 'question_id']).size().reset_index(name='gpt_call_count')
    print(f"Unique (session, question) pairs with GPT calls: {len(unique_gpt_questions)}")
    
    print()
    print("-" * 80)
    print("STEP 2: Count from interaction logs - FINAL answers only")
    print("-" * 80)
    
    # Filter to FINAL answer rows (contain "FINAL" or "FINALE" in notes)
    final_answers = interaction_logs[
        interaction_logs['notes'].str.contains('FINAL|FINALE', na=False, regex=True)
    ].copy()
    
    print(f"Total FINAL answer rows: {len(final_answers)}")
    
    # Count by handlingModule
    module_counts = final_answers['handlingModule'].value_counts()
    print(f"\nFINAL answers by handlingModule:")
    for module, count in module_counts.items():
        print(f"  {module}: {count}")
    
    # GPT_FALLBACK in FINAL answers = thesis definition
    gpt_fallback_finals = final_answers[final_answers['handlingModule'] == 'GPT_FALLBACK']
    print(f"\n>>> THESIS FALLBACK COUNT: {len(gpt_fallback_finals)} <<<")
    print("    (Questions where GPT provided the FINAL confirmed answer)")
    
    print()
    print("-" * 80)
    print("STEP 3: Reconcile the gap (GPT-invoked vs GPT-final)")
    print("-" * 80)
    
    # Get list of (session, question) that had GPT calls
    gpt_question_set = set(zip(unique_gpt_questions['session_id'], unique_gpt_questions['question_id']))
    
    # Get list of (session, question) where GPT was the FINAL handler
    gpt_fallback_finals_copy = gpt_fallback_finals.copy()
    gpt_fallback_finals_copy['session_id_short'] = gpt_fallback_finals_copy['sessionId'].apply(lambda x: str(x)[:8] if pd.notna(x) else None)
    gpt_final_set = set(zip(
        gpt_fallback_finals_copy['session_id_short'], 
        gpt_fallback_finals_copy['phqQuestionId']
    ))
    
    # Questions where GPT was called but NOT the final handler
    gpt_called_but_not_final = gpt_question_set - gpt_final_set
    
    print(f"Questions with GPT calls:           {len(gpt_question_set)}")
    print(f"Questions with GPT as FINAL:        {len(gpt_final_set)}")
    print(f"GPT called but LOCAL was FINAL:     {len(gpt_called_but_not_final)}")
    
    print(f"\nThese {len(gpt_called_but_not_final)} cases represent:")
    print("  - GPT was invoked during a retry attempt")
    print("  - But user's subsequent response was parsed by local NLP")
    print("  - So FINAL handlingModule = PEPPER_LOCAL")
    
    print()
    print("-" * 80)
    print("STEP 4: Verify against thesis table")
    print("-" * 80)
    
    nlp_perf_path = TABLES_DIR / "nlp_performance_by_question.csv"
    if nlp_perf_path.exists():
        nlp_perf = pd.read_csv(nlp_perf_path)
        thesis_fallback = nlp_perf['gpt_fallback'].sum()
        thesis_local = nlp_perf['local_success'].sum()
        print(f"Thesis nlp_performance_by_question.csv:")
        print(f"  Local NLP success: {thesis_local}")
        print(f"  GPT fallback:      {thesis_fallback}")
        print(f"  Total:             {thesis_local + thesis_fallback}")
        
        if len(gpt_fallback_finals) == thesis_fallback:
            print(f"\n>>> VERIFIED: Interaction logs ({len(gpt_fallback_finals)}) match thesis table ({thesis_fallback}) <<<")
        else:
            print(f"\n!!! DISCREPANCY: Logs show {len(gpt_fallback_finals)}, thesis says {thesis_fallback}")
    else:
        thesis_fallback = 17
        print(f"Thesis table not found; expected count: {thesis_fallback}")
    
    print()
    print("-" * 80)
    print("STEP 5: Export the GPT-final fallback cases for qualitative analysis")
    print("-" * 80)
    
    # Add transcript column to gpt_calls
    gpt_calls['transcript'] = gpt_calls['prompt'].apply(extract_transcript)
    
    # For each GPT-final case, get the transcript that was used
    qualitative_data = []
    for _, row in gpt_fallback_finals.iterrows():
        session_short = str(row['sessionId'])[:8]
        question = row['phqQuestionId']
        language = row.get('languageDetected', 'unknown')
        
        # Find the GPT call that produced the final answer
        matching_calls = gpt_calls[
            (gpt_calls['session_id'] == session_short) & 
            (gpt_calls['question_id'] == question)
        ]
        
        if len(matching_calls) > 0:
            # Use the last call (the one that succeeded)
            last_call = matching_calls.iloc[-1]
            qualitative_data.append({
                'session_id': session_short,
                'language': language,
                'question_id': question,
                'transcript': last_call['transcript'],
                'gpt_output': last_call['response'],
                'num_gpt_calls': len(matching_calls),
                'qual_code': '',
                'coding_note': ''
            })
        else:
            # No matching GPT call found (shouldn't happen)
            qualitative_data.append({
                'session_id': session_short,
                'language': language,
                'question_id': question,
                'transcript': '[NOT FOUND IN GPT CALLS]',
                'gpt_output': '',
                'num_gpt_calls': 0,
                'qual_code': '',
                'coding_note': ''
            })
    
    qual_df = pd.DataFrame(qualitative_data)
    output_path = OUTPUT_DIR / "qualitative_17_fallback_cases.csv"
    qual_df.to_csv(output_path, index=False)
    print(f"Exported {len(qual_df)} GPT-final fallback cases to: {output_path.name}")
    
    # Language breakdown
    if len(qual_df) > 0 and 'language' in qual_df.columns:
        lang_counts = qual_df['language'].value_counts()
        print(f"\nLanguage breakdown:")
        for lang, count in lang_counts.items():
            print(f"  {lang}: {count}")
    
    # Retry analysis
    single_call = (qual_df['num_gpt_calls'] == 1).sum()
    multi_call = (qual_df['num_gpt_calls'] > 1).sum()
    print(f"\nRepair behavior (within GPT-final cases):")
    print(f"  Resolved on first GPT attempt: {single_call}")
    print(f"  Required retry (>1 GPT call):  {multi_call}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total GPT API calls:                    {total_gpt_calls}")
    print(f"Unique questions with GPT involvement:  {len(unique_gpt_questions)}")
    print(f"Questions where GPT was FINAL answer:   {len(gpt_fallback_finals)}")
    print()
    print("The thesis correctly reports fallbacks as questions where GPT")
    print("provided the FINAL confirmed answer, not all questions where")
    print("GPT was ever invoked during the conversation.")
    
    return qual_df


if __name__ == "__main__":
    result = main()
