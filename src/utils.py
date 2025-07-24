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


def validate_parameter_name(parameter: str) -> bool:
    """
    Validate parameter name format.
    
    Args:
        parameter: Parameter name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not parameter:
        return False
    
    # Check if parameter contains only allowed characters
    pattern = r'^[a-z][a-z0-9_]*$'
    return bool(re.match(pattern, parameter))


def format_confidence_score(confidence: float) -> str:
    """
    Format confidence score for display.
    
    Args:
        confidence: Confidence value (0.0-1.0)
        
    Returns:
        Formatted confidence string
    """
    if not isinstance(confidence, (int, float)):
        return "Unknown"
    
    if confidence < 0 or confidence > 1:
        return "Invalid"
    
    percentage = confidence * 100
    if percentage >= 90:
        return f"{percentage:.1f}% (High)"
    elif percentage >= 70:
        return f"{percentage:.1f}% (Medium)"
    elif percentage >= 50:
        return f"{percentage:.1f}% (Moderate)"
    else:
        return f"{percentage:.1f}% (Low)"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_filename(filename: str) -> str:
    """
    Create safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed_file"
    
    # Remove or replace invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    safe_name = ''.join(char for char in safe_name if ord(char) >= 32)
    
    # Ensure it doesn't start with dot or space
    safe_name = safe_name.lstrip('. ')
    
    # Limit length
    safe_name = safe_name[:255]
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name


def parse_time_duration(duration_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse duration text into structured format.
    
    Args:
        duration_text: Text containing duration information
        
    Returns:
        Dictionary with parsed duration or None
    """
    if not duration_text:
        return None
    
    duration_text = duration_text.lower().strip()
    
    # Common duration patterns
    patterns = [
        (r'(\d+)\s*years?', 'years'),
        (r'(\d+)\s*months?', 'months'),
        (r'(\d+)\s*weeks?', 'weeks'),
        (r'(\d+)\s*days?', 'days'),
    ]
    
    result = {}
    
    for pattern, unit in patterns:
        match = re.search(pattern, duration_text)
        if match:
            result[unit] = int(match.group(1))
    
    # Try to find date ranges
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|until|through|-)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    date_match = re.search(date_pattern, duration_text)
    
    if date_match:
        result['start_date'] = date_match.group(1)
        result['end_date'] = date_match.group(2)
    
    return result if result else None


def extract_monetary_values(text: str) -> List[Dict[str, Any]]:
    """
    Extract monetary values from text.
    
    Args:
        text: Text containing monetary values
        
    Returns:
        List of monetary value dictionaries
    """
    if not text:
        return []
    
    monetary_values = []
    
    # Currency patterns (USD, EUR, etc.)
    currency_patterns = [
        r'\$\s*([\d,]+(?:\.\d{2})?)',  # $1,000.00
        r'([\d,]+(?:\.\d{2})?)\s*USD',  # 1000.00 USD
        r'([\d,]+(?:\.\d{2})?)\s*dollars?',  # 1000 dollars
        r'€\s*([\d,]+(?:\.\d{2})?)',  # €1,000.00
        r'([\d,]+(?:\.\d{2})?)\s*EUR',  # 1000.00 EUR
    ]
    
    for pattern in currency_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1).replace(',', '')
            try:
                value = float(value_str)
                monetary_values.append({
                    'value': value,
                    'original_text': match.group(0),
                    'position': match.span()
                })
            except ValueError:
                continue
    
    return monetary_values


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0-1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    text1 = normalize_string(text1.lower())
    text2 = normalize_string(text2.lower())
    
    # Simple word-based similarity
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


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