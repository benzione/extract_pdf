"""
Page tagging module for the Tender Document Analysis application.
Handles classification and tagging of individual document pages.
"""

import logging
import re
import json
import os
from typing import List, Dict, Any, Set
from enum import Enum
from .document_parser import DocumentPage
from .exceptions import PageTaggingError


class PageType(Enum):
    """Enumeration of different page types in tender documents."""
    COVER_PAGE = "cover_page"
    TABLE_OF_CONTENTS = "table_of_contents" 
    GENERAL_INFO = "general_info"
    TECHNICAL_SPECS = "technical_specs"
    FINANCIAL_INFO = "financial_info"
    LEGAL_TERMS = "legal_terms"
    EVALUATION_CRITERIA = "evaluation_criteria"
    SUBMISSION_REQUIREMENTS = "submission_requirements"
    CONTACT_INFO = "contact_info"
    APPENDIX = "appendix"
    OTHER = "other"


class PageTagger:
    """Handles tagging and classification of document pages."""
    
    def __init__(self, config_manager):
        """
        Initialize page tagger.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._load_keywords_from_config()
    
    def _load_keywords_from_config(self) -> None:
        """Load keyword patterns from JSON configuration file."""
        try:
            # Load keywords from centralized config file
            keywords_path = os.path.join('config', 'keywords_config.json')
            with open(keywords_path, 'r', encoding='utf-8') as f:
                self.keywords_config = json.load(f)
            
            # Build page type keywords
            self.page_type_keywords = {}
            page_config = self.keywords_config.get('page_classification', {})
            
            for page_type_str, keywords_data in page_config.items():
                page_type = PageType(page_type_str)
                combined_keywords = []
                
                # Add English keywords
                if 'english' in keywords_data:
                    combined_keywords.extend(keywords_data['english'])
                
                # Add Hebrew keywords
                if 'hebrew' in keywords_data:
                    if isinstance(keywords_data['hebrew'], list):
                        combined_keywords.extend(keywords_data['hebrew'])
                    elif isinstance(keywords_data['hebrew'], dict):
                        for hebrew_list in keywords_data['hebrew'].values():
                            combined_keywords.extend(hebrew_list)
                
                self.page_type_keywords[page_type] = combined_keywords
            
            # Build parameter keywords
            self.parameter_keywords = {}
            param_config = self.keywords_config.get('parameter_matching', {})
            
            for param, keywords_data in param_config.items():
                combined_keywords = []
                
                # Add English keywords
                if 'english' in keywords_data:
                    combined_keywords.extend(keywords_data['english'])
                
                # Add Hebrew keywords
                if 'hebrew' in keywords_data:
                    if isinstance(keywords_data['hebrew'], list):
                        combined_keywords.extend(keywords_data['hebrew'])
                    elif isinstance(keywords_data['hebrew'], dict):
                        for hebrew_list in keywords_data['hebrew'].values():
                            combined_keywords.extend(hebrew_list)
                
                self.parameter_keywords[param] = combined_keywords
            
            self.logger.info("Keywords loaded successfully from configuration file")
            
        except Exception as e:
            self.logger.error(f"Failed to load keywords from config: {e}")
            # Fallback to basic keywords if config loading fails
            self._initialize_fallback_keywords()
    
    def _initialize_fallback_keywords(self) -> None:
        """Initialize basic fallback keywords if config loading fails."""
        try:
            # Try to load fallback keywords from config if available
            # keywords_path = os.path.join('config', 'keywords_config.json')
            # if os.path.exists(keywords_path):
            #     with open(keywords_path, 'r', encoding='utf-8') as f:
            #         keywords_config = json.load(f)
                
                fallback_config = self.keywords_config.get('fallback_keywords', {})
                
                # Load fallback page type keywords
                page_fallback = fallback_config.get('page_classification', {})
                self.page_type_keywords = {}
                for page_type_str, keywords in page_fallback.items():
                    if page_type_str != 'other':
                        page_type = PageType(page_type_str)
                        self.page_type_keywords[page_type] = keywords
                    else:
                        self.page_type_keywords[PageType.OTHER] = keywords
                
                # Load fallback parameter keywords
                param_fallback = fallback_config.get('parameter_matching', {})
                self.parameter_keywords = param_fallback
                
                self.logger.info("Fallback keywords loaded from configuration file")
                return
                
        except Exception as e:
            self.logger.warning(f"Could not load fallback keywords from config: {e}")
        
        # Ultimate fallback - minimal hardcoded keywords
        self.page_type_keywords = {
            PageType.COVER_PAGE: ['tender', 'מכרז'],
            PageType.OTHER: []
        }
        self.parameter_keywords = keywords_config.get('parameter_matching', {})
    
    def tag_pages(self, pages: List[DocumentPage]) -> List[DocumentPage]:
        """
        Tag all pages with their types and relevant parameters.
        
        Args:
            pages: List of document pages to tag
            
        Returns:
            List of tagged pages with updated metadata
            
        Raises:
            PageTaggingError: If tagging fails
        """
        try:
            self.logger.info(f"Starting page tagging for {len(pages)} pages")
            
            tagged_pages = []
            for page in pages:
                tagged_page = self._tag_single_page(page)
                tagged_pages.append(tagged_page)
            
            # Post-process tags for consistency
            tagged_pages = self._post_process_tags(tagged_pages)
            
            self.logger.info("Page tagging completed successfully")
            return tagged_pages
            
        except Exception as e:
            self.logger.error(f"Page tagging failed: {e}", exc_info=True)
            raise PageTaggingError(f"Failed to tag pages: {e}")
    
    def _tag_single_page(self, page: DocumentPage) -> DocumentPage:
        """Tag a single page with type and parameter relevance."""
        content_lower = page.cleaned_content.lower()
        
        # Determine page type
        page_type = self._classify_page_type(content_lower)
        
        # Find relevant parameters for this page
        relevant_parameters = self._find_relevant_parameters(content_lower)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(content_lower, page_type, relevant_parameters)
        
        # Update page metadata
        page.metadata.update({
            'page_type': page_type.value,
            'relevant_parameters': relevant_parameters,
            'confidence_scores': confidence_scores,
            'tagging_complete': True
        })
        
        self.logger.debug(f"Page {page.page_number} tagged as {page_type.value} with parameters: {relevant_parameters}")
        
        return page
    
    def _classify_page_type(self, content_lower: str) -> PageType:
        """Classify the type of page based on content."""
        type_scores = {}
        
        for page_type, keywords in self.page_type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
                    # Boost score for exact matches at sentence boundaries
                    if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                        score += 1
            
            type_scores[page_type] = score
        
        # Return the type with highest score, or OTHER if no matches
        if max(type_scores.values()) > 0:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return PageType.OTHER
    
    def _find_relevant_parameters(self, content_lower: str) -> List[str]:
        """Find which parameters are likely to be found on this page."""
        relevant_params = []
        
        for param, keywords in self.parameter_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
                if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                    score += 1
            
            # Consider parameter relevant if it has a reasonable score
            if score >= 2:
                relevant_params.append(param)
        
        return relevant_params
    
    def _calculate_confidence_scores(self, content_lower: str, page_type: PageType, 
                                   relevant_parameters: List[str]) -> Dict[str, float]:
        """Calculate confidence scores for page classification and parameter relevance."""
        scores = {
            'page_type_confidence': 0.0,
            'parameter_confidence': {}
        }
        
        # Page type confidence based on keyword density
        if page_type in self.page_type_keywords:
            total_keywords = len(self.page_type_keywords[page_type])
            matched_keywords = sum(1 for kw in self.page_type_keywords[page_type] if kw in content_lower)
            scores['page_type_confidence'] = matched_keywords / total_keywords if total_keywords > 0 else 0.0
        
        # Parameter confidence scores
        for param in relevant_parameters:
            if param in self.parameter_keywords:
                total_keywords = len(self.parameter_keywords[param])
                matched_keywords = sum(1 for kw in self.parameter_keywords[param] if kw in content_lower)
                scores['parameter_confidence'][param] = matched_keywords / total_keywords if total_keywords > 0 else 0.0
        
        return scores
    
    def _post_process_tags(self, pages: List[DocumentPage]) -> List[DocumentPage]:
        """Post-process page tags for consistency and logic."""
        # Identify cover page (usually first page with tender-related content)
        for i, page in enumerate(pages):
            if i < 3 and page.metadata.get('page_type') == PageType.COVER_PAGE.value:
                # Ensure first few pages are properly classified
                break
        
        # Identify table of contents (usually early in document)
        for i, page in enumerate(pages[:5]):
            content_lower = page.cleaned_content.lower()
            if 'table of contents' in content_lower or 'contents' in content_lower:
                page.metadata['page_type'] = PageType.TABLE_OF_CONTENTS.value
        
        return pages
    
    def get_pages_by_type(self, pages: List[DocumentPage], page_type: PageType) -> List[DocumentPage]:
        """Get all pages of a specific type."""
        return [page for page in pages if page.metadata.get('page_type') == page_type.value]
    
    def get_pages_with_parameter(self, pages: List[DocumentPage], parameter: str) -> List[DocumentPage]:
        """Get all pages that might contain a specific parameter."""
        return [
            page for page in pages 
            if parameter in page.metadata.get('relevant_parameters', [])
        ]
    
    def get_tagging_summary(self, pages: List[DocumentPage]) -> Dict[str, Any]:
        """Get summary of page tagging results."""
        type_counts = {}
        parameter_counts = {}
        
        for page in pages:
            page_type = page.metadata.get('page_type', 'unknown')
            type_counts[page_type] = type_counts.get(page_type, 0) + 1
            
            for param in page.metadata.get('relevant_parameters', []):
                parameter_counts[param] = parameter_counts.get(param, 0) + 1
        
        summary = {
            'total_pages': len(pages),
            'page_type_distribution': type_counts,
            'parameter_distribution': parameter_counts,
            'pages_with_no_parameters': len([p for p in pages if not p.metadata.get('relevant_parameters')])
        }
        
        self.logger.info(f"Tagging summary: {summary}")
        return summary 