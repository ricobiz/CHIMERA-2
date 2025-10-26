// Planner Module: Converts high-level goals into ActionPlans
import { ActionPlan, ActionStep, PlannerResponse } from './types.ts';
import { generatePlan } from '../services/api';

class PlannerService {
  private plannerModel: string = 'openai/gpt-5';

  setModel(modelId: string) {
    this.plannerModel = modelId;
  }

  /**
   * Generates an ActionPlan from a high-level goal using backend LLM
   */
  async getPlan(goal: string): Promise<PlannerResponse> {
    console.log(`[Planner] Generating plan for goal: "${goal}"`);

    try {
      // Call backend planning API with LLM
      console.log(`[Planner] Calling backend API with model: ${this.plannerModel}`);
      const response = await generatePlan(goal, this.plannerModel);
      
      console.log(`[Planner] ✅ Response received from backend:`, response);
      console.log(`[Planner] Plan object:`, response.plan);
      console.log(`[Planner] Plan steps:`, response.plan?.steps);
      console.log(`[Planner] Plan generated: ${response.estimatedSteps} steps, complexity: ${response.complexity}`);
      
      return {
        plan: response.plan,
        complexity: response.complexity as 'simple' | 'moderate' | 'complex',
        estimatedSteps: response.estimatedSteps
      };

    } catch (error) {
      console.error('[Planner] ❌ Error generating plan from backend:', error);
      console.error('[Planner] Error details:', error.message, error.stack);
      
      // Fallback to local heuristic generation
      console.warn('[Planner] Using fallback local planning');
      return this.generateLocalFallbackPlan(goal);
    }
  }

  /**
   * Local fallback plan generator when backend API fails
   */
  private generateLocalFallbackPlan(goal: string): PlannerResponse {
    const goalLower = goal.toLowerCase();
    
    // Extract URL from goal
    const urlMatch = goal.match(/https?:\/\/[^\s]+|[\w-]+\.[\w-]+/);
    const url = urlMatch ? urlMatch[0] : 'https://google.com';
    const fullUrl = url.startsWith('http') ? url : `https://${url}`;
    
    const steps: ActionStep[] = [
      {
        id: 'step-1',
        actionType: 'NAVIGATE',
        targetDescription: `Navigate to ${fullUrl}`,
        targetSelector: fullUrl,
        expectedOutcome: 'Page loaded successfully',
        maxRetries: 3
      },
      {
        id: 'step-2',
        actionType: 'WAIT',
        targetDescription: 'Wait for page to load',
        targetSelector: '',
        expectedOutcome: 'Page fully loaded',
        maxRetries: 1
      }
    ];
    
    // Add registration steps if mentioned
    if (goalLower.includes('register') || goalLower.includes('sign up')) {
      steps.push(
        {
          id: 'step-3',
          actionType: 'CLICK',
          targetDescription: 'sign up button or register link',
          targetSelector: '',
          expectedOutcome: 'Registration form visible',
          maxRetries: 3
        },
        {
          id: 'step-4',
          actionType: 'TYPE',
          targetDescription: 'email field',
          targetSelector: '',
          inputValue: `testuser${Date.now()}@gmail.com`,
          expectedOutcome: 'Email entered',
          maxRetries: 2
        },
        {
          id: 'step-5',
          actionType: 'TYPE',
          targetDescription: 'username field',
          targetSelector: '',
          inputValue: `user${Date.now()}`,
          expectedOutcome: 'Username entered',
          maxRetries: 2
        },
        {
          id: 'step-6',
          actionType: 'TYPE',
          targetDescription: 'password field',
          targetSelector: '',
          inputValue: 'TestPass123!',
          expectedOutcome: 'Password entered',
          maxRetries: 2
        }
      );
      
      // Add bio if mentioned
      if (goalLower.includes('bio') || goalLower.includes('description')) {
        steps.push({
          id: 'step-7',
          actionType: 'TYPE',
          targetDescription: 'bio or description field',
          targetSelector: '',
          inputValue: 'I am a test user created for automation testing purposes.',
          expectedOutcome: 'Bio entered',
          maxRetries: 2
        });
      }
      
      // Add captcha if mentioned
      if (goalLower.includes('captcha')) {
        steps.push({
          id: 'step-8',
          actionType: 'CAPTCHA',
          targetDescription: 'visual captcha element',
          targetSelector: '',
          expectedOutcome: 'Captcha solved',
          maxRetries: 5
        });
      }
      
      // Add submit
      steps.push({
        id: 'step-9',
        actionType: 'CLICK',
        targetDescription: 'submit button or register button',
        targetSelector: '',
        expectedOutcome: 'Form submitted successfully',
        maxRetries: 3
      });
    }
    
    const plan: ActionPlan = {
      goal,
      steps,
      estimatedDuration: steps.length * 5
    };
    
    return {
      plan,
      complexity: 'moderate',
      estimatedSteps: steps.length
    };
  }
}

export const plannerService = new PlannerService();
