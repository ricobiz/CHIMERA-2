#!/usr/bin/env python3
"""
Backend API Testing for Lovable.dev Clone
Tests all backend endpoints including OpenRouter integration
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://codegen-preview-2.preview.emergentagent.com/api"

class LovableBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_project_id = None
        
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
    
    def test_generate_code_endpoint(self):
        """Test POST /api/generate-code endpoint"""
        print("\n🧪 Testing Code Generation Endpoint...")
        
        # Test data
        test_prompt = "A simple counter app"
        payload = {
            "prompt": test_prompt,
            "conversation_history": []
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
                    # Validate code content
                    code = data['code']
                    if 'function' in code and ('useState' in code or 'const' in code):
                        self.log_test(
                            "Generate Code - Valid Response",
                            True,
                            f"Generated {len(code)} characters of React code",
                            {"prompt": test_prompt, "code_length": len(code)}
                        )
                        
                        # Test with conversation history
                        self.test_generate_code_with_history()
                        
                    else:
                        self.log_test(
                            "Generate Code - Invalid Code",
                            False,
                            "Generated code doesn't appear to be valid React/JavaScript",
                            {"code_preview": code[:200]}
                        )
                else:
                    self.log_test(
                        "Generate Code - Missing Fields",
                        False,
                        "Response missing required 'code' or 'message' fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Generate Code - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Generate Code - Timeout",
                False,
                "Request timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "Generate Code - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_generate_code_with_history(self):
        """Test code generation with conversation history"""
        payload = {
            "prompt": "Make the counter red and add a reset button",
            "conversation_history": [
                {"role": "user", "content": "A simple counter app"},
                {"role": "assistant", "content": "I've created a simple counter app for you."}
            ]
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-code",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'code' in data and 'message' in data:
                    self.log_test(
                        "Generate Code - With History",
                        True,
                        "Successfully generated code with conversation history",
                        {"history_length": len(payload["conversation_history"])}
                    )
                else:
                    self.log_test(
                        "Generate Code - With History Failed",
                        False,
                        "Response missing required fields with history",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Generate Code - With History HTTP Error",
                    False,
                    f"HTTP {response.status_code} with conversation history",
                    {"status_code": response.status_code}
                )
        except Exception as e:
            self.log_test(
                "Generate Code - With History Exception",
                False,
                f"Error with conversation history: {str(e)}",
                {"error": str(e)}
            )
    
    def test_create_project_endpoint(self):
        """Test POST /api/projects endpoint"""
        print("\n🧪 Testing Create Project Endpoint...")
        
        # Generate test project data
        project_data = {
            "name": f"Test Counter App {int(time.time())}",
            "description": "A test project created by automated testing",
            "code": """function App() {
  const [count, setCount] = useState(0);
  
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <h1 className="text-4xl font-bold mb-8">Counter App</h1>
      <div className="text-6xl font-mono mb-8">{count}</div>
      <div className="space-x-4">
        <button 
          onClick={() => setCount(count + 1)}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Increment
        </button>
        <button 
          onClick={() => setCount(count - 1)}
          className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600"
        >
          Decrement
        </button>
      </div>
    </div>
  );
}

export default App;""",
            "conversation_history": [
                {"role": "user", "content": "Create a counter app"},
                {"role": "assistant", "content": "I've created a counter app for you!"}
            ]
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/projects",
                json=project_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'last_accessed']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.created_project_id = data['id']
                    self.log_test(
                        "Create Project - Success",
                        True,
                        f"Project created with ID: {data['id']}",
                        {"project_id": data['id'], "name": data['name']}
                    )
                else:
                    self.log_test(
                        "Create Project - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Create Project - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Create Project - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_projects_endpoint(self):
        """Test GET /api/projects endpoint"""
        print("\n🧪 Testing Get Projects Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/projects", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_test(
                        "Get Projects - Success",
                        True,
                        f"Retrieved {len(data)} projects",
                        {"project_count": len(data)}
                    )
                    
                    # Check time_ago format if projects exist
                    if data:
                        project = data[0]
                        required_fields = ['id', 'name', 'description', 'last_accessed', 'icon']
                        missing_fields = [field for field in required_fields if field not in project]
                        
                        if not missing_fields:
                            # Check time_ago format
                            time_ago = project['last_accessed']
                            if any(word in time_ago for word in ['minutes', 'hours', 'days', 'ago']):
                                self.log_test(
                                    "Get Projects - Time Format",
                                    True,
                                    f"Time format correct: '{time_ago}'",
                                    {"time_format": time_ago}
                                )
                            else:
                                self.log_test(
                                    "Get Projects - Time Format Invalid",
                                    False,
                                    f"Invalid time format: '{time_ago}'",
                                    {"time_format": time_ago}
                                )
                        else:
                            self.log_test(
                                "Get Projects - Missing Fields",
                                False,
                                f"Project missing fields: {missing_fields}",
                                {"missing_fields": missing_fields}
                            )
                else:
                    self.log_test(
                        "Get Projects - Invalid Response",
                        False,
                        "Response is not a list",
                        {"response_type": type(data).__name__}
                    )
            else:
                self.log_test(
                    "Get Projects - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get Projects - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_specific_project_endpoint(self):
        """Test GET /api/projects/{project_id} endpoint"""
        print("\n🧪 Testing Get Specific Project Endpoint...")
        
        if not self.created_project_id:
            self.log_test(
                "Get Specific Project - No Project ID",
                False,
                "No project ID available for testing (create project failed)",
                {"created_project_id": self.created_project_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/projects/{self.created_project_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all required fields
                required_fields = ['id', 'name', 'description', 'code', 'conversation_history', 
                                 'created_at', 'updated_at', 'last_accessed', 'icon']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Get Specific Project - Success",
                        True,
                        f"Retrieved project: {data['name']}",
                        {"project_id": data['id'], "name": data['name']}
                    )
                else:
                    self.log_test(
                        "Get Specific Project - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            elif response.status_code == 404:
                self.log_test(
                    "Get Specific Project - Not Found",
                    False,
                    "Project not found (404)",
                    {"project_id": self.created_project_id, "status_code": 404}
                )
            else:
                self.log_test(
                    "Get Specific Project - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get Specific Project - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_invalid_project_id(self):
        """Test GET /api/projects/{invalid_id} endpoint"""
        print("\n🧪 Testing Invalid Project ID...")
        
        invalid_id = "invalid-project-id-12345"
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/projects/{invalid_id}",
                timeout=15
            )
            
            if response.status_code == 404:
                self.log_test(
                    "Invalid Project ID - Correct 404",
                    True,
                    "Correctly returned 404 for invalid project ID",
                    {"invalid_id": invalid_id}
                )
            else:
                self.log_test(
                    "Invalid Project ID - Wrong Status",
                    False,
                    f"Expected 404, got {response.status_code}",
                    {"expected": 404, "actual": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Invalid Project ID - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_openrouter_integration(self):
        """Test OpenRouter API integration specifically"""
        print("\n🧪 Testing OpenRouter Integration...")
        
        # Test with a specific prompt that should generate recognizable React code
        payload = {
            "prompt": "Create a simple todo list app with add and delete functionality",
            "conversation_history": []
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-code",
                json=payload,
                timeout=45  # Longer timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                code = data.get('code', '')
                
                # Check for React patterns
                react_patterns = ['useState', 'function', 'return', 'className', 'onClick']
                found_patterns = [pattern for pattern in react_patterns if pattern in code]
                
                if len(found_patterns) >= 3:
                    self.log_test(
                        "OpenRouter Integration - React Code",
                        True,
                        f"Generated valid React code with {len(found_patterns)}/5 patterns",
                        {"patterns_found": found_patterns, "code_length": len(code)}
                    )
                else:
                    self.log_test(
                        "OpenRouter Integration - Invalid React",
                        False,
                        f"Generated code missing React patterns (found {len(found_patterns)}/5)",
                        {"patterns_found": found_patterns, "code_preview": code[:300]}
                    )
            else:
                self.log_test(
                    "OpenRouter Integration - API Error",
                    False,
                    f"OpenRouter API call failed: HTTP {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "OpenRouter Integration - Timeout",
                False,
                "OpenRouter API call timed out",
                {"timeout": 45}
            )
        except Exception as e:
            self.log_test(
                "OpenRouter Integration - Exception",
                False,
                f"OpenRouter integration error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Lovable.dev Clone Backend API Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test all endpoints
        self.test_generate_code_endpoint()
        self.test_openrouter_integration()
        self.test_create_project_endpoint()
        self.test_get_projects_endpoint()
        self.test_get_specific_project_endpoint()
        self.test_invalid_project_id()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
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
    tester = LovableBackendTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if tests failed
    exit(0 if failed == 0 else 1)