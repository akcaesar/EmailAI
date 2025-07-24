
"""
  Author: Akshay NS
  Contains: Ollama service for executing tools and generating responses with AI
"""

import ollama
from typing import Optional, Dict, Any
from django.conf import settings
import logging
from functools import wraps
import os
import re
from dotenv import load_dotenv

  # Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OllamaService:
      def __init__(self):
          self.client = ollama.Client(host=os.getenv('OLLAMA_HOST'))
          self.default_model = os.getenv('OLLAMA_DEFAULT_MODEL', 'deepseek-r1:1.5b')
    
      def _clean_response(self, response_text: str) -> str:
          """Remove thinking content and other AI artifacts from response"""
          if not response_text:
              return ""
          
          # Remove thinking tags and their content
          cleaned = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
          cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
          
          # Remove other common AI artifacts
          cleaned = re.sub(r'<reason>.*?</reason>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
          cleaned = re.sub(r'<analysis>.*?</analysis>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
          
          # Clean up extra whitespace and newlines
          cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # Multiple newlines to single
          cleaned = cleaned.strip()
          
          return cleaned

      def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
          """Generic method to get response from Ollama"""
          try:
              logger.info(f"Sending prompt to Ollama: {prompt[:100]}...")

              # Use requests timeout instead of signal for thread safety
              response = self.client.generate(
                  model=model or self.default_model,
                  prompt=prompt,
                  **kwargs
              )

              logger.info(f"Raw Ollama response: {response}")

              # Check if response is valid
              if not response:
                  logger.warning("Empty response from Ollama")
                  return ""

              # Extract the response content
              response_content = response.get('response', '')

              if not response_content or not response_content.strip():
                  logger.warning("Empty response content from Ollama")
                  return ""

              logger.info(f"Ollama response content: {response_content}")
              
              # Clean the response to remove thinking content and artifacts
              cleaned_content = self._clean_response(response_content)
              logger.info(f"Cleaned Ollama response: {cleaned_content}")
              
              return cleaned_content

          except Exception as e:
              logger.error(f"Error generating response from Ollama: {str(e)}")
              return ""  # Return empty string instead of raising exception

      def chat(self, messages: list, model: Optional[str] = None, **kwargs) -> str:
          """Chat completion style interaction"""
          try:
              logger.info(f"Sending chat messages to Ollama: {messages}")

              # Use requests timeout instead of signal for thread safety
              response = self.client.chat(
                  model=model or self.default_model,
                  messages=messages,
                  **kwargs
              )

              logger.info(f"Raw Ollama chat response: {response}")

              if not response:
                  logger.warning("Empty chat response from Ollama")
                  return ""

              # Extract the message content
              message_content = response.get('message', {}).get('content', '')

              if not message_content or not message_content.strip():
                  logger.warning("Empty message content from Ollama")
                  return ""

              logger.info(f"Ollama chat content: {message_content}")
              
              # Clean the response to remove thinking content and artifacts
              cleaned_content = self._clean_response(message_content)
              logger.info(f"Cleaned Ollama chat response: {cleaned_content}")
              
              return cleaned_content

          except Exception as e:
              logger.error(f"Error in Ollama chat: {str(e)}")
              return ""  # Return empty string instead of raising exception

      def get_embedding(self, text: str, model: Optional[str] = None) -> list:
          """Get embeddings for text"""
          try:
              response = self.client.embeddings(
                  model=model or self.default_model,
                  prompt=text
              )
              return response.get('embedding', [])
          except Exception as e:
              logger.error(f"Error getting embeddings: {str(e)}")
              return []

  # LangChain Tool Integration
class OllamaTools:
      def __init__(self, ollama_service: OllamaService):
          self.ollama = ollama_service

      def as_tool(self, func):
          """Decorator to convert methods to LangChain tools"""
          @wraps(func)
          def wrapper(*args, **kwargs):
              try:
                  return func(*args, **kwargs)
              except Exception as e:
                  return f"Error: {str(e)}"
          return wrapper

      @property
      def email_processor_tool(self):
          """Tool for processing emails"""
          @self.as_tool
          def process_email(email_text: str) -> Dict[str, Any]:
              """Processes email content and returns analysis"""
              summary = self.ollama.generate(
                  prompt=f"Summarize this email: {email_text}",
                  options={'temperature': 0.1}
              )

              classification = self.ollama.generate(
                  prompt=f"Classify this email: {email_text}",
                  options={'temperature': 0.1}
              )

              return {
                  'summary': summary,
                  'classification': classification,
                  'status': 'processed'
              }
          return process_email