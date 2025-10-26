// Planner Module: Converts high-level goals into ActionPlans
import { ActionPlan, ActionStep, PlannerResponse } from './types.ts';
import { researchTask } from '../services/api';

class PlannerService {
  private plannerModel: string = 'anthropic/claude-3.5-sonnet';

  setModel(modelId: string) {
    this.plannerModel = modelId;
  }

  /**
   * Generates an ActionPlan from a high-level goal
   */
  async getPlan(goal: string): Promise<PlannerResponse> {
    console.log(`[Planner] Generating plan for goal: "${goal}"`);

    try {
      // First, analyze complexity with Research Planner
      const research = await researchTask(goal, this.plannerModel, 'analyze');
      
      const complexity = research.complexity_assessment || 'moderate';
      const requiresResearch = research.requires_research;

      console.log(`[Planner] Task complexity: ${complexity}, requires research: ${requiresResearch}`);

      // Generate step-by-step plan
      // In production, this would call the LLM to break down the task
      // For now, we create a structured plan based on common patterns
      
      const steps = this.generateStepsForGoal(goal);

      const plan: ActionPlan = {
        goal,
        steps,
        estimatedDuration: steps.length * 3 // 3 seconds per step average
      };

      return {
        plan,
        complexity: complexity as 'simple' | 'moderate' | 'complex',
        estimatedSteps: steps.length
      };

    } catch (error) {
      console.error('[Planner] Error generating plan:', error);
      
      // Fallback to basic plan
      const steps = this.generateStepsForGoal(goal);
      return {
        plan: {
          goal,
          steps,
          estimatedDuration: steps.length * 3
        },
        complexity: 'moderate',
        estimatedSteps: steps.length
      };
    }
  }

  /**
   * Generate action steps based on goal analysis
   * This is a smart heuristic-based generator
   */
  private generateStepsForGoal(goal: string): ActionStep[] {
    const steps: ActionStep[] = [];
    const goalLower = goal.toLowerCase();

    // Pattern matching for common automation tasks
    if (goalLower.includes('gmail') || goalLower.includes('google account')) {
      return this.generateGmailRegistrationSteps();
    }

    if (goalLower.includes('amazon') || goalLower.includes('buy') || goalLower.includes('shop')) {
      return this.generateShoppingSteps(goal);
    }

    if (goalLower.includes('login') || goalLower.includes('sign in')) {
      return this.generateLoginSteps(goal);
    }

    if (goalLower.includes('search') || goalLower.includes('find')) {
      return this.generateSearchSteps(goal);
    }

    if (goalLower.includes('form') || goalLower.includes('fill') || goalLower.includes('submit')) {
      return this.generateFormSteps(goal);
    }

    // Generic task breakdown
    return this.generateGenericSteps(goal);
  }

  private generateGmailRegistrationSteps(): ActionStep[] {
    return [
      {
        id: 'step-1',
        actionType: 'NAVIGATE',
        targetDescription: 'Google Account Creation Page',
        targetSelector: '',
        expectedOutcome: 'Page loads with "Create your Google Account" form',
        maxRetries: 3
      },
      {
        id: 'step-2',
        actionType: 'TYPE',
        targetDescription: 'First Name field',
        targetSelector: 'input[name="firstName"]',
        inputValue: '[AUTO_GENERATE]',
        expectedOutcome: 'First name entered successfully',
        maxRetries: 2
      },
      {
        id: 'step-3',
        actionType: 'TYPE',
        targetDescription: 'Last Name field',
        targetSelector: 'input[name="lastName"]',
        inputValue: '[AUTO_GENERATE]',
        expectedOutcome: 'Last name entered successfully',
        maxRetries: 2
      },
      {
        id: 'step-4',
        actionType: 'TYPE',
        targetDescription: 'Username field',
        targetSelector: 'input[name="Username"]',
        inputValue: '[AUTO_GENERATE]',
        expectedOutcome: 'Username entered and available',
        maxRetries: 5
      },
      {
        id: 'step-5',
        actionType: 'TYPE',
        targetDescription: 'Password field',
        targetSelector: 'input[name="Passwd"]',
        inputValue: '[AUTO_GENERATE_STRONG]',
        expectedOutcome: 'Password meets requirements',
        maxRetries: 2
      },
      {
        id: 'step-6',
        actionType: 'CLICK',
        targetDescription: 'Next button',
        targetSelector: 'button[type="button"]',
        expectedOutcome: 'Proceeds to phone verification',
        maxRetries: 3
      },
      {
        id: 'step-7',
        actionType: 'WAIT',
        targetDescription: 'Wait for phone verification page',
        expectedOutcome: 'Phone input field visible',
        maxRetries: 1
      }
    ];
  }

  private generateShoppingSteps(goal: string): ActionStep[] {
    return [
      {
        id: 'step-1',
        actionType: 'NAVIGATE',
        targetDescription: 'E-commerce website',
        expectedOutcome: 'Homepage loads',
        maxRetries: 3
      },
      {
        id: 'step-2',
        actionType: 'TYPE',
        targetDescription: 'Search box',
        targetSelector: 'input[type="search"]',
        inputValue: '[EXTRACTED_FROM_GOAL]',
        expectedOutcome: 'Search term entered',
        maxRetries: 2
      },
      {
        id: 'step-3',
        actionType: 'CLICK',
        targetDescription: 'Search button',
        targetSelector: 'button[type="submit"]',
        expectedOutcome: 'Search results displayed',
        maxRetries: 2
      },
      {
        id: 'step-4',
        actionType: 'CLICK',
        targetDescription: 'First product result',
        targetSelector: '.product-item:first-child',
        expectedOutcome: 'Product page opens',
        maxRetries: 2
      },
      {
        id: 'step-5',
        actionType: 'CLICK',
        targetDescription: 'Add to cart button',
        targetSelector: 'button[name="add-to-cart"]',
        expectedOutcome: 'Item added to cart',
        maxRetries: 3
      }
    ];
  }

  private generateLoginSteps(goal: string): ActionStep[] {
    return [
      {
        id: 'step-1',
        actionType: 'NAVIGATE',
        targetDescription: 'Login page',
        expectedOutcome: 'Login form visible',
        maxRetries: 3
      },
      {
        id: 'step-2',
        actionType: 'TYPE',
        targetDescription: 'Email/Username field',
        targetSelector: 'input[type="email"], input[name="username"]',
        inputValue: '[USER_PROVIDED]',
        expectedOutcome: 'Credentials entered',
        maxRetries: 2
      },
      {
        id: 'step-3',
        actionType: 'TYPE',
        targetDescription: 'Password field',
        targetSelector: 'input[type="password"]',
        inputValue: '[USER_PROVIDED]',
        expectedOutcome: 'Password entered',
        maxRetries: 2
      },
      {
        id: 'step-4',
        actionType: 'CLICK',
        targetDescription: 'Login button',
        targetSelector: 'button[type="submit"]',
        expectedOutcome: 'Successfully logged in',
        maxRetries: 3
      }
    ];
  }

  private generateSearchSteps(goal: string): ActionStep[] {
    return [
      {
        id: 'step-1',
        actionType: 'NAVIGATE',
        targetDescription: 'Search engine or target website',
        expectedOutcome: 'Page loads with search capability',
        maxRetries: 3
      },
      {
        id: 'step-2',
        actionType: 'TYPE',
        targetDescription: 'Search input field',
        targetSelector: 'input[type="search"], input[name="q"]',
        inputValue: '[EXTRACTED_FROM_GOAL]',
        expectedOutcome: 'Search query entered',
        maxRetries: 2
      },
      {
        id: 'step-3',
        actionType: 'SUBMIT',
        targetDescription: 'Submit search',
        targetSelector: 'form[role="search"]',
        expectedOutcome: 'Search results displayed',
        maxRetries: 2
      }
    ];
  }

  private generateFormSteps(goal: string): ActionStep[] {
    return [
      {
        id: 'step-1',
        actionType: 'NAVIGATE',
        targetDescription: 'Form page',
        expectedOutcome: 'Form visible and ready',
        maxRetries: 3
      },
      {
        id: 'step-2',
        actionType: 'TYPE',
        targetDescription: 'Fill form fields',
        targetSelector: 'input, textarea, select',
        inputValue: '[AUTO_GENERATE_OR_USER_PROVIDED]',
        expectedOutcome: 'All required fields filled',
        maxRetries: 2
      },
      {
        id: 'step-3',
        actionType: 'SUBMIT',
        targetDescription: 'Submit form',
        targetSelector: 'button[type="submit"], input[type="submit"]',
        expectedOutcome: 'Form submitted successfully',
        maxRetries: 3
      }
    ];
  }

  private generateGenericSteps(goal: string): ActionStep[] {
    // Generic breakdown for any task
    const words = goal.split(' ');
    const steps: ActionStep[] = [];

    steps.push({
      id: 'step-1',
      actionType: 'NAVIGATE',
      targetDescription: 'Navigate to target website',
      expectedOutcome: 'Page loaded successfully',
      maxRetries: 3
    });

    steps.push({
      id: 'step-2',
      actionType: 'WAIT',
      targetDescription: 'Wait for page to fully load',
      expectedOutcome: 'All elements loaded',
      maxRetries: 1
    });

    steps.push({
      id: 'step-3',
      actionType: 'CLICK',
      targetDescription: 'Interact with primary element',
      targetSelector: 'button, a, input',
      expectedOutcome: 'Action completed',
      maxRetries: 2
    });

    return steps;
  }
}

export const plannerService = new PlannerService();
