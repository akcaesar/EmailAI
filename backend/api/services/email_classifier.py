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

          classification_prompt = f"""Classify this job application email. Return ONLY valid JSON.

Categories: confirmation, rejection, interview, query

Email:
Subject: {subject}
Content: {email_body}

JSON response:
{{"category": "category_name", "confidence": 0.95, "reasoning": "brief explanation"}}"""

          try:
              logger.info(f"Ollama classifying email: {subject[:50]}...")

              # Get response from Ollama with optimized settings
              response = self.ollama.generate(
                  prompt=classification_prompt,
                  model='gemma3:1b',  # Use available model better suited for structured output
                  options={
                      'temperature': 0.1,  # Lower temperature for consistent classification
                      'num_predict': 200,  # Increase tokens to complete JSON response
                      'top_p': 0.8
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
          """Extract and validate JSON response from Ollama with improved parsing."""

          if not response or not response.strip():
              return None

          # Clean the response first
          cleaned_response = response.strip()
          
          # List of improved patterns to try for JSON extraction
          json_patterns = [
              # JSON in code blocks
              r'```(?:json)?\s*(\{[^`]*?\})\s*```',
              # JSON object with category field (more specific)
              r'(\{[^{}]*?"category"\s*:\s*"[^"]*"[^{}]*?\})',
              # Any JSON-like structure
              r'(\{[^{}]*?"[^"]*"\s*:[^{}]*?\})',
              # Direct response (if it looks like JSON)
              r'^(\{.*\})$'
          ]

          for i, pattern in enumerate(json_patterns):
              try:
                  matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
                  for match in matches:
                      json_str = match.strip()
                      
                      # Skip obviously malformed JSON
                      if not (json_str.startswith('{') and json_str.endswith('}')):
                          continue
                          
                      # Try to parse JSON
                      try:
                          parsed = json.loads(json_str)
                      except json.JSONDecodeError:
                          # Try to fix common JSON issues
                          json_str = self._fix_common_json_issues(json_str)
                          try:
                              parsed = json.loads(json_str)
                          except json.JSONDecodeError:
                              continue

                      # Validate structure and required fields
                      if not isinstance(parsed, dict):
                          continue
                          
                      category = parsed.get('category', '').lower()
                      if category not in ['confirmation', 'rejection', 'interview', 'query']:
                          continue

                      # Set priority based on category (1=urgent, 4=low)
                      priority_map = {'interview': 1, 'query': 2, 'rejection': 3, 'confirmation': 4}
                      
                      # Build validated result with safe type conversion
                      validated_result = {
                          'category': category,
                          'confidence': self._safe_float(parsed.get('confidence'), 0.7),
                          'reasoning': str(parsed.get('reasoning', 'AI classification'))[:200],  # Limit reasoning length
                          'priority': priority_map[category]
                      }

                      logger.info(f"Successfully parsed JSON using pattern {i+1}: {validated_result}")
                      return validated_result

              except Exception as e:
                  logger.debug(f"Pattern {i+1} failed: {e}")
                  continue

          logger.warning(f"All JSON parsing attempts failed for response: {cleaned_response[:100]}...")
          return None
      
      def _fix_common_json_issues(self, json_str: str) -> str:
          """Fix common JSON formatting issues."""
          # Fix single quotes to double quotes
          json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
          json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
          
          # Fix missing quotes around values
          json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[,}]', r': "\1",', json_str)
          json_str = re.sub(r':\s*([0-9.]+)\s*[,}]', r': \1,', json_str)
          
          # Fix trailing commas
          json_str = re.sub(r',\s*}', '}', json_str)
          json_str = re.sub(r',\s*]', ']', json_str)
          
          return json_str
      
      def _safe_float(self, value: Any, default: float = 0.0) -> float:
          """Safely convert value to float with bounds checking."""
          try:
              result = float(value)
              return max(0.0, min(1.0, result))  # Clamp between 0 and 1
          except (ValueError, TypeError):
              return default

      def _get_minimal_fallback(self, subject: str, email_body: str) -> Dict[str, Any]:
          """Enhanced fallback classification with improved keyword detection."""

          content = f"{subject} {email_body}".lower()

          # Enhanced keyword patterns for better accuracy
          rejection_keywords = [
              'leider', 'unfortunately', 'not selected', 'regret', 'rejection', 'nicht berücksichtigen',
              'other candidates', 'position filled', 'decided not to', 'move forward with', 'absage',
              'bedauern', 'after careful consideration', 'unfortunately we cannot', 'we regret',
              'nicht in der lage', 'können nicht', 'anzahl anderer', 'qualifizierter kandidaten',
              'zu diesem zeitpunkt', 'nicht fortfahren', 'anderer bewerber'
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

          # Set priority based on category
          priority_map = {'interview': 1, 'query': 2, 'rejection': 3, 'confirmation': 4}

          return {
              "category": category,
              "confidence": confidence,
              "reasoning": f"Fallback classification - {best_score} keywords matched",
              "priority": priority_map[category]
          }

      def generate_summary(self, email_body: str) -> str:
          """Generate summary using Ollama AI."""

          if len(email_body) > 1500:
              email_body = email_body[:1500] + "... [truncated]"

          summary_prompt = f"""Summarize this job application email in 1-2 sentences:

{email_body}

Summary:"""

          try:
              summary = self.ollama.generate(
                  prompt=summary_prompt,
                  model='gemma3:1b',  # Use available model for summaries too
                  options={
                      'temperature': 0.2,
                      'num_predict': 80,  # Shorter for concise summaries
                      'stop': ['\n\n', 'Note:', 'Additional:']
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