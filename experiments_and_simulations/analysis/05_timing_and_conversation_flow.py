"""
05_timing_and_conversation_flow.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Analyze timing, turns, and conversation flow patterns
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


def load_data():
    """Load required datasets"""
    base_path = Path(__file__).parent.parent
    
    master_file = base_path / "results" / "tables" / "simulation_master.csv"
    interactions_file = base_path / "results" / "tables" / "all_interaction_logs.csv"
    
    if not master_file.exists() or not interactions_file.exists():
        print(" Required data files not found. Run 01_load_and_clean.py first!")
        return None, None
    
    df_master = pd.read_csv(master_file)
    df_interactions = pd.read_csv(interactions_file)
    
    df_master['language'] = df_master['language'].replace({'UNKNOWN': 'EN'})
    
    return df_master, df_interactions


def analyze_timing(df_master, df_interactions):
    """Analyze session timing and turn patterns"""
    print("="*80)
    print("TIMING AND CONVERSATION FLOW ANALYSIS")
    print("="*80)
    
    # Session duration analysis
    df_master['duration_minutes'] = df_master['duration_seconds'] / 60
    
    print(f"\n⏱ Session Duration:")
    print(f"Mean duration: {df_master['duration_minutes'].mean():.2f} minutes")
    print(f"Std deviation: {df_master['duration_minutes'].std():.2f} minutes")
    print(f"Range: [{df_master['duration_minutes'].min():.2f}, {df_master['duration_minutes'].max():.2f}] minutes")
    
    # By language
    print(f"\n Duration by Language:")
    for lang in ['EN', 'DE']:
        lang_data = df_master[df_master['language'] == lang]
        if len(lang_data) > 0:
            print(f"  • {lang}: {lang_data['duration_minutes'].mean():.2f} ± {lang_data['duration_minutes'].std():.2f} minutes")
    
    # Turn count analysis
    print(f"\n Turn Count Analysis:")
    
    turn_counts = df_interactions.groupby('session_folder').size()
    mean_turns = turn_counts.mean()
    
    print(f"Mean turns per session: {mean_turns:.1f}")
    print(f"Range: [{turn_counts.min()}, {turn_counts.max()}] turns")
    
    # Turns per question
    phq_turns = df_interactions[df_interactions['phqQuestionId'].str.startswith('Q', na=False)]
    turns_per_q = phq_turns.groupby('phqQuestionId').size()
    
    print(f"\n Turns per Question:")
    for q_id in sorted(turns_per_q.index):
        mean_per_q = turns_per_q[q_id] / len(df_master)
        print(f"  • {q_id}: {turns_per_q[q_id]} total ({mean_per_q:.1f} per session avg)")
    
    # Correlation analysis
    print(f"\n Correlation Analysis:")
    correlations = df_master[['duration_seconds', 'total_score', 'total_gpt_calls', 'total_retries']].corr()
    print(f"\nDuration correlations:")
    print(f"  • with Total Score: r = {correlations.loc['duration_seconds', 'total_score']:.3f}")
    print(f"  • with GPT Calls: r = {correlations.loc['duration_seconds', 'total_gpt_calls']:.3f}")
    print(f"  • with Retries: r = {correlations.loc['duration_seconds', 'total_retries']:.3f}")
    
    return turn_counts


def create_timing_visualizations(df_master, df_interactions, turn_counts, output_dir):
    """Create timing and flow visualizations"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("GENERATING TIMING VISUALIZATIONS")
    print("="*80)
    
    # 1. Session Duration Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df_master['duration_minutes'], bins=15, color='steelblue', 
             alpha=0.7, edgecolor='black')
    plt.axvline(df_master['duration_minutes'].mean(), color='red', linestyle='--',
                linewidth=2, label=f'Mean: {df_master["duration_minutes"].mean():.1f} min')
    plt.xlabel('Session Duration (minutes)', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Sessions', fontsize=12, fontweight='bold')
    plt.title('Distribution of Session Durations', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig1 = output_dir / "16_duration_distribution.png"
    plt.savefig(fig1, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig1.name}")
    
    # 2. Duration vs Total Score Scatter
    plt.figure(figsize=(10, 6))
    colors = ['steelblue' if lang == 'EN' else 'coral' for lang in df_master['language']]
    plt.scatter(df_master['total_score'], df_master['duration_minutes'],
                c=colors, s=100, alpha=0.6, edgecolors='black')
    
    # Add trend line
    z = np.polyfit(df_master['total_score'], df_master['duration_minutes'], 1)
    p = np.poly1d(z)
    plt.plot(df_master['total_score'], p(df_master['total_score']), 
             "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
    
    plt.xlabel('PHQ-9 Total Score', fontsize=12, fontweight='bold')
    plt.ylabel('Session Duration (minutes)', fontsize=12, fontweight='bold')
    plt.title('Session Duration vs PHQ-9 Score', fontsize=14, fontweight='bold')
    
    # Create custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='steelblue', edgecolor='black', label='English'),
        Patch(facecolor='coral', edgecolor='black', label='German'),
        plt.Line2D([0], [0], color='r', linestyle='--', linewidth=2, label='Trend')
    ]
    plt.legend(handles=legend_elements)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    fig2 = output_dir / "17_duration_vs_score.png"
    plt.savefig(fig2, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig2.name}")
    
    # 3. Turn Count Distribution
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(turn_counts)), turn_counts.values, color='coral', 
            alpha=0.7, edgecolor='black')
    plt.axhline(turn_counts.mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {turn_counts.mean():.1f} turns')
    plt.xlabel('Session', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Turns', fontsize=12, fontweight='bold')
    plt.title('Turn Count per Session', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig3 = output_dir / "18_turn_counts.png"
    plt.savefig(fig3, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig3.name}")
    
    # 4. Turns per Question
    phq_turns = df_interactions[df_interactions['phqQuestionId'].str.startswith('Q', na=False)]
    turns_per_q = phq_turns.groupby('phqQuestionId').size()
    
    plt.figure(figsize=(10, 6))
    q_nums = [int(q[1:]) for q in turns_per_q.index]
    q_counts = turns_per_q.values
    
    plt.bar(q_nums, q_counts, color='steelblue', alpha=0.7, edgecolor='black')
    plt.xlabel('Question Number', fontsize=12, fontweight='bold')
    plt.ylabel('Total Turns', fontsize=12, fontweight='bold')
    plt.title('Total Interaction Turns per Question', fontsize=14, fontweight='bold')
    plt.xticks(range(1, 10))
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig4 = output_dir / "19_turns_per_question.png"
    plt.savefig(fig4, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig4.name}")
    
    # 5. Correlation Heatmap
    plt.figure(figsize=(8, 6))
    corr_data = df_master[['duration_seconds', 'total_score', 'total_gpt_calls', 'total_retries']].corr()
    
    sns.heatmap(corr_data, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={'label': 'Correlation'})
    plt.title('Correlation Matrix: Duration, Score, GPT, Retries', 
              fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig5 = output_dir / "20_correlation_heatmap.png"
    plt.savefig(fig5, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig5.name}")
    
    print("\n All timing visualizations generated!")


def extract_conversation_examples(df_interactions, output_dir):
    """Extract example conversation excerpts"""
    print("\n" + "="*80)
    print("EXTRACTING CONVERSATION EXAMPLES")
    print("="*80)
    
    output_file = output_dir / "conversation_examples.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("CONVERSATION EXAMPLES FOR THESIS\n")
        f.write("="*80 + "\n\n")
        
        # Example 1: Successful local NLP
        f.write("1. EXAMPLE: Successful Local NLP Interpretation\n")
        f.write("-" * 80 + "\n")
        
        local_success = df_interactions[
            (df_interactions['pepperLocalNlpSuccess'] == True) &
            (df_interactions['phqQuestionId'].str.startswith('Q', na=False))
        ].head(1)
        
        if len(local_success) > 0:
            row = local_success.iloc[0]
            f.write(f"Question: {row['phqQuestionId']}\n")
            f.write(f"User said: \"{row['userRawSpeech']}\"\n")
            f.write(f"ASR transcribed: \"{row['asrTranscript']}\"\n")
            f.write(f"Handling: {row['handlingModule']}\n")
            f.write(f"Local NLP: SUCCESS ✓\n")
            f.write(f"GPT used: {row['gptUsed']}\n")
            f.write(f"Robot output: \"{row['finalRobotOutput']}\"\n\n")
        
        # Example 2: GPT Fallback
        f.write("2. EXAMPLE: GPT Fallback Case\n")
        f.write("-" * 80 + "\n")
        
        gpt_fallback = df_interactions[
            (df_interactions['gptUsed'] == True) &
            (df_interactions['handlingModule'] == 'GPT_FALLBACK') &
            (df_interactions['phqQuestionId'].str.startswith('Q', na=False))
        ].head(1)
        
        if len(gpt_fallback) > 0:
            row = gpt_fallback.iloc[0]
            f.write(f"Question: {row['phqQuestionId']}\n")
            f.write(f"User said: \"{row['userRawSpeech']}\"\n")
            f.write(f"ASR transcribed: \"{row['asrTranscript']}\"\n")
            f.write(f"Local NLP: FAILED ✗\n")
            f.write(f"Handling: {row['handlingModule']}\n")
            f.write(f"GPT used: {row['gptUsed']}\n")
            f.write(f"GPT reason: {row['gptReason']}\n")
            if pd.notna(row.get('gptPromptSnippet')):
                f.write(f"GPT prompt (snippet): \"{row['gptPromptSnippet']}\"\n")
            if pd.notna(row.get('gptResponse')):
                f.write(f"GPT response: \"{row['gptResponse']}\"\n")
            f.write(f"Robot output: \"{row['finalRobotOutput']}\"\n\n")
        
        # Example 3: Retry sequence (if any)
        f.write("3. EXAMPLE: Retry Sequence\n")
        f.write("-" * 80 + "\n")
        
        retry_examples = df_interactions[
            df_interactions['notes'].str.contains('retry', case=False, na=False)
        ].head(1)
        
        if len(retry_examples) > 0:
            row = retry_examples.iloc[0]
            f.write(f"Question: {row['phqQuestionId']}\n")
            f.write(f"User said: \"{row['userRawSpeech']}\"\n")
            f.write(f"Notes: {row['notes']}\n")
            f.write(f"Robot output: \"{row['finalRobotOutput']}\"\n\n")
        
        # Example 4: Button-based consent
        f.write("4. EXAMPLE: Button-Based Consent (No Voice/GPT)\n")
        f.write("-" * 80 + "\n")
        
        button_consent = df_interactions[
            df_interactions['handlingModule'] == 'BUTTON'
        ].head(1)
        
        if len(button_consent) > 0:
            row = button_consent.iloc[0]
            f.write(f"User action: {row['userRawSpeech']}\n")
            f.write(f"Handling: {row['handlingModule']}\n")
            f.write(f"GPT used: {row['gptUsed']} (button click, no NLP needed)\n")
            f.write(f"Robot output: \"{row['finalRobotOutput']}\"\n\n")
    
    print(f"✓ Saved conversation examples to: {output_file}")


def save_timing_tables(df_master, output_dir):
    """Save timing statistics tables"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timing_stats = df_master.groupby('language').agg({
        'duration_seconds': ['count', 'mean', 'std', 'min', 'max'],
        'duration_minutes': ['mean', 'std']
    }).round(2)
    
    timing_file = output_dir / "timing_statistics.csv"
    timing_stats.to_csv(timing_file)
    print(f"\n✓ Saved: {timing_file}")


def main():
    """Main execution"""
    print("="*80)
    print("PHQ-9 VOICE SCREENING - TIMING AND FLOW ANALYSIS")
    print("="*80)
    print()
    
    # Load data
    df_master, df_interactions = load_data()
    if df_master is None or df_interactions is None:
        return
    
    # Analyze timing
    turn_counts = analyze_timing(df_master, df_interactions)
    
    # Create visualizations
    base_path = Path(__file__).parent.parent
    output_dir = base_path / "results" / "figures"
    create_timing_visualizations(df_master, df_interactions, turn_counts, output_dir)
    
    # Extract conversation examples
    tables_dir = base_path / "results" / "tables"
    extract_conversation_examples(df_interactions, tables_dir)
    
    # Save timing tables
    save_timing_tables(df_master, tables_dir)
    
    print("\n" + "="*80)
    print(" TIMING AND FLOW ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()

