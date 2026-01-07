

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
TABLES_DIR = BASE_DIR / "analysis_tables"
FIGURES_DIR = BASE_DIR / "analysis_figures"


def load_data():
    """Load all required datasets"""
    logs = pd.read_csv(TABLES_DIR / "all_interaction_logs.csv")
    gpt_calls = pd.read_csv(TABLES_DIR / "all_gpt_calls.csv")
    master = pd.read_csv(TABLES_DIR / "simulation_master.csv")
    
    print(f"Loaded {len(logs)} interaction log entries")
    print(f"Loaded {len(gpt_calls)} GPT API calls")
    print(f"Loaded {len(master)} sessions from master")
    
    return logs, gpt_calls, master


def get_final_answers(logs):
    """Extract only FINAL answers (accepted responses for each question)"""
    final_answers = logs[
        logs['notes'].str.contains('FINAL|FINALE', na=False, regex=True)
    ].copy()
    
    # Add language column based on question ID prefix
    final_answers['language'] = final_answers['phqQuestionId'].apply(
        lambda x: 'EN' if str(x).startswith('Q') else 'DE' if str(x).startswith('F') else 'unknown'
    )
    
    # Normalize question number (Q7 and F7 both become 7)
    final_answers['question_num'] = final_answers['phqQuestionId'].str.extract(r'[QF](\d)').astype(int)
    
    return final_answers


def analyze_nlp_performance(final_answers):
    """Analyze NLP performance on FINAL answers"""
    print("\n" + "=" * 70)
    print("NLP PERFORMANCE ANALYSIS (FINAL ANSWERS ONLY)")
    print("=" * 70)
    
    # Overall
    total = len(final_answers)
    local_success = len(final_answers[final_answers['handlingModule'] == 'PEPPER_LOCAL'])
    gpt_fallback = len(final_answers[final_answers['handlingModule'] == 'GPT_FALLBACK'])
    
    print(f"\nOverall ({total} FINAL answers):")
    print(f"  Local NLP success: {local_success} ({100*local_success/total:.1f}%)")
    print(f"  GPT fallback: {gpt_fallback} ({100*gpt_fallback/total:.1f}%)")
    
    # By language
    for lang in ['EN', 'DE']:
        lang_data = final_answers[final_answers['language'] == lang]
        lang_total = len(lang_data)
        lang_local = len(lang_data[lang_data['handlingModule'] == 'PEPPER_LOCAL'])
        lang_gpt = len(lang_data[lang_data['handlingModule'] == 'GPT_FALLBACK'])
        
        lang_name = "English" if lang == 'EN' else "German"
        print(f"\n{lang_name} ({lang_total} FINAL answers):")
        print(f"  Local NLP success: {lang_local} ({100*lang_local/lang_total:.1f}%)")
        print(f"  GPT fallback: {lang_gpt} ({100*lang_gpt/lang_total:.1f}%)")
    
    return {
        'total': total,
        'local_success': local_success,
        'gpt_fallback': gpt_fallback,
        'success_rate': 100 * local_success / total
    }


def generate_nlp_tables(final_answers, output_dir):
    """Generate NLP performance tables"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("GENERATING NLP PERFORMANCE TABLES")
    print("=" * 70)
    
    # 1. Performance by question (combined)
    perf_by_q = []
    for q_num in range(1, 10):
        # Get both Q and F versions
        q_data = final_answers[final_answers['question_num'] == q_num]
        total = len(q_data)
        local = len(q_data[q_data['handlingModule'] == 'PEPPER_LOCAL'])
        gpt = len(q_data[q_data['handlingModule'] == 'GPT_FALLBACK'])
        
        # Get EN and DE separately
        en_data = q_data[q_data['language'] == 'EN']
        de_data = q_data[q_data['language'] == 'DE']
        en_local = len(en_data[en_data['handlingModule'] == 'PEPPER_LOCAL'])
        de_local = len(de_data[de_data['handlingModule'] == 'PEPPER_LOCAL'])
        en_gpt = len(en_data[en_data['handlingModule'] == 'GPT_FALLBACK'])
        de_gpt = len(de_data[de_data['handlingModule'] == 'GPT_FALLBACK'])
        
        perf_by_q.append({
            'question': q_num,
            'total': total,
            'local_success': local,
            'gpt_fallback': gpt,
            'success_rate': 100 * local / total if total > 0 else 0,
            'en_local': en_local,
            'en_gpt': en_gpt,
            'de_local': de_local,
            'de_gpt': de_gpt
        })
    
    perf_df = pd.DataFrame(perf_by_q)
    perf_file = output_dir / "nlp_performance_by_question_bilingual.csv"
    perf_df.to_csv(perf_file, index=False)
    print(f"Saved: {perf_file.name}")
    
    # 2. Performance by language
    lang_perf = []
    for lang in ['EN', 'DE']:
        lang_data = final_answers[final_answers['language'] == lang]
        total = len(lang_data)
        local = len(lang_data[lang_data['handlingModule'] == 'PEPPER_LOCAL'])
        gpt = len(lang_data[lang_data['handlingModule'] == 'GPT_FALLBACK'])
        
        lang_perf.append({
            'language': lang,
            'total_answers': total,
            'local_success': local,
            'gpt_fallback': gpt,
            'success_rate': 100 * local / total if total > 0 else 0
        })
    
    # Add combined row
    total = len(final_answers)
    local = len(final_answers[final_answers['handlingModule'] == 'PEPPER_LOCAL'])
    gpt = len(final_answers[final_answers['handlingModule'] == 'GPT_FALLBACK'])
    lang_perf.append({
        'language': 'TOTAL',
        'total_answers': total,
        'local_success': local,
        'gpt_fallback': gpt,
        'success_rate': 100 * local / total
    })
    
    lang_df = pd.DataFrame(lang_perf)
    lang_file = output_dir / "nlp_performance_by_language.csv"
    lang_df.to_csv(lang_file, index=False)
    print(f"Saved: {lang_file.name}")
    
    return perf_df, lang_df


def generate_nlp_figures(final_answers, output_dir):
    """Generate NLP performance visualizations"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("GENERATING NLP PERFORMANCE FIGURES")
    print("=" * 70)
    
    # 1. Overall NLP vs GPT pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    local = len(final_answers[final_answers['handlingModule'] == 'PEPPER_LOCAL'])
    gpt = len(final_answers[final_answers['handlingModule'] == 'GPT_FALLBACK'])
    
    colors = ['#2ecc71', '#e74c3c']
    ax.pie([local, gpt], labels=[f'Local NLP\n({local}, {100*local/len(final_answers):.1f}%)',
                                  f'GPT Fallback\n({gpt}, {100*gpt/len(final_answers):.1f}%)'],
           colors=colors, autopct='', startangle=90, explode=(0.02, 0.02))
    ax.set_title('Response Handling Distribution\n(N=90 FINAL Answers, Both Languages)', fontweight='bold')
    
    fig1 = output_dir / "nlp_vs_gpt_bilingual.png"
    plt.savefig(fig1, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig1.name}")
    
    # 2. By language comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    languages = ['English', 'German', 'Combined']
    en_data = final_answers[final_answers['language'] == 'EN']
    de_data = final_answers[final_answers['language'] == 'DE']
    
    local_counts = [
        len(en_data[en_data['handlingModule'] == 'PEPPER_LOCAL']),
        len(de_data[de_data['handlingModule'] == 'PEPPER_LOCAL']),
        len(final_answers[final_answers['handlingModule'] == 'PEPPER_LOCAL'])
    ]
    gpt_counts = [
        len(en_data[en_data['handlingModule'] == 'GPT_FALLBACK']),
        len(de_data[de_data['handlingModule'] == 'GPT_FALLBACK']),
        len(final_answers[final_answers['handlingModule'] == 'GPT_FALLBACK'])
    ]
    
    x = range(len(languages))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], local_counts, width, label='Local NLP', color='#2ecc71')
    bars2 = ax.bar([i + width/2 for i in x], gpt_counts, width, label='GPT Fallback', color='#e74c3c')
    
    ax.set_ylabel('Number of FINAL Answers', fontweight='bold')
    ax.set_xlabel('Language', fontweight='bold')
    ax.set_title('NLP Performance by Language\n(FINAL Answers Only)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(languages)
    ax.legend()
    
    # Add value labels
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(int(bar.get_height())), ha='center', va='bottom')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(int(bar.get_height())), ha='center', va='bottom')
    
    plt.tight_layout()
    fig2 = output_dir / "nlp_by_language_comparison.png"
    plt.savefig(fig2, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig2.name}")
    
    # 3. Success rate by question (heatmap)
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create matrix: questions x languages
    questions = list(range(1, 10))
    matrix = []
    
    for q in questions:
        row = []
        for lang in ['EN', 'DE']:
            q_data = final_answers[(final_answers['question_num'] == q) & (final_answers['language'] == lang)]
            if len(q_data) > 0:
                success_rate = 100 * len(q_data[q_data['handlingModule'] == 'PEPPER_LOCAL']) / len(q_data)
            else:
                success_rate = 0
            row.append(success_rate)
        matrix.append(row)
    
    matrix_df = pd.DataFrame(matrix, index=[f'Q{q}' for q in questions], columns=['English', 'German'])
    
    sns.heatmap(matrix_df, annot=True, fmt='.0f', cmap='RdYlGn', vmin=0, vmax=100,
                cbar_kws={'label': 'Local NLP Success Rate (%)'}, ax=ax)
    ax.set_title('Local NLP Success Rate by Question and Language\n(FINAL Answers)', fontweight='bold')
    ax.set_xlabel('Language', fontweight='bold')
    ax.set_ylabel('PHQ-9 Question', fontweight='bold')
    
    plt.tight_layout()
    fig3 = output_dir / "nlp_success_heatmap_bilingual.png"
    plt.savefig(fig3, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig3.name}")
    
    # 4. GPT fallback by question (stacked bar)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    questions = [f'Q{i}' for i in range(1, 10)]
    en_gpt = []
    de_gpt = []
    
    for q in range(1, 10):
        en_data = final_answers[(final_answers['question_num'] == q) & (final_answers['language'] == 'EN')]
        de_data = final_answers[(final_answers['question_num'] == q) & (final_answers['language'] == 'DE')]
        en_gpt.append(len(en_data[en_data['handlingModule'] == 'GPT_FALLBACK']))
        de_gpt.append(len(de_data[de_data['handlingModule'] == 'GPT_FALLBACK']))
    
    x = range(len(questions))
    ax.bar(x, en_gpt, label='English', color='#3498db')
    ax.bar(x, de_gpt, bottom=en_gpt, label='German', color='#e67e22')
    
    ax.set_ylabel('GPT Fallback Count', fontweight='bold')
    ax.set_xlabel('PHQ-9 Question', fontweight='bold')
    ax.set_title('GPT Fallback Distribution by Question\n(Both Languages, N=29 total)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(questions)
    ax.legend()
    
    plt.tight_layout()
    fig4 = output_dir / "gpt_fallback_by_question_bilingual.png"
    plt.savefig(fig4, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig4.name}")


def update_definitive_numbers(final_answers, output_dir):
    """Update the definitive thesis numbers file"""
    
    en_data = final_answers[final_answers['language'] == 'EN']
    de_data = final_answers[final_answers['language'] == 'DE']
    
    en_local = len(en_data[en_data['handlingModule'] == 'PEPPER_LOCAL'])
    en_gpt = len(en_data[en_data['handlingModule'] == 'GPT_FALLBACK'])
    de_local = len(de_data[de_data['handlingModule'] == 'PEPPER_LOCAL'])
    de_gpt = len(de_data[de_data['handlingModule'] == 'GPT_FALLBACK'])
    
    total_local = en_local + de_local
    total_gpt = en_gpt + de_gpt
    
    content = f"""DEFINITIVE THESIS NUMBERS - BILINGUAL ANALYSIS
================================================================================
Generated: December 2025
Methodology: FINAL answers only (accepted response per question)
================================================================================

=== SESSION OVERVIEW ===
total_sessions: 10
en_sessions: 5
de_sessions: 5
questions_per_session: 9
total_final_answers: 90

=== NLP PERFORMANCE (FINAL ANSWERS) ===
# English (Q1-Q9)
en_final_answers: {len(en_data)}
en_local_success: {en_local}
en_gpt_fallback: {en_gpt}
en_success_rate: {100*en_local/len(en_data):.1f}%

# German (F1-F9)
de_final_answers: {len(de_data)}
de_local_success: {de_local}
de_gpt_fallback: {de_gpt}
de_success_rate: {100*de_local/len(de_data):.1f}%

# Combined (Both Languages)
total_final_answers: {len(final_answers)}
total_local_success: {total_local}
total_gpt_fallback: {total_gpt}
total_success_rate: {100*total_local/len(final_answers):.1f}%

=== GPT API CALLS ===
total_gpt_api_calls: 38
# Note: 38 total API calls includes retries during conversation
# 29 unique FINAL answers required GPT fallback

=== KEY CLARIFICATION ===
These numbers are based on FINAL answers only (the accepted answer for each 
question in each session). This differs from earlier analysis that counted
all interaction turns including retry attempts.

Previous (incorrect) English-only counts: 73/90 local, 17/90 GPT (81.1%)
Corrected bilingual counts: 61/90 local, 29/90 GPT (67.8%)
"""
    
    output_file = output_dir / "DEFINITIVE_THESIS_NUMBERS_CORRECTED.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\nSaved: {output_file.name}")


def main():
    """Main execution"""
    print("=" * 70)
    print("BILINGUAL ANALYSIS - CORRECTED")
    print("PHQ-9 Voice Screening System")
    print("=" * 70)
    
    # Load data
    logs, gpt_calls, master = load_data()
    
    # Get FINAL answers only
    final_answers = get_final_answers(logs)
    print(f"\nExtracted {len(final_answers)} FINAL answers")
    
    # Analyze performance
    stats = analyze_nlp_performance(final_answers)
    
    # Generate tables
    perf_df, lang_df = generate_nlp_tables(final_answers, TABLES_DIR)
    
    # Generate figures
    generate_nlp_figures(final_answers, FIGURES_DIR)
    
    # Update definitive numbers
    update_definitive_numbers(final_answers, TABLES_DIR)
    
    print("\n" + "=" * 70)
    print("BILINGUAL ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nKey findings:")
    print(f"  Total FINAL answers: {stats['total']}")
    print(f"  Local NLP success: {stats['local_success']} ({stats['success_rate']:.1f}%)")
    print(f"  GPT fallback: {stats['gpt_fallback']} ({100-stats['success_rate']:.1f}%)")
    
    return final_answers, perf_df, lang_df


if __name__ == "__main__":
    final_answers, perf_df, lang_df = main()
