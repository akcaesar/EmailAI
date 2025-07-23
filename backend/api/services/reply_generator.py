"""
Professional email reply generator for job applications.
Generates clean replies FROM the job applicant TO the company.

Author: Akshay NS
"""

from typing import Optional
from .ollama_service import OllamaService
import logging
import re

logger = logging.getLogger(__name__)

class ReplyGenerator:
      def __init__(self, model: Optional[str] = None):
          self.ollama = OllamaService()
          self.applicant_name = "Akshay Shewatkar"
          self.model = model or "llava:latest"  # Default to llava which is more stable

      def generate_reply(self, email_body: str, category: str, sender_name: str = "", model: Optional[str] = None) -> str:
          """Generate an appropriate reply based on email category and content."""

          # Use specified model or default
          selected_model = model or self.model

          # Clean the email body first
          cleaned_email = self._clean_email_content(email_body)

          # Try AI generation first
          ai_reply = self._try_ai_generation(cleaned_email, category, sender_name, selected_model)

          # If AI fails or produces poor quality, use intelligent fallback
          if not ai_reply or len(ai_reply) < 30 or "After that" in ai_reply:
              logger.warning(f"AI generation failed for {category}, using intelligent fallback")
              return self._get_intelligent_fallback(category, cleaned_email, sender_name)

          return ai_reply

      def _clean_email_content(self, email_body: str) -> str:
          """Clean email content for better AI processing."""
          cleaned = re.sub(r'\s+', ' ', email_body.strip())
          if len(cleaned) > 800:
              cleaned = cleaned[:800] + "..."
          return cleaned

      def _try_ai_generation(self, email_content: str, category: str, sender_name: str, model: str) -> str:
          """Try to generate reply using AI with different approaches."""

          # Try simple prompt first
          simple_prompt = self._create_simple_prompt(email_content, category, sender_name)

          try:
              response = self.ollama.generate(
                  prompt=simple_prompt,
                  model=model,
                  options={
                      'temperature': 0.2,
                      'num_predict': 150,
                      'top_p': 0.8,
                      'repeat_penalty': 1.2
                  }
              )

              logger.info(f"AI response from {model}: {response[:100]}...")

              # Clean the response
              cleaned = self._clean_ai_response(response)

              # Validate quality
              if self._is_good_quality(cleaned):
                  return cleaned
              else:
                  logger.warning(f"Poor quality response from {model}")
                  return ""

          except Exception as e:
              logger.error(f"AI generation failed with {model}: {e}")
              return ""

      def _create_simple_prompt(self, email_content: str, category: str, sender_name: str) -> str:
          """Create a simple, clear prompt."""

          greeting = f"Dear {sender_name}," if sender_name else "Dear Hiring Manager,"

          if category == 'query':
              if 'form' in email_content.lower():
                  return f"""Write a professional email reply from {self.applicant_name} to a company.

  Company's message: {email_content}

  Reply with:
  {greeting}

  Thank you for your email. I will complete the requested form promptly and submit it as requested.

  Please let me know if you need any additional information.

  Best regards,
  {self.applicant_name}"""

              elif any(word in email_content.lower() for word in ['document', 'certificate', 'salary', 'information']):
                  return f"""Write a professional email reply from {self.applicant_name} to a company.

  Company's message: {email_content}

  Reply with:
  {greeting}

  Thank you for your email. I will provide the requested information/documents promptly.

  Please let me know if you need anything else.

  Best regards,
  {self.applicant_name}"""

          elif category == 'interview':
              return f"""Write a professional email reply from {self.applicant_name} to a company.

  Company's message: {email_content}

  Reply with:
  {greeting}

  Thank you for the interview invitation. I am very interested in the position and would be happy to attend the interview at your proposed time.

  Please let me know if you need any additional information from me.

  Best regards,
  {self.applicant_name}"""

          elif category == 'confirmation':
              return f"""Write a professional email reply from {self.applicant_name} to a company.

  Company's message: {email_content}

  Reply with:
  {greeting}

  Thank you for confirming receipt of my application. I look forward to hearing from you about the next steps.

  Best regards,
  {self.applicant_name}"""

          # Generic prompt for all categories
          return f"""Write a brief professional email reply from {self.applicant_name} to a company.

  Company's message: {email_content}

  The reply should be professional, brief, and appropriate. Start with "{greeting}" and end with "Best regards, {self.applicant_name}".

  Reply:"""

      def _clean_ai_response(self, response: str) -> str:
          """Clean AI response with enhanced processing to prevent artifacts."""

          # Remove thinking tags and common AI artifacts
          cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
          cleaned = re.sub(r'Write a.*?reply.*?\n', '', cleaned, flags=re.IGNORECASE)
          cleaned = re.sub(r'Company\'s message:.*?\n', '', cleaned, flags=re.IGNORECASE)
          cleaned = re.sub(r'Reply with:.*?\n', '', cleaned, flags=re.IGNORECASE)
          cleaned = re.sub(r'Reply:.*?\n', '', cleaned, flags=re.IGNORECASE)
          
          # Remove instructional text and meta-commentary
          cleaned = re.sub(r'Write a professional.*?\n', '', cleaned, flags=re.IGNORECASE)
          cleaned = re.sub(r'Response:.*?\n', '', cleaned, flags=re.IGNORECASE)
          cleaned = re.sub(r'Here\'s a.*?reply.*?\n', '', cleaned, flags=re.IGNORECASE)
          
          # Remove duplicate greetings - keep only the first one
          lines = cleaned.split('\n')
          clean_lines = []
          greeting_found = False
          
          for line in lines:
              if re.match(r'^\s*dear\s+', line.strip(), re.IGNORECASE):
                  if not greeting_found:
                      clean_lines.append(line)
                      greeting_found = True
                  # Skip duplicate greetings
              else:
                  clean_lines.append(line)
          
          cleaned = '\n'.join(clean_lines)
          
          # Clean up whitespace and line breaks
          cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Max 2 consecutive newlines
          cleaned = re.sub(r'^\s*\n+', '', cleaned)  # Remove leading newlines
          cleaned = re.sub(r'\n+\s*$', '', cleaned)  # Remove trailing newlines
          cleaned = cleaned.strip()

          # Ensure proper email structure
          if not cleaned.lower().startswith(('dear', 'hello', 'hi')):
              cleaned = f"Dear Hiring Manager,\n\n{cleaned}"

          # Handle closing properly - avoid duplicates
          if not cleaned.endswith(self.applicant_name):
              # Check if there's already a closing signature
              if re.search(r'(best\s+regards|sincerely|regards),?\s*$', cleaned, re.IGNORECASE):
                  cleaned += f"\n{self.applicant_name}"
              else:
                  cleaned += f"\n\nBest regards,\n{self.applicant_name}"

          return cleaned

      def _is_good_quality(self, response: str) -> bool:
          """Check if the response is good quality."""

          if not response or len(response) < 20:
              return False

          # Check for common AI artifacts that indicate poor quality
          bad_indicators = [
              'After that', 'Step 1', 'Step 2', 'First,', 'Second,', 'Then,',
              'I should', 'Let me', 'The user', 'The company', 'This email',
              'Write a', 'Generate', 'Create a', 'Note:', 'Remember:', 'Please note',
              'Here is', 'Here\'s', 'I will', 'I am', 'You should', 'You can',
              'Based on', 'According to', 'In response to', 'Regarding your',
              'Thank you for your message', 'I received your', 'Your email',
              'Company\'s message', 'Reply with', 'Response:', 'Email content:'
          ]

          response_lower = response.lower()
          for indicator in bad_indicators:
              if indicator.lower() in response_lower:
                  return False

          # Check for incomplete sentences (common AI artifact)
          if response.endswith('...') or response.endswith(' and') or response.endswith(' or'):
              return False

          # Check for duplicate greetings
          greeting_count = sum(1 for greeting in ['dear', 'hello', 'hi'] 
                              if response_lower.count(greeting) > 1)
          if greeting_count > 0:
              return False

          # Check for proper email structure
          has_greeting = any(greeting in response_lower for greeting in ['dear', 'hello', 'hi'])
          has_closing = any(closing in response_lower for closing in ['regards', 'sincerely'])
          has_name = self.applicant_name in response

          # Check for reasonable length (not too short, not too long)
          if len(response) < 50 or len(response) > 800:
              return False

          return has_greeting and has_closing and has_name

      def _get_intelligent_fallback(self, category: str, email_content: str, sender_name: str) -> str:
          """Generate intelligent fallback based on email content analysis."""

          greeting = f"Dear {sender_name}," if sender_name else "Dear Hiring Manager,"
          content_lower = email_content.lower()

          if category == 'query':
              if 'form' in content_lower:
                  return f"""{greeting}

  Thank you for your email. I will complete the requested form and submit it promptly.

  Please let me know if you need any additional information from me.

  Best regards,
  {self.applicant_name}"""

              elif 'document' in content_lower or 'certificate' in content_lower:
                  return f"""{greeting}

  Thank you for your email. I will provide the requested documents at your earliest convenience.

  Please let me know if you need anything else from me.

  Best regards,
  {self.applicant_name}"""

              elif 'salary' in content_lower or 'expectation' in content_lower:
                  return f"""{greeting}

  Thank you for your email. I will provide my salary expectations and any other requested information promptly.

  Please let me know if you need any additional details.

  Best regards,
  {self.applicant_name}"""

              else:
                  return f"""{greeting}

  Thank you for your email. I will provide the requested information promptly.

  Please let me know if you need anything else from me.

  Best regards,
  {self.applicant_name}"""

          elif category == 'interview':
              return f"""{greeting}

  Thank you for the interview invitation. I am very interested in the position and would be happy to attend the interview at your proposed time.

  Please let me know if you need any additional information from me.

  Best regards,
  {self.applicant_name}"""

          elif category == 'confirmation':
              return f"""{greeting}

  Thank you for confirming receipt of my application. I look forward to hearing from you about the next steps.

  Best regards,
  {self.applicant_name}"""

          elif category == 'rejection':
              return f"""{greeting}

  Thank you for informing me of your decision. I appreciate the time you took to consider my application and would be grateful if you could keep me in mind for       
  future opportunities.

  Best regards,
  {self.applicant_name}"""

          else:
              return f"""{greeting}

  Thank you for your email. I appreciate your communication and look forward to hearing from you.

  Best regards,
  {self.applicant_name}"""

      def generate_follow_up(self, original_email: str, days_passed: int) -> str:
          """Generate follow-up email for pending responses."""

          return f"""Dear Hiring Manager,

  I wanted to follow up on my application from {days_passed} days ago. I remain very interested in this opportunity and would appreciate any update on the status     
   of my application.

  Please let me know if you need any additional information from me.

  Best regards,
  {self.applicant_name}"""


  