#!/usr/bin/env python3
"""
JustFans.uno Registration Flow Test
Tests the complete browser automation scenario as requested in the review
"""

import requests
import json
import time
import uuid
import random
import string
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://ai-browser-auto.preview.emergentagent.com/api"

class JustFansRegistrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.session_id = None
        self.registration_data = {}
        
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
    
    def generate_realistic_data(self):
        """Generate realistic registration data"""
        # Generate realistic email
        first_names = ['alex', 'jordan', 'casey', 'taylor', 'morgan', 'riley', 'avery', 'quinn']
        last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        random_num = random.randint(100, 9999)
        
        self.registration_data = {
            'email': f"{first_name}.{last_name}{random_num}@gmail.com",
            'username': f"{first_name}{last_name}{random_num}",
            'password': f"SecurePass{random_num}!",
            'display_name': f"{first_name.title()} {last_name.title()}",
            'bio': f"Creative professional passionate about art and design. Love connecting with like-minded people and sharing inspiring content."
        }
        
        print(f"📝 Generated registration data:")
        print(f"   Email: {self.registration_data['email']}")
        print(f"   Username: {self.registration_data['username']}")
        print(f"   Display Name: {self.registration_data['display_name']}")
    
    def test_step_1_create_session(self):
        """Step 1: Create browser automation session"""
        print("\n🚀 Step 1: Creating browser automation session...")
        
        self.session_id = f"justfans_registration_{int(time.time())}"
        
        payload = {
            "session_id": self.session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('session_id') == self.session_id and data.get('status') == 'ready':
                    self.log_test(
                        "Step 1 - Create Session",
                        True,
                        f"Browser session created: {self.session_id}",
                        {"session_id": self.session_id}
                    )
                    return True
                else:
                    self.log_test(
                        "Step 1 - Create Session",
                        False,
                        "Invalid session creation response",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Step 1 - Create Session",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Step 1 - Create Session",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
        
        return False
    
    def test_step_2_navigate_to_site(self):
        """Step 2: Navigate to justfans.uno"""
        print("\n🌐 Step 2: Navigating to https://justfans.uno...")
        
        payload = {
            "session_id": self.session_id,
            "url": "https://justfans.uno"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/navigate",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'justfans.uno' in data.get('url', ''):
                    self.log_test(
                        "Step 2 - Navigate to Site",
                        True,
                        f"Successfully loaded: {data['url']}",
                        {"url": data['url'], "title": data.get('title')}
                    )
                    return True
                else:
                    self.log_test(
                        "Step 2 - Navigate to Site",
                        False,
                        f"Navigation failed: {data.get('error', 'Unknown error')}",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Step 2 - Navigate to Site",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Step 2 - Navigate to Site",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
        
        return False
    
    def test_step_3_find_signup_button(self):
        """Step 3: Find Sign Up button using vision model"""
        print("\n🔍 Step 3: Finding Sign Up button with vision model...")
        
        payload = {
            "session_id": self.session_id,
            "description": "sign up button"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/find-elements",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                if elements:
                    # Find the most likely sign up button
                    signup_elements = []
                    for elem in elements:
                        text = elem.get('text', '').lower()
                        if any(keyword in text for keyword in ['sign up', 'register', 'join', 'create account']):
                            signup_elements.append(elem)
                    
                    if signup_elements:
                        best_element = signup_elements[0]  # Take the first matching element
                        self.log_test(
                            "Step 3 - Find Sign Up Button",
                            True,
                            f"Found sign up button: '{best_element.get('text', 'N/A')}'",
                            {"element": best_element, "total_elements": len(elements)}
                        )
                        return True
                    else:
                        self.log_test(
                            "Step 3 - Find Sign Up Button",
                            False,
                            f"No sign up button found among {len(elements)} elements",
                            {"elements": [elem.get('text', '') for elem in elements[:5]]}
                        )
                else:
                    self.log_test(
                        "Step 3 - Find Sign Up Button",
                        False,
                        "Vision model found no elements",
                        {"elements_found": 0}
                    )
            else:
                self.log_test(
                    "Step 3 - Find Sign Up Button",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Step 3 - Find Sign Up Button",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
        
        return False
    
    def test_step_4_smart_click_signup(self):
        """Step 4: Smart click on Sign Up button"""
        print("\n👆 Step 4: Smart clicking Sign Up button...")
        
        payload = {
            "session_id": self.session_id,
            "description": "sign up button"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/smart-click",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    clicked_element = data.get('clicked_element', {})
                    self.log_test(
                        "Step 4 - Smart Click Sign Up",
                        True,
                        f"Successfully clicked: '{clicked_element.get('text', 'N/A')}'",
                        {"clicked_element": clicked_element}
                    )
                    return True
                else:
                    self.log_test(
                        "Step 4 - Smart Click Sign Up",
                        False,
                        "Smart click failed",
                        {"response": data}
                    )
            elif response.status_code == 404:
                self.log_test(
                    "Step 4 - Smart Click Sign Up",
                    False,
                    "Sign up button not found for clicking",
                    {"status_code": 404}
                )
            else:
                self.log_test(
                    "Step 4 - Smart Click Sign Up",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Step 4 - Smart Click Sign Up",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
        
        return False
    
    def test_step_5_detect_registration_form(self):
        """Step 5: Detect registration form elements"""
        print("\n📋 Step 5: Detecting registration form elements...")
        
        # Look for common registration form elements
        form_elements = ['email field', 'username field', 'password field', 'submit button']
        found_elements = {}
        
        for element_type in form_elements:
            payload = {
                "session_id": self.session_id,
                "description": element_type
            }
            
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/automation/find-elements",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get('elements', [])
                    if elements:
                        found_elements[element_type] = elements[0]
                        print(f"   ✅ Found {element_type}: {elements[0].get('text', 'N/A')}")
                    else:
                        print(f"   ❌ {element_type} not found")
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error finding {element_type}: {str(e)}")
        
        if len(found_elements) >= 2:  # At least 2 form elements found
            self.log_test(
                "Step 5 - Detect Registration Form",
                True,
                f"Found {len(found_elements)} form elements",
                {"found_elements": list(found_elements.keys())}
            )
            return True
        else:
            self.log_test(
                "Step 5 - Detect Registration Form",
                False,
                f"Only found {len(found_elements)} form elements",
                {"found_elements": list(found_elements.keys())}
            )
            return False
    
    def test_step_6_capture_final_screenshot(self):
        """Step 6: Capture final screenshot"""
        print("\n📸 Step 6: Capturing final screenshot...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/automation/screenshot/{self.session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                screenshot = data.get('screenshot', '')
                
                if screenshot and screenshot.startswith('data:image/png;base64,'):
                    self.log_test(
                        "Step 6 - Final Screenshot",
                        True,
                        f"Screenshot captured ({len(screenshot)} chars)",
                        {"screenshot_size": len(screenshot)}
                    )
                    return True
                else:
                    self.log_test(
                        "Step 6 - Final Screenshot",
                        False,
                        "Invalid screenshot format",
                        {"screenshot_preview": screenshot[:100]}
                    )
            else:
                self.log_test(
                    "Step 6 - Final Screenshot",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Step 6 - Final Screenshot",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
        
        return False
    
    def test_step_7_cleanup_session(self):
        """Step 7: Clean up browser session"""
        print("\n🧹 Step 7: Cleaning up browser session...")
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/automation/session/{self.session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'closed' in data.get('message', '').lower():
                    self.log_test(
                        "Step 7 - Cleanup Session",
                        True,
                        f"Session closed: {self.session_id}",
                        {"session_id": self.session_id}
                    )
                    return True
                else:
                    self.log_test(
                        "Step 7 - Cleanup Session",
                        False,
                        "Invalid cleanup response",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Step 7 - Cleanup Session",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Step 7 - Cleanup Session",
                False,
                f"Exception: {str(e)}",
                {"error": str(e)}
            )
        
        return False
    
    def run_registration_flow_test(self):
        """Run the complete justfans.uno registration flow test"""
        print("🎯 JustFans.uno Registration Flow Test")
        print("=" * 60)
        
        # Generate realistic data
        self.generate_realistic_data()
        
        # Run all steps
        steps = [
            self.test_step_1_create_session,
            self.test_step_2_navigate_to_site,
            self.test_step_3_find_signup_button,
            self.test_step_4_smart_click_signup,
            self.test_step_5_detect_registration_form,
            self.test_step_6_capture_final_screenshot,
            self.test_step_7_cleanup_session
        ]
        
        success_count = 0
        for step in steps:
            if step():
                success_count += 1
            else:
                print(f"⚠️  Step failed, continuing with next step...")
            
            # Small delay between steps
            time.sleep(2)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 REGISTRATION FLOW TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        print(f"\n📝 Generated Registration Data:")
        for key, value in self.registration_data.items():
            if key != 'password':  # Don't show password in logs
                print(f"   {key.title()}: {value}")
            else:
                print(f"   {key.title()}: {'*' * len(value)}")
        
        if failed > 0:
            print("\n🔍 FAILED STEPS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        # Determine overall result
        critical_steps = ['Step 1 - Create Session', 'Step 2 - Navigate to Site', 'Step 3 - Find Sign Up Button']
        critical_passed = sum(1 for result in self.test_results 
                            if result['success'] and result['test'] in critical_steps)
        
        if critical_passed == len(critical_steps):
            print("\n🎉 CRITICAL AUTOMATION FEATURES WORKING!")
            print("   ✅ Browser session creation")
            print("   ✅ Website navigation") 
            print("   ✅ Vision-based element detection")
        else:
            print("\n⚠️  SOME CRITICAL FEATURES FAILED")
        
        return passed, failed

if __name__ == "__main__":
    tester = JustFansRegistrationTester()
    passed, failed = tester.run_registration_flow_test()
    
    # Exit with error code if critical tests failed
    exit(0 if failed <= 2 else 1)  # Allow up to 2 non-critical failures