"""
Improved Professional email reply generator for job applications.
Generates clean, reliable replies FROM the job applicant TO the company.

Key improvements:
- Simplified AI prompts
- Better template system
- Smarter fallback logic
- Consistent quality output

Author: Akshay NS
"""

from typing import Optional, Dict
from .ollama_service import OllamaService
import logging
import re

logger = logging.getLogger(__name__)

class ImprovedReplyGenerator:
    def __init__(self, model: Optional[str] = None):
        self.ollama = OllamaService()
        self.applicant_name = "Akshay Shewatkar"
        self.model = model or "deepseek-r1:1.5b"  # Use lighter, faster model
        
        # Template-based replies for reliability
        self.templates = {
            'query': {
                'form': """Dear {greeting},

Thank you for your email. I will complete and submit the requested form promptly.

Please let me know if you need any additional information.

Best regards,
{name}""",
                'documents': """Dear {greeting},

Thank you for your email. I will provide the requested documents at your earliest convenience.

Please let me know if you need anything else.

Best regards,
{name}""",
                'salary': """Dear {greeting},

Thank you for your email. I will provide my salary expectations and any other requested information promptly.

Please let me know if you need any additional details.

Best regards,
{name}""",
                'default': """Dear {greeting},

Thank you for your email. I will provide the requested information promptly.

Please let me know if you need anything else.

Best regards,
{name}"""
            },
            'interview': """Dear {greeting},

Thank you for the interview invitation. I am very interested in the position and would be happy to attend at your proposed time.

Please let me know if you need any additional information from me.

Best regards,
{name}""",
            'confirmation': """Dear {greeting},

Thank you for confirming receipt of my application. I look forward to hearing from you about the next steps.

Best regards,
{name}""",
            'rejection': """Dear {greeting},

Thank you for informing me of your decision. I appreciate the time you took to consider my application and would be grateful if you could keep me in mind for future opportunities.

Best regards,
{name}"""
        }

    def generate_reply(self, email_body: str, category: str, sender_name: str = "", model: Optional[str] = None) -> str:
        """Generate an appropriate reply based on email category and content."""
        
        # Clean input
        cleaned_email = self._clean_email_content(email_body)
        greeting = self._get_greeting(sender_name)
        
        # Use template-first approach for reliability
        template_reply = self._get_template_reply(category, cleaned_email, greeting)
        
        # For simple categories, return template directly
        if category in ['confirmation', 'rejection', 'interview']:
            return template_reply
        
        # For query emails, try AI enhancement first, fallback to template
        if category == 'query':
            ai_reply = self._try_ai_enhancement(cleaned_email, template_reply, model or self.model)
            if ai_reply and self._is_valid_reply(ai_reply):
                return ai_reply
            return template_reply
        
        # Default fallback
        return template_reply

    def _clean_email_content(self, email_body: str) -> str:
        """Clean email content for processing."""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', email_body.strip())
        # Truncate if too long
        if len(cleaned) > 600:
            cleaned = cleaned[:600] + "..."
        return cleaned

    def _get_greeting(self, sender_name: str) -> str:
        """Get appropriate greeting."""
        if sender_name and sender_name.strip():
            return sender_name.strip()
        return "Hiring Manager"

    def _get_template_reply(self, category: str, email_content: str, greeting: str) -> str:
        """Get template-based reply."""
        
        if category == 'query':
            # Analyze content for specific query type
            content_lower = email_content.lower()
            
            if any(word in content_lower for word in ['form', 'application form', 'fill out']):
                template = self.templates['query']['form']
            elif any(word in content_lower for word in ['document', 'certificate', 'resume', 'cv']):
                template = self.templates['query']['documents']
            elif any(word in content_lower for word in ['salary', 'expectation', 'compensation']):
                template = self.templates['query']['salary']
            else:
                template = self.templates['query']['default']
        else:
            template = self.templates.get(category, self.templates['query']['default'])
        
        return template.format(greeting=greeting, name=self.applicant_name)

    def _try_ai_enhancement(self, email_content: str, template_reply: str, model: str) -> str:
        """Try to enhance template with AI, but keep it simple."""
        
        # Simple, direct prompt
        prompt = f"""Based on this email: "{email_content}"
        
Improve this reply to be more specific and professional:
"{template_reply}"

Return only the improved email reply, no explanations."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model=model,
                options={
                    'temperature': 0.1,  # Low temperature for consistency
                    'num_predict': 200,  # Limit response length
                    'top_p': 0.7,
                    'repeat_penalty': 1.1
                }
            )
            
            if response:
                cleaned = self._clean_ai_response(response)
                logger.info(f"AI enhanced reply: {cleaned[:100]}...")
                return cleaned
                
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
        
        return ""

    def _clean_ai_response(self, response: str) -> str:
        """Clean AI response with minimal processing."""
        
        # Remove common AI artifacts
        cleaned = re.sub(r'(Here\'s|Here is).*?reply:?\s*', '', response, flags=re.IGNORECASE)
        cleaned = re.sub(r'(Improved|Enhanced).*?reply:?\s*', '', response, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(Based on|Given).*?\n', '', cleaned, flags=re.IGNORECASE)
        
        # Clean whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Ensure proper structure
        if not cleaned.lower().startswith('dear'):
            lines = cleaned.split('\n')
            for i, line in enumerate(lines):
                if line.lower().startswith('dear'):
                    cleaned = '\n'.join(lines[i:])
                    break
        
        return cleaned

    def _is_valid_reply(self, response: str) -> bool:
        """Simple validation for reply quality."""
        
        if not response or len(response) < 50:
            return False
        
        # Check for basic email structure
        has_greeting = response.lower().startswith('dear')
        has_name = self.applicant_name in response
        has_regards = 'regards' in response.lower()
        
        # Check for common AI artifacts
        artifacts = [
            'here is', 'here\'s', 'based on', 'improved', 'enhanced',
            'step 1', 'step 2', 'note:', 'remember:', 'please note'
        ]
        
        has_artifacts = any(artifact in response.lower() for artifact in artifacts)
        
        return has_greeting and has_name and has_regards and not has_artifacts

    def generate_follow_up(self, original_email: str, days_passed: int) -> str:
        """Generate follow-up email for pending responses."""
        
        return f"""Dear Hiring Manager,

I hope this email finds you well. I wanted to follow up on my application submitted {days_passed} days ago.

I remain very interested in this opportunity and would appreciate any update on the status of my application.

Please let me know if you need any additional information from me.

Best regards,
{self.applicant_name}"""

# Backward compatibility
ReplyGenerator = ImprovedReplyGenerator