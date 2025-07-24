"""
Prompt building module for the Tender Document Analysis application.
Constructs LLM prompts for parameter extraction from document pages.
"""

import logging
from typing import List, Dict, Any
from .parameter_matcher import ParameterMatch
from .exceptions import ParameterMatchingError


class PromptBuilder:
    """Handles construction of LLM prompts for parameter extraction."""
    
    def __init__(self, config_manager):
        """
        Initialize prompt builder.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize prompt templates for different parameter types."""
        
        # Base system prompt for all extractions
        self.system_prompt = """You are an expert document analyst specializing in tender and procurement documents. Your task is to extract specific information from document pages with high accuracy.

Instructions:
1. Extract the requested information from the provided document pages
2. Provide both a direct answer and additional details/context
3. If the information is not found, respond with "NOT_FOUND" for both answer and details
4. Be precise and base your response only on the document content
5. For details, provide relevant context, expanded wording, or interpretation from the document
6. **IMPORTANT: Respond in Hebrew for both the answer and details fields. Extract information in Hebrew as it appears in the document or translate to Hebrew if the document is in another language.**

Response format: Return your response as JSON with two fields:
{
  "answer": "direct extracted value in Hebrew",
  "details": "additional context and interpretation from document in Hebrew"
}"""

        # Parameter-specific templates with Hebrew descriptions
        self.parameter_templates = {
            'client_name': {
                'instruction': """Extract the CLIENT NAME (שם הזוכה שכורם את המכרז) - the organization name that is issuing this tender/procurement.

Hebrew Description: שם הזוכה שכורם את המכרז (למשל: רשות, תאגיד, עירייה)

Look for:
- Organization name, company name, agency name (שם הארגון, שם החברה, שם הרשות)
- Government department or authority (משרד ממשלתי או רשות)
- Contracting party or procuring entity (הגורם המתקשר או הרכש)
- Client organization mentioned in the document (ארגון הלקוח המוזכר במסמך)

For the answer: Return the full official name as it appears in the document **in Hebrew**.
For the details: Provide any additional context about the organization, their role, or how they are described in the document **in Hebrew**.""",
                'examples': [
                    '{"answer": "משרד הבריאות", "details": "משרד ממשלתי האחראי על שירותי הבריאות ורכש ציוד רפואי"}',
                    '{"answer": "חברת ABC בע״מ", "details": "חברה פרטית הפועלת כרשות מתקשרת לרכש זה"}',
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            },
            
            'tender_name': {
                'instruction': """Extract the TENDER NAME (שם המכרז) - the project title or contract title.

Hebrew Description: שם מלא של המכרז, כולל מספר וכו' (פומבי, דו-שלבי וכו')

Look for:
- Tender title or name (כותרת או שם המכרז)
- Project name or title (שם הפרויקט או הכותרת)
- Contract description (תיאור החוזה)
- RFP title or subject (כותרת הצעת המחיר)
- Work description or service title (תיאור העבודה או שם השירות)

For the answer: Return the complete title as it appears in the document **in Hebrew**.
For the details: Provide any additional description, scope details, or context about the project from the document **in Hebrew**.""",
                'examples': [
                    '{"answer": "אספקת ציוד רפואי", "details": "רכש ציוד רפואי ברמה בית חולים וציוד אבחון למתקני בריאות אזוריים"}',
                    '{"answer": "בניית גשר כביש ראשי", "details": "פרויקט תשתית לבניית גשר פלדה באורך 200 מטר על מעבר הנהר הראשי"}',
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            },
            
            'threshold_conditions': {
                'instruction': """Extract THRESHOLD CONDITIONS (תנאי סף) - qualifying requirements for bidders.

Hebrew Description: דרישות חובה להשתתפות - דוגמה: ניסיון, עמידה בחוקים, רישוי

Look for:
- Minimum qualifications or requirements (כישורים מינימליים או דרישות)
- Eligibility criteria or conditions (קריטריוני זכאות או תנאים)
- Technical thresholds or limits (ספי טכניים או מגבלות)
- Financial requirements or thresholds (דרישות כספיות או ספים)
- Experience requirements or minimum standards (דרישות ניסיון או סטנדרטים מינימליים)

For the answer: Return the specific conditions or requirements as stated **in Hebrew**.
For the details: Provide additional context about why these conditions exist, how they are verified, or related qualification details **in Hebrew**.""",
                'examples': [
                    '{"answer": "ניסיון מינימלי של 5 שנים בפרויקטים דומים", "details": "הניסיון חייב להיות מוכח באמצעות פרויקטים שהושלמו בהיקף ובמורכבות דומים, מאומת על ידי המלצות לקוחות"}',
                    '{"answer": "מחזור שנתי של לפחות מיליון שקל", "details": "סף כספי להבטחת יכולת המציע, חייב להיות מגובה בדוחות כספיים מבוקרים משלוש השנים האחרונות"}',
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            },
            
            'contract_period': {
                'instruction': """Extract the CONTRACT PERIOD (תקופת ההתקשרות) - duration or timeframe for project completion.

Hebrew Description: כמה זמן תמשך ההתקשרות, ואם קיימות אופציות להארכה

Look for:
- Contract duration or period (משך החוזה או התקופה)
- Project timeline or schedule (לוח זמנים של הפרויקט)
- Completion timeframe (מסגרת זמן להשלמה)
- Start and end dates (תאריכי התחלה וסיום)
- Service period or term (תקופת השירות)

For the answer: Return the time period as specified in the document **in Hebrew**.
For the details: Provide additional context about project phases, milestones, or timeline requirements mentioned in the document **in Hebrew**.""",
                'examples': [
                    '{"answer": "12 חודשים", "details": "משך החוזה כולל שלב הכנה של 3 חודשים, שלב יישום של 8 חודשים ותקופת אחריות של חודש אחד"}',
                    '{"answer": "ינואר 2024 עד דצמבר 2025", "details": "תקופת חוזה של שנתיים עם אופציה להארכה לשנה נוספת על בסיס הערכת ביצועים"}',
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            },
            
            'evaluation_method': {
                'instruction': """Extract the EVALUATION METHOD (שיטת הערכה) - criteria used to assess bids.

Hebrew Description: כיצד נשקלת את ההצעות - מחיר מול איכות, קריטריונים לניקוד

Look for:
- Evaluation criteria or method (קריטריוני הערכה או שיטה)
- Scoring system or methodology (מערכת ניקוד או מתודולוגיה)
- Assessment approach (גישת הערכה)
- Selection criteria (קריטריוני בחירה)
- Weighting system for bid evaluation (מערכת שקלול להערכת הצעות)

For the answer: Return the evaluation method as described in the document **in Hebrew**.
For the details: Provide additional information about the evaluation process, scoring breakdown, or assessment criteria mentioned **in Hebrew**.""",
                'examples': [
                    '{"answer": "70% ניקוד טכני, 30% ניקוד כספי", "details": "הערכה טכנית כוללת ניסיון, מתודולוגיה וכישורי הצוות; הערכה כספית מבוססת על עלות כוללת ויחס עלות-תועלת"}',
                    '{"answer": "תהליך הערכה דו-שלבי", "details": "שלב א: ביקורת כישורים טכניים; שלב ב: הערכת הצעה כספית למציעים שעברו הכשרה טכנית בלבד"}',
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            },
            
            'bid_guarantee': {
                'instruction': """Extract BID GUARANTEE (ערבות מכרז) - security requirements for submission.

Hebrew Description: סכום הערבות, סוג הערבות, הצגה לפורעון, תוקף

Look for:
- Bid security or guarantee amount (סכום ערבות או ביטחון המכרז)
- Bank guarantee requirements (דרישות ערבות בנקאית)
- Performance bond details (פרטי ערבות ביצוע)
- Deposit or security requirements (דרישות פיקדון או ביטחון)
- Financial guarantee specifications (מפרטי ערבות כספית)

For the answer: Return the guarantee requirements as specified **in Hebrew**.
For the details: Provide additional context about the guarantee purpose, validity period, or related security requirements **in Hebrew**.""",
                'examples': [
                    '{"answer": "2% מערך ההצעה כערבות בנקאית", "details": "ערבות המכרז חייבת להיות בתוקף ל-90 יום ממועד הגשת ההצעה, מונפקת על ידי בנק מורשה, ומכסה התחייבות רצינית להצעה"}',
                    '{"answer": "פיקדון ביטחון של 10,000 שקל", "details": "סכום פיקדון קבוע הנדרש עם הגשת ההצעה, יוחזר למציעים שלא זכו בתוך 30 יום מהזכייה"}'
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            },
            
            'idea_author': {
                'instruction': """Extract the IDEA AUTHOR (חותן הרעיון) - consultant or entity that prepared/designed this tender.

Hebrew Description: פרטי המידע לא זמינים במכרז בזווה - אין לצפות שימצא במסמך (אלא אמוריכ לטלפון ו/או פת כרגנל)

Look for:
- Consultant name or firm (שם יועץ או משרד)
- Document author or preparer (כותב או מכין המסמך)
- Design firm or architect (משרד תכנון או אדריכל)
- Technical author or expert (כותב טכני או מומחה)
- "Prepared by" or "Designed by" information (מידע "הוכן על ידי" או "תוכנן על ידי")

NOTE: This parameter is typically not found in tender documents according to the specification.

For the answer: Return the name of the author/consultant as mentioned **in Hebrew**, or "NOT_FOUND" if not present.
For the details: Provide additional context about their role, expertise, or involvement in the project as described in the document **in Hebrew**.""",
                'examples': [
                    '{"answer": "חברת יעוץ הנדסי XYZ", "details": "משרד יעוץ טכני האחראי על תכנון הפרויקט והכנת מסמכי המכרז, מתמחה בפרויקטי תשתית"}',
                    '{"answer": "NOT_FOUND", "details": "NOT_FOUND"}'
                ]
            }
        }
    
    def build_extraction_prompt(self, parameter_match: ParameterMatch) -> str:
        """
        Build complete prompt for parameter extraction.
        
        Args:
            parameter_match: ParameterMatch object containing parameter and pages
            
        Returns:
            Complete prompt string for LLM
        """
        try:
            parameter = parameter_match.parameter
            
            # Get parameter template
            if parameter not in self.parameter_templates:
                template = self._create_generic_template(parameter)
            else:
                template = self.parameter_templates[parameter]
            
            # Build the prompt
            prompt_parts = []
            
            # Add parameter-specific instruction
            prompt_parts.append(f"TASK: {template['instruction']}")
            
            # Add examples if available
            if 'examples' in template and template['examples']:
                prompt_parts.append("\nEXAMPLES:")
                for example in template['examples']:
                    prompt_parts.append(f"- {example}")
            
            # Add document content
            prompt_parts.append("\nDOCUMENT CONTENT:")
            prompt_parts.append("=" * 50)
            
            # Add page content with clear separation
            for i, page in enumerate(parameter_match.pages):
                if page.word_count > 0:  # Only include pages with content
                    prompt_parts.append(f"\n--- PAGE {page.page_number} ---")
                    prompt_parts.append(page.cleaned_content)
            
            prompt_parts.append("=" * 50)
            prompt_parts.append(f"\nExtract the {parameter.replace('_', ' ').title()} from the above document content.")
            prompt_parts.append("Return your response as JSON with 'answer' and 'details' fields.")
            prompt_parts.append("**CRITICAL: Respond in Hebrew for both answer and details fields.**")
            prompt_parts.append("If not found, use 'NOT_FOUND' for both fields.")
            
            full_prompt = "\n".join(prompt_parts)
            
            self.logger.debug(f"Built prompt for {parameter}: {len(full_prompt)} characters")
            return full_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to build prompt for {parameter}: {e}", exc_info=True)
            raise ParameterMatchingError(f"Failed to build prompt: {e}")
    
    def _create_generic_template(self, parameter: str) -> Dict[str, Any]:
        """Create a generic template for unknown parameters."""
        return {
            'instruction': f"""Extract the {parameter.replace('_', ' ').upper()} from the document.

Look for any information related to "{parameter.replace('_', ' ')}" in the document content.

For the answer: Return the relevant information as it appears in the document **in Hebrew**.
For the details: Provide additional context or interpretation about this information from the document **in Hebrew**.""",
            'examples': [
                f'{{"answer": "ערך שחולץ בעברית", "details": "הקשר נוסף מהמסמך בעברית"}}'
            ]
        }
    
    def build_batch_prompts(self, parameter_matches: List[ParameterMatch]) -> List[Dict[str, Any]]:
        """
        Build prompts for batch processing of multiple parameters.
        
        Args:
            parameter_matches: List of ParameterMatch objects
            
        Returns:
            List of prompt dictionaries with parameter names, prompts, and page numbers
        """
        try:
            prompts = []
            
            for match in parameter_matches:
                if match.pages:  # Only create prompts for parameters with matched pages
                    prompt = self.build_extraction_prompt(match)
                    page_numbers = [page.page_number for page in match.pages]
                    prompts.append({
                        'parameter': match.parameter,
                        'prompt': prompt,
                        'page_count': len(match.pages),
                        'confidence': match.confidence,
                        'page_numbers': page_numbers
                    })
                else:
                    self.logger.warning(f"No pages found for parameter: {match.parameter}")
                    prompts.append({
                        'parameter': match.parameter,
                        'prompt': None,
                        'page_count': 0,
                        'confidence': 0.0,
                        'page_numbers': []
                    })
            
            self.logger.info(f"Built {len(prompts)} prompts for batch processing")
            return prompts
            
        except Exception as e:
            self.logger.error(f"Failed to build batch prompts: {e}", exc_info=True)
            raise ParameterMatchingError(f"Failed to build batch prompts: {e}")
    
    def validate_prompt_length(self, prompt: str) -> bool:
        """
        Validate that prompt length is within acceptable limits.
        
        Args:
            prompt: The prompt string to validate
            
        Returns:
            True if valid, False otherwise
        """
        max_tokens = self.config_manager.get_max_tokens_per_page() * self.config_manager.get_max_pages_per_prompt()
        
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) / 4
        
        if estimated_tokens > max_tokens:
            self.logger.warning(f"Prompt too long: {estimated_tokens} tokens (max: {max_tokens})")
            return False
        
        return True
    
    def truncate_prompt_if_needed(self, prompt: str) -> str:
        """
        Truncate prompt if it exceeds length limits.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Truncated prompt if necessary
        """
        if self.validate_prompt_length(prompt):
            return prompt
        
        max_tokens = self.config_manager.get_max_tokens_per_page() * self.config_manager.get_max_pages_per_prompt()
        max_chars = int(max_tokens * 4 * 0.9)  # Leave 10% buffer
        
        if len(prompt) > max_chars:
            # Find a good truncation point (end of a sentence or paragraph)
            truncated = prompt[:max_chars]
            
            # Try to truncate at paragraph boundary
            last_paragraph = truncated.rfind('\n\n')
            if last_paragraph > max_chars * 0.7:  # If we have at least 70% of content
                truncated = truncated[:last_paragraph]
            else:
                # Try to truncate at sentence boundary
                last_sentence = truncated.rfind('. ')
                if last_sentence > max_chars * 0.8:  # If we have at least 80% of content
                    truncated = truncated[:last_sentence + 1]
            
            truncated += "\n\n[CONTENT TRUNCATED FOR LENGTH]"
            
            self.logger.warning(f"Prompt truncated from {len(prompt)} to {len(truncated)} characters")
            return truncated
        
        return prompt
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for LLM initialization."""
        return self.system_prompt
    
    def get_prompt_statistics(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about generated prompts."""
        valid_prompts = [p for p in prompts if p['prompt'] is not None]
        
        if not valid_prompts:
            return {
                'total_prompts': len(prompts),
                'valid_prompts': 0,
                'average_length': 0,
                'total_pages': 0
            }
        
        stats = {
            'total_prompts': len(prompts),
            'valid_prompts': len(valid_prompts),
            'average_length': sum(len(p['prompt']) for p in valid_prompts) / len(valid_prompts),
            'max_length': max(len(p['prompt']) for p in valid_prompts),
            'min_length': min(len(p['prompt']) for p in valid_prompts),
            'total_pages': sum(p['page_count'] for p in valid_prompts),
            'average_confidence': sum(p['confidence'] for p in valid_prompts) / len(valid_prompts)
        }
        
        self.logger.info(f"Prompt statistics: {stats}")
        return stats 