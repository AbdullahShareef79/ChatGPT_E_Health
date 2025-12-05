"""
PHQ-9 Simulation Data Visualization
Creates charts and graphs for thesis results section
"""

import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter
import statistics

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
    """Split sessions by language (manually categorized for now)"""
    # For now, we'll need to manually categorize or add language field
    # Placeholder: assume all are EN until we have DE sessions
    english = []
    german = []
    
    for session in sessions:
        # Check if there's a language indicator in the data
        # For now, categorize based on file or add language field
        # Temporary: all current sessions are EN
        lang = session.get('language', 'EN')
        if lang == 'DE':
            german.append(session)
        else:
            english.append(session)
    
    return english, german

def plot_total_scores_comparison(en_sessions, de_sessions, output_path):
    """Bar chart: Total PHQ-9 scores EN vs DE"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    en_scores = [s.get('total_score', 0) for s in en_sessions if 'total_score' in s]
    de_scores = [s.get('total_score', 0) for s in de_sessions if 'total_score' in s]
    
    # Create box plot
    data_to_plot = []
    labels = []
    
    if en_scores:
        data_to_plot.append(en_scores)
        labels.append(f'English (n={len(en_scores)})')
    
    if de_scores:
        data_to_plot.append(de_scores)
        labels.append(f'German (n={len(de_scores)})')
    
    if not data_to_plot:
        print("No data to plot for total scores")
        return
    
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    # Color the boxes
    colors = ['#4CAF50', '#FF5722']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('PHQ-9 Total Score', fontsize=12)
    ax.set_xlabel('Language Group', fontsize=12)
    ax.set_title('PHQ-9 Total Scores: English vs German', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 27)
    ax.grid(axis='y', alpha=0.3)
    
    # Add mean lines
    for i, scores in enumerate(data_to_plot):
        mean = statistics.mean(scores)
        ax.plot([i+1], [mean], 'D', color='red', markersize=8, label='Mean' if i == 0 else '')
    
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def plot_gpt_usage_comparison(en_sessions, de_sessions, output_path):
    """Bar chart: GPT API calls EN vs DE"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    en_gpt = [len(s.get('gpt_calls', [])) for s in en_sessions]
    de_gpt = [len(s.get('gpt_calls', [])) for s in de_sessions]
    
    # Calculate means
    en_mean = statistics.mean(en_gpt) if en_gpt else 0
    de_mean = statistics.mean(de_gpt) if de_gpt else 0
    
    # Bar chart
    languages = ['English', 'German']
    means = [en_mean, de_mean]
    colors = ['#4CAF50', '#FF5722']
    
    bars = ax.bar(languages, means, color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_ylabel('Average GPT API Calls per Session', fontsize=12)
    ax.set_xlabel('Language Group', fontsize=12)
    ax.set_title('GPT Usage: English vs German', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def plot_session_duration_comparison(en_sessions, de_sessions, output_path):
    """Bar chart: Session duration EN vs DE"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    en_durations = [s.get('duration_seconds', 0)/60 for s in en_sessions if 'duration_seconds' in s]
    de_durations = [s.get('duration_seconds', 0)/60 for s in de_sessions if 'duration_seconds' in s]
    
    # Box plot
    data_to_plot = []
    labels = []
    
    if en_durations:
        data_to_plot.append(en_durations)
        labels.append(f'English (n={len(en_durations)})')
    
    if de_durations:
        data_to_plot.append(de_durations)
        labels.append(f'German (n={len(de_durations)})')
    
    if not data_to_plot:
        print("No data to plot for duration")
        return
    
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    colors = ['#4CAF50', '#FF5722']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Session Duration (minutes)', fontsize=12)
    ax.set_xlabel('Language Group', fontsize=12)
    ax.set_title('Session Duration: English vs German', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def plot_per_question_scores(sessions, output_path):
    """Heatmap: Average score per question"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Collect responses
    all_responses = [s.get('phq9_responses', []) for s in sessions if 'phq9_responses' in s]
    
    if not all_responses or not all(len(r) == 9 for r in all_responses):
        print("No valid response data for per-question plot")
        return
    
    # Calculate mean and count per score for each question
    questions = list(range(1, 10))
    means = []
    
    for q_idx in range(9):
        q_scores = [r[q_idx] for r in all_responses]
        means.append(statistics.mean(q_scores))
    
    # Bar chart
    bars = ax.bar(questions, means, color='#2196F3', alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=10)
    
    ax.set_xlabel('PHQ-9 Question Number', fontsize=12)
    ax.set_ylabel('Average Score (0-3)', fontsize=12)
    ax.set_title('Average Score per PHQ-9 Question', fontsize=14, fontweight='bold')
    ax.set_xticks(questions)
    ax.set_ylim(0, 3)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def plot_severity_distribution(sessions, output_path):
    """Pie chart: Severity distribution"""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    severities = [s.get('severity', 'unknown') for s in sessions if 'severity' in s]
    
    if not severities:
        print("No severity data to plot")
        return
    
    # Count severities
    severity_counts = Counter(severities)
    
    # Define order and colors
    severity_order = ['minimal', 'mild', 'moderate', 'moderately severe', 'severe']
    colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']
    
    # Filter and sort
    labels = []
    sizes = []
    plot_colors = []
    
    for sev, color in zip(severity_order, colors):
        if sev in severity_counts:
            labels.append(f'{sev.capitalize()} (n={severity_counts[sev]})')
            sizes.append(severity_counts[sev])
            plot_colors.append(color)
    
    # Pie chart
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=plot_colors,
                                        autopct='%1.1f%%', startangle=90,
                                        textprops={'fontsize': 11})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('PHQ-9 Severity Distribution', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def plot_score_distribution(sessions, output_path):
    """Histogram: Distribution of individual question scores"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Collect all individual scores
    all_scores = []
    for session in sessions:
        responses = session.get('phq9_responses', [])
        all_scores.extend(responses)
    
    if not all_scores:
        print("No score data to plot")
        return
    
    # Count each score
    score_counts = Counter(all_scores)
    scores = [0, 1, 2, 3]
    counts = [score_counts.get(s, 0) for s in scores]
    
    # Bar chart
    colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
    bars = ax.bar(scores, counts, color=colors, alpha=0.7, edgecolor='black')
    
    # Add labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Score', fontsize=12)
    ax.set_ylabel('Frequency (across all questions and sessions)', fontsize=12)
    ax.set_title('Distribution of PHQ-9 Response Scores', fontsize=14, fontweight='bold')
    ax.set_xticks(scores)
    ax.set_xticklabels(['0\n(Not at all)', '1\n(Several days)', 
                         '2\n(More than half)', '3\n(Nearly every day)'])
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

def main():
    """Generate all visualizations"""
    print("="*70)
    print("PHQ-9 SIMULATION DATA VISUALIZATION")
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
    
    # Generate plots
    print("\nGenerating visualizations...")
    
    # 1. Total scores comparison
    if en_sessions or de_sessions:
        plot_total_scores_comparison(en_sessions, de_sessions, 
                                     output_dir / "1_total_scores_comparison.png")
    
    # 2. GPT usage comparison
    if en_sessions or de_sessions:
        plot_gpt_usage_comparison(en_sessions, de_sessions,
                                  output_dir / "2_gpt_usage_comparison.png")
    
    # 3. Session duration comparison
    if en_sessions or de_sessions:
        plot_session_duration_comparison(en_sessions, de_sessions,
                                         output_dir / "3_duration_comparison.png")
    
    # 4. Per-question average scores
    plot_per_question_scores(sessions, output_dir / "4_per_question_scores.png")
    
    # 5. Severity distribution
    plot_severity_distribution(sessions, output_dir / "5_severity_distribution.png")
    
    # 6. Score distribution
    plot_score_distribution(sessions, output_dir / "6_score_distribution.png")
    
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\nAll figures saved to: {output_dir}/")
    print("\nGenerated figures:")
    print("  1. Total Scores: EN vs DE comparison (box plot)")
    print("  2. GPT Usage: Average API calls per session (bar chart)")
    print("  3. Duration: Session length comparison (box plot)")
    print("  4. Per-Question: Average score for each Q1-Q9 (bar chart)")
    print("  5. Severity: Distribution across categories (pie chart)")
    print("  6. Scores: Overall response distribution (histogram)")
    print()

if __name__ == "__main__":
    main()

