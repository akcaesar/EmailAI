To test:

go to localhost:8000/api/test-ollama
or 127.0.0.1:8000/api/test-ollama


# README.md

# 📬 AI Email Assistant for Job Applications

An intelligent, local-first assistant that reads your job application emails (via IMAP), classifies them using a local LLM (via Ollama), and automatically generates polished replies using Django REST Framework as the backend.

## Project Overview

This project aims to streamline the job application process by automating email management. The assistant will fetch emails, classify them, and generate responses, making it easier for users to manage their job applications efficiently.

## Features

- **Fetch**: Retrieve job application emails via IMAP.
- **Filter**: Classify emails based on predefined criteria.
- **Summarize**: Generate polished replies to job application emails.

## Tech Stack

- **Backend**: Django REST Framework
- **Local LLM**: Ollama
- **Email Handling**: IMAP

## Steps for Development

1. **Set Up the Environment**: 
   - Create a virtual environment and activate it.
   - Install dependencies using `pip install -r requirements.txt`.

2. **Configure Django Settings**: 
   - Update `settings.py` with database configurations and any other necessary settings.

3. **Define Models**: 
   - Create models in `models.py` to represent the email data structure.

4. **Create Serializers**: 
   - Implement serializers in `serializers.py` to handle data conversion.

5. **Develop Views**: 
   - Write view logic in `views.py` for fetching, filtering, and summarizing emails.

6. **Set Up URLs**: 
   - Define API endpoints in `urls.py` for the application and the API.
#####################Optional for now######################
7. **Implement Background Tasks**: 
   - Use `tasks.py` for any asynchronous processing of emails.

8. **Integrate Ollama**: 
   - Use `ollama_service.py` to connect with the local LLM for email classification.
#####################Optional for now######################
9. **Testing**: 
   - Write tests to ensure the functionality of models, views, and integrations.

10. **Documentation**: 
   - Update this README with setup instructions, usage, and contribution guidelines.

## Collaboration

- Use version control (e.g., Git) to manage code changes.

- #####################Optional for now######################
- Set up a project management tool (e.g., Trello, Jira) for task assignments.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
