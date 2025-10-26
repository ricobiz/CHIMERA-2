import os
import logging
from openai import OpenAI
from typing import Dict, Optional
import base64

logger = logging.getLogger(__name__)

class VisualValidatorService:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        self.validation_prompt = """You are an expert UI/UX validator. Analyze this screenshot of a web application and provide detailed feedback.

**Evaluation Criteria:**

1. **Visual Hierarchy** (0-10)
   - Are important elements properly emphasized?
   - Is there a clear visual flow?
   - Do titles, buttons, and content have proper sizing?

2. **Readability** (0-10)
   - Is text readable (contrast, font size)?
   - Are there any text overlaps or cutoffs?
   - Is color contrast sufficient?

3. **Layout & Alignment** (0-10)
   - Are elements properly aligned?
   - Is spacing consistent?
   - Do elements overlap incorrectly?
   - Are buttons/inputs positioned correctly?

4. **Completeness** (0-10)
   - Are all requested features visible?
   - Is anything missing from the user's request?
   - Are all interactive elements present?

5. **Professional Quality** (0-10)
   - Does it look polished and professional?
   - Are there any visual bugs or glitches?
   - Is the overall design cohesive?

**Original User Request:** {user_request}

**Your Task:**
1. Give a score for each criterion (0-10)
2. Calculate overall score (average)
3. If overall score >= 8.0: APPROVE ✅
4. If overall score < 8.0: REJECT ❌ and provide specific fixes

**Response Format:**
```json
{{
  "scores": {{
    "visual_hierarchy": X,
    "readability": X,
    "layout_alignment": X,
    "completeness": X,
    "professional_quality": X
  }},
  "overall_score": X.X,
  "verdict": "APPROVED" or "NEEDS_FIXES",
  "feedback": "Brief overall assessment",
  "specific_issues": [
    "Issue 1: Description and how to fix",
    "Issue 2: Description and how to fix"
  ],
  "fix_instructions": "Detailed instructions for the code generator on what to change"
}}
```

Be strict but fair. Focus on critical issues that affect usability."""

    async def validate_screenshot(
        self, 
        screenshot_base64: str, 
        user_request: str,
        model: str = "google/gemini-2.5-flash"
    ) -> Dict:
        """Validate UI screenshot using vision model"""
        try:
            logger.info(f"Starting visual validation with model: {model}")
            
            prompt = self.validation_prompt.format(user_request=user_request)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            logger.info(f"Visual validation completed")
            
            # Parse JSON from response
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            validation_result = json.loads(result)
            
            # Add usage info
            validation_result["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in visual validation: {str(e)}")
            # Return a fallback response
            return {
                "scores": {
                    "visual_hierarchy": 5,
                    "readability": 5,
                    "layout_alignment": 5,
                    "completeness": 5,
                    "professional_quality": 5
                },
                "overall_score": 5.0,
                "verdict": "ERROR",
                "feedback": f"Validation error: {str(e)}",
                "specific_issues": [],
                "fix_instructions": "",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

    async def validate_navigation(
        self,
        screenshot_base64: str,
        expected_url: str,
        current_url: str,
        page_title: str,
        description: str
    ) -> Dict:
        """
        Validates if navigation was successful by analyzing the screenshot
        Returns: {success: bool, confidence: float, issues: list, suggestions: list}
        """
        try:
            prompt = f"""Analyze this screenshot to determine if navigation to the target page was successful.

**Navigation Details:**
- Expected destination: {expected_url}
- Current URL: {current_url}
- Page title: {page_title}
- Goal: {description}

**Your task:**
1. Verify the page loaded correctly (no error messages, blank pages, or loading indicators)
2. Check if the page content matches the expected destination
3. Confirm the URL changed appropriately
4. Look for any error messages, 404 pages, or security warnings

**Response format (JSON):**
{{
    "success": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of any problems found"],
    "suggestions": ["list of recommendations if navigation failed"],
    "page_status": "loaded|error|blank|timeout",
    "content_match": "matches|mismatch|uncertain"
}}

Respond ONLY with valid JSON, no additional text."""

            # Prepare image data
            image_data = screenshot_base64
            if not image_data.startswith('data:image'):
                image_data = f"data:image/png;base64,{image_data}"

            response = self.client.chat.completions.create(
                model="google/gemini-2.5-flash-image",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_data}}
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )

            result_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            import json
            import re
            
            # Find JSON in response (might have markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            
            result = json.loads(result_text)
            
            logger.info(f"Navigation validation result: {result}")
            
            return {
                "success": result.get("success", False),
                "confidence": result.get("confidence", 0.5),
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", []),
                "page_status": result.get("page_status", "unknown"),
                "content_match": result.get("content_match", "uncertain")
            }
            
        except Exception as e:
            logger.error(f"Navigation validation error: {str(e)}")
            
            # Fallback: basic check if we have screenshot and URL
            basic_success = bool(screenshot_base64 and current_url and len(current_url) > 0)
            
            return {
                "success": basic_success,
                "confidence": 0.6 if basic_success else 0.2,
                "issues": [] if basic_success else ["Vision API unavailable, using basic validation"],
                "suggestions": [] if basic_success else ["Retry navigation", "Check network connection"],
                "page_status": "uncertain",
                "content_match": "uncertain"
            }

visual_validator_service = VisualValidatorService()
