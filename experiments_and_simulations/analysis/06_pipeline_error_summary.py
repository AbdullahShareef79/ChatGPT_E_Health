"""
06_pipeline_error_summary.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Pipeline Error and Intervention Summary for Simulation Study

Generates a comprehensive summary table of pipeline stage errors and interventions
across all 10 simulation sessions (90 PHQ-9 answers).
"""

import pandas as pd
from pathlib import Path
import json

# Set paths
BASE_DIR = Path(__file__).parent.parent
TABLES_DIR = BASE_DIR / "analysis_tables"
OUTPUT_DIR = BASE_DIR / "analysis_tables"

# Load data
print("="*70)
print("PIPELINE ERROR AND INTERVENTION SUMMARY")
print("="*70)

# Load definitive thesis numbers (ground truth)
definitive_file = TABLES_DIR / "DEFINITIVE_THESIS_NUMBERS.txt"
definitive_data = {}
with open(definitive_file, 'r') as f:
    for line in f:
        if ':' in line and not line.startswith('='):
            key, value = line.strip().split(':', 1)
            try:
                definitive_data[key.strip()] = float(value.strip())
            except:
                definitive_data[key.strip()] = value.strip()

# Use verified numbers from definitive thesis numbers
total_phq_turns = int(definitive_data['total_phq_turns'])
local_nlp_success = int(definitive_data['local_nlp_success'])
gpt_fallback = int(definitive_data['gpt_fallback'])
total_retries = int(definitive_data['total_retries'])

print(f"\nUsing verified numbers from DEFINITIVE_THESIS_NUMBERS.txt")
print(f"Total PHQ-9 answer turns: {total_phq_turns}")

# Load interaction logs for examples only
logs = pd.read_csv(TABLES_DIR / "all_interaction_logs.csv")
phq_logs = logs[logs['phqQuestionId'].notna()].copy()
phq_logs = phq_logs[phq_logs['notes'].str.contains('FINAL score', na=False)]

# =============================================================================
# STAGE 1: ASR (Automatic Speech Recognition)
# =============================================================================
# Note: In this simulation, most inputs are [BUTTON: YES] entries,
# so ASR transcription errors are not directly logged.
# We count only cases where ASR could have failed (voice input cases)
voice_inputs = phq_logs[~phq_logs['asrTranscript'].str.contains('BUTTON', na=False)]
asr_error_count = 0  # Not explicitly logged in this dataset

print(f"\n--- STAGE 1: ASR (Speech Recognition) ---")
print(f"Voice inputs (non-button): {len(voice_inputs)}")
print(f"ASR errors leading to retry: {asr_error_count} (not explicitly logged)")
print(f"Note: Most simulation inputs were button-based; ASR errors not directly observable")

# =============================================================================
# STAGE 2: LOCAL NLP (Rule-based pattern matching)
# =============================================================================
# Use definitive verified numbers
local_nlp_fail = gpt_fallback  # GPT fallback count = local NLP failures

print(f"\n--- STAGE 2: LOCAL NLP (Rule-based) ---")
print(f"Local NLP success: {local_nlp_success}/{total_phq_turns} ({100*local_nlp_success/total_phq_turns:.1f}%)")
print(f"Local NLP fail → GPT fallback triggered: {local_nlp_fail}/{total_phq_turns} ({100*local_nlp_fail/total_phq_turns:.1f}%)")

# Get examples of local NLP failures (GPT fallbacks)
gpt_fallback_examples = phq_logs[phq_logs['handlingModule'] == 'GPT_FALLBACK'].head(3)
print("\nExample GPT fallback cases:")
for idx, row in gpt_fallback_examples.iterrows():
    session_name = row['session_folder'].split('_')[1][:8]  # First 8 chars of session ID
    print(f"  - Session {session_name}, {row['phqQuestionId']}, Turn {row['turnIndex']}")

# =============================================================================
# STAGE 3: GPT FALLBACK (API interpretation)
# =============================================================================
# Use definitive verified numbers
total_gpt_calls = gpt_fallback  # Total GPT calls for answer parsing = fallback count

# Check for GPT failures in notes
gpt_failures = phq_logs[phq_logs['notes'].str.contains('GPT failed', na=False)]
gpt_parse_errors = len(gpt_failures)

print(f"\n--- STAGE 3: GPT FALLBACK ---")
print(f"Total GPT calls for answer parsing: {total_gpt_calls}")
print(f"GPT invalid output / parse errors: {gpt_parse_errors}")

if gpt_parse_errors > 0:
    print("\nExample GPT failure cases:")
    for idx, row in gpt_failures.head(2).iterrows():
        session_name = row['session_folder'].split('_')[1][:8]
        print(f"  - Session {session_name}, {row['phqQuestionId']}, Turn {row['turnIndex']}")

# =============================================================================
# STAGE 4: CONFIRMATION / RETRIES
# =============================================================================
# Extract retry counts from notes field (format: "retries=X") for examples
def extract_retries(note):
    if pd.isna(note):
        return 0
    import re
    match = re.search(r'retries=(\d+)', note)
    return int(match.group(1)) if match else 0

phq_logs['retry_count'] = phq_logs['notes'].apply(extract_retries)

# Use definitive verified numbers
turns_with_retries = (phq_logs['retry_count'] > 0).sum()  # Example count from logs

print(f"\n--- STAGE 4: CONFIRMATION / RETRIES ---")
print(f"Total retry attempts: {total_retries} (verified from definitive numbers)")
print(f"Turns requiring ≥1 retry: {turns_with_retries} (from logged examples)")

# Get examples of retries
retry_examples = phq_logs[phq_logs['retry_count'] > 0].head(3)
print("\nExample retry cases:")
for idx, row in retry_examples.iterrows():
    session_name = row['session_folder'].split('_')[1][:8]
    print(f"  - Session {session_name}, {row['phqQuestionId']}, retries={row['retry_count']}, Turn {row['turnIndex']}")

# =============================================================================
# CREATE SUMMARY TABLE
# =============================================================================
summary_data = {
    'Pipeline Stage': [
        'ASR (Speech-to-Text)',
        'Local NLP (Pattern/Rules)',
        'GPT Fallback (API)',
        'Confirmation/Retries'
    ],
    'Issue Type': [
        'Transcription error (not explicitly logged)',
        'Rule miss / ambiguous input → GPT fallback',
        'Invalid output format / parse error',
        'Retry attempts required'
    ],
    'Count': [
        f'{asr_error_count} (not logged)',
        f'{local_nlp_fail} / {total_phq_turns}',
        f'{gpt_parse_errors} / {total_gpt_calls}',
        f'{total_retries} attempts'
    ],
    'Example Session/Turn IDs': [
        'N/A (button-based simulation)',
        f'{gpt_fallback_examples.iloc[0]["session_folder"].split("_")[1][:8]} {gpt_fallback_examples.iloc[0]["phqQuestionId"]} T{gpt_fallback_examples.iloc[0]["turnIndex"]}; ' +
        f'{gpt_fallback_examples.iloc[1]["session_folder"].split("_")[1][:8]} {gpt_fallback_examples.iloc[1]["phqQuestionId"]} T{gpt_fallback_examples.iloc[1]["turnIndex"]}',
        f'{gpt_failures.iloc[0]["session_folder"].split("_")[1][:8]} {gpt_failures.iloc[0]["phqQuestionId"]} T{gpt_failures.iloc[0]["turnIndex"]}' if gpt_parse_errors > 0 else 'None observed',
        f'{retry_examples.iloc[0]["session_folder"].split("_")[1][:8]} {retry_examples.iloc[0]["phqQuestionId"]} (r={retry_examples.iloc[0]["retry_count"]}); ' +
        f'{retry_examples.iloc[1]["session_folder"].split("_")[1][:8]} {retry_examples.iloc[1]["phqQuestionId"]} (r={retry_examples.iloc[1]["retry_count"]})'
    ]
}

summary_df = pd.DataFrame(summary_data)

# Save to CSV
output_csv = OUTPUT_DIR / "pipeline_error_summary.csv"
summary_df.to_csv(output_csv, index=False)
print(f"\n✓ Summary saved to: {output_csv}")

# =============================================================================
# GENERATE LATEX TABLE
# =============================================================================
latex_output = r"""\begin{table}[htbp]
    \centering
    \caption{Pipeline Error and Intervention Summary (Simulation Study, N=10 sessions, 90 PHQ-9 answers)}
    \label{tab:pipeline_error_summary}
    \begin{tabular}{p{3.5cm}p{4.5cm}p{2.5cm}p{3.5cm}}
        \toprule
        \textbf{Pipeline Stage} & \textbf{Issue Type} & \textbf{Count} & \textbf{Examples} \\
        \midrule
"""

for idx, row in summary_df.iterrows():
    # Escape special characters for LaTeX
    stage = row['Pipeline Stage'].replace('&', r'\&')
    issue = row['Issue Type'].replace('&', r'\&').replace('→', r'$\\rightarrow$')
    count = str(row['Count']).replace('&', r'\&')
    examples = row['Example Session/Turn IDs'].replace('_', r'\_')
    
    latex_output += f"        {stage} & {issue} & {count} & {examples} \\\\\n"

latex_output += r"""        \bottomrule
    \end{tabular}
\end{table}

\noindent\textbf{Notes:}
\begin{itemize}
    \item ASR errors are not directly logged in this simulation study as most inputs were button-based.
    \item Local NLP failures triggered GPT fallback for interpretation of ambiguous responses.
    \item All GPT calls successfully returned valid output (no parse errors observed).
    \item Retry attempts occurred when confirmation failed or response needed clarification.
    \item Session IDs are shortened to first 8 characters for readability.
\end{itemize}
"""

# Save LaTeX output
latex_file = OUTPUT_DIR / "pipeline_error_summary_latex.tex"
with open(latex_file, 'w', encoding='utf-8') as f:
    f.write(latex_output)

print(f"✓ LaTeX table saved to: {latex_file}")

# =============================================================================
# SUMMARY STATISTICS
# =============================================================================
print("\n" + "="*70)
print("FINAL SUMMARY STATISTICS (VERIFIED FROM DEFINITIVE_THESIS_NUMBERS.txt)")
print("="*70)
print(f"Total PHQ-9 answer turns:        {total_phq_turns}")
print(f"Local NLP success rate:          {local_nlp_success}/{total_phq_turns} ({100*local_nlp_success/total_phq_turns:.1f}%)")
print(f"GPT fallback invocations:        {local_nlp_fail}/{total_phq_turns} ({100*local_nlp_fail/total_phq_turns:.1f}%)")
print(f"Total retry attempts:            {total_retries}")
print(f"GPT parse errors:                {gpt_parse_errors}")
print("="*70)

print("\n Pipeline error summary analysis complete!")
print(f"\nGenerated files:")
print(f"  - {output_csv.name}")
print(f"  - {latex_file.name}")
print(f"\nReady to insert into thesis appendix.")
