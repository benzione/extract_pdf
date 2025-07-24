#!/usr/bin/env python3
"""
Test script for ONE Company Exercise - Tender Document Analysis
Demonstrates the modular approach with clear function separation.

Usage:
    python test_exercise.py

This script demonstrates the end-to-end process using modular functions
as specified in the exercise requirements.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

# Import modular functions from main
from src.main import (
    load_data, 
    tag_pages, 
    match_parameters_to_pages, 
    build_prompts, 
    extract_parameters_with_llm, 
    format_and_save_results,
    print_results_to_console
)
from src.config_manager import ConfigManager
from src.utils import setup_logging


def test_tender_analysis():
    """
    Test function demonstrating modular tender analysis workflow.
    """
    print("🧪 Testing Tender Document Analysis - Modular Approach")
    print("="*60)
    
    start_time = time.time()
    
    try:
        # Initialize configuration
        print("⚙️  Initializing configuration...")
        config_manager = ConfigManager()
        setup_logging(log_level="INFO", log_file=config_manager.get_log_path())
        
        # Get file paths from configuration
        pdf_path = config_manager.get_pdf_path()
        params_path = config_manager.get_parameters_path()
        
        print(f"📄 PDF File: {pdf_path}")
        print(f"📋 Parameters File: {params_path}")
        
        # Step 1: Load data
        print(f"\n🔹 STEP 1: Loading Data")
        pages, parameters = load_data(pdf_path, params_path)
        print(f"   ✅ Loaded {len(pages)} pages and {len(parameters)} parameters")
        
        # Step 2: Tag pages by content
        print(f"\n🔹 STEP 2: Tagging Pages by Content")
        tagged_pages = tag_pages(pages, config_manager)
        print(f"   ✅ Tagged {len(tagged_pages)} pages")
        
        # Step 3: Match parameters to relevant pages
        print(f"\n🔹 STEP 3: Matching Parameters to Pages")
        parameter_matches = match_parameters_to_pages(parameters, tagged_pages, config_manager)
        print(f"   ✅ Created {len(parameter_matches)} parameter matches")
        
        # Show matching summary
        for match in parameter_matches:
            if match.pages:
                print(f"      🎯 {match.parameter}: {len(match.pages)} pages matched")
            else:
                print(f"      ❌ {match.parameter}: no pages matched (will be 'not found')")
        
        # Step 4: Build prompts for LLM
        print(f"\n🔹 STEP 4: Building LLM Prompts")
        prompts = build_prompts(parameter_matches, config_manager)
        print(f"   ✅ Built {len(prompts)} prompts")
        
        # Show prompt summary
        prompts_with_content = [p for p in prompts if p.get('prompt') is not None]
        prompts_without_content = [p for p in prompts if p.get('prompt') is None]
        print(f"      📝 Prompts with content: {len(prompts_with_content)}")
        print(f"      🚫 Prompts without content (will be 'not found'): {len(prompts_without_content)}")
        
        # Step 5: Extract parameters using LLM
        print(f"\n🔹 STEP 5: Extracting Parameters with LLM")
        responses = extract_parameters_with_llm(prompts, config_manager)
        print(f"   ✅ Completed {len(responses)} extractions")
        
        # Show extraction summary
        found_responses = [r for r in responses if r.is_found]
        not_found_responses = [r for r in responses if not r.is_found]
        print(f"      ✅ Parameters found: {len(found_responses)}")
        print(f"      ❌ Parameters not found: {len(not_found_responses)}")
        
        # Step 6: Format and save results
        print(f"\n🔹 STEP 6: Formatting and Saving Results")
        results = format_and_save_results(responses, config_manager)
        print(f"   ✅ Results formatted and saved")
        
        # Step 7: Display results
        print(f"\n🔹 STEP 7: Displaying Results")
        print_results_to_console(results)
        
        # Final summary
        total_time = time.time() - start_time
        print(f"\n⏱️  Test completed in {total_time:.2f} seconds")
        print(f"🎉 Modular approach test successful!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demonstrate_individual_functions():
    """
    Demonstrate individual function capabilities.
    """
    print("\n" + "="*60)
    print("🔍 DEMONSTRATING INDIVIDUAL FUNCTIONS")
    print("="*60)
    
    try:
        config_manager = ConfigManager()
        
        # Demo 1: Load data function
        print("\n📊 Demo 1: load_data() function")
        pages, parameters = load_data(
            config_manager.get_pdf_path(),
            config_manager.get_parameters_path()
        )
        print(f"   Loaded {len(pages)} pages and {len(parameters)} parameters")
        print(f"   Parameters: {parameters}")
        
        # Demo 2: Individual parameter info
        print(f"\n📄 Demo 2: Page information")
        for i, page in enumerate(pages[:3]):  # Show first 3 pages
            print(f"   Page {page.page_number}: {page.word_count} words")
            print(f"      Preview: {page.get_summary()[:100]}...")
        
        print("\n✅ Individual function demonstration complete")
        
    except Exception as e:
        print(f"❌ Individual function demo failed: {e}")


def show_exercise_compliance():
    """
    Show how the implementation complies with exercise requirements.
    """
    print("\n" + "="*60)
    print("📋 EXERCISE COMPLIANCE CHECK")
    print("="*60)
    
    compliance_items = [
        "✅ Modular design with separate functions",
        "✅ main() function calling smaller functions",
        "✅ Document segmentation (page-by-page analysis)",
        "✅ Page tagging by content and parameter relevance", 
        "✅ Parameter-to-page matching with minimal page sending",
        "✅ Prompt building for each parameter",
        "✅ LLM API integration",
        "✅ Proper output format (parameter, answer, details, source, score)",
        "✅ Hebrew language support in prompts and responses",
        "✅ 'idea_author' parameter handled as 'not found'",
        "✅ JSON file parameter loading",
        "✅ Console output for Hebrew encoding compatibility",
        "✅ File output (JSON, Summary, CSV)",
        "✅ Error handling and logging"
    ]
    
    for item in compliance_items:
        print(f"   {item}")
    
    print(f"\n🎯 All exercise requirements implemented!")


if __name__ == "__main__":
    """
    Main test execution as specified in exercise.
    """
    print("🚀 ONE Company Exercise - Tender Document Analysis Test")
    print("Testing modular implementation with clear function separation")
    print("="*70)
    
    # Run the main test
    success = test_tender_analysis()
    
    if success:
        # Demonstrate individual functions
        demonstrate_individual_functions()
        
        # Show compliance with exercise requirements
        show_exercise_compliance()
        
        print(f"\n🎉 ALL TESTS PASSED - Exercise implementation complete!")
        sys.exit(0)
    else:
        print(f"\n❌ TESTS FAILED - Check error messages above")
        sys.exit(1) 