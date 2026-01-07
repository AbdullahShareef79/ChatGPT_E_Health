"""
02_descriptive_metrics.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Generate descriptive statistics and visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Set style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

def load_master_data():
    """Load the master dataset"""
    base_path = Path(__file__).parent.parent
    data_file = base_path / "results" / "tables" / "simulation_master.csv"
    
    if not data_file.exists():
        print(" Master dataset not found. Run 01_load_and_clean.py first!")
        return None
    
    df = pd.read_csv(data_file)
    # Clean up language column
    df['language'] = df['language'].replace({'UNKNOWN': 'EN'})  # Assume unknown are English
    return df


def compute_descriptives(df):
    """Compute descriptive statistics"""
    print("="*80)
    print("DESCRIPTIVE STATISTICS")
    print("="*80)
    
    # Overall statistics
    print("\n Overall Session Statistics:")
    print(f"Total sessions: {len(df)}")
    print(f"  • English: {len(df[df['language']=='EN'])}")
    print(f"  • German: {len(df[df['language']=='DE'])}")
    print(f"\nDuration (seconds):")
    print(f"  Mean: {df['duration_seconds'].mean():.1f} ± {df['duration_seconds'].std():.1f}")
    print(f"  Range: [{df['duration_seconds'].min():.1f}, {df['duration_seconds'].max():.1f}]")
    print(f"\nPHQ-9 Total Scores:")
    print(f"  Mean: {df['total_score'].mean():.2f} ± {df['total_score'].std():.2f}")
    print(f"  Range: [{df['total_score'].min()}, {df['total_score'].max()}]")
    print(f"\nGPT Calls per Session:")
    print(f"  Mean: {df['total_gpt_calls'].mean():.2f} ± {df['total_gpt_calls'].std():.2f}")
    print(f"  Range: [{df['total_gpt_calls'].min()}, {df['total_gpt_calls'].max()}]")
    print(f"\nRetries per Session:")
    print(f"  Mean: {df['total_retries'].mean():.2f} ± {df['total_retries'].std():.2f}")
    print(f"  Range: [{df['total_retries'].min()}, {df['total_retries'].max()}]")
    
    # By language
    print("\n" + "="*80)
    print("BY LANGUAGE COMPARISON")
    print("="*80)
    
    summary = df.groupby('language').agg({
        'duration_seconds': ['count', 'mean', 'std', 'min', 'max'],
        'total_score': ['mean', 'std'],
        'total_gpt_calls': ['mean', 'std'],
        'total_retries': ['mean', 'std']
    }).round(2)
    
    print("\n", summary)
    
    # Severity distribution
    print("\n Severity Distribution:")
    severity_counts = df['severity'].value_counts()
    print(severity_counts)
    
    return summary


def create_visualizations(df, output_dir):
    """Create all visualizations"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)
    
    # 1. PHQ-9 Total Scores Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df['total_score'], bins=range(0, int(df['total_score'].max())+2), 
             edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlabel('PHQ-9 Total Score', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Sessions', fontsize=12, fontweight='bold')
    plt.title('Distribution of PHQ-9 Total Scores', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig1 = output_dir / "01_total_score_distribution.png"
    plt.savefig(fig1, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig1.name}")
    
    # 2. Total Score by Language (Boxplot)
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=df, x='language', y='total_score', palette='Set2')
    sns.swarmplot(data=df, x='language', y='total_score', color='black', alpha=0.5, size=8)
    plt.xlabel('Language', fontsize=12, fontweight='bold')
    plt.ylabel('PHQ-9 Total Score', fontsize=12, fontweight='bold')
    plt.title('PHQ-9 Scores by Language', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig2 = output_dir / "02_scores_by_language.png"
    plt.savefig(fig2, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig2.name}")
    
    # 3. Duration by Language (Boxplot)
    plt.figure(figsize=(8, 6))
    df['duration_minutes'] = df['duration_seconds'] / 60
    sns.boxplot(data=df, x='language', y='duration_minutes', palette='Set2')
    sns.swarmplot(data=df, x='language', y='duration_minutes', color='black', alpha=0.5, size=8)
    plt.xlabel('Language', fontsize=12, fontweight='bold')
    plt.ylabel('Session Duration (minutes)', fontsize=12, fontweight='bold')
    plt.title('Session Duration by Language', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig3 = output_dir / "03_duration_by_language.png"
    plt.savefig(fig3, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig3.name}")
    
    # 4. GPT Calls Comparison
    plt.figure(figsize=(8, 6))
    lang_gpt_mean = df.groupby('language')['total_gpt_calls'].mean()
    lang_gpt_std = df.groupby('language')['total_gpt_calls'].std()
    x_pos = np.arange(len(lang_gpt_mean))
    plt.bar(x_pos, lang_gpt_mean, yerr=lang_gpt_std, capsize=5, 
            color=['steelblue', 'coral'], alpha=0.8, edgecolor='black')
    plt.xticks(x_pos, lang_gpt_mean.index)
    plt.xlabel('Language', fontsize=12, fontweight='bold')
    plt.ylabel('Mean GPT Calls per Session', fontsize=12, fontweight='bold')
    plt.title('GPT Usage by Language', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig4 = output_dir / "04_gpt_usage_by_language.png"
    plt.savefig(fig4, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig4.name}")
    
    # 5. Retry Counts Comparison
    plt.figure(figsize=(8, 6))
    lang_retry_mean = df.groupby('language')['total_retries'].mean()
    lang_retry_std = df.groupby('language')['total_retries'].std()
    x_pos = np.arange(len(lang_retry_mean))
    plt.bar(x_pos, lang_retry_mean, yerr=lang_retry_std, capsize=5,
            color=['steelblue', 'coral'], alpha=0.8, edgecolor='black')
    plt.xticks(x_pos, lang_retry_mean.index)
    plt.xlabel('Language', fontsize=12, fontweight='bold')
    plt.ylabel('Mean Retries per Session', fontsize=12, fontweight='bold')
    plt.title('Retry Counts by Language', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig5 = output_dir / "05_retries_by_language.png"
    plt.savefig(fig5, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig5.name}")
    
    # 6. Severity Distribution
    plt.figure(figsize=(10, 6))
    severity_order = ['minimal', 'mild', 'moderate', 'moderately severe', 'severe']
    severity_counts = df['severity'].value_counts()
    severity_sorted = [severity_counts.get(s, 0) for s in severity_order]
    colors = ['green', 'yellow', 'orange', 'red', 'darkred']
    plt.bar(range(len(severity_order)), severity_sorted, color=colors, alpha=0.7, edgecolor='black')
    plt.xticks(range(len(severity_order)), [s.title() for s in severity_order], rotation=45, ha='right')
    plt.xlabel('Severity Level', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Sessions', fontsize=12, fontweight='bold')
    plt.title('PHQ-9 Severity Distribution', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig6 = output_dir / "06_severity_distribution.png"
    plt.savefig(fig6, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig6.name}")
    
    # 7. Per-Question Score Heatmap
    q_cols = [f'Q{i}_score' for i in range(1, 10)]
    if all(col in df.columns for col in q_cols):
        plt.figure(figsize=(12, 8))
        q_data = df[q_cols].T
        q_data.columns = [f"S{i+1}" for i in range(len(df))]
        sns.heatmap(q_data, cmap='YlOrRd', cbar_kws={'label': 'Score (0-3)'}, 
                    linewidths=0.5, linecolor='gray', annot=True, fmt='d')
        plt.xlabel('Session', fontsize=12, fontweight='bold')
        plt.ylabel('Question', fontsize=12, fontweight='bold')
        plt.title('Per-Question Scores Across All Sessions', fontsize=14, fontweight='bold')
        plt.tight_layout()
        fig7 = output_dir / "07_per_question_heatmap.png"
        plt.savefig(fig7, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig7.name}")
    
    print("\n All visualizations generated!")


def save_descriptive_tables(df, summary, output_dir):
    """Save descriptive statistics tables"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Session-level descriptives
    descriptives_file = output_dir / "descriptives_sessions.csv"
    summary.to_csv(descriptives_file)
    print(f"\n✓ Saved: {descriptives_file}")
    
    # Per-question mean scores
    q_cols = [f'Q{i}_score' for i in range(1, 10)]
    if all(col in df.columns for col in q_cols):
        q_means = df[q_cols].mean().to_frame(name='mean_score')
        q_means['std_score'] = df[q_cols].std()
        q_means.index = [f'Question {i}' for i in range(1, 10)]
        q_file = output_dir / "per_question_means.csv"
        q_means.to_csv(q_file)
        print(f"✓ Saved: {q_file}")


def main():
    """Main execution"""
    print("="*80)
    print("PHQ-9 VOICE SCREENING - DESCRIPTIVE METRICS")
    print("="*80)
    print()
    
    # Load data
    df = load_master_data()
    if df is None:
        return
    
    # Compute descriptives
    summary = compute_descriptives(df)
    
    # Create visualizations
    base_path = Path(__file__).parent.parent
    output_dir = base_path / "results" / "figures"
    create_visualizations(df, output_dir)
    
    # Save tables
    tables_dir = base_path / "results" / "tables"
    save_descriptive_tables(df, summary, tables_dir)
    
    print("\n" + "="*80)
    print(" DESCRIPTIVE ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()

