"""
04_local_nlp_performance.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Analyze local NLP performance and retry patterns
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
    
    # Clean up language
    df_master['language'] = df_master['language'].replace({'UNKNOWN': 'EN'})
    
    return df_master, df_interactions


def analyze_nlp_performance(df_master, df_interactions):
    """Analyze local NLP performance"""
    print("="*80)
    print("LOCAL NLP PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Filter to PHQ-9 question turns only
    df_phq = df_interactions[df_interactions['phqQuestionId'].str.startswith('Q', na=False)].copy()
    
    # Overall success rate
    total_turns = len(df_phq)
    local_success = len(df_phq[df_phq['pepperLocalNlpSuccess'] == True])
    local_rate = (local_success / total_turns) * 100 if total_turns > 0 else 0
    
    print(f"\n Overall NLP Performance:")
    print(f"Total PHQ-9 answer turns: {total_turns}")
    print(f"Local NLP success: {local_success} ({local_rate:.1f}%)")
    print(f"Required GPT fallback: {total_turns - local_success} ({100-local_rate:.1f}%)")
    
    # Success rate by language
    print(f"\n Performance by Language:")
    for lang in df_interactions['languageDetected'].unique():
        if pd.isna(lang):
            continue
        lang_turns = df_phq[df_phq['languageDetected'] == lang]
        if len(lang_turns) > 0:
            lang_success = len(lang_turns[lang_turns['pepperLocalNlpSuccess'] == True])
            lang_rate = (lang_success / len(lang_turns)) * 100
            print(f"  • {lang}: {lang_success}/{len(lang_turns)} ({lang_rate:.1f}% success)")
    
    # Success rate per question
    print(f"\n Performance by Question:")
    for q_num in range(1, 10):
        q_id = f'Q{q_num}'
        q_turns = df_phq[df_phq['phqQuestionId'] == q_id]
        
        if len(q_turns) > 0:
            q_success = len(q_turns[q_turns['pepperLocalNlpSuccess'] == True])
            q_rate = (q_success / len(q_turns)) * 100
            print(f"  • Q{q_num}: {q_success}/{len(q_turns)} ({q_rate:.1f}% success)")
    
    # Retry analysis
    print(f"\n Retry Analysis:")
    retry_cols = [f'Q{i}_retries' for i in range(1, 10)]
    if all(col in df_master.columns for col in retry_cols):
        retry_data = df_master[retry_cols]
        total_retries = retry_data.sum().sum()
        mean_retries = retry_data.mean().mean()
        
        print(f"Total retries across all sessions: {int(total_retries)}")
        print(f"Mean retries per question: {mean_retries:.2f}")
        
        print(f"\nRetries by Question:")
        for i, col in enumerate(retry_cols, 1):
            q_retries = retry_data[col].sum()
            q_mean = retry_data[col].mean()
            print(f"  • Q{i}: {int(q_retries)} total (mean: {q_mean:.2f} per session)")
    
    return df_phq


def create_nlp_visualizations(df_master, df_phq, output_dir):
    """Create NLP performance visualizations"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("GENERATING NLP VISUALIZATIONS")
    print("="*80)
    
    # 1. Success Rate Heatmap by Question
    plt.figure(figsize=(10, 6))
    
    success_matrix = []
    q_labels = []
    
    for q_num in range(1, 10):
        q_id = f'Q{q_num}'
        q_turns = df_phq[df_phq['phqQuestionId'] == q_id]
        
        if len(q_turns) > 0:
            success_rate = (len(q_turns[q_turns['pepperLocalNlpSuccess'] == True]) / len(q_turns)) * 100
            success_matrix.append(success_rate)
            q_labels.append(f'Q{q_num}')
    
    if success_matrix:
        success_df = pd.DataFrame({'Success Rate (%)': success_matrix}, index=q_labels)
        
        sns.heatmap(success_df.T, annot=True, fmt='.1f', cmap='RdYlGn', 
                    vmin=0, vmax=100, cbar_kws={'label': 'Success Rate (%)'}, 
                    linewidths=1, linecolor='black')
        plt.xlabel('Question', fontsize=12, fontweight='bold')
        plt.ylabel('', fontsize=12, fontweight='bold')
        plt.title('Local NLP Success Rate by Question', fontsize=14, fontweight='bold')
        plt.tight_layout()
        fig1 = output_dir / "12_nlp_success_heatmap.png"
        plt.savefig(fig1, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig1.name}")
    
    # 2. Retries per Question
    retry_cols = [f'Q{i}_retries' for i in range(1, 10)]
    if all(col in df_master.columns for col in retry_cols):
        plt.figure(figsize=(10, 6))
        
        retry_means = df_master[retry_cols].mean()
        retry_stds = df_master[retry_cols].std()
        
        x_pos = np.arange(len(retry_cols))
        plt.bar(x_pos, retry_means.values, yerr=retry_stds.values, capsize=5,
                color='coral', alpha=0.8, edgecolor='black')
        plt.xticks(x_pos, [f'Q{i}' for i in range(1, 10)])
        plt.xlabel('Question', fontsize=12, fontweight='bold')
        plt.ylabel('Mean Retries per Session', fontsize=12, fontweight='bold')
        plt.title('Retry Counts per Question', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        fig2 = output_dir / "13_retries_per_question.png"
        plt.savefig(fig2, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig2.name}")
    
    # 3. NLP Success by Language
    plt.figure(figsize=(8, 6))
    
    lang_success = []
    lang_labels = []
    
    for lang in ['EN', 'DE']:
        lang_turns = df_phq[df_phq['languageDetected'] == lang]
        if len(lang_turns) > 0:
            success_rate = (len(lang_turns[lang_turns['pepperLocalNlpSuccess'] == True]) / len(lang_turns)) * 100
            lang_success.append(success_rate)
            lang_labels.append(lang)
    
    if lang_success:
        colors = ['steelblue', 'coral']
        plt.bar(range(len(lang_labels)), lang_success, color=colors[:len(lang_labels)], 
                alpha=0.8, edgecolor='black')
        plt.xticks(range(len(lang_labels)), lang_labels)
        plt.xlabel('Language', fontsize=12, fontweight='bold')
        plt.ylabel('Local NLP Success Rate (%)', fontsize=12, fontweight='bold')
        plt.title('Local NLP Performance by Language', fontsize=14, fontweight='bold')
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        fig3 = output_dir / "14_nlp_success_by_language.png"
        plt.savefig(fig3, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig3.name}")
    
    # 4. Handling Module Distribution
    plt.figure(figsize=(10, 6))
    
    module_counts = df_phq['handlingModule'].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(module_counts)))
    
    plt.pie(module_counts.values, labels=module_counts.index, autopct='%1.1f%%',
            colors=colors, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    plt.title('Answer Handling Module Distribution', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig4 = output_dir / "15_handling_module_distribution.png"
    plt.savefig(fig4, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {fig4.name}")
    
    print("\n All NLP visualizations generated!")


def save_nlp_tables(df_master, df_phq, output_dir):
    """Save NLP performance tables"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Success rate by question
    success_by_q = []
    for q_num in range(1, 10):
        q_id = f'Q{q_num}'
        q_turns = df_phq[df_phq['phqQuestionId'] == q_id]
        
        if len(q_turns) > 0:
            total = len(q_turns)
            success = len(q_turns[q_turns['pepperLocalNlpSuccess'] == True])
            rate = (success / total) * 100
            
            success_by_q.append({
                'question': f'Q{q_num}',
                'total_turns': total,
                'local_success': success,
                'gpt_fallback': total - success,
                'success_rate': rate
            })
    
    success_df = pd.DataFrame(success_by_q)
    success_file = output_dir / "nlp_performance_by_question.csv"
    success_df.to_csv(success_file, index=False)
    print(f"\n✓ Saved: {success_file}")
    
    # Retry statistics
    retry_cols = [f'Q{i}_retries' for i in range(1, 10)]
    if all(col in df_master.columns for col in retry_cols):
        retry_stats = df_master[retry_cols].describe().T
        retry_stats.index = [f'Q{i}' for i in range(1, 10)]
        retry_file = output_dir / "retry_statistics.csv"
        retry_stats.to_csv(retry_file)
        print(f"✓ Saved: {retry_file}")


def main():
    """Main execution"""
    print("="*80)
    print("PHQ-9 VOICE SCREENING - LOCAL NLP PERFORMANCE")
    print("="*80)
    print()
    
    # Load data
    df_master, df_interactions = load_data()
    if df_master is None or df_interactions is None:
        return
    
    # Analyze NLP performance
    df_phq = analyze_nlp_performance(df_master, df_interactions)
    
    # Create visualizations
    base_path = Path(__file__).parent.parent
    output_dir = base_path / "results" / "figures"
    create_nlp_visualizations(df_master, df_phq, output_dir)
    
    # Save tables
    tables_dir = base_path / "results" / "tables"
    save_nlp_tables(df_master, df_phq, tables_dir)
    
    print("\n" + "="*80)
    print(" LOCAL NLP PERFORMANCE ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()

