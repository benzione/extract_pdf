"""
Utility functions for the Tender Document Analysis application.
Contains general-purpose helper functions for string processing and validation.
"""

import logging
import re
import unicodedata
from typing import List, Dict, Any, Optional


def normalize_string(text: str) -> str:
    """
    Normalize string for consistent processing.
    
    Args:
        text: Input string to normalize
        
    Returns:
        Normalized string
    """
    if not text:
        return ""
    
    # Unicode normalization
    text = unicodedata.normalize('NFKD', text)
    
    # Remove control characters
    text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_extracted_value(value: str) -> str:
    """
    Clean extracted values for consistency.
    
    Args:
        value: Raw extracted value
        
    Returns:
        Cleaned value
    """
    if not value or value == "NOT_FOUND":
        return value
    
    # Normalize the string
    cleaned = normalize_string(value)
    
    # Remove common prefixes/suffixes that might be extracted by mistake
    prefixes_to_remove = [
        "answer:", "result:", "value:", "the", "a", "an",
        "extracted:", "found:", "parameter:", "is:"
    ]
    
    for prefix in prefixes_to_remove:
        pattern = rf'^{re.escape(prefix)}\s*'
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove trailing punctuation that's not part of the value
    cleaned = re.sub(r'[.,:;]\s*$', '', cleaned)
    
    # Final whitespace cleanup
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Ensure log directory exists
            import os
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            
            logging.info(f"Logging to file: {log_file}")
        except Exception as e:
            logging.warning(f"Could not setup file logging: {e}")


def validate_pdf_file(file_path: str) -> bool:
    """
    Validate if file is a valid PDF.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        True if valid PDF, False otherwise
    """
    import os
    
    if not os.path.exists(file_path):
        return False
    
    if not file_path.lower().endswith('.pdf'):
        return False
    
    # Check file size (should be > 0)
    if os.path.getsize(file_path) == 0:
        return False
    
    # Check PDF magic bytes
    try:
        with open(file_path, 'rb') as file:
            header = file.read(4)
            return header == b'%PDF'
    except Exception:
        return False


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    import os
    
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0 