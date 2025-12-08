"""
03_gpt_usage_analysis.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Analyze GPT usage patterns and performance
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
    """Load GPT calls and interaction logs"""
    base_path = Path(__file__).parent.parent
    
    gpt_file = base_path / "results" / "tables" / "all_gpt_calls.csv"
    interactions_file = base_path / "results" / "tables" / "all_interaction_logs.csv"
    
    if not gpt_file.exists() or not interactions_file.exists():
        print("❌ Required data files not found. Run 01_load_and_clean.py first!")
        return None, None
    
    df_gpt = pd.read_csv(gpt_file)
    df_interactions = pd.read_csv(interactions_file)
    
    return df_gpt, df_interactions


def analyze_gpt_usage(df_gpt, df_interactions):
    """Analyze GPT usage patterns"""
    print("="*80)
    print("GPT USAGE ANALYSIS")
    print("="*80)
    
    # Overall statistics
    print(f"\n📊 Overall GPT Statistics:")
    print(f"Total GPT calls: {len(df_gpt)}")
    
    if 'tokens_used' in df_gpt.columns:
        total_tokens = df_gpt['tokens_used'].sum()
        mean_tokens = df_gpt['tokens_used'].mean()
        print(f"Total tokens: {total_tokens:,}")
        print(f"Mean tokens per call: {mean_tokens:.1f} ± {df_gpt['tokens_used'].std():.1f}")
    
    # GPT calls by purpose
    if 'purpose' in df_gpt.columns:
        print(f"\n🎯 GPT Calls by Purpose:")
        purpose_counts = df_gpt['purpose'].value_counts()
        for purpose, count in purpose_counts.items():
            pct = (count / len(df_gpt)) * 100
            print(f"  • {purpose}: {count} ({pct:.1f}%)")
    
    # Extract question number from purpose if available
    df_gpt['question_num'] = df_gpt['purpose'].str.extract(r'Q(\d+)').astype(float)
    
    # Per-question GPT usage from interactions
    print(f"\n📈 GPT Usage by Question:")
    gpt_by_question = df_interactions[df_interactions['gptUsed'] == True].groupby('phqQuestionId').size()
    for q_id, count in gpt_by_question.items():
        if q_id and q_id.startswith('Q'):
            print(f"  • {q_id}: {count} calls")
    
    # Success rate analysis
    if 'gptUsed' in df_interactions.columns:
        total_turns = len(df_interactions[df_interactions['phqQuestionId'].str.startswith('Q', na=False)])
        gpt_turns = len(df_interactions[
            (df_interactions['gptUsed'] == True) & 
            (df_interactions['phqQuestionId'].str.startswith('Q', na=False))
        ])
        local_success = total_turns - gpt_turns
        
        print(f"\n✅ Local NLP vs GPT Fallback:")
        print(f"  • Total answer turns: {total_turns}")
        print(f"  • Local NLP success: {local_success} ({local_success/total_turns*100:.1f}%)")
        print(f"  • GPT fallback needed: {gpt_turns} ({gpt_turns/total_turns*100:.1f}%)")
    
    return purpose_counts if 'purpose' in df_gpt.columns else None


def create_gpt_visualizations(df_gpt, df_interactions, output_dir):
    """Create GPT usage visualizations"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("GENERATING GPT VISUALIZATIONS")
    print("="*80)
    
    # 1. GPT Calls by Question
    plt.figure(figsize=(10, 6))
    gpt_interactions = df_interactions[
        (df_interactions['gptUsed'] == True) & 
        (df_interactions['phqQuestionId'].str.startswith('Q', na=False))
    ]
    
    if len(gpt_interactions) > 0:
        q_counts = gpt_interactions['phqQuestionId'].value_counts().sort_index()
        q_nums = [int(q[1:]) for q in q_counts.index]
        
        plt.bar(q_nums, q_counts.values, color='steelblue', alpha=0.8, edgecolor='black')
        plt.xlabel('PHQ-9 Question Number', fontsize=12, fontweight='bold')
        plt.ylabel('Number of GPT Calls', fontsize=12, fontweight='bold')
        plt.title('GPT Fallback Usage per Question', fontsize=14, fontweight='bold')
        plt.xticks(range(1, 10))
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        fig1 = output_dir / "08_gpt_calls_per_question.png"
        plt.savefig(fig1, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig1.name}")
    
    # 2. GPT Reasons Distribution
    if 'gptReason' in df_interactions.columns:
        plt.figure(figsize=(10, 6))
        gpt_reasons = df_interactions[df_interactions['gptUsed'] == True]['gptReason'].value_counts()
        
        if len(gpt_reasons) > 0:
            colors = plt.cm.Set3(np.linspace(0, 1, len(gpt_reasons)))
            plt.bar(range(len(gpt_reasons)), gpt_reasons.values, color=colors, edgecolor='black')
            plt.xticks(range(len(gpt_reasons)), gpt_reasons.index, rotation=45, ha='right')
            plt.xlabel('GPT Reason', fontsize=12, fontweight='bold')
            plt.ylabel('Count', fontsize=12, fontweight='bold')
            plt.title('GPT Usage Reasons Distribution', fontsize=14, fontweight='bold')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            fig2 = output_dir / "09_gpt_reasons_distribution.png"
            plt.savefig(fig2, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ {fig2.name}")
    
    # 3. Tokens per GPT Call
    if 'tokens_used' in df_gpt.columns:
        plt.figure(figsize=(10, 6))
        plt.hist(df_gpt['tokens_used'].dropna(), bins=20, color='coral', 
                 alpha=0.7, edgecolor='black')
        plt.axvline(df_gpt['tokens_used'].mean(), color='red', linestyle='--', 
                    linewidth=2, label=f'Mean: {df_gpt["tokens_used"].mean():.1f}')
        plt.xlabel('Tokens Used', fontsize=12, fontweight='bold')
        plt.ylabel('Number of Calls', fontsize=12, fontweight='bold')
        plt.title('Token Usage Distribution per GPT Call', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        fig3 = output_dir / "10_tokens_distribution.png"
        plt.savefig(fig3, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig3.name}")
    
    # 4. Local NLP Success vs GPT Fallback
    plt.figure(figsize=(8, 6))
    
    # Calculate success rates per question
    q_success = []
    q_labels = []
    
    for q_num in range(1, 10):
        q_id = f'Q{q_num}'
        q_turns = df_interactions[df_interactions['phqQuestionId'] == q_id]
        
        if len(q_turns) > 0:
            local_success = len(q_turns[q_turns['pepperLocalNlpSuccess'] == True])
            gpt_used = len(q_turns[q_turns['gptUsed'] == True])
            
            q_success.append([local_success, gpt_used])
            q_labels.append(f'Q{q_num}')
    
    if q_success:
        q_success = np.array(q_success)
        x = np.arange(len(q_labels))
        width = 0.35
        
        plt.bar(x - width/2, q_success[:, 0], width, label='Local NLP Success', 
                color='green', alpha=0.7, edgecolor='black')
        plt.bar(x + width/2, q_success[:, 1], width, label='GPT Fallback', 
                color='orange', alpha=0.7, edgecolor='black')
        
        plt.xlabel('Question', fontsize=12, fontweight='bold')
        plt.ylabel('Count', fontsize=12, fontweight='bold')
        plt.title('Local NLP Success vs GPT Fallback per Question', fontsize=14, fontweight='bold')
        plt.xticks(x, q_labels)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        fig4 = output_dir / "11_nlp_success_vs_gpt.png"
        plt.savefig(fig4, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {fig4.name}")
    
    print("\n✅ All GPT visualizations generated!")


def save_gpt_tables(df_gpt, df_interactions, output_dir):
    """Save GPT analysis tables"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # GPT usage by question
    gpt_by_question = df_interactions[
        (df_interactions['gptUsed'] == True) & 
        (df_interactions['phqQuestionId'].str.startswith('Q', na=False))
    ].groupby('phqQuestionId').size().to_frame(name='gpt_calls')
    
    gpt_file = output_dir / "gpt_usage_by_question.csv"
    gpt_by_question.to_csv(gpt_file)
    print(f"\n✓ Saved: {gpt_file}")
    
    # GPT reasons summary
    if 'gptReason' in df_interactions.columns:
        reasons_summary = df_interactions[df_interactions['gptUsed'] == True]['gptReason'].value_counts().to_frame(name='count')
        reasons_file = output_dir / "gpt_reasons_summary.csv"
        reasons_summary.to_csv(reasons_file)
        print(f"✓ Saved: {reasons_file}")


def main():
    """Main execution"""
    print("="*80)
    print("PHQ-9 VOICE SCREENING - GPT USAGE ANALYSIS")
    print("="*80)
    print()
    
    # Load data
    df_gpt, df_interactions = load_data()
    if df_gpt is None or df_interactions is None:
        return
    
    # Analyze GPT usage
    analyze_gpt_usage(df_gpt, df_interactions)
    
    # Create visualizations
    base_path = Path(__file__).parent.parent
    output_dir = base_path / "results" / "figures"
    create_gpt_visualizations(df_gpt, df_interactions, output_dir)
    
    # Save tables
    tables_dir = base_path / "results" / "tables"
    save_gpt_tables(df_gpt, df_interactions, tables_dir)
    
    print("\n" + "="*80)
    print("✅ GPT USAGE ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()

