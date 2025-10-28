#!/usr/bin/env python3
"""
User Reported Issues Testing - Mobile Chat & Models List
Tests specific endpoints mentioned in user review request
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://antibot-layer.preview.emergentagent.com/api"

class UserReportedIssuesTester:
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
    
    def test_health_basic_connectivity(self):
        """1) Health/basic connectivity: Try hitting /api/openrouter/overview"""
        print("\n🧪 Testing Health/Basic Connectivity - /api/openrouter/overview...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/openrouter/overview", timeout=30)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_test(
                        "Health Check - OpenRouter Overview",
                        True,
                        f"Status 200 - Server is UP (latency: {latency}ms)",
                        {"status_code": 200, "latency_ms": latency, "has_models": bool(data.get('models')), "has_balance": 'balance' in data}
                    )
                    return True, data
                except json.JSONDecodeError:
                    self.log_test(
                        "Health Check - Invalid JSON",
                        False,
                        f"Status 200 but invalid JSON response (latency: {latency}ms)",
                        {"status_code": 200, "latency_ms": latency, "response_preview": response.text[:200]}
                    )
                    return False, None
            else:
                # Retry once as requested
                print("   First attempt failed, retrying once...")
                time.sleep(2)
                
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/openrouter/overview", timeout=30)
                latency = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test(
                            "Health Check - OpenRouter Overview (Retry)",
                            True,
                            f"Status 200 on retry - Server is UP (latency: {latency}ms)",
                            {"status_code": 200, "latency_ms": latency, "retry": True}
                        )
                        return True, data
                    except json.JSONDecodeError:
                        self.log_test(
                            "Health Check - Invalid JSON (Retry)",
                            False,
                            f"Status 200 on retry but invalid JSON (latency: {latency}ms)",
                            {"status_code": 200, "latency_ms": latency, "retry": True}
                        )
                        return False, None
                else:
                    self.log_test(
                        "Health Check - Server Down",
                        False,
                        f"Status {response.status_code} on retry - Server may be DOWN (latency: {latency}ms)",
                        {"status_code": response.status_code, "latency_ms": latency, "error_body": response.text[:500]}
                    )
                    return False, None
                    
        except requests.exceptions.Timeout:
            self.log_test(
                "Health Check - Timeout",
                False,
                "Request timed out after 30 seconds - Server may be DOWN",
                {"timeout": 30, "error": "Connection timeout"}
            )
            return False, None
        except requests.exceptions.ConnectionError as e:
            self.log_test(
                "Health Check - Connection Error",
                False,
                f"Connection error - Server is DOWN: {str(e)}",
                {"error": str(e), "error_type": "ConnectionError"}
            )
            return False, None
        except Exception as e:
            self.log_test(
                "Health Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False, None
    
    def test_models_endpoints(self, overview_data=None):
        """2) Models endpoints: /api/models (if exists) or only /api/openrouter/overview"""
        print("\n🧪 Testing Models Endpoints...")
        
        # First try /api/models
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/models", timeout=15)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    models = data.get('models', data if isinstance(data, list) else [])
                    
                    if len(models) > 10:
                        self.log_test(
                            "Models Endpoint - /api/models",
                            True,
                            f"Found {len(models)} models (>10 as required) (latency: {latency}ms)",
                            {"model_count": len(models), "latency_ms": latency, "endpoint": "/api/models"}
                        )
                        return True
                    else:
                        self.log_test(
                            "Models Endpoint - Insufficient Models",
                            False,
                            f"Only {len(models)} models found (<10 required) (latency: {latency}ms)",
                            {"model_count": len(models), "latency_ms": latency}
                        )
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Models Endpoint - Invalid JSON",
                        False,
                        f"/api/models returned invalid JSON (latency: {latency}ms)",
                        {"status_code": 200, "latency_ms": latency}
                    )
            else:
                print(f"   /api/models returned {response.status_code}, checking overview data...")
                
        except Exception as e:
            print(f"   /api/models failed: {str(e)}, checking overview data...")
        
        # Check overview data if provided
        if overview_data:
            models = overview_data.get('models', [])
            balance = overview_data.get('balance')
            
            if len(models) > 10:
                balance_present = balance is not None
                self.log_test(
                    "Models Endpoint - OpenRouter Overview",
                    True,
                    f"Found {len(models)} models (>10) and balance present: {balance_present}",
                    {"model_count": len(models), "balance_present": balance_present, "balance_value": balance}
                )
                return True
            else:
                self.log_test(
                    "Models Endpoint - Insufficient Models in Overview",
                    False,
                    f"Only {len(models)} models in overview (<10 required)",
                    {"model_count": len(models), "balance_present": balance is not None}
                )
                return False
        else:
            self.log_test(
                "Models Endpoint - No Data Available",
                False,
                "No models data available from any endpoint",
                {"overview_data": overview_data is not None}
            )
            return False
    
    def test_chat_endpoint(self):
        """3) Chat endpoint: POST /api/chat with openai/gpt-5 model"""
        print("\n🧪 Testing Chat Endpoint - POST /api/chat...")
        
        payload = {
            "message": "Hello, can you help me with a simple question?",
            "history": [],
            "model": "openai/gpt-5"  # Model specified in review request
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload,
                timeout=45
            )
            latency = round((time.time() - start_time) * 1000, 2)
            
            self.log_test(
                "Chat Endpoint - Status Code",
                response.status_code == 200,
                f"Status: {response.status_code} (latency: {latency}ms)",
                {"status_code": response.status_code, "latency_ms": latency}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for required fields
                    has_message = 'message' in data
                    has_response = 'response' in data
                    
                    if has_message or has_response:
                        message_content = data.get('message', data.get('response', ''))
                        
                        # Check if content is empty
                        if not message_content or len(message_content.strip()) == 0:
                            self.log_test(
                                "Chat Endpoint - Empty Content",
                                False,
                                "Response has empty content",
                                {"message_length": len(message_content), "response_body": data}
                            )
                        else:
                            # Check for stub patterns
                            stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                            is_stub = any(pattern.lower() in message_content.lower() for pattern in stub_patterns)
                            
                            self.log_test(
                                "Chat Endpoint - Content Quality",
                                not is_stub,
                                f"Response: {'Stub detected' if is_stub else 'Valid content'} ({len(message_content)} chars)",
                                {
                                    "content_length": len(message_content), 
                                    "is_stub": is_stub,
                                    "content_preview": message_content[:100],
                                    "has_cost": bool(data.get('cost'))
                                }
                            )
                    else:
                        self.log_test(
                            "Chat Endpoint - Missing Fields",
                            False,
                            "Response missing 'message' or 'response' field",
                            {"response_keys": list(data.keys()), "response_body": data}
                        )
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Chat Endpoint - Invalid JSON",
                        False,
                        f"Status 200 but invalid JSON response",
                        {"response_preview": response.text[:200]}
                    )
            else:
                # Include error body for non-200 responses as requested
                self.log_test(
                    "Chat Endpoint - HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code, "error_body": response.text[:1000]}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Chat Endpoint - Timeout",
                False,
                "Request timed out after 45 seconds",
                {"timeout": 45}
            )
        except Exception as e:
            self.log_test(
                "Chat Endpoint - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def test_automation_endpoints(self):
        """4) Automation sample: GET /api/hook/log and GET /api/automation/screenshot (should fail with 400/404)"""
        print("\n🧪 Testing Automation Endpoints (Expected Failures)...")
        
        # Test 1: GET /api/hook/log
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/hook/log", timeout=15)
            latency = round((time.time() - start_time) * 1000, 2)
            
            expected_codes = [400, 404]
            if response.status_code in expected_codes:
                self.log_test(
                    "Automation - Hook Log (Expected Failure)",
                    True,
                    f"Correctly returned {response.status_code} as expected (latency: {latency}ms)",
                    {"status_code": response.status_code, "latency_ms": latency, "expected": expected_codes}
                )
            else:
                self.log_test(
                    "Automation - Hook Log (Unexpected Success)",
                    False,
                    f"Unexpected status {response.status_code} (expected 400/404) (latency: {latency}ms)",
                    {"status_code": response.status_code, "expected": expected_codes, "error_body": response.text[:500]}
                )
                
        except Exception as e:
            self.log_test(
                "Automation - Hook Log Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
        
        # Test 2: GET /api/automation/screenshot (without params)
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/automation/screenshot", timeout=15)
            latency = round((time.time() - start_time) * 1000, 2)
            
            expected_codes = [400, 404]
            if response.status_code in expected_codes:
                self.log_test(
                    "Automation - Screenshot (Expected Failure)",
                    True,
                    f"Correctly returned {response.status_code} as expected (latency: {latency}ms)",
                    {"status_code": response.status_code, "latency_ms": latency, "expected": expected_codes}
                )
            else:
                self.log_test(
                    "Automation - Screenshot (Unexpected Success)",
                    False,
                    f"Unexpected status {response.status_code} (expected 400/404) (latency: {latency}ms)",
                    {"status_code": response.status_code, "expected": expected_codes, "error_body": response.text[:500]}
                )
                
        except Exception as e:
            self.log_test(
                "Automation - Screenshot Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def check_backend_status(self):
        """5) Check if backend is up and report any proxy/auth errors"""
        print("\n🧪 Checking Backend Status & Proxy/Auth Errors...")
        
        # Test basic server status
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                self.log_test(
                    "Backend Status - Root Endpoint",
                    True,
                    f"Backend is UP and responding (latency: {latency}ms)",
                    {"status_code": 200, "latency_ms": latency}
                )
            else:
                self.log_test(
                    "Backend Status - Root Endpoint Error",
                    False,
                    f"Backend responding with status {response.status_code} (latency: {latency}ms)",
                    {"status_code": response.status_code, "latency_ms": latency, "error_body": response.text[:500]}
                )
                
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e).lower()
            if 'proxy' in error_msg:
                self.log_test(
                    "Backend Status - Proxy Error",
                    False,
                    f"Proxy connection error detected: {str(e)}",
                    {"error": str(e), "error_type": "ProxyError"}
                )
            elif 'ssl' in error_msg or 'certificate' in error_msg:
                self.log_test(
                    "Backend Status - SSL/Certificate Error",
                    False,
                    f"SSL/Certificate error detected: {str(e)}",
                    {"error": str(e), "error_type": "SSLError"}
                )
            elif 'auth' in error_msg or 'unauthorized' in error_msg:
                self.log_test(
                    "Backend Status - Auth Error",
                    False,
                    f"Authentication error detected: {str(e)}",
                    {"error": str(e), "error_type": "AuthError"}
                )
            else:
                self.log_test(
                    "Backend Status - Connection Error",
                    False,
                    f"Backend is DOWN - Connection error: {str(e)}",
                    {"error": str(e), "error_type": "ConnectionError"}
                )
        except Exception as e:
            self.log_test(
                "Backend Status - Exception",
                False,
                f"Backend status check failed: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    def run_all_tests(self):
        """Run all user-reported issue tests"""
        print("🚀 Starting User Reported Issues Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # 1. Health/Basic Connectivity
        server_up, overview_data = self.test_health_basic_connectivity()
        
        # 2. Models Endpoints
        if server_up:
            self.test_models_endpoints(overview_data)
        else:
            print("⚠️  Skipping models test - server appears to be down")
        
        # 3. Chat Endpoint
        if server_up:
            self.test_chat_endpoint()
        else:
            print("⚠️  Skipping chat test - server appears to be down")
        
        # 4. Automation Endpoints (Expected Failures)
        if server_up:
            self.test_automation_endpoints()
        else:
            print("⚠️  Skipping automation tests - server appears to be down")
        
        # 5. Backend Status & Proxy/Auth Check
        self.check_backend_status()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = UserReportedIssuesTester()
    results = tester.run_all_tests()