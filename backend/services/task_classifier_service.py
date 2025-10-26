"""
Task Classifier Service
Determines if user input is:
- Browser automation task
- Code generation task
- Document verification task
- General chat
"""

import logging
from typing import Dict
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class TaskClassifierService:
    def __init__(self):
        self.classification_prompt = """You are a task classifier. Analyze the user's message and determine what type of task it is.

User message: "{message}"

Classify this message into ONE of these categories:

1. **browser_automation**: User wants to automate browser actions (navigate, click, fill forms, scrape data, interact with websites)
   Examples: "Go to Google and search for AI", "Login to Twitter", "Fill out this form", "Click the buy button"

2. **code_generation**: User wants to generate/create an application, website, or code
   Examples: "Build a todo app", "Create a calculator", "Make a dashboard", "Design a login page"

3. **document_verification**: User wants to verify/check a document for authenticity
   Examples: "Check if this document is real", "Verify this ID", "Is this document fake?"

4. **general_chat**: General conversation, questions, or requests that don't fit above categories
   Examples: "What can you do?", "Explain browser automation", "How does this work?"

Respond with ONLY a JSON object in this exact format:
{{
  "task_type": "browser_automation" | "code_generation" | "document_verification" | "general_chat",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}"""

    async def classify_task(self, user_message: str, model: str = "anthropic/claude-3.5-sonnet") -> Dict:
        """
        Classify user message to determine task type
        
        Returns:
            {
                "task_type": str,
                "confidence": float,
                "reasoning": str
            }
        """
        try:
            prompt = self.classification_prompt.format(message=user_message)
            
            messages = [
                {"role": "system", "content": "You are a precise task classifier. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            logger.info(f"Classifying task: {user_message[:100]}...")
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=model,
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=200
            )
            
            response_text = response['choices'][0]['message']['content'].strip()
            
            # Extract JSON from response
            import json
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            classification = json.loads(response_text)
            
            logger.info(f"Classification result: {classification['task_type']} (confidence: {classification['confidence']})")
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying task: {str(e)}")
            # Default to code_generation if classification fails
            return {
                "task_type": "code_generation",
                "confidence": 0.5,
                "reasoning": f"Classification failed, defaulting to code generation. Error: {str(e)}"
            }

# Global instance
task_classifier = TaskClassifierService()
