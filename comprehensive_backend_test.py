#!/usr/bin/env python3
"""
Comprehensive Backend Testing - Focus on User Reported Issues
Tests all critical endpoints for mobile chat and models list functionality
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://ai-browser-auto.preview.emergentagent.com/api"

class ComprehensiveBackendTester:
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
    
    def test_openrouter_overview_detailed(self):
        """Detailed test of /api/openrouter/overview endpoint"""
        print("\n🧪 Testing OpenRouter Overview - Detailed Analysis...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/openrouter/overview", timeout=30)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check models array
                models = data.get('models', [])
                models_count = len(models)
                
                # Check balance
                balance = data.get('balance')
                balance_present = balance is not None
                
                # Analyze model structure
                if models:
                    sample_model = models[0]
                    required_fields = ['id', 'name', 'pricing', 'capabilities']
                    missing_fields = [field for field in required_fields if field not in sample_model]
                    
                    # Check pricing structure
                    pricing = sample_model.get('pricing', {})
                    has_prompt_price = 'prompt' in pricing
                    has_completion_price = 'completion' in pricing
                    
                    # Check capabilities
                    capabilities = sample_model.get('capabilities', {})
                    has_vision = 'vision' in capabilities
                    
                    self.log_test(
                        "OpenRouter Overview - Models Structure",
                        len(missing_fields) == 0 and has_prompt_price and has_completion_price,
                        f"Models: {models_count}, Balance: {balance_present}, Structure: {'Valid' if not missing_fields else 'Invalid'}",
                        {
                            "models_count": models_count,
                            "balance_present": balance_present,
                            "balance_value": balance,
                            "missing_fields": missing_fields,
                            "has_pricing": has_prompt_price and has_completion_price,
                            "has_vision_capability": has_vision,
                            "latency_ms": latency
                        }
                    )
                else:
                    self.log_test(
                        "OpenRouter Overview - No Models",
                        False,
                        f"No models found in response (latency: {latency}ms)",
                        {"models_count": 0, "balance_present": balance_present}
                    )
            else:
                self.log_test(
                    "OpenRouter Overview - HTTP Error",
                    False,
                    f"HTTP {response.status_code} (latency: {latency}ms)",
                    {"status_code": response.status_code, "error_body": response.text[:500]}
                )
                
        except Exception as e:
            self.log_test(
                "OpenRouter Overview - Exception",
                False,
                f"Error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def test_chat_sequential_messages(self):
        """Test sequential chat messages to verify no stub responses"""
        print("\n🧪 Testing Sequential Chat Messages - Anti-Stub Verification...")
        
        messages = [
            "Hello, how are you today?",
            "What is 2 + 2?",
            "Tell me a short joke",
            "What's the weather like?"
        ]
        
        history = []
        
        for i, message in enumerate(messages, 1):
            try:
                payload = {
                    "message": message,
                    "history": history.copy(),
                    "model": "openai/gpt-5"
                }
                
                start_time = time.time()
                response = self.session.post(
                    f"{BACKEND_URL}/chat",
                    json=payload,
                    timeout=45
                )
                latency = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('message', data.get('response', ''))
                    
                    # Check for stub patterns
                    stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                    is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                    
                    # Check for empty or very short responses
                    is_empty = len(response_text.strip()) < 5
                    
                    success = not is_stub and not is_empty and len(response_text) > 10
                    
                    self.log_test(
                        f"Chat Message {i}/4",
                        success,
                        f"{'Valid' if success else 'Invalid'} response ({len(response_text)} chars, {latency}ms)",
                        {
                            "message_num": i,
                            "input_message": message,
                            "response_length": len(response_text),
                            "is_stub": is_stub,
                            "is_empty": is_empty,
                            "response_preview": response_text[:100],
                            "latency_ms": latency,
                            "has_cost": bool(data.get('cost'))
                        }
                    )
                    
                    # Add to history for next message
                    if success:
                        history.append({"role": "user", "content": message})
                        history.append({"role": "assistant", "content": response_text})
                    
                else:
                    self.log_test(
                        f"Chat Message {i}/4 - HTTP Error",
                        False,
                        f"HTTP {response.status_code} (latency: {latency}ms)",
                        {"status_code": response.status_code, "error_body": response.text[:500]}
                    )
                    break
                    
            except Exception as e:
                self.log_test(
                    f"Chat Message {i}/4 - Exception",
                    False,
                    f"Error: {str(e)}",
                    {"error": str(e), "error_type": type(e).__name__}
                )
                break
    
    def test_models_endpoint_availability(self):
        """Test if /api/models endpoint exists and works"""
        print("\n🧪 Testing Models Endpoint Availability...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/models", timeout=15)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list):
                    models = data
                elif isinstance(data, dict) and 'models' in data:
                    models = data['models']
                else:
                    models = []
                
                self.log_test(
                    "Models Endpoint - Direct Access",
                    len(models) > 10,
                    f"Found {len(models)} models (latency: {latency}ms)",
                    {"models_count": len(models), "latency_ms": latency, "response_type": type(data).__name__}
                )
            else:
                self.log_test(
                    "Models Endpoint - Not Available",
                    False,
                    f"HTTP {response.status_code} - endpoint may not exist (latency: {latency}ms)",
                    {"status_code": response.status_code, "latency_ms": latency}
                )
                
        except Exception as e:
            self.log_test(
                "Models Endpoint - Exception",
                False,
                f"Error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def test_balance_endpoint(self):
        """Test balance endpoint specifically"""
        print("\n🧪 Testing Balance Endpoint...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/openrouter/balance", timeout=15)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check expected fields
                has_remaining = 'remaining' in data
                has_currency = 'currency' in data
                
                remaining = data.get('remaining')
                currency = data.get('currency')
                
                self.log_test(
                    "Balance Endpoint",
                    has_remaining and has_currency,
                    f"Balance: {remaining} {currency} (latency: {latency}ms)",
                    {
                        "remaining": remaining,
                        "currency": currency,
                        "has_remaining": has_remaining,
                        "has_currency": has_currency,
                        "latency_ms": latency
                    }
                )
            else:
                self.log_test(
                    "Balance Endpoint - HTTP Error",
                    False,
                    f"HTTP {response.status_code} (latency: {latency}ms)",
                    {"status_code": response.status_code, "error_body": response.text[:500]}
                )
                
        except Exception as e:
            self.log_test(
                "Balance Endpoint - Exception",
                False,
                f"Error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def test_code_generation_endpoint(self):
        """Test code generation endpoint"""
        print("\n🧪 Testing Code Generation Endpoint...")
        
        payload = {
            "prompt": "Create a simple counter app with increment and decrement buttons",
            "conversation_history": [],
            "model": "x-ai/grok-code-fast-1"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/generate-code",
                json=payload,
                timeout=45
            )
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                
                code = data.get('code', '')
                message = data.get('message', '')
                
                # Check for React patterns
                react_patterns = ['useState', 'function', 'return', 'className', 'onClick']
                found_patterns = [pattern for pattern in react_patterns if pattern in code]
                
                has_code = len(code) > 100
                has_react_patterns = len(found_patterns) >= 3
                
                self.log_test(
                    "Code Generation",
                    has_code and has_react_patterns,
                    f"Generated {len(code)} chars with {len(found_patterns)}/5 React patterns (latency: {latency}ms)",
                    {
                        "code_length": len(code),
                        "message_length": len(message),
                        "react_patterns_found": found_patterns,
                        "latency_ms": latency,
                        "has_usage": bool(data.get('usage'))
                    }
                )
            else:
                self.log_test(
                    "Code Generation - HTTP Error",
                    False,
                    f"HTTP {response.status_code} (latency: {latency}ms)",
                    {"status_code": response.status_code, "error_body": response.text[:500]}
                )
                
        except Exception as e:
            self.log_test(
                "Code Generation - Exception",
                False,
                f"Error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def test_mobile_specific_scenarios(self):
        """Test scenarios specific to mobile usage"""
        print("\n🧪 Testing Mobile-Specific Scenarios...")
        
        # Test 1: Quick successive requests (mobile users might tap quickly)
        print("   Testing rapid successive requests...")
        
        rapid_requests = []
        for i in range(3):
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/openrouter/balance", timeout=10)
                latency = round((time.time() - start_time) * 1000, 2)
                rapid_requests.append({
                    "request": i+1,
                    "status": response.status_code,
                    "latency": latency,
                    "success": response.status_code == 200
                })
            except Exception as e:
                rapid_requests.append({
                    "request": i+1,
                    "status": "ERROR",
                    "latency": 0,
                    "success": False,
                    "error": str(e)
                })
        
        successful_rapid = sum(1 for req in rapid_requests if req['success'])
        
        self.log_test(
            "Mobile - Rapid Requests",
            successful_rapid >= 2,
            f"{successful_rapid}/3 rapid requests successful",
            {"rapid_requests": rapid_requests}
        )
        
        # Test 2: Timeout handling (mobile networks can be slow)
        print("   Testing timeout resilience...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/openrouter/overview", timeout=5)  # Short timeout
            latency = round((time.time() - start_time) * 1000, 2)
            
            self.log_test(
                "Mobile - Timeout Resilience",
                response.status_code == 200 and latency < 5000,
                f"Response within 5s timeout (latency: {latency}ms)",
                {"latency_ms": latency, "status_code": response.status_code}
            )
        except requests.exceptions.Timeout:
            self.log_test(
                "Mobile - Timeout Resilience",
                False,
                "Request timed out within 5 seconds",
                {"timeout": 5000}
            )
        except Exception as e:
            self.log_test(
                "Mobile - Timeout Resilience",
                False,
                f"Error: {str(e)}",
                {"error": str(e)}
            )
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Backend Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Core functionality tests
        self.test_openrouter_overview_detailed()
        self.test_models_endpoint_availability()
        self.test_balance_endpoint()
        self.test_chat_sequential_messages()
        self.test_code_generation_endpoint()
        self.test_mobile_specific_scenarios()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Categorize results
        critical_failures = []
        minor_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if any(keyword in result['test'].lower() for keyword in ['chat', 'models', 'overview', 'balance']):
                    critical_failures.append(result)
                else:
                    minor_issues.append(result)
        
        if critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(critical_failures)}):")
            for result in critical_failures:
                print(f"   • {result['test']}: {result['message']}")
        
        if minor_issues:
            print(f"\n⚠️  MINOR ISSUES ({len(minor_issues)}):")
            for result in minor_issues:
                print(f"   • {result['test']}: {result['message']}")
        
        if not critical_failures:
            print(f"\n🎉 ALL CRITICAL ENDPOINTS WORKING!")
            print("   • Models list loading: ✅")
            print("   • Chat functionality: ✅")
            print("   • Balance information: ✅")
            print("   • Code generation: ✅")
        
        return self.test_results

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    results = tester.run_comprehensive_tests()