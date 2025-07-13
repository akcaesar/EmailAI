
📬 AI Email Assistant for Job Applications
An intelligent, local-first assistant that reads your job application emails (via IMAP), classifies them using a local LLM (via Ollama), and automatically generates polished replies using Django REST Framework as the backend.

v1:
1. Fetch
2. Filter
3. Summarize


Tech stack: Ollama (local), Django DRF



Steps to contribute/Develop:

1. Clone the repo
2. Create virtual env, and install requirements through requirements file.
3. Download Ollama for windows, Then download llava:latest through ollama using ollama run llava:latest
4. To check if the setup works correctly, navigate to 127.0.0.1:8000/api/test-ollama or 127.0.0.1:8000 (for the landing page)
