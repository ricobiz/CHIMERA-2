import os
import httpx
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

OR_BASE = "https://openrouter.ai/api/v1"

class OpenRouterService:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-coder')
        
        self.http_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://lovable.studio"),
            "X-Title": os.environ.get("OPENROUTER_X_TITLE", "Lovable Studio"),
        }
        
        self.system_prompt = """You are an expert full-stack developer specializing in React, HTML, CSS, and JavaScript.

IMPORTANT INSTRUCTIONS:
1. Generate complete, production-ready React code based on user requirements
2. Return ONLY valid React/JavaScript code that can be directly rendered
3. Use modern React patterns with hooks (useState, useEffect, etc.)
4. Include Tailwind CSS classes for styling
5. Make the code self-contained and functional
6. Do NOT include import statements for React or ReactDOM - they're already available
7. Export a default function component
8. Make the app interactive and visually appealing
9. Use proper component structure

Code format example:
function App() {
  const [state, setState] = useState(initialValue);
  
  return (
    <div className="container">
      {/* Your JSX here */}
    </div>
  );
}

export default App;
"""

    async def generate_code(self, prompt: str, conversation_history: List[Dict] = None, model: str = None) -> Dict[str, str]:
        """Generate code using OpenRouter API"""
        try:
            # Use provided model or default
            selected_model = model if model else self.model
            
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend([{"role": msg["role"], "content": msg["content"]} 
                               for msg in conversation_history])
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"Sending request to OpenRouter with model: {selected_model}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{OR_BASE}/chat/completions",
                    headers=self.http_headers,
                    json={
                        "model": selected_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )
                resp.raise_for_status()
                response = resp.json()
            
            generated_content = response['choices'][0]['message']['content']
            
            # Extract code from markdown code blocks if present
            code = self._extract_code(generated_content)
            
            # Generate explanation
            explanation = f"I've created {prompt.lower()}. The code is ready in the preview panel!"
            
            # Get usage statistics
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            
            logger.info(f"Code generated successfully. Tokens used: {usage['total_tokens']}")
            
            return {
                "code": code,
                "message": explanation,
                "usage": usage
            }
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise Exception(f"Failed to generate code: {str(e)}")
    
    def _extract_code(self, content: str) -> str:
        """Extract code from markdown code blocks"""
        # Remove markdown code blocks
        if "```" in content:
            # Extract content between code blocks
            parts = content.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Code block
                    # Remove language identifier
                    lines = part.split('\n')
                    if lines[0].strip() in ['javascript', 'jsx', 'js', 'react', 'tsx', 'typescript']:
                        return '\n'.join(lines[1:])
                    return part
        return content
    
    async def chat_completion(self, messages: List[Dict], model: str = None, temperature: float = 0.7, max_tokens: int = 1000) -> Dict:
        """Generic chat completion method for context management"""
        try:
            selected_model = model if model else self.model
            
            logger.info(f"Chat completion request to OpenRouter with model: {selected_model}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{OR_BASE}/chat/completions",
                    headers=self.http_headers,
                    json={
                        "model": selected_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
            return {
                'choices': [{
                    'message': {
                        'content': data['choices'][0]['message']['content'] if data.get('choices') else ''
                    }
                }],
                'usage': data.get('usage', {})
            }
            
        except httpx.HTTPStatusError as http_err:
            try:
                data = http_err.response.json()
                logger.error(f"Chat completion HTTP error {http_err.response.status_code}: {data}")
                # If rate limited or empty content, return safe fallback
                msg = data.get('error', {}).get('message') if isinstance(data, dict) else str(data)
            except Exception:
                msg = str(http_err)
            raise Exception(f"OpenRouter HTTP error: {msg}")
            
        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise Exception(f"Failed to complete chat: {str(e)}")

    async def get_models(self) -> Dict:
        """Fetch available models and their context limits from OpenRouter API"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://lovable.dev",
                        "X-Title": "Lovable Dev"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch models from OpenRouter: {str(e)}")
            return {"data": []}

openrouter_service = OpenRouterService()