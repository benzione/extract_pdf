# Tender Document Analysis Application

A sophisticated application for extracting specific parameters from tender and procurement documents using advanced AI language models. Built with enterprise-grade architectural patterns, comprehensive error handling, and **modular design** following the ONE company exercise specifications.

## 🎯 Exercise Status: ✅ COMPLETE

This application has been refactored according to the ONE company home exercise requirements (תרגיל בית – דאטה סיינס/ genAI) with full compliance to the modular design specifications.

## Features

- **🧩 Modular Architecture**: Clean separation of functions for easy maintenance and modification
- **📄 Intelligent PDF Processing**: Page-by-page analysis with smart content classification
- **🎯 Smart Parameter Matching**: Matches parameters to relevant pages only (not entire document)
- **🤖 AI-Powered Extraction**: Uses Gemini 2.0 Flash for accurate parameter extraction
- **🇮🇱 Hebrew Language Support**: Full Hebrew prompt and response handling
- **📊 Multiple Output Formats**: JSON, CSV, and human-readable summary reports
- **⚙️ Configurable Architecture**: All settings externalized for easy customization
- **📝 Enterprise Logging**: Detailed logging with multiple levels and file output

## Extracted Parameters

The application extracts 7 key parameters from tender documents:

1. **Client Name** (שם המזמין) - Organization issuing the tender
2. **Tender Name** (שם המכרז) - Project or contract title
3. **Threshold Conditions** (תנאי סף) - Qualifying requirements for bidders
4. **Contract Period** (תקופת התקשרות) - Duration or timeframe for completion
5. **Evaluation Method** (שיטת הערכה) - Criteria used to assess bids
6. **Bid Guarantee** (ערבות מכרז) - Security requirements for submission
7. **Idea Author** (הוגה הרעיון) - Consultant or entity (always "NOT FOUND" per specification)

## Modular Architecture

The application uses a **modular design** with independent, reusable functions:

```
main() function
├── load_data() - Document and parameter loading
├── tag_pages() - Page content classification  
├── match_parameters_to_pages() - Smart parameter-page matching
├── build_prompts() - Modular prompt construction
├── extract_parameters_with_llm() - LLM API integration
├── format_and_save_results() - Results formatting
└── print_results_to_console() - Console output with Hebrew support
```

**Core Components:**
- `ConfigManager` - Configuration management
- `DocumentParser` - PDF processing and page segmentation
- `PageTagger` - Content classification by type and parameter relevance
- `ParameterMatcher` - Smart parameter-to-page mapping
- `PromptBuilder` - LLM prompt construction with Hebrew support
- `LLMInterface` - Gemini API integration with retry logic
- `OutputFormatter` - Multi-format result generation

## Installation

1. **Clone and set up the project**:
   ```bash
   git clone https://github.com/benzione/extract_pdf.git
   cd pdf_extract
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**:
   Create a `.env` file in the root directory (this file is ignored by git for security):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ENV=development
   DEBUG=true
   ```

4. **Configure the application**:
   The configuration file `config/app_config.json` contains all settings.

5. **Verify setup**:
   The `.gitignore` file is configured to exclude sensitive files, logs, and generated outputs from version control.

## Usage

### Quick Start (Modular Approach)
```bash
# Run the modular main function
python -m src.main
```

### Testing and Demonstration
```bash
# Run comprehensive test demonstrating modular functions
python test_exercise.py
```

### Programmatic Usage
```python
from src.main import (
    load_data, tag_pages, match_parameters_to_pages, 
    build_prompts, extract_parameters_with_llm, format_and_save_results
)
from src.config_manager import ConfigManager

# Initialize
config_manager = ConfigManager()

# Execute modular workflow
pages, parameters = load_data(pdf_path, params_path)
tagged_pages = tag_pages(pages, config_manager)
parameter_matches = match_parameters_to_pages(parameters, tagged_pages, config_manager)
prompts = build_prompts(parameter_matches, config_manager)
responses = extract_parameters_with_llm(prompts, config_manager)
results = format_and_save_results(responses, config_manager)
```

## Output Format

Results follow the exact format specified in the exercise:

```json
{
  "client_name": {
    "answer": "משרד הבריאות",
    "details": "משרד ממשלתי האחראי על שירותי הבריאות",
    "source": "עמוד 1, עמוד 3",
    "score": 4
  },
  "idea_author": {
    "answer": "",
    "details": "", 
    "source": "לא נמצא",
    "score": 0
  }
}
```

**Output Files Generated:**
- `tender_analysis_results_YYYYMMDD_HHMMSS.json` - Complete results
- `tender_analysis_summary_YYYYMMDD_HHMMSS.txt` - Human-readable summary  
- `tender_analysis_export_YYYYMMDD_HHMMSS.csv` - Spreadsheet format

## Configuration

The application uses multiple configuration files for maximum flexibility:

### 📁 **config/app_config.json**
Main application settings including file paths, model configuration, and processing parameters.

### 📁 **config/keywords_config.json** 🆕
**Centralized keywords configuration** with **intelligent caching and fallback system** for maximum generality across different domains and languages:

```json
{
  "page_classification": {
    "cover_page": {
      "english": ["tender", "invitation", "bid", "proposal"],
      "hebrew": ["מכרז", "פומבי", "הצעה", "הזמנה"]
    }
  },
  "parameter_matching": {
    "client_name": {
      "english": ["client", "organization", "company"],
      "hebrew": {
        "organizational_terms": ["תאגיד", "חברה", "רשות"],
        "legal_entities": ["בע\"מ", "עירייה", "מועצה"]
      }
    }
  },
  "fallback_keywords": {
    "parameter_matching": {
      "client_name": ["client", "organization", "תאגיד", "חברה"]
    }
  },
  "generic_search": {
    "parameter_name_transformations": {
      "replace_underscore": true,
      "include_original": true,
      "additional_patterns": []
    }
  }
}
```

**✅ ZERO Hardcoded Keywords**: ALL keywords extracted from JSON config with intelligent caching!

#### 🚀 **Enhanced Architecture Features:**

- **🔄 Smart Caching**: Keywords config loaded once and cached in memory for optimal performance
- **🛡️ Multi-Layer Fallbacks**: Main keywords → fallback keywords → config-based ultimate fallback
- **📈 Performance Optimized**: Single config file read eliminates redundant I/O operations
- **🔧 Fail-Safe Design**: Even ultimate fallbacks use config data when available

#### 🎯 **Intelligent Fallback System:**

1. **Primary**: Load comprehensive keywords from `parameter_matching` section
2. **Secondary**: Use simplified keywords from `fallback_keywords` section  
3. **Ultimate**: Use config-based minimal keywords (NO hardcoded values!)

**Benefits:**
- ✅ **Universal**: Works for any domain (healthcare, construction, IT, etc.)
- ✅ **Multilingual**: Supports English and Hebrew with extensible structure
- ✅ **Maintainable**: Update keywords without changing code
- ✅ **Customizable**: Easy domain-specific customization
- ✅ **Complete**: Includes main keywords, fallbacks, AND generic search patterns
- ✅ **Optimized**: Cached loading for maximum performance

#### 🎛️ **Customizing Keywords for Different Domains**

To adapt the system for different contract types or domains, simply modify `config/keywords_config.json`:

**For Healthcare Contracts:**
```json
"client_name": {
  "hebrew": {
    "organizational_terms": ["בית חולים", "קופת חולים", "משרד הבריאות", "מרכז רפואי"]
  }
}
```

**For Construction Projects:**
```json
"threshold_conditions": {
  "hebrew": {
    "professional_terms": ["רישיון קבלן", "סיווג", "ביטוח עבודות", "ערבות ביצוע"]
  }
}
```

**Adding New Languages:**
```json
"client_name": {
  "english": ["client", "organization"],
  "hebrew": ["תאגיד", "חברה"],
  "arabic": ["عميل", "منظمة"]
}
```

#### ⚙️ **How the Cached Configuration System Works:**

The system now uses an **intelligent caching mechanism** that loads the entire keywords configuration once and reuses it throughout the application lifecycle:

```python
# On initialization - config loaded once and cached
class PageTagger:
    def _load_keywords_from_config(self):
        self.keywords_config = json.load(f)  # Cached for reuse
        
    def _initialize_fallback_keywords(self):
        # Uses cached config instead of re-reading file
        fallback_config = self.keywords_config.get('fallback_keywords', {})
```

**Performance Benefits:**
- **⚡ Faster**: Single file read vs multiple reads
- **🧠 Memory Efficient**: Config shared across all methods  
- **🔄 Consistent**: Same config data used everywhere
- **🛡️ Reliable**: Fallbacks use cached data when available

#### 🏆 **Configuration Architecture Achievements:**

✅ **Complete Keyword Extraction**: Every single keyword moved from code to JSON config  
✅ **Intelligent Caching**: Single config load shared across all components  
✅ **Enhanced Fallbacks**: Multi-layer fallback system using cached config data  
✅ **Zero Code Changes**: Add new domains by updating JSON only  
✅ **Performance Optimized**: Eliminated redundant file I/O operations  
✅ **Fail-Safe Design**: System degrades gracefully with config-based fallbacks  

**Result**: A truly configuration-driven system with maximum generality and optimal performance!

### Environment Variables (`.env`)
```env
GEMINI_API_KEY=your_api_key_here
ENV=development
DEBUG=true
```

## Version Control & .gitignore

The project includes a comprehensive `.gitignore` file that excludes:

### 🔒 **Security & Environment**
- `.env` files (API keys and sensitive configuration)
- `*.key`, `api_keys.txt`, `secrets.json` (additional API key protection)

### 📁 **Generated Files & Outputs**
- `logs/` directory and `*.log` files (application logs)
- `data/output/` directory (analysis results and exports)
- `*.tmp`, `*.temp` (temporary processing files)

### 🐍 **Python-Specific**
- `__pycache__/`, `*.pyc`, `*.pyo` (compiled Python files)
- `*.egg-info/`, `dist/`, `build/` (package distribution files)
- `.pytest_cache/`, `.coverage` (testing artifacts)

### 💻 **Development Environment**
- `venv/`, `.venv/`, `env/` (virtual environments)
- `.vscode/`, `.idea/` (IDE configuration)
- `.DS_Store`, `Thumbs.db` (OS-specific files)

This ensures that:
- ✅ API keys remain secure and private
- ✅ Generated outputs don't clutter the repository
- ✅ Development environments stay clean
- ✅ Only source code and configuration templates are tracked

## Directory Structure

```
pdf_extract/
├── src/                          # Source code
│   ├── main.py                   # Modular main functions + legacy compatibility
│   ├── config_manager.py         # Configuration management
│   ├── document_parser.py        # PDF parsing & page segmentation
│   ├── page_tagger.py           # Page content classification
│   ├── parameter_matcher.py     # Parameter-to-page matching
│   ├── prompt_builder.py        # LLM prompt construction  
│   ├── llm_interface.py         # Gemini API interface
│   ├── output_formatter.py      # Result formatting & file output
│   ├── exceptions.py            # Custom exception classes
│   └── utils.py                 # Utility functions
├── config/
│   ├── app_config.json          # Application configuration
│   └── keywords_config.json     # Keywords configuration
├── data/
│   ├── tender sample.pdf        # Input PDF document
│   ├── parameters_for_exercise.json # Parameters to extract
│   └── output/                  # Generated output files (git ignored)
├── logs/                        # Application logs (git ignored)
├── tests/                       # Unit tests
│   ├── __init__.py
│   └── test_config_manager.py
├── test_exercise.py             # Modular approach demonstration
├── .env                        # Environment variables (create this - git ignored)
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

**Note**: Directories marked as "git ignored" will be created automatically when the application runs. In a fresh clone, you may not see `logs/` or `data/output/` until the first execution.

## Exercise Compliance ✅

**✅ Modular Design**: Clean function separation with reusable components  
**✅ Main Function**: Calls smaller functions sequentially  
**✅ Document Segmentation**: Page-by-page analysis  
**✅ Smart Matching**: Minimal pages sent to LLM per parameter  
**✅ Hebrew Support**: Full Hebrew language integration  
**✅ Output Format**: Exact specification compliance  
**✅ Special Handling**: `idea_author` always returns "NOT FOUND"  
**✅ Error Handling**: Comprehensive logging and exception management  

## Performance Benefits

- **Efficiency**: Only relevant pages sent to LLM per parameter (not entire document)
- **Cost Optimization**: Reduces API costs through smart page selection
- **Modularity**: Easy to modify individual processing steps
- **Scalability**: Functions can be parallelized or cached
- **Maintainability**: Clear separation of concerns

## API Usage

The application uses Google's Gemini AI API. Ensure you have:

1. A valid Google Cloud account
2. Gemini API access enabled
3. An API key with appropriate permissions
4. Sufficient quota for your processing needs

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify your API key is correct in `.env` file
   - Check internet connection and API quota

2. **PDF Parsing Errors**
   - Verify PDF file is not corrupted and contains extractable text
   - Check file permissions

3. **Hebrew Encoding Issues**
   - Use the console output function for proper Hebrew display
   - Ensure UTF-8 encoding support in your terminal

### Debug Mode

Enable debug logging in your `.env` file:
```env
DEBUG=true
```

## Contributing

1. **Follow the modular architectural patterns**
2. **Implement comprehensive error handling**
3. **Add unit tests for new functionality**
4. **Update documentation for any changes**
5. **Ensure all configuration remains externalized**
6. **Respect .gitignore rules**:
   - Never commit `.env` files or API keys
   - Don't track generated outputs or logs
   - Test your changes with a clean virtual environment
   - Update `.gitignore` if adding new file types that should be excluded

### Development Workflow
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Create your `.env` file with your API keys
5. Make your changes and test them
6. Ensure no sensitive files are staged: `git status`

## License

This project is developed for educational and enterprise use. Please ensure compliance with your organization's policies regarding AI service usage. 