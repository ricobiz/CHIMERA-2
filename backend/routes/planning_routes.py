from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["planning"])

class PlanningRequest(BaseModel):
    goal: str
    model: str = "openai/gpt-5"

class ActionStep(BaseModel):
    id: str
    actionType: str
    targetDescription: str
    targetSelector: str = ""
    inputValue: str = ""
    expectedOutcome: str
    maxRetries: int = 3

class ActionPlan(BaseModel):
    goal: str
    steps: List[ActionStep]
    estimatedDuration: int

class PlanningResponse(BaseModel):
    plan: ActionPlan
    complexity: str
    estimatedSteps: int

@router.post("/planning/generate")
async def generate_plan(request: PlanningRequest):
    """
    Generate detailed action plan for browser automation using LLM
    """
    try:
        logger.info(f"Generating plan for goal: {request.goal}")
        
        # Create detailed prompt for LLM
        prompt = f"""You are a browser automation planner. Given a user goal, generate a detailed step-by-step action plan.

USER GOAL: {request.goal}

Generate a JSON plan with the following structure:
{{
  "steps": [
    {{
      "id": "step-1",
      "actionType": "NAVIGATE",  // Options: NAVIGATE, CLICK, TYPE, WAIT, SUBMIT, CAPTCHA
      "targetDescription": "Human-readable description of target element",
      "targetSelector": "CSS selector or URL (for NAVIGATE)",
      "inputValue": "[AUTO_GENERATE]" or actual value,
      "expectedOutcome": "What should happen after this step",
      "maxRetries": 3
    }},
    ...
  ],
  "complexity": "simple|moderate|complex",
  "notes": "Any important notes about the plan"
}}

IMPORTANT INSTRUCTIONS:
1. For NAVIGATE actions, put the full URL in targetSelector
2. For CLICK/TYPE actions, use clear targetDescription (e.g., "sign up button", "email field")
3. Use [AUTO_GENERATE] for fields that need realistic random data
4. Include CAPTCHA step if visual captcha is mentioned
5. Break down complex tasks into small, atomic steps
6. For registration: navigate → find form → fill fields → solve captcha → submit
7. Be specific and detailed

Generate the plan now (respond ONLY with valid JSON):"""

        # Call LLM
        messages = [
            {"role": "system", "content": "You are a precise JSON-generating automation planner. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        response = await openrouter_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=0.3  # Low temperature for consistent planning
        )
        
        # Parse LLM response
        import json
        plan_text = response['choices'][0]['message']['content']
        
        # Extract JSON from response (in case LLM adds markdown)
        if '```json' in plan_text:
            plan_text = plan_text.split('```json')[1].split('```')[0].strip()
        elif '```' in plan_text:
            plan_text = plan_text.split('```')[1].split('```')[0].strip()
        
        plan_data = json.loads(plan_text)
        
        # Build response
        steps = []
        for i, step in enumerate(plan_data.get('steps', [])):
            steps.append(ActionStep(
                id=step.get('id', f'step-{i+1}'),
                actionType=step.get('actionType', 'WAIT'),
                targetDescription=step.get('targetDescription', ''),
                targetSelector=step.get('targetSelector', ''),
                inputValue=step.get('inputValue', ''),
                expectedOutcome=step.get('expectedOutcome', ''),
                maxRetries=step.get('maxRetries', 3)
            ))
        
        action_plan = ActionPlan(
            goal=request.goal,
            steps=steps,
            estimatedDuration=len(steps) * 5  # 5 seconds per step
        )
        
        return {
            "plan": action_plan,
            "complexity": plan_data.get('complexity', 'moderate'),
            "estimatedSteps": len(steps),
            "notes": plan_data.get('notes', '')
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
        logger.error(f"LLM Response: {plan_text}")
        
        # Fallback to basic plan
        return generate_fallback_plan(request.goal)
        
    except Exception as e:
        logger.error(f"Planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")

def generate_fallback_plan(goal: str) -> Dict:
    """Generate a basic fallback plan when LLM fails"""
    goal_lower = goal.lower()
    
    # Extract URL if present
    import re
    url_match = re.search(r'https?://[^\s]+|[\w-]+\.[\w-]+', goal)
    url = url_match.group(0) if url_match else 'https://google.com'
    if not url.startswith('http'):
        url = f'https://{url}'
    
    steps = [
        ActionStep(
            id='step-1',
            actionType='NAVIGATE',
            targetDescription=f'Navigate to {url}',
            targetSelector=url,
            expectedOutcome='Page loaded successfully',
            maxRetries=3
        ),
        ActionStep(
            id='step-2',
            actionType='WAIT',
            targetDescription='Wait for page to load',
            expectedOutcome='Page fully loaded',
            maxRetries=1
        )
    ]
    
    # Add registration steps if mentioned
    if 'register' in goal_lower or 'sign up' in goal_lower:
        steps.extend([
            ActionStep(
                id='step-3',
                actionType='CLICK',
                targetDescription='sign up button',
                expectedOutcome='Registration form visible',
                maxRetries=3
            ),
            ActionStep(
                id='step-4',
                actionType='TYPE',
                targetDescription='email field',
                inputValue='[AUTO_GENERATE]',
                expectedOutcome='Email entered',
                maxRetries=2
            ),
            ActionStep(
                id='step-5',
                actionType='TYPE',
                targetDescription='username field',
                inputValue='[AUTO_GENERATE]',
                expectedOutcome='Username entered',
                maxRetries=2
            ),
            ActionStep(
                id='step-6',
                actionType='TYPE',
                targetDescription='password field',
                inputValue='[AUTO_GENERATE]',
                expectedOutcome='Password entered',
                maxRetries=2
            ),
            ActionStep(
                id='step-7',
                actionType='CLICK',
                targetDescription='submit button',
                expectedOutcome='Form submitted',
                maxRetries=3
            )
        ])
    
    return {
        "plan": ActionPlan(
            goal=goal,
            steps=steps,
            estimatedDuration=len(steps) * 5
        ),
        "complexity": "moderate",
        "estimatedSteps": len(steps),
        "notes": "Fallback plan - LLM planning unavailable"
    }
