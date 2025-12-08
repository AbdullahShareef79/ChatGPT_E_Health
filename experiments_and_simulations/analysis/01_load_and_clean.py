"""
01_load_and_clean.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Load and clean all session data into a master dataset
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np

def load_all_sessions(sessions_root):
    """
    Load all session_data.json files from the sessions directory structure.
    
    Returns:
        DataFrame with all session metadata
    """
    sessions_data = []
    
    # Check both language-specific folders and root sessions folder
    search_paths = [
        sessions_root / "english",
        sessions_root / "german",
        sessions_root  # Root level sessions
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        # Find all session folders
        for session_folder in search_path.iterdir():
            if not session_folder.is_dir():
                continue
            
            session_json = session_folder / "session_data.json"
            
            if not session_json.exists():
                print(f"⚠️  Skipping {session_folder.name} - no session_data.json")
                continue
            
            try:
                with open(session_json, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Extract key information
                session_info = {
                    'session_id': session_data.get('session_id', session_folder.name),
                    'session_folder': session_folder.name,
                    'language': session_data.get('language', 'UNKNOWN'),
                    'participant_id': session_data.get('participant_info', {}).get('id', 'N/A'),
                    'proficiency': session_data.get('participant_info', {}).get('proficiency', 'N/A'),
                    'start_time': session_data.get('start_time', ''),
                    'end_time': session_data.get('end_time', ''),
                    'duration_seconds': session_data.get('duration_seconds', 0),
                    'total_score': session_data.get('total_score', 0),
                    'severity': session_data.get('severity', 'unknown'),
                    'total_gpt_calls': session_data.get('total_gpt_calls', 0),
                }
                
                # Add individual PHQ-9 scores
                phq9_responses = session_data.get('phq9_responses', [])
                for i, score in enumerate(phq9_responses, 1):
                    session_info[f'Q{i}_score'] = score
                
                # Add retry counts
                retry_counts = session_data.get('retry_counts', {})
                total_retries = 0
                for i in range(9):
                    retry_val = retry_counts.get(str(i), 0)
                    session_info[f'Q{i+1}_retries'] = retry_val
                    total_retries += retry_val
                
                session_info['total_retries'] = total_retries
                
                sessions_data.append(session_info)
                print(f"✓ Loaded {session_folder.name} ({session_info['language']})")
                
            except Exception as e:
                print(f"❌ Error loading {session_folder.name}: {e}")
                continue
    
    df = pd.DataFrame(sessions_data)
    return df


def load_interaction_logs(sessions_root):
    """
    Load all interaction_logs.csv files and combine them.
    
    Returns:
        DataFrame with all interaction turns
    """
    all_logs = []
    
    search_paths = [
        sessions_root / "english",
        sessions_root / "german",
        sessions_root
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        for session_folder in search_path.iterdir():
            if not session_folder.is_dir():
                continue
            
            csv_file = session_folder / "interaction_logs.csv"
            
            if not csv_file.exists():
                continue
            
            try:
                df_log = pd.read_csv(csv_file)
                df_log['session_folder'] = session_folder.name
                all_logs.append(df_log)
                
            except Exception as e:
                print(f"❌ Error loading CSV from {session_folder.name}: {e}")
                continue
    
    if all_logs:
        return pd.concat(all_logs, ignore_index=True)
    else:
        return pd.DataFrame()


def load_gpt_calls(sessions_root):
    """
    Load all gpt_api_calls.json files and combine them.
    
    Returns:
        DataFrame with all GPT API calls
    """
    all_gpt_calls = []
    
    search_paths = [
        sessions_root / "english",
        sessions_root / "german",
        sessions_root
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        for session_folder in search_path.iterdir():
            if not session_folder.is_dir():
                continue
            
            gpt_file = session_folder / "gpt_api_calls.json"
            
            if not gpt_file.exists():
                continue
            
            try:
                with open(gpt_file, 'r', encoding='utf-8') as f:
                    gpt_data = json.load(f)
                
                for call in gpt_data:
                    call['session_folder'] = session_folder.name
                    all_gpt_calls.append(call)
                    
            except Exception as e:
                print(f"❌ Error loading GPT calls from {session_folder.name}: {e}")
                continue
    
    if all_gpt_calls:
        return pd.DataFrame(all_gpt_calls)
    else:
        return pd.DataFrame()


def main():
    """Main execution"""
    print("="*80)
    print("PHQ-9 VOICE SCREENING - DATA LOADING AND CLEANING")
    print("="*80)
    print()
    
    # Set paths
    base_path = Path(__file__).parent.parent
    sessions_root = base_path / "data" / "sessions"
    output_dir = base_path / "results" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load session metadata
    print("📁 Loading session metadata...")
    df_sessions = load_all_sessions(sessions_root)
    print(f"\n✓ Loaded {len(df_sessions)} sessions")
    print(f"  • English: {len(df_sessions[df_sessions['language']=='EN'])}")
    print(f"  • German: {len(df_sessions[df_sessions['language']=='DE'])}")
    print(f"  • Other/Unknown: {len(df_sessions[~df_sessions['language'].isin(['EN', 'DE'])])}")
    
    # Load interaction logs
    print("\n📊 Loading interaction logs...")
    df_interactions = load_interaction_logs(sessions_root)
    if not df_interactions.empty:
        print(f"✓ Loaded {len(df_interactions)} interaction turns")
        print(f"  • GPT used: {df_interactions['gptUsed'].sum() if 'gptUsed' in df_interactions else 'N/A'}")
        print(f"  • Local NLP success: {df_interactions['pepperLocalNlpSuccess'].sum() if 'pepperLocalNlpSuccess' in df_interactions else 'N/A'}")
    
    # Load GPT calls
    print("\n🤖 Loading GPT API calls...")
    df_gpt = load_gpt_calls(sessions_root)
    if not df_gpt.empty:
        print(f"✓ Loaded {len(df_gpt)} GPT API calls")
        if 'tokens_used' in df_gpt.columns:
            total_tokens = df_gpt['tokens_used'].sum()
            print(f"  • Total tokens: {total_tokens:,}")
    
    # Save master datasets
    print("\n💾 Saving cleaned datasets...")
    
    # Master sessions table
    sessions_file = output_dir / "simulation_master.csv"
    df_sessions.to_csv(sessions_file, index=False)
    print(f"  ✓ {sessions_file}")
    
    # Interaction logs
    if not df_interactions.empty:
        interactions_file = output_dir / "all_interaction_logs.csv"
        df_interactions.to_csv(interactions_file, index=False)
        print(f"  ✓ {interactions_file}")
    
    # GPT calls
    if not df_gpt.empty:
        gpt_file = output_dir / "all_gpt_calls.csv"
        df_gpt.to_csv(gpt_file, index=False)
        print(f"  ✓ {gpt_file}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\n📈 Session Overview:")
    print(df_sessions[['language', 'duration_seconds', 'total_score', 'severity', 
                       'total_gpt_calls', 'total_retries']].describe())
    
    print("\n📊 By Language:")
    summary = df_sessions.groupby('language').agg({
        'duration_seconds': ['mean', 'std'],
        'total_score': ['mean', 'std'],
        'total_gpt_calls': ['mean', 'std'],
        'total_retries': ['mean', 'std']
    }).round(2)
    print(summary)
    
    print("\n✅ Data loading and cleaning complete!")
    print(f"   Master dataset saved to: {sessions_file}")


if __name__ == "__main__":
    main()

