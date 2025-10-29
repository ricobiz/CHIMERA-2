#!/usr/bin/env python3
"""
Browser Automation Testing Only
Tests the browser automation endpoints for justfans.uno registration scenario
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://aios-automation.preview.emergentagent.com/api"

class AutomationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_automation_session_id = None
        
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
    
    def test_browser_automation_create_session(self):
        """Test POST /api/automation/session/create endpoint"""
        print("\n🧪 Testing Browser Automation - Create Session...")
        
        # Generate unique session ID
        session_id = f"test_session_{int(time.time())}"
        
        payload = {
            "session_id": session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['session_id', 'status']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    if data['session_id'] == session_id and data['status'] == 'ready':
                        self.created_automation_session_id = session_id
                        self.log_test(
                            "Browser Automation - Create Session",
                            True,
                            f"Session created successfully: {session_id}",
                            {"session_id": session_id, "status": data['status']}
                        )
                    else:
                        self.log_test(
                            "Browser Automation - Create Session - Invalid Response",
                            False,
                            "Session creation response invalid",
                            {"expected_session": session_id, "actual_session": data.get('session_id')}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Create Session - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Browser Automation - Create Session - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Create Session - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_navigate(self):
        """Test POST /api/automation/navigate endpoint"""
        print("\n🧪 Testing Browser Automation - Navigate...")
        
        if not self.created_automation_session_id:
            self.log_test(
                "Browser Automation - Navigate - No Session",
                False,
                "No automation session available for testing",
                {"session_id": None}
            )
            return
        
        # Test navigation to justfans.uno as per review request
        payload = {
            "session_id": self.created_automation_session_id,
            "url": "https://justfans.uno"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/navigate",
                json=payload,
                timeout=45  # Longer timeout for page load
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    # Check if we got a screenshot and proper URL
                    if 'screenshot' in data and 'url' in data:
                        self.log_test(
                            "Browser Automation - Navigate to justfans.uno",
                            True,
                            f"Successfully navigated to {data['url']}",
                            {"url": data['url'], "title": data.get('title', 'N/A'), "has_screenshot": bool(data['screenshot'])}
                        )
                    else:
                        self.log_test(
                            "Browser Automation - Navigate - Missing Data",
                            False,
                            "Navigation successful but missing screenshot or URL",
                            {"response_keys": list(data.keys())}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Navigate - Failed",
                        False,
                        f"Navigation failed: {data.get('error', 'Unknown error')}",
                        {"error": data.get('error')}
                    )
            else:
                self.log_test(
                    "Browser Automation - Navigate - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Navigate - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_find_elements(self):
        """Test POST /api/automation/find-elements endpoint (Vision Model)"""
        print("\n🧪 Testing Browser Automation - Find Elements with Vision...")
        
        if not self.created_automation_session_id:
            self.log_test(
                "Browser Automation - Find Elements - No Session",
                False,
                "No automation session available for testing",
                {"session_id": None}
            )
            return
        
        # Test finding sign up button as per review request
        payload = {
            "session_id": self.created_automation_session_id,
            "description": "sign up button"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/find-elements",
                json=payload,
                timeout=45  # Vision model processing can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'elements' in data:
                    elements = data['elements']
                    if elements:
                        # Check element structure
                        first_element = elements[0]
                        required_fields = ['selector', 'text', 'box']
                        missing_fields = [field for field in required_fields if field not in first_element]
                        
                        if not missing_fields:
                            self.log_test(
                                "Browser Automation - Find Elements Vision",
                                True,
                                f"Vision model found {len(elements)} elements matching 'sign up button'",
                                {"element_count": len(elements), "first_element": first_element}
                            )
                        else:
                            self.log_test(
                                "Browser Automation - Find Elements - Invalid Structure",
                                False,
                                f"Element missing required fields: {missing_fields}",
                                {"missing_fields": missing_fields, "element_keys": list(first_element.keys())}
                            )
                    else:
                        self.log_test(
                            "Browser Automation - Find Elements - No Elements",
                            False,
                            "Vision model found no elements matching 'sign up button'",
                            {"elements_found": 0}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Find Elements - Missing Elements Key",
                        False,
                        "Response missing 'elements' key",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Browser Automation - Find Elements - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Find Elements - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_cleanup(self):
        """Test DELETE /api/automation/session/{session_id} endpoint"""
        print("\n🧪 Testing Browser Automation - Session Cleanup...")
        
        if not self.created_automation_session_id:
            self.log_test(
                "Browser Automation - Cleanup - No Session",
                False,
                "No automation session available for cleanup",
                {"session_id": None}
            )
            return
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/automation/session/{self.created_automation_session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'closed' in data['message'].lower():
                    self.log_test(
                        "Browser Automation - Session Cleanup",
                        True,
                        f"Session closed successfully: {self.created_automation_session_id}",
                        {"session_id": self.created_automation_session_id, "message": data['message']}
                    )
                else:
                    self.log_test(
                        "Browser Automation - Cleanup - Invalid Response",
                        False,
                        "Session cleanup response invalid",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Browser Automation - Cleanup - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Cleanup - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def run_automation_tests(self):
        """Run browser automation tests"""
        print("🤖 Starting Browser Automation Tests for justfans.uno")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test Browser Automation endpoints
        self.test_browser_automation_create_session()
        self.test_browser_automation_navigate()
        self.test_browser_automation_find_elements()
        self.test_browser_automation_cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 AUTOMATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        return passed, failed

if __name__ == "__main__":
    tester = AutomationTester()
    passed, failed = tester.run_automation_tests()
    
    # Exit with error code if tests failed
    exit(0 if failed == 0 else 1)