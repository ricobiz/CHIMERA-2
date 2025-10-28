#!/usr/bin/env python3
"""
OpenRouter Integration Testing - Focused on Review Request
Tests the new OpenRouter integration changes as specified in the review request
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://antibot-layer.preview.emergentagent.com/api"

class OpenRouterTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_openrouter_overview_endpoint(self):
        """Test GET /api/openrouter/overview - Models + Balance"""
        print("\n🧪 Testing OpenRouter Overview Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/openrouter/overview", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required top-level keys
                required_keys = ['models', 'balance']
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test(
                        "OpenRouter Overview - Missing Keys",
                        False,
                        f"Response missing required keys: {missing_keys}",
                        {"missing_keys": missing_keys, "response_keys": list(data.keys())}
                    )
                    return
                
                # Validate models array
                models = data.get('models', [])
                if not isinstance(models, list):
                    self.log_test(
                        "OpenRouter Overview - Invalid Models Type",
                        False,
                        f"Models should be array, got {type(models).__name__}",
                        {"models_type": type(models).__name__}
                    )
                    return
                
                # Check models count (should be > 50 as per review)
                if len(models) <= 50:
                    self.log_test(
                        "OpenRouter Overview - Insufficient Models",
                        False,
                        f"Expected >50 models, got {len(models)}",
                        {"model_count": len(models)}
                    )
                else:
                    self.log_test(
                        "OpenRouter Overview - Model Count",
                        True,
                        f"Retrieved {len(models)} models (>50 as expected)",
                        {"model_count": len(models)}
                    )
                
                # Validate model structure
                if models:
                    sample_model = models[0]
                    required_model_fields = ['id', 'name', 'pricing', 'capabilities']
                    missing_model_fields = [field for field in required_model_fields if field not in sample_model]
                    
                    if missing_model_fields:
                        self.log_test(
                            "OpenRouter Overview - Model Structure Invalid",
                            False,
                            f"Model missing fields: {missing_model_fields}",
                            {"missing_fields": missing_model_fields, "sample_model_keys": list(sample_model.keys())}
                        )
                    else:
                        # Check pricing structure
                        pricing = sample_model.get('pricing', {})
                        required_pricing_fields = ['prompt', 'completion']
                        missing_pricing_fields = [field for field in required_pricing_fields if field not in pricing]
                        
                        if missing_pricing_fields:
                            self.log_test(
                                "OpenRouter Overview - Pricing Structure Invalid",
                                False,
                                f"Pricing missing fields: {missing_pricing_fields}",
                                {"missing_pricing_fields": missing_pricing_fields}
                            )
                        else:
                            # Check capabilities structure
                            capabilities = sample_model.get('capabilities', {})
                            if 'vision' not in capabilities:
                                self.log_test(
                                    "OpenRouter Overview - Capabilities Missing Vision",
                                    False,
                                    "Capabilities missing 'vision' boolean field",
                                    {"capabilities_keys": list(capabilities.keys())}
                                )
                            else:
                                self.log_test(
                                    "OpenRouter Overview - Model Structure Valid",
                                    True,
                                    "Model structure contains all required fields",
                                    {
                                        "sample_model_id": sample_model['id'],
                                        "has_pricing": bool(pricing),
                                        "has_vision_capability": isinstance(capabilities.get('vision'), bool)
                                    }
                                )
                
                # Validate balance (number or null)
                balance = data.get('balance')
                if balance is not None and not isinstance(balance, (int, float)):
                    self.log_test(
                        "OpenRouter Overview - Invalid Balance Type",
                        False,
                        f"Balance should be number or null, got {type(balance).__name__}",
                        {"balance_type": type(balance).__name__, "balance_value": balance}
                    )
                else:
                    self.log_test(
                        "OpenRouter Overview - Balance Valid",
                        True,
                        f"Balance is valid: {balance}",
                        {"balance": balance, "balance_type": type(balance).__name__}
                    )
                
                # Overall success if we got here
                self.log_test(
                    "OpenRouter Overview - Overall Success",
                    True,
                    f"Overview endpoint working correctly with {len(models)} models",
                    {"total_models": len(models), "balance": balance}
                )
                
            else:
                self.log_test(
                    "OpenRouter Overview - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response_body": response.text}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "OpenRouter Overview - Timeout",
                False,
                "Request timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "OpenRouter Overview - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "error_message": str(e)}
            )
    
    def test_openrouter_balance_endpoint(self):
        """Test GET /api/openrouter/balance"""
        print("\n🧪 Testing OpenRouter Balance Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/openrouter/balance", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['remaining', 'currency']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "OpenRouter Balance - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
                else:
                    # Validate remaining (number or null)
                    remaining = data.get('remaining')
                    currency = data.get('currency')
                    
                    remaining_valid = remaining is None or isinstance(remaining, (int, float))
                    currency_valid = isinstance(currency, str)
                    
                    if not remaining_valid:
                        self.log_test(
                            "OpenRouter Balance - Invalid Remaining Type",
                            False,
                            f"Remaining should be number or null, got {type(remaining).__name__}",
                            {"remaining_type": type(remaining).__name__, "remaining_value": remaining}
                        )
                    elif not currency_valid:
                        self.log_test(
                            "OpenRouter Balance - Invalid Currency Type",
                            False,
                            f"Currency should be string, got {type(currency).__name__}",
                            {"currency_type": type(currency).__name__, "currency_value": currency}
                        )
                    else:
                        self.log_test(
                            "OpenRouter Balance - Success",
                            True,
                            f"Balance endpoint working: remaining={remaining}, currency={currency}",
                            {"remaining": remaining, "currency": currency}
                        )
                
            else:
                self.log_test(
                    "OpenRouter Balance - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response_body": response.text}
                )
                
        except Exception as e:
            self.log_test(
                "OpenRouter Balance - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "error_message": str(e)}
            )
    
    def test_chat_with_openai_gpt5(self):
        """Test POST /api/chat with model: openai/gpt-5 (frontend model separation)"""
        print("\n🧪 Testing Chat with OpenAI GPT-5 Model...")
        
        payload = {
            "message": "Hi",
            "history": [],
            "model": "openai/gpt-5"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['message', 'usage']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Chat GPT-5 - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
                else:
                    # Validate usage structure
                    usage = data.get('usage', {})
                    required_usage_fields = ['prompt_tokens', 'completion_tokens']
                    missing_usage_fields = [field for field in required_usage_fields if field not in usage]
                    
                    if missing_usage_fields:
                        self.log_test(
                            "Chat GPT-5 - Missing Usage Fields",
                            False,
                            f"Usage missing fields: {missing_usage_fields}",
                            {"missing_usage_fields": missing_usage_fields, "usage_keys": list(usage.keys())}
                        )
                    else:
                        message_text = data.get('message', '')
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        
                        self.log_test(
                            "Chat GPT-5 - Success",
                            True,
                            f"Chat with GPT-5 working: {len(message_text)} chars, {prompt_tokens}+{completion_tokens} tokens",
                            {
                                "model": "openai/gpt-5",
                                "message_length": len(message_text),
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens
                            }
                        )
                
            else:
                self.log_test(
                    "Chat GPT-5 - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response_body": response.text}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Chat GPT-5 - Timeout",
                False,
                "Chat request timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "Chat GPT-5 - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "error_message": str(e)}
            )
    
    def test_generate_code_regression(self):
        """Test POST /api/generate-code with model: x-ai/grok-code-fast-1 (regression sanity)"""
        print("\n🧪 Testing Generate Code Regression with Grok...")
        
        payload = {
            "prompt": "Create a simple counter component",
            "conversation_history": [],
            "model": "x-ai/grok-code-fast-1"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-code",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                if 'code' in data and 'message' in data:
                    code = data.get('code', '')
                    message = data.get('message', '')
                    
                    # Basic validation that it's React-like code
                    react_patterns = ['function', 'const', 'return', 'useState']
                    found_patterns = [pattern for pattern in react_patterns if pattern in code]
                    
                    if len(found_patterns) >= 2:
                        self.log_test(
                            "Generate Code Regression - Success",
                            True,
                            f"Code generation working: {len(code)} chars, {len(found_patterns)} React patterns",
                            {
                                "model": "x-ai/grok-code-fast-1",
                                "code_length": len(code),
                                "react_patterns_found": found_patterns
                            }
                        )
                    else:
                        self.log_test(
                            "Generate Code Regression - Invalid Code",
                            False,
                            f"Generated code doesn't look like React ({len(found_patterns)} patterns found)",
                            {"code_preview": code[:200], "patterns_found": found_patterns}
                        )
                else:
                    self.log_test(
                        "Generate Code Regression - Missing Fields",
                        False,
                        "Response missing 'code' or 'message' fields",
                        {"response_keys": list(data.keys())}
                    )
                
            else:
                self.log_test(
                    "Generate Code Regression - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response_body": response.text}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Generate Code Regression - Timeout",
                False,
                "Code generation timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "Generate Code Regression - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "error_message": str(e)}
            )
    
    def run_all_tests(self):
        """Run all OpenRouter integration tests"""
        print("🚀 Starting OpenRouter Integration Tests...")
        print("=" * 60)
        
        # Test in the order specified in the review request
        self.test_openrouter_overview_endpoint()
        self.test_openrouter_balance_endpoint()
        self.test_chat_with_openai_gpt5()
        self.test_generate_code_regression()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = OpenRouterTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)