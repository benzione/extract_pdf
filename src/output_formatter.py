"""
Output formatting module for the Tender Document Analysis application.
Handles formatting and writing of extraction results to JSON files.
"""

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from .llm_interface import LLMResponse
from .exceptions import OutputFormattingError


class OutputFormatter:
    """Handles formatting and writing of extraction results."""
    
    def __init__(self, config_manager):
        """
        Initialize output formatter.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def format_results(self, responses: List[LLMResponse], 
                      document_summary: Dict[str, Any] = None,
                      processing_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format extraction results into simplified output structure.
        
        Args:
            responses: List of LLM responses
            document_summary: Summary of document processing
            processing_stats: Statistics about the processing
            
        Returns:
            Formatted results dictionary with simplified structure
        """
        try:
            self.logger.info("Formatting extraction results")
            
            # Create simplified result structure
            result = {}
            
            for response in responses:
                result[response.parameter] = {
                    "answer": response.extracted_value if response.is_found else "",
                    "details": response.details if response.is_found else "",
                    "source": self._generate_source(response),
                    "score": self._convert_confidence_to_score(response.confidence)
                }
            
            self.logger.info("Results formatted successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to format results: {e}", exc_info=True)
            raise OutputFormattingError(f"Failed to format results: {e}")
    
    def _generate_source(self, response: LLMResponse) -> str:
        """Generate source text with actual page numbers in Hebrew."""
        if not response.is_found or not response.page_numbers:
            return "לא נמצא"
        
        # Sort page numbers and format in Hebrew
        sorted_pages = sorted(response.page_numbers)
        
        if len(sorted_pages) == 1:
            return f"עמוד {sorted_pages[0]}"
        elif len(sorted_pages) == 2:
            return f"עמוד {sorted_pages[0]}, עמוד {sorted_pages[1]}"
        else:
            # For multiple pages, format as "עמוד X, עמוד Y, עמוד Z"
            page_strings = [f"עמוד {page}" for page in sorted_pages]
            return ", ".join(page_strings)
    
    def _convert_confidence_to_score(self, confidence: float) -> int:
        """
        Convert confidence score (0.0-1.0) to integer score (0-5).
        
        Args:
            confidence: Confidence value between 0.0 and 1.0
            
        Returns:
            Integer score between 0 and 5
        """
        if confidence >= 0.9:
            return 5
        elif confidence >= 0.8:
            return 4
        elif confidence >= 0.6:
            return 3
        elif confidence >= 0.4:
            return 2
        elif confidence >= 0.2:
            return 1
        else:
            return 0
    
    def write_results_to_file(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Write results to JSON file.
        
        Args:
            results: Formatted results dictionary
            filename: Optional custom filename
            
        Returns:
            Path to the written file
            
        Raises:
            OutputFormattingError: If writing fails
        """
        try:
            # Ensure output directory exists
            output_dir = self.config_manager.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tender_analysis_results_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            file_path = os.path.join(output_dir, filename)
            
            # Write results to file with proper encoding for Hebrew text
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(results, file, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results written to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to write results to file: {e}", exc_info=True)
            raise OutputFormattingError(f"Failed to write results: {e}")
    
    def create_summary_report(self, results: Dict[str, Any]) -> str:
        """
        Create a human-readable summary report.
        
        Args:
            results: Formatted results dictionary
            
        Returns:
            Summary report as string
        """
        try:
            lines = []
            lines.append("=" * 60)
            lines.append("TENDER DOCUMENT ANALYSIS REPORT")
            lines.append("=" * 60)
            lines.append("")
            
            # Add timestamp
            lines.append(f"Generated: {datetime.now().isoformat()}")
            lines.append("")
            
            # Extraction Results
            lines.append("EXTRACTION RESULTS:")
            lines.append("-" * 20)
            
            for parameter, data in results.items():
                param_name = parameter.replace('_', ' ').title()
                score = data.get('score', 0)
                answer = data.get('answer', '')
                details = data.get('details', '')
                source = data.get('source', '')
                
                if score > 0 and answer:
                    lines.append(f"{param_name}: {answer}")
                    if details:
                        lines.append(f"  Details: {details}")
                    lines.append(f"  Source: {source} (Score: {score}/5)")
                else:
                    lines.append(f"{param_name}: NOT FOUND (Score: 0/5)")
                lines.append("")
            
            # Summary statistics
            total_params = len(results)
            found_params = len([r for r in results.values() if r.get('score', 0) > 0])
            avg_score = sum(r.get('score', 0) for r in results.values()) / total_params if total_params > 0 else 0
            
            lines.append("SUMMARY:")
            lines.append("-" * 20)
            lines.append(f"Total parameters: {total_params}")
            lines.append(f"Parameters found: {found_params}")
            lines.append(f"Success rate: {found_params/total_params:.1%}")
            lines.append(f"Average score: {avg_score:.1f}/5")
            
            lines.append("")
            lines.append("=" * 60)
            
            report = "\n".join(lines)
            self.logger.debug("Summary report created")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to create summary report: {e}", exc_info=True)
            return f"Error creating summary report: {e}"
    
    def write_summary_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Write summary report to text file.
        
        Args:
            results: Formatted results dictionary
            filename: Optional custom filename
            
        Returns:
            Path to the written report file
        """
        try:
            # Generate summary report
            report = self.create_summary_report(results)
            
            # Ensure output directory exists
            output_dir = self.config_manager.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tender_analysis_summary_{timestamp}.txt"
            
            # Ensure .txt extension
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            file_path = os.path.join(output_dir, filename)
            
            # Write report to file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(report)
            
            self.logger.info(f"Summary report written to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to write summary report: {e}", exc_info=True)
            raise OutputFormattingError(f"Failed to write summary report: {e}")
    
    def create_csv_export(self, results: Dict[str, Any]) -> str:
        """
        Create CSV export of extraction results.
        
        Args:
            results: Formatted results dictionary
            
        Returns:
            CSV content as string
        """
        try:
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Parameter', 'Answer', 'Details', 'Source', 'Score'])
            
            # Write data
            for parameter, data in results.items():
                writer.writerow([
                    parameter.replace('_', ' ').title(),
                    data.get('answer', ''),
                    data.get('details', ''),
                    data.get('source', ''),
                    data.get('score', 0)
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            self.logger.debug("CSV export created")
            return csv_content
            
        except Exception as e:
            self.logger.error(f"Failed to create CSV export: {e}", exc_info=True)
            return f"Error creating CSV export: {e}"
    
    def write_csv_export(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Write CSV export to file.
        
        Args:
            results: Formatted results dictionary
            filename: Optional custom filename
            
        Returns:
            Path to the written CSV file
        """
        try:
            # Generate CSV content
            csv_content = self.create_csv_export(results)
            
            # Ensure output directory exists
            output_dir = self.config_manager.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tender_analysis_export_{timestamp}.csv"
            
            # Ensure .csv extension
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            file_path = os.path.join(output_dir, filename)
            
            # Write CSV to file
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                file.write(csv_content)
            
            self.logger.info(f"CSV export written to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to write CSV export: {e}", exc_info=True)
            raise OutputFormattingError(f"Failed to write CSV export: {e}")
    
    def validate_output(self, results: Dict[str, Any]) -> bool:
        """
        Validate the output format and content.
        
        Args:
            results: Results dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check that results is a dictionary
            if not isinstance(results, dict):
                self.logger.error("Results must be a dictionary")
                return False
            
            # Validate each parameter entry
            for param, data in results.items():
                if not isinstance(data, dict):
                    self.logger.error(f"Parameter {param} data must be a dictionary")
                    return False
                
                required_fields = ['answer', 'details', 'source', 'score']
                for field in required_fields:
                    if field not in data:
                        self.logger.error(f"Missing field {field} in parameter {param}")
                        return False
                
                # Validate score is integer between 0-5
                score = data.get('score')
                if not isinstance(score, int) or score < 0 or score > 5:
                    self.logger.error(f"Score for {param} must be integer between 0-5, got: {score}")
                    return False
            
            self.logger.info("Output validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Output validation failed: {e}", exc_info=True)
            return False 