import os
import csv
import json
from pathlib import Path
from datetime import datetime
import shutil

def repair_session(session_path):
    """Repair CSV logs using data from GPT JSON logs"""
    csv_path = session_path / "interaction_logs.csv"
    json_path = session_path / "gpt_api_calls.json"
    
    if not csv_path.exists() or not json_path.exists():
        return False
    
    print(f"Processing {session_path.name}...")
    
    # Load GPT calls
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            gpt_calls = json.load(f)
    except Exception as e:
        print(f"  Error loading JSON: {e}")
        return False
        
    # Index GPT calls by timestamp (approximate matching)
    # Convert ISO to millis
    gpt_by_time = []
    for call in gpt_calls:
        try:
            dt = datetime.fromisoformat(call['timestamp'])
            ts_millis = int(dt.timestamp() * 1000)
            gpt_by_time.append((ts_millis, call))
        except:
            pass
            
    # Read CSV
    rows = []
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
    except Exception as e:
        print(f"  Error loading CSV: {e}")
        return False
    
    updated_count = 0
    
    for row in rows:
        # Skip if already has GPT info
        if row.get('gptUsed') == 'True':
            continue
            
        # Check if we have a GPT call matching this timestamp
        try:
            row_ts = int(row['timestamp'])
        except:
            continue
            
        # Find match within 500ms
        match = None
        for gpt_ts, call in gpt_by_time:
            if abs(gpt_ts - row_ts) < 500:
                match = call
                break
        
        if match:
            # Update row
            row['gptUsed'] = 'True'
            row['gptReason'] = match.get('purpose', '')
            row['gptModel'] = match.get('model', '')
            row['gptPromptSnippet'] = match.get('prompt', '')[:100].replace('\n', ' ') + "..."
            row['gptResponse'] = match.get('response', '')
            
            # If handlingModule was PEPPER_LOCAL but GPT was used, update it?
            # Only if it was a fallback. But let's leave handlingModule if it's ambiguous.
            # Actually, if GPT was used, it implies fallback or parsing.
            if row.get('handlingModule') == 'PEPPER_LOCAL':
                 row['handlingModule'] = 'GPT_ENHANCED'
            
            updated_count += 1
            
    if updated_count > 0:
        # Backup original
        shutil.copy(csv_path, str(csv_path) + ".bak")
        
        # Write updated CSV
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Updated {updated_count} rows in CSV.")
        return True
    else:
        print("  No matching missing data found.")
        return False

def main():
    root_dir = Path("data/sessions")
    if not root_dir.exists():
        print("data/sessions not found")
        return

    # Process all sessions
    for lang_dir in root_dir.iterdir():
        if lang_dir.is_dir():
            for session_dir in lang_dir.iterdir():
                if session_dir.is_dir():
                    repair_session(session_dir)

if __name__ == "__main__":
    main()

