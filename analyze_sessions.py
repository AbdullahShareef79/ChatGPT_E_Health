"""
PHQ-9 Simulation Session Analysis
Analyzes session data from simulation experiments
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import statistics

def load_session_data(session_path):
    """Load session data from a folder"""
    session_data = {}
    
    # Load main session JSON
    json_file = session_path / "session_data.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    
    # Load interaction logs CSV
    csv_file = session_path / "interaction_logs.csv"
    if csv_file.exists():
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            session_data['interaction_logs'] = list(reader)
    
    # Load GPT logs if available
    gpt_json = session_path / "gpt_api_calls.json"
    if gpt_json.exists():
        with open(gpt_json, 'r', encoding='utf-8') as f:
            session_data['gpt_calls'] = json.load(f)
    
    return session_data

def analyze_single_session(session_data, session_name):
    """Analyze a single session"""
    print(f"\n{'='*70}")
    print(f"SESSION: {session_name}")
    print(f"{'='*70}")
    
    # Basic info
    if 'session_id' in session_data:
        lang = session_data.get('language', 'UNKNOWN')
        print(f"\nSession ID: {session_data['session_id']}")
        print(f"Language: {lang}")
        print(f"Start: {session_data.get('start_time', 'N/A')}")
        print(f"End: {session_data.get('end_time', 'N/A')}")
        print(f"Duration: {session_data.get('duration_seconds', 0):.1f} seconds")
    
    # PHQ-9 Results
    if 'phq9_responses' in session_data:
        responses = session_data['phq9_responses']
        total = session_data.get('total_score', sum(responses))
        severity = session_data.get('severity', 'unknown')
        
        print(f"\nPHQ-9 RESULTS:")
        print(f"  Responses (Q1-Q9): {responses}")
        print(f"  Total Score: {total}/27")
        print(f"  Severity: {severity.upper()}")
        
        # Score distribution
        print(f"\nScore Distribution:")
        for score in range(4):
            count = responses.count(score)
            print(f"  Score {score}: {count} questions ({count/9*100:.1f}%)")
    
    # GPT Usage
    if 'gpt_calls' in session_data:
        gpt_calls = session_data['gpt_calls']
        print(f"\nGPT USAGE:")
        print(f"  Total GPT calls: {len(gpt_calls)}")
        
        # Count by purpose
        purposes = {}
        total_tokens = 0
        for call in gpt_calls:
            purpose = call.get('purpose', 'unknown')
            purposes[purpose] = purposes.get(purpose, 0) + 1
            total_tokens += call.get('tokens_used', 0)
        
        print(f"  Calls by purpose:")
        for purpose, count in purposes.items():
            print(f"    - {purpose}: {count}")
        
        print(f"  Total tokens used: {total_tokens}")
    elif 'total_gpt_calls' in session_data:
        print(f"\nGPT USAGE:")
        print(f"  Total GPT calls: {session_data['total_gpt_calls']}")
    
    # Interaction logs analysis
    if 'interaction_logs' in session_data:
        logs = session_data['interaction_logs']
        print(f"\nINTERACTION METRICS:")
        print(f"  Total turns: {len(logs)}")
        
        # Language detection
        if logs and 'languageDetected' in logs[0]:
            langs = [row['languageDetected'] for row in logs if row.get('languageDetected')]
            lang_counts = {}
            for lang in langs:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            print(f"  Languages detected: {lang_counts}")
        
        # GPT usage from logs
        if logs and 'gptUsed' in logs[0]:
            gpt_used_count = sum(1 for row in logs if row.get('gptUsed', '').lower() in ['true', '1', 'yes'])
            print(f"  Turns using GPT: {gpt_used_count}")
    
    # Transcript length
    if 'transcript' in session_data:
        print(f"\nTRANSCRIPT:")
        print(f"  Total exchanges: {len(session_data['transcript'])}")
    
    return {
        'session_name': session_name,
        'language': session_data.get('language', 'UNKNOWN'),
        'total_score': session_data.get('total_score', None),
        'severity': session_data.get('severity', None),
        'duration': session_data.get('duration_seconds', None),
        'gpt_calls': len(session_data.get('gpt_calls', [])),
        'responses': session_data.get('phq9_responses', [])
    }

def compare_sessions(sessions_stats):
    """Compare multiple sessions"""
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    
    print(f"\nTotal sessions analyzed: {len(sessions_stats)}")
    
    # Group by language
    en_sessions = [s for s in sessions_stats if s.get('language') == 'EN']
    de_sessions = [s for s in sessions_stats if s.get('language') == 'DE']
    
    if en_sessions or de_sessions:
        print(f"  - English sessions: {len(en_sessions)}")
        print(f"  - German sessions: {len(de_sessions)}")
    
    # Aggregate statistics
    if sessions_stats:
        scores = [s['total_score'] for s in sessions_stats if s['total_score'] is not None]
        durations = [s['duration'] for s in sessions_stats if s['duration'] is not None]
        gpt_calls = [s['gpt_calls'] for s in sessions_stats if s['gpt_calls'] is not None]
        
        if scores:
            print(f"\nTOTAL SCORES (All Sessions):")
            print(f"  Mean: {statistics.mean(scores):.1f}")
            print(f"  Median: {statistics.median(scores):.1f}")
            print(f"  Range: {min(scores)}-{max(scores)}")
            print(f"  St.Dev: {statistics.stdev(scores):.2f}" if len(scores) > 1 else "  St.Dev: N/A")
        
        # Language-specific scores
        if en_sessions:
            en_scores = [s['total_score'] for s in en_sessions if s['total_score'] is not None]
            if en_scores:
                print(f"\nENGLISH SESSIONS:")
                print(f"  Mean score: {statistics.mean(en_scores):.1f}")
                print(f"  Mean GPT calls: {statistics.mean([s['gpt_calls'] for s in en_sessions]):.1f}")
        
        if de_sessions:
            de_scores = [s['total_score'] for s in de_sessions if s['total_score'] is not None]
            if de_scores:
                print(f"\nGERMAN SESSIONS:")
                print(f"  Mean score: {statistics.mean(de_scores):.1f}")
                print(f"  Mean GPT calls: {statistics.mean([s['gpt_calls'] for s in de_sessions]):.1f}")
        
        if durations:
            print(f"\nDURATIONS:")
            print(f"  Mean: {statistics.mean(durations):.1f} seconds ({statistics.mean(durations)/60:.1f} minutes)")
            print(f"  Range: {min(durations):.1f}-{max(durations):.1f} seconds")
        
        if gpt_calls:
            print(f"\nGPT USAGE:")
            print(f"  Mean calls per session: {statistics.mean(gpt_calls):.1f}")
            print(f"  Total calls: {sum(gpt_calls)}")
            print(f"  Range: {min(gpt_calls)}-{max(gpt_calls)}")
        
        # Severity distribution
        severities = [s['severity'] for s in sessions_stats if s['severity']]
        if severities:
            print(f"\nSEVERITY DISTRIBUTION:")
            from collections import Counter
            sev_counts = Counter(severities)
            for sev, count in sev_counts.items():
                print(f"  {sev.capitalize()}: {count} ({count/len(severities)*100:.1f}%)")
        
        # Per-question score analysis
        all_responses = [s['responses'] for s in sessions_stats if s['responses']]
        if all_responses and all(len(r) == 9 for r in all_responses):
            print(f"\nPER-QUESTION ANALYSIS:")
            for q_idx in range(9):
                q_scores = [r[q_idx] for r in all_responses]
                print(f"  Q{q_idx+1}: Mean={statistics.mean(q_scores):.2f}, "
                      f"Range={min(q_scores)}-{max(q_scores)}")

def main():
    """Main analysis function"""
    print("="*70)
    print("PHQ-9 SIMULATION SESSION ANALYSIS")
    print("="*70)
    
    # Find all session folders in both language directories
    sessions_dir = Path("data/sessions")
    if not sessions_dir.exists():
        print("ERROR: data/sessions directory not found!")
        return
    
    session_folders = []
    
    # Check for language-specific folders
    english_dir = sessions_dir / "english"
    german_dir = sessions_dir / "german"
    
    if english_dir.exists():
        session_folders.extend([d for d in english_dir.iterdir() if d.is_dir()])
    
    if german_dir.exists():
        session_folders.extend([d for d in german_dir.iterdir() if d.is_dir()])
    
    # Also check root sessions folder for backward compatibility
    root_sessions = [d for d in sessions_dir.iterdir() if d.is_dir() and d.name not in ['english', 'german']]
    session_folders.extend(root_sessions)
    
    if not session_folders:
        print("No session data found!")
        print(f"Checked:")
        print(f"  - {english_dir}")
        print(f"  - {german_dir}")
        print(f"  - {sessions_dir}")
        return
    
    print(f"\nFound {len(session_folders)} session(s)")
    
    # Analyze each session
    sessions_stats = []
    for session_folder in sorted(session_folders):
        try:
            session_data = load_session_data(session_folder)
            # Determine language from folder path if not in data
            if 'language' not in session_data:
                if 'english' in str(session_folder):
                    session_data['language'] = 'EN'
                elif 'german' in str(session_folder):
                    session_data['language'] = 'DE'
            stats = analyze_single_session(session_data, session_folder.name)
            sessions_stats.append(stats)
        except Exception as e:
            print(f"\nERROR analyzing {session_folder.name}: {e}")
    
    # Compare all sessions
    if len(sessions_stats) > 1:
        compare_sessions(sessions_stats)
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

