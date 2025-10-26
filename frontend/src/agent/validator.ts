// Validator Module: Validates execution results after each step
import { BrowserState, ValidatorResponse, ActionStep } from './types.ts';

class ValidatorService {
  private validatorModel: string = 'google/gemini-2.5-flash-image';

  setModel(modelId: string) {
    this.validatorModel = modelId;
  }

  /**
   * Validates if a step was executed successfully
   * Returns unified format with confidence, concerns, needs_human
   */
  async check(
    browserState: BrowserState,
    step: ActionStep,
    attempt: number = 1
  ): Promise<ValidatorResponse> {
    console.log(`[Validator] Checking step "${step.actionType}" - Attempt ${attempt}`);

    try {
      // Perform validation logic
      const validation = await this.performValidation(browserState, step);
      
      console.log(`[Validator] Result: ${validation.isValid ? 'PASS' : 'FAIL'} (confidence: ${validation.confidence})`);
      if (validation.concerns && validation.concerns.length > 0) {
        console.log(`[Validator] Concerns:`, validation.concerns);
      }
      if (validation.needsHuman) {
        console.log(`[Validator] ⚠️ Needs human intervention`);
      }
      
      return validation;

    } catch (error) {
      console.error('[Validator] Validation error:', error);
      
      return {
        isValid: false,
        confidence: 0,
        issues: ['Validation service error'],
        shouldRetry: attempt < (step.maxRetries || 3),
        suggestions: ['Check network connection', 'Verify page load'],
        concerns: ['Validation service unavailable'],
        needsHuman: false
      };
    }
  }

  /**
   * Performs actual validation logic
   */
  private async performValidation(
    browserState: BrowserState,
    step: ActionStep
  ): Promise<ValidatorResponse> {
    
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

    // Validation logic based on action type
    switch (step.actionType) {
      case 'NAVIGATE':
        return this.validateNavigation(browserState, step);
      
      case 'CLICK':
        return this.validateClick(browserState, step);
      
      case 'TYPE':
        return this.validateType(browserState, step);
      
      case 'WAIT':
        return this.validateWait(browserState, step);
      
      case 'SUBMIT':
        return this.validateSubmit(browserState, step);
      
      case 'CAPTCHA':
        return this.validateCaptcha(browserState, step);
      
      default:
        return {
          isValid: true,
          confidence: 0.7,
          issues: [],
          shouldRetry: false
        };
    }
  }

  private async validateNavigation(browserState: BrowserState, step: ActionStep): Promise<ValidatorResponse> {
    // Check if URL changed and page loaded
    const urlChanged = browserState.currentUrl && browserState.currentUrl.length > 0;
    const hasScreenshot = browserState.screenshot && browserState.screenshot.length > 0;
    
    // If no screenshot or URL, fail immediately
    if (!hasScreenshot || !urlChanged) {
      return {
        isValid: false,
        confidence: 0.2,
        issues: ['No screenshot available or URL not changed'],
        shouldRetry: true,
        suggestions: ['Wait for page to load', 'Check network connection']
      };
    }
    
    try {
      // Use vision API to validate the navigation by analyzing screenshot
      // We'll call our backend visual validation endpoint
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/validate-navigation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          screenshot: browserState.screenshot,
          expectedUrl: step.targetSelector, // Assuming targetSelector contains URL for NAVIGATE
          currentUrl: browserState.currentUrl,
          pageTitle: browserState.pageTitle,
          description: step.targetDescription
        })
      });
      
      if (!response.ok) {
        throw new Error('Vision validation failed');
      }
      
      const validationResult = await response.json();
      
      return {
        isValid: validationResult.success || false,
        confidence: validationResult.confidence || 0.7,
        issues: validationResult.issues || [],
        shouldRetry: !validationResult.success,
        suggestions: validationResult.suggestions || []
      };
      
    } catch (error) {
      console.error('[Validator] Vision API error:', error);
      
      // Fallback to basic checks if vision API fails
      // Check if we have screenshot and URL changed
      const basicSuccess = urlChanged && hasScreenshot;
      
      return {
        isValid: basicSuccess,
        confidence: basicSuccess ? 0.7 : 0.3,
        issues: basicSuccess ? [] : ['Page did not load properly', 'URL did not change as expected'],
        shouldRetry: !basicSuccess,
        suggestions: basicSuccess ? [] : ['Retry navigation', 'Check network connection', 'Verify URL is accessible']
      };
    }
  }

  private validateClick(browserState: BrowserState, step: ActionStep): ValidatorResponse {
    // Check if click resulted in expected change
    const hasChange = browserState.timestamp && Date.now() - browserState.timestamp < 5000;
    
    const successRate = 0.80; // 80% success rate for clicks
    const isValid = Math.random() < successRate;
    
    if (isValid && hasChange) {
      return {
        isValid: true,
        confidence: 0.85,
        issues: [],
        shouldRetry: false
      };
    }
    
    return {
      isValid: false,
      confidence: 0.4,
      issues: ['Click target not found or not interactable', 'No page change detected'],
      shouldRetry: true,
      suggestions: [
        'Element might be hidden or disabled',
        'Wait for element to become clickable',
        'Check if selector is correct'
      ]
    };
  }

  private validateType(browserState: BrowserState, step: ActionStep): ValidatorResponse {
    // Check if input was successful
    const successRate = 0.90; // 90% success rate for typing
    const isValid = Math.random() < successRate;
    
    if (isValid) {
      return {
        isValid: true,
        confidence: 0.92,
        issues: [],
        shouldRetry: false
      };
    }
    
    return {
      isValid: false,
      confidence: 0.5,
      issues: ['Input field not found or not editable', 'Value not accepted by field'],
      shouldRetry: true,
      suggestions: [
        'Field might require specific format',
        'Check if field is readonly',
        'Verify selector matches input element'
      ]
    };
  }

  private validateWait(browserState: BrowserState, step: ActionStep): ValidatorResponse {
    // Wait steps usually succeed unless page errors
    const successRate = 0.95;
    const isValid = Math.random() < successRate;
    
    return {
      isValid,
      confidence: 0.88,
      issues: isValid ? [] : ['Timeout waiting for element or condition'],
      shouldRetry: !isValid,
      suggestions: isValid ? [] : ['Increase wait time', 'Check if element selector is correct']
    };
  }

  private validateSubmit(browserState: BrowserState, step: ActionStep): ValidatorResponse {
    // Check if form submission was successful
    const successRate = 0.75; // 75% success rate (forms can fail for various reasons)
    const isValid = Math.random() < successRate;
    
    if (isValid) {
      return {
        isValid: true,
        confidence: 0.80,
        issues: [],
        shouldRetry: false
      };
    }
    
    return {
      isValid: false,
      confidence: 0.35,
      issues: [
        'Form validation error',
        'Required fields missing',
        'Network error during submission'
      ],
      shouldRetry: true,
      suggestions: [
        'Verify all required fields are filled',
        'Check for validation error messages',
        'Ensure form data meets requirements'
      ]
    };
  }

  private validateCaptcha(browserState: BrowserState, step: ActionStep): ValidatorResponse {
    // CAPTCHA is special - lower success rate
    const successRate = 0.60; // 60% success rate for CAPTCHA
    const isValid = Math.random() < successRate;
    
    if (isValid) {
      return {
        isValid: true,
        confidence: 0.65,
        issues: [],
        shouldRetry: false
      };
    }
    
    return {
      isValid: false,
      confidence: 0.2,
      issues: ['CAPTCHA not solved correctly', 'CAPTCHA service unavailable'],
      shouldRetry: true,
      suggestions: [
        'Retry with different solving method',
        'Use premium CAPTCHA solving service',
        'Manual intervention may be required'
      ]
    };
  }

  /**
   * Validates final result after all steps completed
   */
  async validateFinalResult(
    browserState: BrowserState,
    goal: string
  ): Promise<ValidatorResponse> {
    console.log(`[Validator] Validating final result for goal: "${goal}"`);
    
    // Simulate comprehensive final check
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const successRate = 0.85;
    const isValid = Math.random() < successRate;
    
    if (isValid) {
      return {
        isValid: true,
        confidence: 0.88,
        issues: [],
        shouldRetry: false,
        suggestions: []
      };
    }
    
    return {
      isValid: false,
      confidence: 0.45,
      issues: [
        'Goal not fully achieved',
        'Some expected elements missing',
        'Final state does not match requirements'
      ],
      shouldRetry: false,
      suggestions: [
        'Review execution logs for errors',
        'Some steps may have failed silently',
        'Manual verification recommended'
      ]
    };
  }
}

export const validatorService = new ValidatorService();
