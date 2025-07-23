"""
Email classification service using Ollama AI model for job application emails.
Only 4 categories: confirmation, rejection, interview, query

Author: Akshay NS
"""

from typing import Dict, Any, Optional
from .ollama_service import OllamaService
import logging
import json
import re

logger = logging.getLogger(__name__)

class EmailClassifier:
      def __init__(self):
          self.ollama = OllamaService()

      def classify_email(self, email_body: str, subject: str) -> Dict[str, Any]:
          """Classify email using Ollama AI model into exactly 4 job application categories."""

          # Truncate email content if too long
          max_content_length = 3000
          if len(email_body) > max_content_length:
              email_body = email_body[:max_content_length] + "... [truncated]"

          classification_prompt = f"""
  You are an expert email classifier for job application emails. Analyze the email and classify it into EXACTLY ONE category.

  **Categories (choose exactly one):**
  1. "confirmation" - Company confirms receipt of application (acknowledgment only)
  2. "rejection" - Company rejects the application (not selected, position filled)
  3. "interview" - Company invites for interview/meeting or scheduling discussion
  4. "query" - Company requests additional information (documents, salary, forms, clarifications)

  **Email to classify:**
  Subject: {subject}
  Content: {email_body}

  **Classification Rules:**
  - REJECTION: Contains words like "unfortunately", "regret", "not selected", "other candidates", "position filled", "nicht berücksichtigen", "leider"
  - INTERVIEW: Contains words like "interview", "meeting", "schedule", "gespräch", "einladen", "termin", "available", "calendar"
  - QUERY: Contains requests for "documents", "salary", "information", "form", "certificate", "unterlagen", "gehaltsvorstellung", "please provide"
  - CONFIRMATION: Default for acknowledgment emails that don't fit other categories

  **Priority Guidelines:**
  - interview: priority 1 (urgent)
  - query: priority 2 (high) 
  - rejection: priority 3 (medium)
  - confirmation: priority 4 (low)

  **Reply Guidelines:**
  - interview: needs_reply = true
  - query: needs_reply = true
  - rejection: needs_reply = false
  - confirmation: needs_reply = false

  **Response Format (JSON only):**
  {{"category": "one_of_four_categories", "confidence": 0.95, "reasoning": "brief explanation", "priority": 2, "needs_reply": true}}

  Respond with JSON only:
  """

          try:
              logger.info(f"Ollama classifying email: {subject[:50]}...")

              # Get response from Ollama with higher temperature for better reasoning
              response = self.ollama.generate(
                  prompt=classification_prompt,
                  options={
                      'temperature': 0.3,  # Allow some creativity in reasoning
                      'num_predict': 400,  # Allow longer response for reasoning
                      'top_p': 0.9,
                      'repeat_penalty': 1.1
                  }
              )

              logger.info(f"Ollama raw response: '{response}'")

              # Check if response is empty
              if not response or not response.strip():
                  logger.warning("Empty response from Ollama")
                  return self._get_minimal_fallback(subject, email_body)

              # Try to extract and validate JSON
              json_result = self._extract_and_validate_json(response)
              if json_result:
                  logger.info(f"Valid AI classification: {json_result}")
                  return json_result

              # If AI fails, use minimal fallback
              logger.warning(f"AI classification failed, using fallback for: {subject}")
              return self._get_minimal_fallback(subject, email_body)

          except Exception as e:
              logger.error(f"Ollama classification error: {e}")
              return self._get_minimal_fallback(subject, email_body)

      def _extract_and_validate_json(self, response: str) -> Optional[Dict[str, Any]]:
          """Extract and validate JSON response from Ollama."""

          # List of patterns to try for JSON extraction
          json_patterns = [
              # Direct JSON
              r'^(.*)$',
              # JSON in code blocks
              r'```(?:json)?\s*(\{.*?\})\s*```',
              # JSON object anywhere in text
              r'(\{[^{}]*"category"[^{}]*\})',
              # Multiple nested braces
              r'(\{(?:[^{}]|\{[^{}]*\})*\})'
          ]

          for pattern in json_patterns:
              try:
                  matches = re.findall(pattern, response, re.DOTALL)
                  for match in matches:
                      json_str = match.strip()
                      if json_str.startswith('{') and json_str.endswith('}'):
                          parsed = json.loads(json_str)

                          # Validate required fields and category
                          if (isinstance(parsed, dict) and
                              'category' in parsed and
                              parsed['category'] in ['confirmation', 'rejection', 'interview', 'query']):

                              # Ensure all required fields exist with defaults
                              validated_result = {
                                  'category': parsed['category'],
                                  'confidence': float(parsed.get('confidence', 0.7)),
                                  'reasoning': str(parsed.get('reasoning', 'AI classification')),
                                  'priority': int(parsed.get('priority', 3)),
                                  'needs_reply': bool(parsed.get('needs_reply', False))
                              }

                              return validated_result

              except (json.JSONDecodeError, ValueError, KeyError) as e:
                  logger.debug(f"JSON parsing attempt failed: {e}")
                  continue

          return None

      def _get_minimal_fallback(self, subject: str, email_body: str) -> Dict[str, Any]:
          """Enhanced fallback classification with improved keyword detection."""

          content = f"{subject} {email_body}".lower()

          # Enhanced keyword patterns for better accuracy
          rejection_keywords = [
              'leider', 'unfortunately', 'not selected', 'regret', 'rejection', 'nicht berücksichtigen',
              'other candidates', 'position filled', 'decided not to', 'move forward with', 'absage',
              'bedauern', 'after careful consideration', 'unfortunately we cannot', 'we regret'
          ]
          
          interview_keywords = [
              'interview', 'gespräch', 'meeting', 'schedule', 'einladen', 'termin', 'available',
              'calendar', 'invite you for', 'would like to meet', 'discuss your application',
              'phone call', 'video call', 'zoom', 'teams', 'personal conversation'
          ]
          
          query_keywords = [
              'documents', 'certificates', 'salary', 'information', 'unterlagen', 'gehaltsvorstellung',
              'please provide', 'send us', 'we need', 'complete the form', 'fill out',
              'additional information', 'clarification', 'references', 'portfolio'
          ]
          
          confirmation_keywords = [
              'received', 'acknowledgment', 'confirm', 'thank you for', 'application received',
              'will review', 'under review', 'processing', 'bestätigung', 'erhalten'
          ]

          # Score-based classification for better accuracy
          scores = {
              'rejection': sum(1 for word in rejection_keywords if word in content),
              'interview': sum(1 for word in interview_keywords if word in content),
              'query': sum(1 for word in query_keywords if word in content),
              'confirmation': sum(1 for word in confirmation_keywords if word in content)
          }

          # Find category with highest score
          best_category = max(scores, key=scores.get)
          best_score = scores[best_category]

          # If no clear winner, use confirmation as default
          if best_score == 0:
              category = 'confirmation'
              confidence = 0.3
          else:
              category = best_category
              confidence = min(0.8, 0.4 + (best_score * 0.1))  # Max 0.8 for fallback

          # Set priority and needs_reply based on category
          priority_map = {'interview': 1, 'query': 2, 'rejection': 3, 'confirmation': 4}
          needs_reply_map = {'interview': True, 'query': True, 'rejection': False, 'confirmation': False}

          return {
              "category": category,
              "confidence": confidence,
              "reasoning": f"Fallback classification - {best_score} keywords matched",
              "priority": priority_map[category],
              "needs_reply": needs_reply_map[category]
          }

      def generate_summary(self, email_body: str) -> str:
          """Generate summary using Ollama AI."""

          if len(email_body) > 1500:
              email_body = email_body[:1500] + "... [truncated]"

          summary_prompt = f"""
  Create a concise 1-2 sentence summary of this job application email. Focus on the main message and action:

  Email content:
  {email_body}

  Summary (1-2 sentences):"""

          try:
              summary = self.ollama.generate(
                  prompt=summary_prompt,
                  options={
                      'temperature': 0.2,
                      'num_predict': 150
                  }
              )

              if summary and summary.strip():
                  # Clean up the summary
                  clean_summary = summary.strip()
                  
                  # Remove thinking tags and AI artifacts
                  clean_summary = re.sub(r'<think>.*?</think>', '', clean_summary, flags=re.DOTALL | re.IGNORECASE)
                  clean_summary = re.sub(r'<thinking>.*?</thinking>', '', clean_summary, flags=re.DOTALL | re.IGNORECASE)
                  clean_summary = re.sub(r'```.*?```', '', clean_summary, flags=re.DOTALL)
                  
                  # Remove common prefixes
                  for prefix in ['Summary:', 'summary:', 'The email', 'This email']:
                      if clean_summary.startswith(prefix):
                          clean_summary = clean_summary[len(prefix):].strip()
                  
                  # Clean up whitespace
                  clean_summary = re.sub(r'\s+', ' ', clean_summary).strip()

                  return clean_summary if clean_summary else self._generate_fallback_summary(email_body)
              else:
                  return self._generate_fallback_summary(email_body)

          except Exception as e:
              logger.error(f"AI summary generation error: {e}")
              return self._generate_fallback_summary(email_body)

      def _generate_fallback_summary(self, email_body: str) -> str:
          """Simple fallback summary when AI fails."""
          sentences = email_body.split('.')
          if sentences and len(sentences[0]) < 150:
              return sentences[0].strip() + '.'
          else:
              return email_body[:120].strip() + '...'