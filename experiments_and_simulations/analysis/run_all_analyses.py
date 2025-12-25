"""
run_all_analyses.py
Master's Thesis Analysis - PHQ-9 Voice Screening System
Run all analysis scripts in sequence and generate summary report
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_script(script_name, description):
    """Run a Python script and report status"""
    print("\n" + "="*80)
    print(f"RUNNING: {description}")
    print("="*80)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,
            text=True,
            check=True
        )
        print(f"✅ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with error code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def generate_summary_report(output_dir):
    """Generate a summary report of all analyses"""
    report_file = output_dir / "ANALYSIS_SUMMARY_REPORT.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("PHQ-9 VOICE SCREENING SYSTEM - ANALYSIS SUMMARY\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        f.write("THESIS TITLE:\n")
        f.write("Design and Evaluation of a Health Screening Chatbot\n")
        f.write("for the Pepper Robot using GPT-based Natural Language Processing\n\n")
        
        f.write("="*80 + "\n")
        f.write("GENERATED OUTPUTS\n")
        f.write("="*80 + "\n\n")
        
        f.write("📊 TABLES (results/tables/):\n")
        tables = [
            "simulation_master.csv - Combined session metadata",
            "all_interaction_logs.csv - All interaction turns",
            "all_gpt_calls.csv - All GPT API calls",
            "descriptives_sessions.csv - Descriptive statistics by language",
            "per_question_means.csv - Mean scores per question",
            "gpt_usage_by_question.csv - GPT calls per question",
            "gpt_reasons_summary.csv - GPT usage reasons",
            "nlp_performance_by_question.csv - Local NLP success rates",
            "retry_statistics.csv - Retry patterns",
            "timing_statistics.csv - Duration statistics",
            "conversation_examples.txt - Example dialogues for thesis",
            "pipeline_error_summary.csv - Pipeline error and intervention summary"
        ]
        for table in tables:
            f.write(f"  • {table}\n")
        
        f.write("\n📈 FIGURES (results/figures/) - 20 visualizations:\n")
        figures = [
            "01_total_score_distribution.png",
            "02_scores_by_language.png",
            "03_duration_by_language.png",
            "04_gpt_usage_by_language.png",
            "05_retries_by_language.png",
            "06_severity_distribution.png",
            "07_per_question_heatmap.png",
            "08_gpt_calls_per_question.png",
            "09_gpt_reasons_distribution.png",
            "10_tokens_distribution.png",
            "11_nlp_success_vs_gpt.png",
            "12_nlp_success_heatmap.png",
            "13_retries_per_question.png",
            "14_nlp_success_by_language.png",
            "15_handling_module_distribution.png",
            "16_duration_distribution.png",
            "17_duration_vs_score.png",
            "18_turn_counts.png",
            "19_turns_per_question.png",
            "20_correlation_heatmap.png"
        ]
        for fig in figures:
            f.write(f"  • {fig}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("HOW TO USE THESE OUTPUTS IN YOUR THESIS\n")
        f.write("="*80 + "\n\n")
        
        f.write("METHODOLOGY SECTION:\n")
        f.write("  • Use conversation_examples.txt for dialogue examples\n")
        f.write("  • Reference simulation_master.csv for participant demographics\n")
        f.write("  • Include timing_statistics.csv for session duration info\n\n")
        
        f.write("RESULTS SECTION:\n")
        f.write("  • Figures 01-07: Descriptive statistics and distributions\n")
        f.write("  • Figures 08-11: GPT usage analysis\n")
        f.write("  • Figures 12-15: NLP performance metrics\n")
        f.write("  • Figures 16-20: Timing and correlation analysis\n")
        f.write("  • Import CSV tables for detailed statistics\n\n")
        
        f.write("DISCUSSION SECTION:\n")
        f.write("  • nlp_performance_by_question.csv - Identify difficult questions\n")
        f.write("  • gpt_usage_by_question.csv - Discuss when GPT is needed\n")
        f.write("  • correlation analysis (Figure 20) - Discuss relationships\n\n")
        
        f.write("APPENDIX:\n")
        f.write("  • All CSV tables\n")
        f.write("  • Selected high-resolution figures\n")
        f.write("  • Conversation examples\n\n")
        
        f.write("="*80 + "\n")
        f.write("ANALYSIS COMPLETE - ALL FILES READY FOR THESIS!\n")
        f.write("="*80 + "\n")
    
    return report_file


def main():
    """Main execution - run all analyses"""
    print("="*80)
    print("PHQ-9 VOICE SCREENING - COMPLETE ANALYSIS PIPELINE")
    print("="*80)
    print("Running all thesis analysis scripts...")
    print()
    
    base_path = Path(__file__).parent
    
    # Define analysis scripts in order
    scripts = [
        ("01_load_and_clean.py", "Data Loading and Cleaning"),
        ("02_descriptive_metrics.py", "Descriptive Statistics and Metrics"),
        ("03_gpt_usage_analysis.py", "GPT Usage Analysis"),
        ("04_local_nlp_performance.py", "Local NLP Performance Analysis"),
        ("05_timing_and_conversation_flow.py", "Timing and Conversation Flow Analysis"),
        ("06_pipeline_error_summary.py", "Pipeline Error and Intervention Summary")
    ]
    
    results = []
    
    # Run each script
    for script_name, description in scripts:
        script_path = base_path / script_name
        success = run_script(str(script_path), description)
        results.append((script_name, success))
    
    # Generate summary report
    print("\n" + "="*80)
    print("GENERATING SUMMARY REPORT")
    print("="*80)
    
    output_dir = base_path.parent / "results" / "tables"
    report_file = generate_summary_report(output_dir)
    print(f"\n✅ Summary report generated: {report_file}")
    
    # Final status
    print("\n" + "="*80)
    print("ANALYSIS PIPELINE COMPLETE")
    print("="*80)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nScripts completed: {successful}/{total}")
    for script_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {script_name}")
    
    if successful == total:
        print("\n🎉 All analyses completed successfully!")
        print("\n📁 Outputs:")
        print(f"   • Tables: {base_path.parent / 'results' / 'tables'}")
        print(f"   • Figures: {base_path.parent / 'results' / 'figures'}")
        print(f"   • Summary: {report_file}")
        print("\n✅ Ready for thesis writing!")
    else:
        print("\n⚠️  Some analyses failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

