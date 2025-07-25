"""
Custom exception classes for the Tender Document Analysis application.
These provide specific error types for better error handling and debugging.
"""


class DocumentProcessingError(TenderProcessingError):
    """Raised when there's an error processing the PDF document."""
    pass


class LLMAPIError(TenderProcessingError):
    """Raised when there's an error with the LLM API interaction."""
    pass


class InvalidConfigurationError(TenderProcessingError):
    """Raised when configuration is invalid or missing."""
    pass


class ParameterMatchingError(TenderProcessingError):
    """Raised when parameter matching fails."""
    pass


class OutputFormattingError(TenderProcessingError):
    """Raised when output formatting fails."""
    pass


class PageTaggingError(TenderProcessingError):
    """Raised when page tagging fails."""
    pass 