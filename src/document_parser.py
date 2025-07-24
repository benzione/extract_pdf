"""
Document parsing module for the Tender Document Analysis application.
Handles PDF loading and page segmentation for processing very long documents.
"""

import logging
import re
from typing import List, Dict, Any
import PyPDF2
import fitz  # PyMuPDF for better text extraction
from .exceptions import DocumentProcessingError


class DocumentPage:
    """Represents a single page from the document."""
    
    def __init__(self, page_number: int, content: str, metadata: Dict[str, Any] = None):
        """
        Initialize a document page.
        
        Args:
            page_number: The page number (1-indexed)
            content: The text content of the page
            metadata: Additional metadata about the page
        """
        self.page_number = page_number
        self.content = content
        self.metadata = metadata or {}
        self.cleaned_content = self._clean_content(content)
        self.word_count = len(self.cleaned_content.split())
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize page content."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove page headers/footers patterns
        content = re.sub(r'Page \d+ of \d+', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\d+/\d+', '', content)
        
        # Clean up common PDF artifacts
        content = re.sub(r'[^\w\s\-.,;:()[\]{}"/\\&%$#@!?+=<>|~`\'"]', ' ', content)
        
        # Normalize spacing
        content = ' '.join(content.split())
        
        return content.strip()
    
    def get_summary(self) -> str:
        """Get a brief summary of the page content."""
        if len(self.cleaned_content) <= 200:
            return self.cleaned_content
        return self.cleaned_content[:200] + "..."


class DocumentParser:
    """Handles PDF document parsing and page segmentation."""
    
    def __init__(self, config_manager):
        """
        Initialize document parser.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def parse_pdf(self, pdf_path: str) -> List[DocumentPage]:
        """
        Parse PDF document into individual pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of DocumentPage objects
            
        Raises:
            DocumentProcessingError: If PDF parsing fails
        """
        try:
            self.logger.info(f"Starting PDF parsing: {pdf_path}")
            
            # Validate file exists
            import os
            if not os.path.exists(pdf_path):
                raise DocumentProcessingError(f"PDF file not found: {pdf_path}")
            
            pages = []
            
            # Use PyMuPDF for better text extraction
            try:
                pages = self._parse_with_pymupdf(pdf_path)
                self.logger.info(f"Successfully parsed {len(pages)} pages using PyMuPDF")
            except Exception as e:
                self.logger.warning(f"PyMuPDF parsing failed: {e}, falling back to PyPDF2")
                pages = self._parse_with_pypdf2(pdf_path)
                self.logger.info(f"Successfully parsed {len(pages)} pages using PyPDF2")
            
            if not pages:
                raise DocumentProcessingError("No pages extracted from PDF")
            
            self.logger.info(f"PDF parsing completed: {len(pages)} pages extracted")
            return pages
            
        except Exception as e:
            self.logger.error(f"PDF parsing failed: {e}", exc_info=True)
            raise DocumentProcessingError(f"Failed to parse PDF: {e}")
    
    def _parse_with_pymupdf(self, pdf_path: str) -> List[DocumentPage]:
        """Parse PDF using PyMuPDF (fitz) for better text extraction."""
        pages = []
        
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    # Get additional metadata
                    metadata = {
                        'page_rect': page.rect,
                        'rotation': page.rotation,
                        'has_images': len(page.get_images()) > 0,
                        'has_tables': 'table' in text.lower() or '|' in text
                    }
                    
                    doc_page = DocumentPage(
                        page_number=page_num + 1,
                        content=text,
                        metadata=metadata
                    )
                    
                    pages.append(doc_page)
                    self.logger.debug(f"Extracted page {page_num + 1}: {doc_page.word_count} words")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                    # Continue with empty page rather than failing
                    doc_page = DocumentPage(
                        page_number=page_num + 1,
                        content="",
                        metadata={'extraction_error': str(e)}
                    )
                    pages.append(doc_page)
        
        return pages
    
    def _parse_with_pypdf2(self, pdf_path: str) -> List[DocumentPage]:
        """Parse PDF using PyPDF2 as fallback."""
        pages = []
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(reader.pages)):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    
                    metadata = {
                        'extraction_method': 'PyPDF2',
                        'page_rotation': getattr(page, 'rotation', 0)
                    }
                    
                    doc_page = DocumentPage(
                        page_number=page_num + 1,
                        content=text,
                        metadata=metadata
                    )
                    
                    pages.append(doc_page)
                    self.logger.debug(f"Extracted page {page_num + 1}: {doc_page.word_count} words")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                    doc_page = DocumentPage(
                        page_number=page_num + 1,
                        content="",
                        metadata={'extraction_error': str(e)}
                    )
                    pages.append(doc_page)
        
        return pages
    
    def get_page_groups(self, pages: List[DocumentPage], max_pages_per_group: int = None) -> List[List[DocumentPage]]:
        """
        Group pages for processing to handle very long documents.
        
        Args:
            pages: List of document pages
            max_pages_per_group: Maximum pages per group (from config if None)
            
        Returns:
            List of page groups
        """
        if max_pages_per_group is None:
            max_pages_per_group = self.config_manager.get_max_pages_per_prompt()
        
        groups = []
        current_group = []
        
        for page in pages:
            current_group.append(page)
            
            if len(current_group) >= max_pages_per_group:
                groups.append(current_group)
                current_group = []
        
        # Add remaining pages
        if current_group:
            groups.append(current_group)
        
        self.logger.info(f"Created {len(groups)} page groups with max {max_pages_per_group} pages each")
        return groups
    
    def get_document_summary(self, pages: List[DocumentPage]) -> Dict[str, Any]:
        """
        Get summary statistics about the document.
        
        Args:
            pages: List of document pages
            
        Returns:
            Document summary statistics
        """
        total_words = sum(page.word_count for page in pages)
        non_empty_pages = [page for page in pages if page.word_count > 0]
        
        summary = {
            'total_pages': len(pages),
            'non_empty_pages': len(non_empty_pages),
            'total_words': total_words,
            'average_words_per_page': total_words / len(non_empty_pages) if non_empty_pages else 0,
            'pages_with_images': sum(1 for page in pages if page.metadata.get('has_images', False)),
            'pages_with_tables': sum(1 for page in pages if page.metadata.get('has_tables', False))
        }
        
        self.logger.info(f"Document summary: {summary}")
        return summary 