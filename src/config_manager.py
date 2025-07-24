"""
Configuration management module for the Tender Document Analysis application.
Handles loading configuration from JSON files and environment variables.
"""

import json
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from .exceptions import InvalidConfigurationError


class ConfigManager:
    """Manages application configuration from files and environment variables."""
    
    def __init__(self, config_file_path: str = "config/app_config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file_path: Path to the JSON configuration file
        """
        self.config_file_path = config_file_path
        self.config = {}
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from JSON file and environment variables."""
        try:
            # Load environment variables from .env file
            load_dotenv()
            logging.info("Environment variables loaded from .env file")
            
            # Load JSON configuration
            if not os.path.exists(self.config_file_path):
                raise InvalidConfigurationError(
                    f"Configuration file not found: {self.config_file_path}"
                )
            
            with open(self.config_file_path, 'r', encoding='utf-8') as file:
                self.config = json.load(file)
            
            logging.info(f"Configuration loaded from {self.config_file_path}")
            
            # Validate required configuration
            self._validate_configuration()
            
        except json.JSONDecodeError as e:
            raise InvalidConfigurationError(
                f"Invalid JSON in configuration file: {e}"
            )
        except Exception as e:
            raise InvalidConfigurationError(
                f"Error loading configuration: {e}"
            )
    
    def _validate_configuration(self) -> None:
        """Validate that required configuration values are present."""
        required_keys = [
            'pdf_input_path',
            'parameters_json_path', 
            'output_directory',
            'log_file_path',
            'llm_model_name'
        ]
        
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise InvalidConfigurationError(
                f"Missing required configuration keys: {missing_keys}"
            )
        
        # Validate file paths exist
        for path_key in ['pdf_input_path', 'parameters_json_path']:
            if not os.path.exists(self.config[path_key]):
                raise InvalidConfigurationError(
                    f"File not found: {self.config[path_key]}"
                )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def get_env(self, key: str, default: Any = None) -> str:
        """Get environment variable."""
        value = os.getenv(key, default)
        if value is None:
            raise InvalidConfigurationError(f"Required environment variable not set: {key}")
        return value
    
    def get_api_key(self) -> str:
        """Get Gemini API key from environment."""
        return self.get_env('GEMINI_API_KEY')
    
    def get_pdf_path(self) -> str:
        """Get PDF input path."""
        return self.get('pdf_input_path')
    
    def get_parameters_path(self) -> str:
        """Get parameters JSON path."""
        return self.get('parameters_json_path')
    
    def get_output_directory(self) -> str:
        """Get output directory path."""
        return self.get('output_directory')
    
    def get_log_path(self) -> str:
        """Get log file path."""
        return self.get('log_file_path')
    
    def get_model_name(self) -> str:
        """Get LLM model name."""
        return self.get('llm_model_name')
    
    def get_max_pages_per_prompt(self) -> int:
        """Get maximum pages per prompt."""
        return self.get('max_pages_per_prompt', 3)
    
    def get_page_overlap_chars(self) -> int:
        """Get page overlap characters."""
        return self.get('page_overlap_chars', 500)
    
    def get_max_tokens_per_page(self) -> int:
        """Get maximum tokens per page."""
        return self.get('max_tokens_per_page', 4000)
    
    def get_retry_attempts(self) -> int:
        """Get retry attempts for API calls."""
        return self.get('retry_attempts', 3)
    
    def get_timeout_seconds(self) -> int:
        """Get timeout for API calls."""
        return self.get('timeout_seconds', 30) 