"""
Unit tests for config_manager module.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import patch, mock_open

from src.config_manager import ConfigManager
from src.exceptions import InvalidConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def test_valid_configuration_loading(self):
        """Test loading valid configuration file."""
        config_data = {
            "pdf_input_path": "test.pdf",
            "parameters_json_path": "params.json",
            "output_directory": "output",
            "log_file_path": "app.log",
            "llm_model_name": "gemini-2.0-flash"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        # Create dummy files for validation
        with open("test.pdf", 'w') as f:
            f.write("")
        with open("params.json", 'w') as f:
            f.write("[]")
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.get_model_name() == "gemini-2.0-flash"
            assert config_manager.get_pdf_path() == "test.pdf"
        finally:
            # Cleanup
            os.unlink(config_path)
            os.unlink("test.pdf")
            os.unlink("params.json")
    
    def test_missing_configuration_file(self):
        """Test error handling for missing configuration file."""
        with pytest.raises(InvalidConfigurationError):
            ConfigManager("nonexistent.json")
    
    def test_invalid_json_format(self):
        """Test error handling for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_path = f.name
        
        try:
            with pytest.raises(InvalidConfigurationError):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_missing_required_keys(self):
        """Test error handling for missing required configuration keys."""
        config_data = {
            "pdf_input_path": "test.pdf"
            # Missing other required keys
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            with pytest.raises(InvalidConfigurationError):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_environment_variable_access(self):
        """Test accessing environment variables."""
        config_data = {
            "pdf_input_path": "test.pdf",
            "parameters_json_path": "params.json",
            "output_directory": "output",
            "log_file_path": "app.log",
            "llm_model_name": "gemini-2.0-flash"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        # Create dummy files
        with open("test.pdf", 'w') as f:
            f.write("")
        with open("params.json", 'w') as f:
            f.write("[]")
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.get_api_key() == 'test_key'
        finally:
            os.unlink(config_path)
            os.unlink("test.pdf")
            os.unlink("params.json") 