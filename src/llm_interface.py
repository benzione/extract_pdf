"""
LLM interface module for the Tender Document Analysis application.
Handles interaction with the Gemini API for parameter extraction.
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .exceptions import LLMAPIError
import re


class LLMResponse:
    """Represents a response from the LLM API."""
    
    def __init__(self, parameter: str, extracted_value: str, details: str = "", confidence: float = 1.0, 
                 tokens_used: int = 0, response_time: float = 0.0, page_numbers: List[int] = None):
        """
        Initialize LLM response.
        
        Args:
            parameter: The parameter that was extracted
            extracted_value: The extracted value or "NOT_FOUND"
            details: Additional details and context from the document
            confidence: Confidence score (0.0-1.0)
            tokens_used: Number of tokens used in the request
            response_time: Response time in seconds
            page_numbers: List of page numbers where parameter was found
        """
        self.parameter = parameter
        self.extracted_value = extracted_value
        self.details = details
        self.confidence = confidence
        self.tokens_used = tokens_used
        self.response_time = response_time
        self.page_numbers = page_numbers or []
        self.is_found = extracted_value != "NOT_FOUND"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'parameter': self.parameter,
            'value': self.extracted_value,
            'details': self.details,
            'found': self.is_found,
            'confidence': self.confidence,
            'tokens_used': self.tokens_used,
            'response_time': self.response_time,
            'page_numbers': self.page_numbers
        }


class LLMInterface:
    """Handles interaction with the Gemini API."""
    
    def __init__(self, config_manager):
        """
        Initialize LLM interface.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Gemini API client."""
        try:
            api_key = self.config_manager.get_api_key()
            genai.configure(api_key=api_key)
            
            # Initialize the model
            model_name = self.config_manager.get_model_name()
            self.model = genai.GenerativeModel(model_name)
            
            self.logger.info(f"Initialized Gemini API client with model: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API client: {e}", exc_info=True)
            raise LLMAPIError(f"Failed to initialize LLM client: {e}")
    
    def extract_parameter(self, parameter: str, prompt: str, page_numbers: List[int] = None) -> LLMResponse:
        """
        Extract a single parameter using the LLM.
        
        Args:
            parameter: The parameter to extract
            prompt: The prompt for extraction
            page_numbers: List of page numbers being processed
            
        Returns:
            LLMResponse object with extraction results
            
        Raises:
            LLMAPIError: If API call fails
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Extracting parameter: {parameter}")
            
            # Validate prompt
            if not prompt or not prompt.strip():
                raise LLMAPIError(f"Empty prompt provided for parameter: {parameter}")
            
            # Make API call with retry logic
            response = self._make_api_call_with_retry(prompt)
            
            # Process response to extract both answer and details
            extracted_value, details = self._process_response(response)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Estimate tokens used (rough approximation)
            tokens_used = len(prompt.split()) + len(extracted_value.split()) + len(details.split())
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(extracted_value, details, response)
            
            llm_response = LLMResponse(
                parameter=parameter,
                extracted_value=extracted_value,
                details=details,
                confidence=confidence,
                tokens_used=tokens_used,
                response_time=response_time,
                page_numbers=page_numbers or []
            )
            
            self.logger.info(f"Successfully extracted {parameter}: "
                           f"{'Found' if llm_response.is_found else 'Not found'} "
                           f"(confidence: {confidence:.2f})")
            
            return llm_response
            
        except Exception as e:
            self.logger.error(f"Failed to extract parameter {parameter}: {e}", exc_info=True)
            
            # Return error response
            return LLMResponse(
                parameter=parameter,
                extracted_value="NOT_FOUND",
                details="",
                confidence=0.0,
                tokens_used=0,
                response_time=time.time() - start_time,
                page_numbers=page_numbers or []
            )
    
    def _make_api_call_with_retry(self, prompt: str):
        """Make API call with retry logic."""
        retry_attempts = self.config_manager.get_retry_attempts()
        timeout_seconds = self.config_manager.get_timeout_seconds()
        
        for attempt in range(retry_attempts):
            try:
                self.logger.debug(f"API call attempt {attempt + 1}/{retry_attempts}")
                
                # Configure generation parameters
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent extraction
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=1024,
                    stop_sequences=["\n\n\n"]  # Stop on multiple newlines
                )
                
                # Make the API call
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    stream=False
                )
                
                # Check if response is valid
                if not response or not response.text:
                    raise LLMAPIError("Empty response from API")
                
                return response
                
            except Exception as e:
                self.logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                
                if attempt < retry_attempts - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) * 1.0
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Last attempt failed
                    raise LLMAPIError(f"All {retry_attempts} API call attempts failed: {e}")
    
    def _process_response(self, response) -> tuple[str, str]:
        """Process and clean the API response to extract answer and details."""
        try:
            response_text = response.text.strip()
            
            if not response_text:
                return "NOT_FOUND", ""
            
            # Clean the response
            response_text = self._clean_response_text(response_text)
            
            # Try to parse as JSON first
            try:
                parsed_json = json.loads(response_text)
                if isinstance(parsed_json, dict):
                    answer = parsed_json.get('answer', 'NOT_FOUND')
                    details = parsed_json.get('details', '')
                    
                    # Clean the extracted values
                    answer = self._clean_extracted_value(answer)
                    details = self._clean_extracted_value(details)
                    
                    return answer, details
            except json.JSONDecodeError:
                self.logger.debug("Response is not valid JSON, attempting text parsing")
            
            # Fallback: try to extract from text format
            return self._parse_text_response(response_text)
            
        except Exception as e:
            self.logger.error(f"Error processing response: {e}", exc_info=True)
            return "NOT_FOUND", ""
    
    def _parse_text_response(self, text: str) -> tuple[str, str]:
        """Parse non-JSON text response to extract answer and details."""
        # Look for patterns like "Answer: ..." and "Details: ..."
        answer_patterns = [
            r'answer["\s]*:\s*["\s]*([^"\n]+)',
            r'answer["\s]*[:\s]*([^\n]+)',
            r'^([^\n]+)'  # First line as fallback
        ]
        
        details_patterns = [
            r'details["\s]*:\s*["\s]*([^"\n]+)',
            r'details["\s]*[:\s]*([^\n]+)',
        ]
        
        answer = "NOT_FOUND"
        details = ""
        
        # Try to find answer
        for pattern in answer_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                break
        
        # Try to find details
        for pattern in details_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                details = match.group(1).strip()
                break
        
        # Clean the extracted values
        answer = self._clean_extracted_value(answer)
        details = self._clean_extracted_value(details)
        
        return answer, details
    
    def _clean_response_text(self, text: str) -> str:
        """Clean and normalize response text."""
        if not text:
            return ""
        
        # Remove code block markers if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _clean_extracted_value(self, value: str) -> str:
        """Clean extracted values for consistency."""
        if not value:
            return ""
        
        # Remove quotes if they wrap the entire value
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        
        # Check for common "not found" indicators
        not_found_indicators = [
            "not found", "not available", "not specified", "not mentioned",
            "cannot be found", "not provided", "not indicated", "n/a", "na"
        ]
        
        value_lower = value.lower().strip()
        if any(indicator in value_lower for indicator in not_found_indicators):
            return "NOT_FOUND"
        
        # Remove extra whitespace
        value = ' '.join(value.split())
        
        return value.strip()
    
    def _calculate_confidence(self, extracted_value: str, details: str, response) -> float:
        """Calculate confidence score for the extraction."""
        if extracted_value == "NOT_FOUND":
            return 0.0
        
        # Base confidence factors
        confidence_factors = []
        
        # Factor 1: Response length (reasonable length indicates good extraction)
        answer_words = len(extracted_value.split())
        details_words = len(details.split())
        
        if 2 <= answer_words <= 50:
            confidence_factors.append(0.8)
        elif answer_words > 0:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.2)
        
        # Factor 2: Details quality (more details usually indicate better extraction)
        if details_words > 5:
            confidence_factors.append(0.8)
        elif details_words > 0:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Factor 3: Response contains specific content types
        if any(char.isdigit() for char in extracted_value):
            confidence_factors.append(0.7)  # Numbers often indicate specific values
        
        if any(char.isupper() for char in extracted_value):
            confidence_factors.append(0.6)  # Proper nouns/titles
        
        # Factor 4: Response doesn't contain uncertainty indicators
        uncertainty_indicators = ["maybe", "perhaps", "possibly", "unclear", "ambiguous"]
        combined_text = f"{extracted_value} {details}".lower()
        if not any(indicator in combined_text for indicator in uncertainty_indicators):
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)
        
        # Calculate average confidence
        if confidence_factors:
            return min(sum(confidence_factors) / len(confidence_factors), 1.0)
        else:
            return 0.5  # Default moderate confidence
    
    def extract_batch_parameters(self, prompts: List[Dict[str, Any]]) -> List[LLMResponse]:
        """
        Extract multiple parameters in batch.
        
        Args:
            prompts: List of prompt dictionaries with parameter names, prompts, and page numbers
            
        Returns:
            List of LLMResponse objects
        """
        try:
            self.logger.info(f"Starting batch extraction for {len(prompts)} parameters")
            
            responses = []
            for i, prompt_data in enumerate(prompts):
                parameter = prompt_data['parameter']
                prompt = prompt_data.get('prompt')
                page_numbers = prompt_data.get('page_numbers', [])
                
                if prompt is None:
                    # Handle parameters with no prompt (no matching pages)
                    self.logger.warning(f"No prompt available for parameter: {parameter}")
                    response = LLMResponse(
                        parameter=parameter,
                        extracted_value="NOT_FOUND",
                        details="",
                        confidence=0.0,
                        page_numbers=[]
                    )
                else:
                    # Extract parameter
                    response = self.extract_parameter(parameter, prompt, page_numbers)
                
                responses.append(response)
                
                # Log progress
                self.logger.info(f"Completed {i+1}/{len(prompts)} extractions")
            
            self.logger.info("Batch extraction completed successfully")
            return responses
            
        except Exception as e:
            self.logger.error(f"Batch extraction failed: {e}", exc_info=True)
            raise LLMAPIError(f"Failed to extract batch parameters: {e}")
    
    def get_api_statistics(self, responses: List[LLMResponse]) -> Dict[str, Any]:
        """Get statistics about API usage."""
        if not responses:
            return {
                'total_requests': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
                'total_tokens': 0,
                'total_time': 0.0,
                'average_response_time': 0.0
            }
        
        successful = [r for r in responses if r.is_found]
        failed = [r for r in responses if not r.is_found]
        
        stats = {
            'total_requests': len(responses),
            'successful_extractions': len(successful),
            'failed_extractions': len(failed),
            'success_rate': len(successful) / len(responses) if responses else 0,
            'total_tokens': sum(r.tokens_used for r in responses),
            'total_time': sum(r.response_time for r in responses),
            'average_response_time': sum(r.response_time for r in responses) / len(responses),
            'average_confidence': sum(r.confidence for r in successful) / len(successful) if successful else 0
        }
        
        self.logger.info(f"API statistics: {stats}")
        return stats
    
    def test_connection(self) -> bool:
        """Test API connection with a simple request."""
        try:
            self.logger.info("Testing API connection...")
            
            test_prompt = "What is 2+2? Respond with only the number."
            response = self._make_api_call_with_retry(test_prompt)
            
            if response and response.text:
                self.logger.info("API connection test successful")
                return True
            else:
                self.logger.error("API connection test failed: No response")
                return False
                
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}", exc_info=True)
            return False 