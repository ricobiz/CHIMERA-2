#!/usr/bin/env python3
"""
Focused Backend API Testing for Critical Issues
Based on review request - testing specific stuck tasks
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://antibot-layer.preview.emergentagent.com/api"

class FocusedBackendTester:
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
    
    def test_chat_sequential_messages(self):
        """Test the CRITICAL STUCK TASK: Sequential chat messages"""
        print("\n🧪 Testing CRITICAL Chat Flow - Sequential Messages...")
        print("   Issue: Only first message works, rest return stub")
        
        # Test 1: First message
        print("   1. Testing first message...")
        payload_1 = {
            "message": "Hello, how are you?",
            "history": [],
            "model": "x-ai/grok-code-fast-1"
        }
        
        first_response = None
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload_1,
                timeout=90  # Longer timeout for AI processing
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'response' in data:
                    response_text = data['message']
                    # Check for stub patterns
                    stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                    is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                    
                    if len(response_text) > 10 and not is_stub:
                        first_response = data
                        self.log_test(
                            "Chat Sequential - First Message",
                            True,
                            f"First message worked ({len(response_text)} chars)",
                            {"response_length": len(response_text), "cost": data.get('cost', {})}
                        )
                    else:
                        self.log_test(
                            "Chat Sequential - First Message STUB",
                            False,
                            "First message already returning stub",
                            {"response_preview": response_text[:100]}
                        )
                        return
                else:
                    self.log_test(
                        "Chat Sequential - First Message Missing Fields",
                        False,
                        "Response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
                    return
            else:
                self.log_test(
                    "Chat Sequential - First Message HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return
                
        except Exception as e:
            self.log_test(
                "Chat Sequential - First Message Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return
        
        # Test 2: Second message with history (CRITICAL TEST)
        print("   2. Testing second message with history...")
        if first_response:
            history = [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": first_response['message']}
            ]
            
            payload_2 = {
                "message": "What's 2+2?",
                "history": history,
                "model": "x-ai/grok-code-fast-1"
            }
            
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/chat",
                    json=payload_2,
                    timeout=90
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'message' in data:
                        response_text = data['message']
                        stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                        is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                        
                        if len(response_text) > 10 and not is_stub:
                            self.log_test(
                                "Chat Sequential - Second Message",
                                True,
                                f"Second message worked ({len(response_text)} chars)",
                                {"response_length": len(response_text), "contains_4": "4" in response_text}
                            )
                            
                            # Test 3: Third message (CRITICAL)
                            self.test_third_message(history, first_response['message'])
                            
                        else:
                            self.log_test(
                                "Chat Sequential - Second Message CRITICAL FAILURE",
                                False,
                                "Second message returning stub - CONFIRMS USER ISSUE",
                                {"response_preview": response_text[:100], "is_stub": is_stub}
                            )
                    else:
                        self.log_test(
                            "Chat Sequential - Second Message Missing Fields",
                            False,
                            "Response missing message field",
                            {"response_keys": list(data.keys())}
                        )
                else:
                    self.log_test(
                        "Chat Sequential - Second Message HTTP Error",
                        False,
                        f"HTTP {response.status_code}",
                        {"status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.log_test(
                    "Chat Sequential - Second Message Exception",
                    False,
                    f"Error: {str(e)}",
                    {"error_type": type(e).__name__}
                )
    
    def test_third_message(self, previous_history, first_response_text):
        """Test third message in sequence"""
        print("   3. Testing third message with extended history...")
        
        extended_history = previous_history + [
            {"role": "user", "content": "What's 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."}
        ]
        
        payload_3 = {
            "message": "Tell me a joke",
            "history": extended_history,
            "model": "x-ai/grok-code-fast-1"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload_3,
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data:
                    response_text = data['message']
                    stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                    is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                    
                    if len(response_text) > 10 and not is_stub:
                        self.log_test(
                            "Chat Sequential - Third Message",
                            True,
                            f"Third message worked ({len(response_text)} chars)",
                            {"response_length": len(response_text)}
                        )
                    else:
                        self.log_test(
                            "Chat Sequential - Third Message CRITICAL FAILURE",
                            False,
                            "Third message returning stub - CONFIRMS SEQUENTIAL ISSUE",
                            {"response_preview": response_text[:100], "is_stub": is_stub}
                        )
                else:
                    self.log_test(
                        "Chat Sequential - Third Message Missing Fields",
                        False,
                        "Response missing message field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Chat Sequential - Third Message HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Chat Sequential - Third Message Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_code_generation(self):
        """Test POST /api/generate-code - Agent mode"""
        print("\n🧪 Testing Code Generation - Agent Mode...")
        
        payload = {
            "prompt": "Create a todo app",
            "conversation_history": [],
            "model": "x-ai/grok-code-fast-1"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-code",
                json=payload,
                timeout=120  # Longer timeout for code generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'code' in data and 'message' in data:
                    code = data['code']
                    if len(code) > 100 and ('function' in code or 'const' in code):
                        self.log_test(
                            "Code Generation - Agent Mode",
                            True,
                            f"Generated {len(code)} chars of code",
                            {"code_length": len(code), "usage": data.get('usage', {})}
                        )
                    else:
                        self.log_test(
                            "Code Generation - Invalid Code",
                            False,
                            "Generated code appears invalid",
                            {"code_preview": code[:200]}
                        )
                else:
                    self.log_test(
                        "Code Generation - Missing Fields",
                        False,
                        "Response missing code or message fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Code Generation - HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                
        except Exception as e:
            self.log_test(
                "Code Generation - Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_design_generation(self):
        """Test POST /api/generate-design"""
        print("\n🧪 Testing Design Generation...")
        
        payload = {
            "user_request": "Design a fitness tracker app",
            "model": "google/gemini-2.5-flash-image"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-design",
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'design_spec' in data:
                    design_spec = data['design_spec']
                    if len(design_spec) > 100:
                        self.log_test(
                            "Design Generation",
                            True,
                            f"Generated design spec ({len(design_spec)} chars)",
                            {"design_length": len(design_spec), "usage": data.get('usage', {})}
                        )
                        
                        # Test mockup generation
                        self.test_mockup_generation(design_spec, payload["user_request"])
                        
                    else:
                        self.log_test(
                            "Design Generation - Short Spec",
                            False,
                            "Design spec too short",
                            {"design_spec": design_spec}
                        )
                else:
                    self.log_test(
                        "Design Generation - Missing Spec",
                        False,
                        "Response missing design_spec field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Design Generation - HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Design Generation - Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_mockup_generation(self, design_spec, user_request):
        """Test POST /api/generate-mockup"""
        print("   Testing mockup generation...")
        
        payload = {
            "design_spec": design_spec,
            "user_request": user_request,
            "model": "google/gemini-2.5-flash-image-preview"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-mockup",
                json=payload,
                timeout=120  # Longer timeout for image generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'mockup_data' in data:
                    mockup_data = data['mockup_data']
                    self.log_test(
                        "Mockup Generation",
                        True,
                        f"Generated mockup data ({len(str(mockup_data))} chars)",
                        {"mockup_size": len(str(mockup_data)), "usage": data.get('usage', {})}
                    )
                else:
                    self.log_test(
                        "Mockup Generation - Missing Data",
                        False,
                        "Response missing mockup_data field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Mockup Generation - HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Mockup Generation - Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_proxy_status(self):
        """Test GET /api/proxy/status"""
        print("\n🧪 Testing Proxy Status...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/proxy/status", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'enabled' in data:
                    if data['enabled']:
                        self.log_test(
                            "Proxy Status - Enabled",
                            True,
                            f"Proxy enabled with {data.get('total_proxies', 0)} proxies",
                            {"proxy_data": data}
                        )
                    else:
                        self.log_test(
                            "Proxy Status - Disabled",
                            False,
                            "Proxy service disabled - automation with proxy will fail",
                            {"message": data.get('message', 'No message')}
                        )
                else:
                    self.log_test(
                        "Proxy Status - Invalid Response",
                        False,
                        "Response missing enabled field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Proxy Status - HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Proxy Status - Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_automation_session(self):
        """Test POST /api/automation/session/create with proxy"""
        print("\n🧪 Testing Browser Automation Session with Proxy...")
        
        session_id = f"test_session_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "use_proxy": True
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'session_id' in data and 'status' in data:
                    if data['session_id'] == session_id and data['status'] == 'ready':
                        self.log_test(
                            "Automation Session - With Proxy",
                            True,
                            f"Session created with proxy: {session_id}",
                            {"session_data": data}
                        )
                    else:
                        self.log_test(
                            "Automation Session - Invalid Response",
                            False,
                            "Session creation response invalid",
                            {"expected_session": session_id, "actual_data": data}
                        )
                else:
                    self.log_test(
                        "Automation Session - Missing Fields",
                        False,
                        "Response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Automation Session - HTTP Error",
                    False,
                    f"HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Automation Session - Exception",
                False,
                f"Error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def run_focused_tests(self):
        """Run focused tests for critical issues"""
        print("🎯 FOCUSED BACKEND TESTING - CRITICAL ISSUES")
        print(f"Backend URL: {BACKEND_URL}")
        print("="*60)
        
        # PRIORITY 1: STUCK TASK - Chat sequential messages (stuck_count: 2)
        self.test_chat_sequential_messages()
        
        # PRIORITY 2: Core functionality
        self.test_code_generation()
        self.test_design_generation()
        self.test_proxy_status()
        self.test_automation_session()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 FOCUSED TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Critical issues
        chat_issues = [r for r in self.test_results if not r['success'] and 'Chat Sequential' in r['test']]
        if chat_issues:
            print(f"\n🚨 CRITICAL CHAT ISSUES (STUCK TASK):")
            for issue in chat_issues:
                print(f"   ❌ {issue['test']}: {issue['message']}")
        
        # Working features
        working = [r for r in self.test_results if r['success']]
        if working:
            print(f"\n✅ WORKING FEATURES:")
            for success in working:
                print(f"   ✅ {success['test']}")
        
        # Failed features
        failed = [r for r in self.test_results if not r['success'] and 'Chat Sequential' not in r['test']]
        if failed:
            print(f"\n❌ FAILED FEATURES:")
            for failure in failed:
                print(f"   ❌ {failure['test']}: {failure['message']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = FocusedBackendTester()
    tester.run_focused_tests()