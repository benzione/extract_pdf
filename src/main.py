"""
Main module for the Tender Document Analysis application.
Refactored according to ONE company exercise requirements.
"""

import logging
import sys
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from .config_manager import ConfigManager
from .document_parser import DocumentParser
from .page_tagger import PageTagger
from .parameter_matcher import ParameterMatcher
from .prompt_builder import PromptBuilder
from .llm_interface import LLMInterface
from .output_formatter import OutputFormatter
from .utils import setup_logging, validate_pdf_file, get_file_size_mb
from .exceptions import (
    TenderProcessingError, InvalidConfigurationError, 
    DocumentProcessingError, LLMAPIError, OutputFormattingError
)


def load_data(pdf_file_path: str, parameters_json_path: str) -> tuple:
    """
    Load PDF document and parameters list.
    
    Args:
        pdf_file_path: Path to PDF file
        parameters_json_path: Path to parameters JSON file
        
    Returns:
        Tuple of (document_pages, parameters_list)
    """
    print(f"📄 Loading PDF document: {pdf_file_path}")
    
    # Initialize configuration and components
    config_manager = ConfigManager()
    document_parser = DocumentParser(config_manager)
    
    # Validate and load PDF
    if not validate_pdf_file(pdf_file_path):
        raise DocumentProcessingError(f"Invalid PDF file: {pdf_file_path}")
    
    file_size_mb = get_file_size_mb(pdf_file_path)
    print(f"   📊 File size: {file_size_mb:.1f} MB")
    
    # Parse PDF into pages
    pages = document_parser.parse_pdf(pdf_file_path)
    print(f"   📄 Extracted {len(pages)} pages")
    
    # Load parameters from JSON
    print(f"📋 Loading parameters: {parameters_json_path}")
    with open(parameters_json_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)
    print(f"   📋 Loaded {len(parameters)} parameters: {parameters}")
    
    return pages, parameters


def tag_pages(pages: List, config_manager: ConfigManager) -> List:
    """
    Tag pages by content type and parameter relevance.
    
    Args:
        pages: List of document pages
        config_manager: Configuration manager instance
        
    Returns:
        List of tagged pages
    """
    print(f"🏷️  Tagging {len(pages)} pages by content...")
    
    page_tagger = PageTagger(config_manager)
    tagged_pages = page_tagger.tag_pages(pages)
    
    # Print tagging summary
    tagging_summary = page_tagger.get_tagging_summary(tagged_pages)
    print(f"   🏷️  Tagged pages by type:")
    for page_type, count in tagging_summary.get('pages_by_type', {}).items():
        print(f"      - {page_type}: {count} pages")
    
    return tagged_pages


def match_parameters_to_pages(parameters: List[str], tagged_pages: List, 
                            config_manager: ConfigManager) -> Dict:
    """
    Match each parameter to relevant pages in the document.
    
    Args:
        parameters: List of parameter names
        tagged_pages: List of tagged document pages
        config_manager: Configuration manager instance
        
    Returns:
        Dictionary mapping parameters to matched pages
    """
    print(f"🎯 Matching {len(parameters)} parameters to relevant pages...")
    
    parameter_matcher = ParameterMatcher(config_manager)
    page_tagger = PageTagger(config_manager)
    
    # Match each parameter to pages
    parameter_matches = parameter_matcher.match_parameters_to_pages(
        parameters, tagged_pages, page_tagger
    )
    
    # Print matching summary
    print(f"   🎯 Parameter matching results:")
    for match in parameter_matches:
        if match.pages:
            page_nums = [p.page_number for p in match.pages]
            print(f"      - {match.parameter}: pages {page_nums} (confidence: {match.confidence:.2f})")
        else:
            print(f"      - {match.parameter}: no pages found (confidence: {match.confidence:.2f})")
    
    return parameter_matches


def build_prompts(parameter_matches: List, config_manager: ConfigManager) -> List[Dict]:
    """
    Build LLM prompts for parameter extraction.
    
    Args:
        parameter_matches: List of ParameterMatch objects
        config_manager: Configuration manager instance
        
    Returns:
        List of prompt dictionaries
    """
    print(f"🔨 Building prompts for {len(parameter_matches)} parameters...")
    
    prompt_builder = PromptBuilder(config_manager)
    prompts = prompt_builder.build_batch_prompts(parameter_matches)
    
    # Print prompt statistics
    prompt_stats = prompt_builder.get_prompt_statistics(prompts)
    print(f"   🔨 Built {len(prompts)} prompts")
    print(f"      - Total characters: {prompt_stats.get('total_chars', 0):,}")
    print(f"      - Average pages per prompt: {prompt_stats.get('avg_pages_per_prompt', 0):.1f}")
    
    return prompts


def extract_parameters_with_llm(prompts: List[Dict], config_manager: ConfigManager) -> List:
    """
    Extract parameters using LLM API calls.
    
    Args:
        prompts: List of prompt dictionaries
        config_manager: Configuration manager instance
        
    Returns:
        List of LLMResponse objects
    """
    print(f"🤖 Extracting parameters using LLM...")
    
    llm_interface = LLMInterface(config_manager)
    
    # Test API connection first
    print(f"   🔗 Testing API connection...")
    if not llm_interface.test_connection():
        raise LLMAPIError("API connection test failed")
    print(f"   ✅ API connection successful")
    
    # Extract parameters
    print(f"   🤖 Processing {len(prompts)} parameter extractions...")
    responses = llm_interface.extract_batch_parameters(prompts)
    
    # Print extraction summary
    found_count = sum(1 for r in responses if r.is_found)
    print(f"   ✅ Extraction complete: {found_count}/{len(responses)} parameters found")
    
    return responses


def format_and_save_results(responses: List, config_manager: ConfigManager) -> Dict[str, Any]:
    """
    Format results according to exercise requirements and save to files.
    
    Args:
        responses: List of LLMResponse objects
        config_manager: Configuration manager instance
        
        Returns:
        Formatted results dictionary
    """
    print(f"💾 Formatting and saving results...")
    
    output_formatter = OutputFormatter(config_manager)
    
    # Format results according to exercise specification
    results = output_formatter.format_results(responses)
    
    # Validate output format
    if not output_formatter.validate_output(results):
        raise OutputFormattingError("Output validation failed")
    
    # Save to files
    json_file = output_formatter.write_results_to_file(results)
    summary_file = output_formatter.write_summary_report(results)
    csv_file = output_formatter.write_csv_export(results)
    
    print(f"   💾 Results saved:")
    print(f"      - JSON: {json_file}")
    print(f"      - Summary: {summary_file}")
    print(f"      - CSV: {csv_file}")
    
    return results


def print_results_to_console(results: Dict[str, Any]):
    """
    Print results to console for immediate viewing.
    Handles Hebrew encoding issues as mentioned in exercise.
    
    Args:
        results: Formatted results dictionary
    """
    print(f"\n" + "="*60)
    print(f"📊 TENDER ANALYSIS RESULTS")
    print(f"="*60)
    
    total_params = len(results)
    found_params = len([r for r in results.values() if r.get('score', 0) > 0])
    
    print(f"\n📈 Summary:")
    print(f"   Total parameters: {total_params}")
    print(f"   Parameters found: {found_params}")
    print(f"   Success rate: {found_params/total_params:.1%}")
    
    print(f"\n📋 Detailed Results:")
    print(f"-" * 40)
    
    for param_name, data in results.items():
        param_display = param_name.replace('_', ' ').title()
        answer = data.get('answer', '')
        details = data.get('details', '')
        source = data.get('source', '')
        score = data.get('score', 0)
        
        print(f"\n🔍 {param_display}:")
        if score > 0 and answer:
            print(f"   ✅ Answer: {answer}")
            if details:
                print(f"   📝 Details: {details}")
            print(f"   📍 Source: {source}")
            print(f"   🎯 Score: {score}/5")
        else:
            print(f"   ❌ Answer: NOT FOUND")
            print(f"   📍 Source: לא נמצא")
            print(f"   🎯 Score: 0/5")


def main():
    """
    Main entry point - modular design as specified in exercise.
    """
    try:
        print("🚀 Tender Document Analysis - ONE Company Exercise")
        print("="*60)
        
        init_time = time.time()
        
        # Step 1: Load data
        print(f"\n📥 STEP 1: Loading Data")
        config_manager = ConfigManager()
        setup_logging(log_level="INFO", log_file=config_manager.get_log_path())
        
        pdf_path = config_manager.get_pdf_path()
        params_path = config_manager.get_parameters_path()
        
        pages, parameters = load_data(pdf_path, params_path)
        
        # Step 2: Tag pages
        print(f"\n🏷️  STEP 2: Page Content Tagging")
        tagged_pages = tag_pages(pages, config_manager)
        
        # Step 3: Match parameters to pages
        print(f"\n🎯 STEP 3: Parameter-Page Matching")
        parameter_matches = match_parameters_to_pages(parameters, tagged_pages, config_manager)
        
        # Step 4: Build prompts
        print(f"\n🔨 STEP 4: Prompt Building")
        prompts = build_prompts(parameter_matches, config_manager)
        
        # Step 5: Extract with LLM
        print(f"\n🤖 STEP 5: LLM Parameter Extraction")
        responses = extract_parameters_with_llm(prompts, config_manager)
        
        # Step 6: Format and save results
        print(f"\n💾 STEP 6: Results Formatting & Saving")
        results = format_and_save_results(responses, config_manager)
        
        # Step 7: Display results
        print(f"\n📊 STEP 7: Results Display")
        print_results_to_console(results)
        
        # Final summary
        total_time = time.time() - init_time
        print(f"\n⏱️  Processing completed in {total_time:.2f} seconds")
        print(f"🎉 Exercise completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"💡 Check log file for detailed error information")
        logging.error(f"Main execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 