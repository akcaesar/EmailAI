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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.client = ollama.Client(host=os.getenv('OLLAMA_HOST'))
        self.default_model = os.getenv('OLLAMA_DEFAULT_MODEL', 'deepseek-r1:1.5b')

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """Generic method to get response from Ollama"""
        try:
            response = self.client.generate(
                model=model or self.default_model,
                prompt=prompt,
                **kwargs
            )
            return response['response']
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {str(e)}")
            raise

    def chat(self, messages: list, model: Optional[str] = None, **kwargs) -> str:
        """Chat completion style interaction"""
        try:
            response = self.client.chat(
                model=model or self.default_model,
                messages=messages,
                **kwargs
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Error in Ollama chat: {str(e)}")
            raise

    def get_embedding(self, text: str, model: Optional[str] = None) -> list:
        """Get embeddings for text"""
        try:
            response = self.client.embeddings(
                model=model or self.default_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

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