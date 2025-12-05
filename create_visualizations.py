"""
PHQ-9 Simulation Data Visualization - Technical NLP/HRI Evaluation
Creates charts focused on system behavior and language processing performance
"""

import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter
import statistics
import argparse

def load_all_sessions(sessions_dir="data/sessions"):
    """Load all session data"""
    sessions = []
    sessions_path = Path(sessions_dir)
    
    if not sessions_path.exists():
        print(f"ERROR: {sessions_dir} not found!")
        return []
    
    for session_folder in sessions_path.iterdir():
        if not session_folder.is_dir():
            continue
        
        json_file = session_folder / "session_data.json"
        if not json_file.exists():
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load GPT calls
            gpt_file = session_folder / "gpt_api_calls.json"
            if gpt_file.exists():
                with open(gpt_file, 'r', encoding='utf-8') as f:
                    data['gpt_calls'] = json.load(f)
            else:
                data['gpt_calls'] = []
            
            # Load interaction logs for retry counts
            csv_file = session_folder / "interaction_logs.csv"
            if csv_file.exists():
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data['interaction_logs'] = list(reader)
            
            sessions.append(data)
        except Exception as e:
            print(f"Error loading {session_folder.name}: {e}")
    
    return sessions

def split_by_language(sessions):
    """Split sessions by language using 'language' field from session_data"""
    english = []
    german = []
    
    for session in sessions:
        # Check for language field in session data
        lang = session.get('language', 'EN').upper()
        
        # Fallback: detect from interaction logs if language field not present
        if 'language' not in session and 'interaction_logs' in session:
            logs = session['interaction_logs']
            if logs and 'languageDetected' in logs[0]:
                detected_langs = [row.get('languageDetected', 'EN') for row in logs]
                # Use most common detected language
                lang_counts = Counter(detected_langs)
                lang = lang_counts.most_common(1)[0][0] if lang_counts else 'EN'
        
        if lang == 'DE':
            german.append(session)
        else:
            english.append(session)
    
    return english, german

def plot_gpt_usage_comparison(en_sessions, de_sessions, output_path):
    """
    PRIMARY FIGURE: GPT API Usage Comparison (EN vs DE)
    Shows average number of GPT calls per session for each language
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    en_gpt = [len(s.get('gpt_calls', [])) for s in en_sessions]
    de_gpt = [len(s.get('gpt_calls', [])) for s in de_sessions]
    
    # Left panel: Average GPT calls
    en_mean = statistics.mean(en_gpt) if en_gpt else 0
    de_mean = statistics.mean(de_gpt) if de_gpt else 0
    
    languages = ['English', 'German']
    means = [en_mean, de_mean]
    colors = ['#2196F3', '#FF5722']
    
    bars = ax1.bar(languages, means, color=colors, alpha=0.7, edgecolor='black', width=0.6)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax1.set_ylabel('Average GPT API Calls per Session', fontsize=12)
    ax1.set_xlabel('Language Group', fontsize=12)
    ax1.set_title('GPT Usage: English vs German', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, max(means + [1]) * 1.2)
    
    # Right panel: Distribution (if data available)
    if en_gpt or de_gpt:
        data_to_plot = []
        labels = []
        
        if en_gpt:
            data_to_plot.append(en_gpt)
            labels.append(f'EN (n={len(en_gpt)})')
        
        if de_gpt:
            data_to_plot.append(de_gpt)
            labels.append(f'DE (n={len(de_gpt)})')
        
        bp = ax2.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
        
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax2.set_ylabel('GPT API Calls per Session', fontsize=12)
        ax2.set_xlabel('Language Group', fontsize=12)
        ax2.set_title('GPT Usage Distribution', fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_retries_per_question(sessions, output_path):
    """
    KEY FIGURE: Average Retries per Question (Q1-Q9)
    Shows where the system struggles with natural language understanding
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Collect retry counts per question
    retry_counts = {i: [] for i in range(1, 10)}
    
    for session in sessions:
        if 'retry_counts' in session:
            retries = session['retry_counts']
            if isinstance(retries, dict):
                for q_idx, count in retries.items():
                    q_num = int(q_idx) + 1 if isinstance(q_idx, (int, str)) and str(q_idx).isdigit() else None
                    if q_num and 1 <= q_num <= 9:
                        retry_counts[q_num].append(count)
            elif isinstance(retries, list) and len(retries) == 9:
                for q_num, count in enumerate(retries, 1):
                    retry_counts[q_num].append(count)
    
    # Calculate means
    questions = list(range(1, 10))
    means = []
    
    for q_num in questions:
        counts = retry_counts[q_num]
        mean = statistics.mean(counts) if counts else 0
        means.append(mean)
    
    # Create bar chart
    colors = ['#4CAF50' if m == 0 else '#FFC107' if m < 1 else '#FF5722' for m in means]
    bars = ax.bar(questions, means, color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('PHQ-9 Question Number', fontsize=12)
    ax.set_ylabel('Average Number of Retries', fontsize=12)
    ax.set_title('System Retry Behavior per Question', fontsize=14, fontweight='bold')
    ax.set_xticks(questions)
    ax.set_ylim(0, max(means + [0.5]) * 1.2)
    ax.grid(axis='y', alpha=0.3)
    
    # Add legend
    green_patch = mpatches.Patch(color='#4CAF50', alpha=0.7, label='No retries (0)')
    yellow_patch = mpatches.Patch(color='#FFC107', alpha=0.7, label='Few retries (<1)')
    red_patch = mpatches.Patch(color='#FF5722', alpha=0.7, label='Frequent retries (≥1)')
    ax.legend(handles=[green_patch, yellow_patch, red_patch], loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_session_duration_comparison(en_sessions, de_sessions, output_path):
    """
    Session Duration Comparison (EN vs DE)
    Reflects system efficiency and language-specific processing difficulty
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    en_durations = [s.get('duration_seconds', 0)/60 for s in en_sessions if 'duration_seconds' in s]
    de_durations = [s.get('duration_seconds', 0)/60 for s in de_sessions if 'duration_seconds' in s]
    
    # Box plot
    data_to_plot = []
    labels = []
    colors = ['#2196F3', '#FF5722']
    
    if en_durations:
        data_to_plot.append(en_durations)
        labels.append(f'English (n={len(en_durations)})')
    
    if de_durations:
        data_to_plot.append(de_durations)
        labels.append(f'German (n={len(de_durations)})')
    
    if not data_to_plot:
        print("! No duration data available")
        return
    
    bp = ax.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
    
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Add mean markers
    for i, durations in enumerate(data_to_plot):
        mean = statistics.mean(durations)
        ax.plot([i+1], [mean], 'D', color='darkred', markersize=8, 
                label='Mean' if i == 0 else '', zorder=3)
    
    ax.set_ylabel('Session Duration (minutes)', fontsize=12)
    ax.set_xlabel('Language Group', fontsize=12)
    ax.set_title('Session Duration: English vs German', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def plot_gpt_calls_by_purpose(en_sessions, de_sessions, output_path):
    """
    OPTIONAL: GPT Calls by Purpose per Language
    Shows what types of NLP tasks required GPT assistance
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Collect purposes per language
    def get_purposes(sessions):
        purposes = {}
        for session in sessions:
            for call in session.get('gpt_calls', []):
                purpose = call.get('purpose', 'unknown')
                purposes[purpose] = purposes.get(purpose, 0) + 1
        return purposes
    
    en_purposes = get_purposes(en_sessions)
    de_purposes = get_purposes(de_sessions)
    
    if not en_purposes and not de_purposes:
        print("! No GPT purpose data available")
        return
    
    # Get all unique purposes
    all_purposes = sorted(set(list(en_purposes.keys()) + list(de_purposes.keys())))
    
    # Prepare data
    en_counts = [en_purposes.get(p, 0) for p in all_purposes]
    de_counts = [de_purposes.get(p, 0) for p in all_purposes]
    
    # Create grouped bar chart
    x = range(len(all_purposes))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], en_counts, width, 
                    label='English', color='#2196F3', alpha=0.7, edgecolor='black')
    bars2 = ax.bar([i + width/2 for i in x], de_counts, width,
                    label='German', color='#FF5722', alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('GPT Call Purpose', fontsize=12)
    ax.set_ylabel('Total Number of Calls', fontsize=12)
    ax.set_title('GPT Usage by Purpose: English vs German', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace('_', ' ').title() for p in all_purposes], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

# ========== CLINICAL/APPENDIX FIGURES (Optional) ==========

def plot_clinical_figures(sessions, output_dir, en_sessions, de_sessions):
    """Generate clinical/PHQ-9 score figures (for appendix only)"""
    print("\n[APPENDIX] Generating clinical figures...")
    
    # Total scores comparison
    if en_sessions or de_sessions:
        plot_total_scores_comparison_clinical(en_sessions, de_sessions, 
                                              output_dir / "appendix_total_scores.png")
    
    # Severity distribution
    plot_severity_distribution_clinical(sessions, output_dir / "appendix_severity_distribution.png")
    
    # Per-question scores
    plot_per_question_scores_clinical(sessions, output_dir / "appendix_per_question_scores.png")
    
    # Score distribution
    plot_score_distribution_clinical(sessions, output_dir / "appendix_score_distribution.png")

def plot_total_scores_comparison_clinical(en_sessions, de_sessions, output_path):
    """Clinical: Total PHQ-9 scores comparison"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    en_scores = [s.get('total_score', 0) for s in en_sessions if 'total_score' in s]
    de_scores = [s.get('total_score', 0) for s in de_sessions if 'total_score' in s]
    
    data_to_plot = []
    labels = []
    
    if en_scores:
        data_to_plot.append(en_scores)
        labels.append(f'English (n={len(en_scores)})')
    
    if de_scores:
        data_to_plot.append(de_scores)
        labels.append(f'German (n={len(de_scores)})')
    
    if not data_to_plot:
        return
    
    bp = ax.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
    
    colors = ['#4CAF50', '#FF5722']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('PHQ-9 Total Score', fontsize=12)
    ax.set_title('[APPENDIX] PHQ-9 Total Scores', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 27)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()

def plot_severity_distribution_clinical(sessions, output_path):
    """Clinical: Severity distribution pie chart"""
    severities = [s.get('severity', 'unknown') for s in sessions if 'severity' in s]
    if not severities:
        return
    
    fig, ax = plt.subplots(figsize=(8, 8))
    severity_counts = Counter(severities)
    
    labels = [f'{k.capitalize()} (n={v})' for k, v in severity_counts.items()]
    sizes = list(severity_counts.values())
    colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']
    
    ax.pie(sizes, labels=labels, colors=colors[:len(sizes)], autopct='%1.1f%%', startangle=90)
    ax.set_title('[APPENDIX] PHQ-9 Severity Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()

def plot_per_question_scores_clinical(sessions, output_path):
    """Clinical: Average score per question"""
    all_responses = [s.get('phq9_responses', []) for s in sessions if 'phq9_responses' in s]
    if not all_responses or not all(len(r) == 9 for r in all_responses):
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    means = [statistics.mean([r[i] for r in all_responses]) for i in range(9)]
    questions = list(range(1, 10))
    
    ax.bar(questions, means, color='#2196F3', alpha=0.7, edgecolor='black')
    ax.set_xlabel('PHQ-9 Question Number', fontsize=12)
    ax.set_ylabel('Average Score (0-3)', fontsize=12)
    ax.set_title('[APPENDIX] Average Score per Question', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 3)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()

def plot_score_distribution_clinical(sessions, output_path):
    """Clinical: Distribution of individual scores"""
    all_scores = []
    for session in sessions:
        all_scores.extend(session.get('phq9_responses', []))
    
    if not all_scores:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    score_counts = Counter(all_scores)
    scores = [0, 1, 2, 3]
    counts = [score_counts.get(s, 0) for s in scores]
    colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
    
    ax.bar(scores, counts, color=colors, alpha=0.7, edgecolor='black')
    ax.set_xlabel('Score', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('[APPENDIX] PHQ-9 Score Distribution', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()

def main():
    """Generate all visualizations"""
    parser = argparse.ArgumentParser(description='Generate PHQ-9 simulation visualizations')
    parser.add_argument('--include-clinical', action='store_true',
                       help='Include clinical/PHQ-9 score figures (for appendix)')
    args = parser.parse_args()
    
    print("="*70)
    print("PHQ-9 SIMULATION VISUALIZATION - NLP/HRI EVALUATION")
    print("="*70)
    
    # Load sessions
    print("\nLoading session data...")
    sessions = load_all_sessions()
    
    if not sessions:
        print("ERROR: No sessions found!")
        return
    
    print(f"Loaded {len(sessions)} session(s)")
    
    # Split by language
    en_sessions, de_sessions = split_by_language(sessions)
    print(f"  - English: {len(en_sessions)}")
    print(f"  - German: {len(de_sessions)}")
    
    # Create output directory
    output_dir = Path("results/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving visualizations to: {output_dir}/")
    
    # Generate PRIMARY technical figures
    print("\n[PRIMARY] Generating technical evaluation figures...")
    
    # 1. GPT Usage Comparison (PRIMARY)
    if en_sessions or de_sessions:
        plot_gpt_usage_comparison(en_sessions, de_sessions, 
                                  output_dir / "fig1_gpt_usage_comparison.png")
    
    # 2. Retry Difficulty Analysis (KEY FIGURE)
    plot_retries_per_question(sessions, output_dir / "fig2_retries_per_question.png")
    
    # 3. Session Duration Comparison
    if en_sessions or de_sessions:
        plot_session_duration_comparison(en_sessions, de_sessions,
                                         output_dir / "fig3_duration_comparison.png")
    
    # 4. GPT Calls by Purpose (OPTIONAL)
    if en_sessions or de_sessions:
        plot_gpt_calls_by_purpose(en_sessions, de_sessions,
                                  output_dir / "fig4_gpt_by_purpose.png")
    
    # Generate CLINICAL figures if requested
    if args.include_clinical:
        plot_clinical_figures(sessions, output_dir, en_sessions, de_sessions)
    
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\nAll figures saved to: {output_dir}/")
    print("\nGenerated figures (TECHNICAL EVALUATION):")
    print("  1. GPT Usage: EN vs DE comparison (PRIMARY)")
    print("  2. Retries per Question: System difficulty analysis (KEY)")
    print("  3. Duration: Session efficiency comparison")
    print("  4. GPT by Purpose: NLP task breakdown")
    
    if args.include_clinical:
        print("\nAdditional figures (APPENDIX - Clinical):")
        print("  - Total scores comparison")
        print("  - Severity distribution")
        print("  - Per-question scores")
        print("  - Score distribution")
    else:
        print("\n(Run with --include-clinical to generate appendix figures)")
    print()

if __name__ == "__main__":
    main()
