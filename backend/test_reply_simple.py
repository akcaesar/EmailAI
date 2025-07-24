"""
Simple test for reply generator logic without Django dependencies.
"""

import re

def test_clean_response():
    """Test the response cleaning logic."""
    
    # Mock the applicant name
    applicant_name = "Akshay Shewatkar"
    
    def clean_ai_response(response: str) -> str:
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
        if not cleaned.endswith(applicant_name):
            # Check if there's already a closing signature
            if re.search(r'(best\s+regards|sincerely|regards),?\s*$', cleaned, re.IGNORECASE):
                cleaned += f"\n{applicant_name}"
            else:
                cleaned += f"\n\nBest regards,\n{applicant_name}"

        return cleaned
    
    # Test cases with problematic AI responses
    test_cases = [
        {
            "name": "Double Greeting",
            "input": "Dear Hiring Manager,\n\nThank you for your email.\n\nDear People Manager,\n\nI appreciate your message.\n\nBest regards,",
            "expected_issues": ["Only one greeting should remain"]
        },
        {
            "name": "Missing Structure",
            "input": "Thank you for your email. I will provide the information requested.",
            "expected_issues": ["Should have proper greeting and closing"]
        },
        {
            "name": "AI Instructions",
            "input": "Write a professional reply:\n\nDear Hiring Manager,\n\nThank you for your email.\n\nBest regards,",
            "expected_issues": ["Should remove AI instructions"]
        },
        {
            "name": "Incomplete Response",
            "input": "Dear Hiring Manager,\n\nThank you for your email and",
            "expected_issues": ["Should complete the response"]
        }
    ]
    
    print("🧪 Testing Reply Cleaning Logic")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📧 Test Case {i}: {test_case['name']}")
        print("-" * 30)
        
        print(f"Input:")
        print(repr(test_case['input']))
        
        cleaned = clean_ai_response(test_case['input'])
        
        print(f"\nCleaned Output:")
        print(repr(cleaned))
        
        print(f"\nFormatted Output:")
        print(cleaned)
        
        # Quality checks
        print(f"\n✅ Quality Checks:")
        print(f"   - Has greeting: {'✓' if cleaned.lower().startswith(('dear', 'hello', 'hi')) else '✗'}")
        print(f"   - Has closing: {'✓' if any(closing in cleaned.lower() for closing in ['regards', 'sincerely']) else '✗'}")
        print(f"   - Has name: {'✓' if applicant_name in cleaned else '✗'}")
        print(f"   - No duplicates: {'✓' if cleaned.lower().count('dear') <= 1 else '✗'}")
        print(f"   - No AI artifacts: {'✓' if not any(artifact in cleaned.lower() for artifact in ['write a', 'reply:', 'response:']) else '✗'}")

if __name__ == "__main__":
    test_clean_response()