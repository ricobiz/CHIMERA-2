#!/usr/bin/env python3
"""
Phase 2 Backend Testing - Design/Mockup/Revision Flows
Tests specific Phase 2 endpoints as requested in review
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://chimera-aios-1.preview.emergentagent.com/api"

class Phase2BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.design_spec = None
        
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
    
    def test_generate_design_endpoint(self):
        """Test POST /api/generate-design with model=google/gemini-2.5-flash-image"""
        print("\n🧪 Testing Phase 2: POST /api/generate-design...")
        
        payload = {
            "user_request": "Design a modern fitness tracker dashboard with dark theme",
            "model": "google/gemini-2.5-flash-image"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-design",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'design_spec' in data and isinstance(data['design_spec'], str):
                    self.design_spec = data['design_spec']
                    design_length = len(self.design_spec)
                    
                    # Check if design spec contains expected elements
                    design_elements = ['color', 'layout', 'theme', 'dark']
                    found_elements = [elem for elem in design_elements if elem.lower() in self.design_spec.lower()]
                    
                    self.log_test(
                        "Generate Design - Success",
                        True,
                        f"Design spec generated ({design_length} chars) with {len(found_elements)}/4 expected elements",
                        {
                            "design_length": design_length,
                            "found_elements": found_elements,
                            "has_usage": bool(data.get('usage')),
                            "model_used": payload["model"]
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Generate Design - Missing Design Spec",
                        False,
                        "Response missing 'design_spec' field or invalid format",
                        {"response_keys": list(data.keys()), "design_spec_type": type(data.get('design_spec'))}
                    )
                    return False
            else:
                self.log_test(
                    "Generate Design - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    {"status_code": response.status_code, "model": payload["model"]}
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Generate Design - Timeout",
                False,
                "Request timed out after 45 seconds",
                {"timeout": 45, "model": payload["model"]}
            )
            return False
        except Exception as e:
            self.log_test(
                "Generate Design - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "model": payload["model"]}
            )
            return False
    
    def test_generate_mockup_endpoint(self):
        """Test POST /api/generate-mockup with design_spec from step 1"""
        print("\n🧪 Testing Phase 2: POST /api/generate-mockup...")
        
        if not self.design_spec:
            self.log_test(
                "Generate Mockup - No Design Spec",
                False,
                "Cannot test mockup generation - no design_spec from previous step",
                {"design_spec_available": False}
            )
            return False
        
        payload = {
            "design_spec": self.design_spec,
            "user_request": "Design a modern fitness tracker dashboard with dark theme",
            "model": "google/gemini-2.5-flash-image"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-mockup",
                json=payload,
                timeout=60  # Longer timeout for image generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'mockup_data' in data:
                    mockup_data = data['mockup_data']
                    mockup_size = len(str(mockup_data))
                    
                    # Determine mockup type (URL, base64, or text description)
                    mockup_type = "unknown"
                    if isinstance(mockup_data, str):
                        if mockup_data.startswith('http'):
                            mockup_type = "URL"
                        elif mockup_data.startswith('data:image') or len(mockup_data) > 1000:
                            mockup_type = "base64"
                        else:
                            mockup_type = "text_description"
                    
                    self.log_test(
                        "Generate Mockup - Success",
                        True,
                        f"Mockup generated ({mockup_size} chars, type: {mockup_type})",
                        {
                            "mockup_size": mockup_size,
                            "mockup_type": mockup_type,
                            "has_usage": bool(data.get('usage')),
                            "model_used": payload["model"]
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Generate Mockup - Missing Mockup Data",
                        False,
                        "Response missing 'mockup_data' field",
                        {"response_keys": list(data.keys())}
                    )
                    return False
            else:
                self.log_test(
                    "Generate Mockup - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    {"status_code": response.status_code, "model": payload["model"]}
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Generate Mockup - Timeout",
                False,
                "Request timed out after 60 seconds",
                {"timeout": 60, "model": payload["model"]}
            )
            return False
        except Exception as e:
            self.log_test(
                "Generate Mockup - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "model": payload["model"]}
            )
            return False
    
    def test_revise_design_endpoint(self):
        """Test POST /api/revise-design with current_design and revision_request"""
        print("\n🧪 Testing Phase 2: POST /api/revise-design...")
        
        if not self.design_spec:
            self.log_test(
                "Revise Design - No Design Spec",
                False,
                "Cannot test design revision - no design_spec from previous step",
                {"design_spec_available": False}
            )
            return False
        
        payload = {
            "current_design": self.design_spec,
            "revision_request": "Move CTA button to top-right, remove avatar",
            "model": "google/gemini-2.5-flash-image"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/revise-design",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'design_spec' in data and isinstance(data['design_spec'], str):
                    revised_design = data['design_spec']
                    revision_length = len(revised_design)
                    
                    # Check if revision contains requested changes
                    revision_keywords = ['top-right', 'cta', 'button', 'avatar']
                    found_keywords = [kw for kw in revision_keywords if kw.lower() in revised_design.lower()]
                    
                    # Check if it's different from original
                    is_different = revised_design != self.design_spec
                    
                    self.log_test(
                        "Revise Design - Success",
                        True,
                        f"Design revised ({revision_length} chars, {len(found_keywords)}/4 keywords found, changed: {is_different})",
                        {
                            "revision_length": revision_length,
                            "found_keywords": found_keywords,
                            "is_different_from_original": is_different,
                            "has_usage": bool(data.get('usage')),
                            "model_used": payload["model"]
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Revise Design - Missing Design Spec",
                        False,
                        "Response missing 'design_spec' field or invalid format",
                        {"response_keys": list(data.keys()), "design_spec_type": type(data.get('design_spec'))}
                    )
                    return False
            else:
                self.log_test(
                    "Revise Design - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    {"status_code": response.status_code, "model": payload["model"]}
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Revise Design - Timeout",
                False,
                "Request timed out after 45 seconds",
                {"timeout": 45, "model": payload["model"]}
            )
            return False
        except Exception as e:
            self.log_test(
                "Revise Design - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "model": payload["model"]}
            )
            return False
    
    def test_generate_code_regression(self):
        """Regression test: POST /api/generate-code with model x-ai/grok-code-fast-1"""
        print("\n🧪 Testing Regression: POST /api/generate-code...")
        
        payload = {
            "prompt": "Create a simple calculator with basic operations",
            "conversation_history": [],
            "model": "x-ai/grok-code-fast-1"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-code",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'code' in data and 'message' in data:
                    code = data['code']
                    code_length = len(code)
                    
                    # Check for React patterns
                    react_patterns = ['useState', 'function', 'return', 'className', 'onClick']
                    found_patterns = [pattern for pattern in react_patterns if pattern in code]
                    
                    self.log_test(
                        "Generate Code Regression - Success",
                        True,
                        f"Code generated ({code_length} chars) with {len(found_patterns)}/5 React patterns",
                        {
                            "code_length": code_length,
                            "react_patterns_found": found_patterns,
                            "has_usage": bool(data.get('usage')),
                            "model_used": payload["model"]
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Generate Code Regression - Missing Fields",
                        False,
                        "Response missing required 'code' or 'message' fields",
                        {"response_keys": list(data.keys())}
                    )
                    return False
            else:
                self.log_test(
                    "Generate Code Regression - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    {"status_code": response.status_code, "model": payload["model"]}
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Generate Code Regression - Timeout",
                False,
                "Request timed out after 45 seconds",
                {"timeout": 45, "model": payload["model"]}
            )
            return False
        except Exception as e:
            self.log_test(
                "Generate Code Regression - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "model": payload["model"]}
            )
            return False
    
    def run_all_tests(self):
        """Run all Phase 2 backend tests in sequence"""
        print("🚀 Starting Phase 2 Backend Testing...")
        print("=" * 60)
        
        # Test sequence as specified in review request
        test_results = []
        
        # 1. Generate Design
        result1 = self.test_generate_design_endpoint()
        test_results.append(("Generate Design", result1))
        
        # 2. Generate Mockup (depends on step 1)
        result2 = self.test_generate_mockup_endpoint()
        test_results.append(("Generate Mockup", result2))
        
        # 3. Revise Design (depends on step 1)
        result3 = self.test_revise_design_endpoint()
        test_results.append(("Revise Design", result3))
        
        # 4. Regression test
        result4 = self.test_generate_code_regression()
        test_results.append(("Generate Code Regression", result4))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PHASE 2 BACKEND TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All Phase 2 backend flows are healthy!")
        else:
            print("⚠️  Some Phase 2 backend flows need attention.")
        
        return test_results

def main():
    """Main test execution"""
    tester = Phase2BackendTester()
    results = tester.run_all_tests()
    
    # Return exit code based on results
    all_passed = all(result for _, result in results)
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())