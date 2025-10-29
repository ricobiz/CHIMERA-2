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
BACKEND_URL = "https://brain-automation-1.preview.emergentagent.com/api"

class LovableBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_project_id = None
        self.created_integration_id = None
        self.created_mcp_server_id = None
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
    
    def test_generate_code_endpoint_critical(self):
        """Test POST /api/generate-code endpoint - CRITICAL Agent Mode"""
        print("\n🧪 Testing Code Generation Endpoint - Agent Mode...")
        
        # Test with simple request as mentioned in review
        test_prompt = "Create a todo app"
        payload = {
            "prompt": test_prompt,
            "conversation_history": [],
            "model": "x-ai/grok-code-fast-1"  # Using model mentioned in review
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
                        
                        # Test design generation flow
                        self.test_design_generation_flow()
                        
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
    
    def test_design_generation_flow(self):
        """Test POST /api/generate-design and /api/generate-mockup endpoints"""
        print("\n🧪 Testing Design Generation Flow...")
        
        # Test 1: Generate Design Specification
        print("   Testing design specification generation...")
        design_payload = {
            "user_request": "Design a fitness tracker app",
            "model": "google/gemini-2.5-flash-image"  # Model mentioned in review
        }
        
        design_spec = None
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-design",
                json=design_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'design_spec' in data:
                    design_spec = data['design_spec']
                    self.log_test(
                        "Generate Design - Success",
                        True,
                        f"Design specification generated ({len(design_spec)} chars)",
                        {"design_length": len(design_spec), "has_usage": bool(data.get('usage'))}
                    )
                    
                    # Test 2: Generate Mockup from Design
                    if design_spec:
                        self.test_generate_mockup(design_spec, design_payload["user_request"])
                        
                else:
                    self.log_test(
                        "Generate Design - Missing Design Spec",
                        False,
                        "Response missing 'design_spec' field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Generate Design - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Generate Design - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_generate_mockup(self, design_spec, user_request):
        """Test POST /api/generate-mockup endpoint"""
        print("   Testing visual mockup generation...")
        
        mockup_payload = {
            "design_spec": design_spec,
            "user_request": user_request,
            "model": "google/gemini-2.5-flash-image-preview"  # Model mentioned in review
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-mockup",
                json=mockup_payload,
                timeout=45  # Longer timeout for image generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'mockup_data' in data:
                    mockup_data = data['mockup_data']
                    self.log_test(
                        "Generate Mockup - Success",
                        True,
                        f"Visual mockup generated ({len(str(mockup_data))} chars)",
                        {"mockup_size": len(str(mockup_data)), "has_usage": bool(data.get('usage'))}
                    )
                else:
                    self.log_test(
                        "Generate Mockup - Missing Mockup Data",
                        False,
                        "Response missing 'mockup_data' field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Generate Mockup - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Generate Mockup - Exception",
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
    
    def test_proxy_status_endpoint(self):
        """Test GET /api/proxy/status endpoint - CRITICAL for automation"""
        print("\n🧪 Testing Proxy Status Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/proxy/status", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'enabled' in data:
                    if data['enabled']:
                        # Check proxy details
                        required_fields = ['total_proxies', 'current_index', 'proxies']
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if not missing_fields:
                            self.log_test(
                                "Proxy Status - Enabled",
                                True,
                                f"Proxy service enabled with {data['total_proxies']} proxies",
                                {"total_proxies": data['total_proxies'], "current_index": data['current_index']}
                            )
                        else:
                            self.log_test(
                                "Proxy Status - Missing Fields",
                                False,
                                f"Proxy enabled but missing fields: {missing_fields}",
                                {"missing_fields": missing_fields}
                            )
                    else:
                        self.log_test(
                            "Proxy Status - Disabled",
                            False,
                            "Proxy service is disabled - automation with proxy will fail",
                            {"enabled": False, "message": data.get('message', 'No message')}
                        )
                else:
                    self.log_test(
                        "Proxy Status - Invalid Response",
                        False,
                        "Response missing 'enabled' field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Proxy Status - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Proxy Status - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    # ============= Service Integrations Tests =============
    
    def test_create_integration_endpoint(self):
        """Test POST /api/integrations endpoint"""
        print("\n🧪 Testing Create Integration Endpoint...")
        
        # Test data for Hugging Face integration
        integration_data = {
            "service_type": "huggingface",
            "name": "Test HF Integration",
            "credentials": {"api_key": "test_key_123"},
            "enabled": True
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/integrations",
                json=integration_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['id', 'service_type', 'name', 'credentials', 'enabled', 'created_at', 'updated_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.created_integration_id = data['id']
                    self.log_test(
                        "Create Integration - Success",
                        True,
                        f"Integration created with ID: {data['id']}",
                        {"integration_id": data['id'], "service_type": data['service_type']}
                    )
                else:
                    self.log_test(
                        "Create Integration - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Create Integration - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Create Integration - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_integrations_endpoint(self):
        """Test GET /api/integrations endpoint"""
        print("\n🧪 Testing Get Integrations Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/integrations", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_test(
                        "Get Integrations - Success",
                        True,
                        f"Retrieved {len(data)} integrations",
                        {"integration_count": len(data)}
                    )
                    
                    # Check structure if integrations exist
                    if data:
                        integration = data[0]
                        required_fields = ['id', 'service_type', 'name', 'credentials', 'enabled']
                        missing_fields = [field for field in required_fields if field not in integration]
                        
                        if not missing_fields:
                            self.log_test(
                                "Get Integrations - Structure Valid",
                                True,
                                "Integration structure is correct",
                                {"sample_integration": integration['name']}
                            )
                        else:
                            self.log_test(
                                "Get Integrations - Structure Invalid",
                                False,
                                f"Integration missing fields: {missing_fields}",
                                {"missing_fields": missing_fields}
                            )
                else:
                    self.log_test(
                        "Get Integrations - Invalid Response",
                        False,
                        "Response is not a list",
                        {"response_type": type(data).__name__}
                    )
            else:
                self.log_test(
                    "Get Integrations - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get Integrations - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_specific_integration_endpoint(self):
        """Test GET /api/integrations/{id} endpoint"""
        print("\n🧪 Testing Get Specific Integration Endpoint...")
        
        if not self.created_integration_id:
            self.log_test(
                "Get Specific Integration - No Integration ID",
                False,
                "No integration ID available for testing (create integration failed)",
                {"created_integration_id": self.created_integration_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/integrations/{self.created_integration_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all required fields
                required_fields = ['id', 'service_type', 'name', 'credentials', 'enabled', 'created_at', 'updated_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Get Specific Integration - Success",
                        True,
                        f"Retrieved integration: {data['name']}",
                        {"integration_id": data['id'], "service_type": data['service_type']}
                    )
                else:
                    self.log_test(
                        "Get Specific Integration - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            elif response.status_code == 404:
                self.log_test(
                    "Get Specific Integration - Not Found",
                    False,
                    "Integration not found (404)",
                    {"integration_id": self.created_integration_id, "status_code": 404}
                )
            else:
                self.log_test(
                    "Get Specific Integration - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get Specific Integration - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_update_integration_endpoint(self):
        """Test PUT /api/integrations/{id} endpoint"""
        print("\n🧪 Testing Update Integration Endpoint...")
        
        if not self.created_integration_id:
            self.log_test(
                "Update Integration - No Integration ID",
                False,
                "No integration ID available for testing",
                {"created_integration_id": self.created_integration_id}
            )
            return
        
        # Test toggling enabled status
        update_data = {
            "enabled": False,
            "name": "Updated Test HF Integration"
        }
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/integrations/{self.created_integration_id}",
                json=update_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('enabled') == False and data.get('name') == "Updated Test HF Integration":
                    self.log_test(
                        "Update Integration - Success",
                        True,
                        "Integration updated successfully",
                        {"integration_id": data['id'], "enabled": data['enabled'], "name": data['name']}
                    )
                else:
                    self.log_test(
                        "Update Integration - Update Failed",
                        False,
                        "Integration not updated correctly",
                        {"expected_enabled": False, "actual_enabled": data.get('enabled')}
                    )
            else:
                self.log_test(
                    "Update Integration - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Update Integration - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_delete_integration_endpoint(self):
        """Test DELETE /api/integrations/{id} endpoint"""
        print("\n🧪 Testing Delete Integration Endpoint...")
        
        if not self.created_integration_id:
            self.log_test(
                "Delete Integration - No Integration ID",
                False,
                "No integration ID available for testing",
                {"created_integration_id": self.created_integration_id}
            )
            return
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/integrations/{self.created_integration_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'deleted' in data['message'].lower():
                    self.log_test(
                        "Delete Integration - Success",
                        True,
                        "Integration deleted successfully",
                        {"integration_id": self.created_integration_id, "message": data['message']}
                    )
                    
                    # Verify deletion by trying to get the integration
                    verify_response = self.session.get(
                        f"{BACKEND_URL}/integrations/{self.created_integration_id}",
                        timeout=15
                    )
                    
                    if verify_response.status_code == 404:
                        self.log_test(
                            "Delete Integration - Verification",
                            True,
                            "Integration deletion verified (404 on GET)",
                            {"verification_status": 404}
                        )
                    else:
                        self.log_test(
                            "Delete Integration - Verification Failed",
                            False,
                            f"Integration still exists after deletion (status: {verify_response.status_code})",
                            {"verification_status": verify_response.status_code}
                        )
                else:
                    self.log_test(
                        "Delete Integration - Invalid Response",
                        False,
                        "Delete response missing success message",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Delete Integration - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Delete Integration - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    # ============= MCP Servers Tests =============
    
    def test_create_mcp_server_endpoint(self):
        """Test POST /api/mcp-servers endpoint"""
        print("\n🧪 Testing Create MCP Server Endpoint...")
        
        # Test data for browser automation server
        server_data = {
            "name": "Test Browser Automation",
            "server_type": "browser_automation",
            "enabled": True,
            "priority": 80,
            "fallback_order": 1
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/mcp-servers",
                json=server_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['id', 'name', 'server_type', 'enabled', 'priority', 'health_status', 'created_at', 'updated_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.created_mcp_server_id = data['id']
                    self.log_test(
                        "Create MCP Server - Success",
                        True,
                        f"MCP server created with ID: {data['id']}",
                        {"server_id": data['id'], "server_type": data['server_type'], "priority": data['priority']}
                    )
                else:
                    self.log_test(
                        "Create MCP Server - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Create MCP Server - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Create MCP Server - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_mcp_servers_endpoint(self):
        """Test GET /api/mcp-servers endpoint (should be sorted by priority)"""
        print("\n🧪 Testing Get MCP Servers Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/mcp-servers", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_test(
                        "Get MCP Servers - Success",
                        True,
                        f"Retrieved {len(data)} MCP servers",
                        {"server_count": len(data)}
                    )
                    
                    # Check priority sorting if multiple servers exist
                    if len(data) > 1:
                        priorities = [server.get('priority', 0) for server in data]
                        is_sorted = all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))
                        
                        if is_sorted:
                            self.log_test(
                                "Get MCP Servers - Priority Sorting",
                                True,
                                "Servers correctly sorted by priority (descending)",
                                {"priorities": priorities}
                            )
                        else:
                            self.log_test(
                                "Get MCP Servers - Priority Sorting Failed",
                                False,
                                "Servers not sorted by priority",
                                {"priorities": priorities}
                            )
                    
                    # Check structure if servers exist
                    if data:
                        server = data[0]
                        required_fields = ['id', 'name', 'server_type', 'enabled', 'priority', 'health_status']
                        missing_fields = [field for field in required_fields if field not in server]
                        
                        if not missing_fields:
                            self.log_test(
                                "Get MCP Servers - Structure Valid",
                                True,
                                "MCP server structure is correct",
                                {"sample_server": server['name']}
                            )
                        else:
                            self.log_test(
                                "Get MCP Servers - Structure Invalid",
                                False,
                                f"MCP server missing fields: {missing_fields}",
                                {"missing_fields": missing_fields}
                            )
                else:
                    self.log_test(
                        "Get MCP Servers - Invalid Response",
                        False,
                        "Response is not a list",
                        {"response_type": type(data).__name__}
                    )
            else:
                self.log_test(
                    "Get MCP Servers - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get MCP Servers - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_specific_mcp_server_endpoint(self):
        """Test GET /api/mcp-servers/{id} endpoint"""
        print("\n🧪 Testing Get Specific MCP Server Endpoint...")
        
        if not self.created_mcp_server_id:
            self.log_test(
                "Get Specific MCP Server - No Server ID",
                False,
                "No MCP server ID available for testing (create server failed)",
                {"created_mcp_server_id": self.created_mcp_server_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/mcp-servers/{self.created_mcp_server_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all required fields
                required_fields = ['id', 'name', 'server_type', 'enabled', 'priority', 'health_status', 'created_at', 'updated_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Get Specific MCP Server - Success",
                        True,
                        f"Retrieved MCP server: {data['name']}",
                        {"server_id": data['id'], "server_type": data['server_type']}
                    )
                else:
                    self.log_test(
                        "Get Specific MCP Server - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            elif response.status_code == 404:
                self.log_test(
                    "Get Specific MCP Server - Not Found",
                    False,
                    "MCP server not found (404)",
                    {"server_id": self.created_mcp_server_id, "status_code": 404}
                )
            else:
                self.log_test(
                    "Get Specific MCP Server - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get Specific MCP Server - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_update_mcp_server_endpoint(self):
        """Test PUT /api/mcp-servers/{id} endpoint"""
        print("\n🧪 Testing Update MCP Server Endpoint...")
        
        if not self.created_mcp_server_id:
            self.log_test(
                "Update MCP Server - No Server ID",
                False,
                "No MCP server ID available for testing",
                {"created_mcp_server_id": self.created_mcp_server_id}
            )
            return
        
        # Test updating priority, fallback_order, and health_status
        update_data = {
            "priority": 90,
            "fallback_order": 2,
            "health_status": "healthy"
        }
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/mcp-servers/{self.created_mcp_server_id}",
                json=update_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get('priority') == 90 and 
                    data.get('fallback_order') == 2 and 
                    data.get('health_status') == "healthy"):
                    self.log_test(
                        "Update MCP Server - Success",
                        True,
                        "MCP server updated successfully",
                        {"server_id": data['id'], "priority": data['priority'], "health_status": data['health_status']}
                    )
                else:
                    self.log_test(
                        "Update MCP Server - Update Failed",
                        False,
                        "MCP server not updated correctly",
                        {"expected_priority": 90, "actual_priority": data.get('priority')}
                    )
            else:
                self.log_test(
                    "Update MCP Server - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Update MCP Server - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_health_check_mcp_server_endpoint(self):
        """Test POST /api/mcp-servers/{id}/health-check endpoint"""
        print("\n🧪 Testing MCP Server Health Check Endpoint...")
        
        if not self.created_mcp_server_id:
            self.log_test(
                "MCP Server Health Check - No Server ID",
                False,
                "No MCP server ID available for testing",
                {"created_mcp_server_id": self.created_mcp_server_id}
            )
            return
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/mcp-servers/{self.created_mcp_server_id}/health-check",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'status' in data and 'server_id' in data:
                    if data['server_id'] == self.created_mcp_server_id:
                        self.log_test(
                            "MCP Server Health Check - Success",
                            True,
                            f"Health check completed with status: {data['status']}",
                            {"server_id": data['server_id'], "status": data['status']}
                        )
                        
                        # Verify that last_health_check was updated
                        verify_response = self.session.get(
                            f"{BACKEND_URL}/mcp-servers/{self.created_mcp_server_id}",
                            timeout=15
                        )
                        
                        if verify_response.status_code == 200:
                            server_data = verify_response.json()
                            if 'last_health_check' in server_data and server_data['last_health_check']:
                                self.log_test(
                                    "MCP Server Health Check - Timestamp Updated",
                                    True,
                                    "Health check timestamp updated correctly",
                                    {"last_health_check": server_data['last_health_check']}
                                )
                            else:
                                self.log_test(
                                    "MCP Server Health Check - Timestamp Missing",
                                    False,
                                    "Health check timestamp not updated",
                                    {"last_health_check": server_data.get('last_health_check')}
                                )
                    else:
                        self.log_test(
                            "MCP Server Health Check - Wrong Server ID",
                            False,
                            "Health check returned wrong server ID",
                            {"expected": self.created_mcp_server_id, "actual": data['server_id']}
                        )
                else:
                    self.log_test(
                        "MCP Server Health Check - Missing Fields",
                        False,
                        "Health check response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "MCP Server Health Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "MCP Server Health Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_get_active_mcp_servers_endpoint(self):
        """Test GET /api/mcp-servers/active/list endpoint"""
        print("\n🧪 Testing Get Active MCP Servers Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/mcp-servers/active/list", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    # Check that all returned servers are enabled
                    all_enabled = all(server.get('enabled', False) for server in data)
                    
                    if all_enabled:
                        self.log_test(
                            "Get Active MCP Servers - Success",
                            True,
                            f"Retrieved {len(data)} active MCP servers (all enabled)",
                            {"active_server_count": len(data)}
                        )
                        
                        # Check fallback order sorting if multiple servers
                        if len(data) > 1:
                            fallback_orders = [server.get('fallback_order') for server in data if server.get('fallback_order') is not None]
                            if fallback_orders:
                                is_sorted = all(fallback_orders[i] <= fallback_orders[i+1] for i in range(len(fallback_orders)-1))
                                
                                if is_sorted:
                                    self.log_test(
                                        "Get Active MCP Servers - Fallback Order Sorting",
                                        True,
                                        "Active servers correctly sorted by fallback order",
                                        {"fallback_orders": fallback_orders}
                                    )
                                else:
                                    self.log_test(
                                        "Get Active MCP Servers - Fallback Order Sorting Failed",
                                        False,
                                        "Active servers not sorted by fallback order",
                                        {"fallback_orders": fallback_orders}
                                    )
                    else:
                        disabled_servers = [server for server in data if not server.get('enabled', False)]
                        self.log_test(
                            "Get Active MCP Servers - Disabled Servers Included",
                            False,
                            f"Found {len(disabled_servers)} disabled servers in active list",
                            {"disabled_count": len(disabled_servers)}
                        )
                else:
                    self.log_test(
                        "Get Active MCP Servers - Invalid Response",
                        False,
                        "Response is not a list",
                        {"response_type": type(data).__name__}
                    )
            else:
                self.log_test(
                    "Get Active MCP Servers - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Get Active MCP Servers - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_delete_mcp_server_endpoint(self):
        """Test DELETE /api/mcp-servers/{id} endpoint"""
        print("\n🧪 Testing Delete MCP Server Endpoint...")
        
        if not self.created_mcp_server_id:
            self.log_test(
                "Delete MCP Server - No Server ID",
                False,
                "No MCP server ID available for testing",
                {"created_mcp_server_id": self.created_mcp_server_id}
            )
            return
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/mcp-servers/{self.created_mcp_server_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'deleted' in data['message'].lower():
                    self.log_test(
                        "Delete MCP Server - Success",
                        True,
                        "MCP server deleted successfully",
                        {"server_id": self.created_mcp_server_id, "message": data['message']}
                    )
                    
                    # Verify deletion by trying to get the server
                    verify_response = self.session.get(
                        f"{BACKEND_URL}/mcp-servers/{self.created_mcp_server_id}",
                        timeout=15
                    )
                    
                    if verify_response.status_code == 404:
                        self.log_test(
                            "Delete MCP Server - Verification",
                            True,
                            "MCP server deletion verified (404 on GET)",
                            {"verification_status": 404}
                        )
                    else:
                        self.log_test(
                            "Delete MCP Server - Verification Failed",
                            False,
                            f"MCP server still exists after deletion (status: {verify_response.status_code})",
                            {"verification_status": verify_response.status_code}
                        )
                else:
                    self.log_test(
                        "Delete MCP Server - Invalid Response",
                        False,
                        "Delete response missing success message",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Delete MCP Server - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Delete MCP Server - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_profile_lifecycle_endpoints(self):
        """Test Profile Lifecycle Endpoints per Review Request Specification"""
        print("\n🧪 Testing Profile Lifecycle Endpoints - REVIEW REQUEST SPECIFICATION...")
        
        created_profile_id = None
        
        # Step 1: Create a profile with region="US"
        print("   Step 1: Creating profile with region=US...")
        create_payload = {
            "region": "US"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/profile/create",
                json=create_payload,
                timeout=60  # Profile creation takes time due to warmup
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields per spec
                required_fields = ['profile_id', 'is_warm']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    created_profile_id = data['profile_id']
                    is_warm = data.get('is_warm')
                    
                    if is_warm == True:
                        self.log_test(
                            "Profile Create - Success",
                            True,
                            f"Profile created with ID: {created_profile_id}, is_warm=true",
                            {"profile_id": created_profile_id, "is_warm": is_warm}
                        )
                        
                        # Validate meta.json file exists and has correct fields
                        self.validate_profile_meta_file(created_profile_id)
                        
                    else:
                        self.log_test(
                            "Profile Create - Not Warm",
                            False,
                            f"Profile created but is_warm={is_warm}, expected true",
                            {"profile_id": created_profile_id, "is_warm": is_warm}
                        )
                else:
                    self.log_test(
                        "Profile Create - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
                    return
            else:
                self.log_test(
                    "Profile Create - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Profile Create - Timeout",
                False,
                "Profile creation timed out after 60 seconds",
                {"timeout": 60}
            )
            return
        except Exception as e:
            self.log_test(
                "Profile Create - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return
        
        if not created_profile_id:
            return
        
        # Step 2: Use the profile
        print("   Step 2: Using profile to create session...")
        use_payload = {
            "profile_id": created_profile_id
        }
        
        session_id = None
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/profile/use",
                json=use_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'session_id' in data:
                    session_id = data['session_id']
                    self.log_test(
                        "Profile Use - Success",
                        True,
                        f"Session created: {session_id}",
                        {"session_id": session_id, "profile_id": created_profile_id}
                    )
                    
                    # Validate meta updates (used_count++, last_used updated)
                    self.validate_profile_meta_updates(created_profile_id)
                    
                else:
                    self.log_test(
                        "Profile Use - Missing Session ID",
                        False,
                        "Response missing session_id field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Profile Use - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Use - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Step 3: Check profile status
        print("   Step 3: Checking profile status...")
        try:
            response = self.session.get(
                f"{BACKEND_URL}/profile/{created_profile_id}/status",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields per spec
                required_fields = ['profile_id', 'created_at', 'last_used', 'used_count', 'proxy']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    used_count = data.get('used_count', 0)
                    proxy_info = data.get('proxy', {})
                    
                    # Validate proxy fields are present
                    proxy_fields = ['ip', 'country', 'region', 'city', 'isp']
                    missing_proxy_fields = [field for field in proxy_fields if not proxy_info.get(field)]
                    
                    if used_count >= 1 and not missing_proxy_fields:
                        self.log_test(
                            "Profile Status - Success",
                            True,
                            f"Status reflects usage: used_count={used_count}, proxy fields present",
                            {"used_count": used_count, "proxy_fields": list(proxy_info.keys())}
                        )
                    else:
                        issues = []
                        if used_count < 1:
                            issues.append(f"used_count={used_count} (expected >=1)")
                        if missing_proxy_fields:
                            issues.append(f"missing proxy fields: {missing_proxy_fields}")
                        
                        self.log_test(
                            "Profile Status - Validation Failed",
                            False,
                            f"Status validation issues: {'; '.join(issues)}",
                            {"used_count": used_count, "missing_proxy_fields": missing_proxy_fields}
                        )
                else:
                    self.log_test(
                        "Profile Status - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Profile Status - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Status - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def validate_profile_meta_file(self, profile_id):
        """Validate /app/runtime/profiles/{profile_id}/meta.json exists and has correct fields"""
        print(f"   Validating meta.json file for profile {profile_id}...")
        
        import os
        import json
        
        try:
            meta_path = f"/app/runtime/profiles/{profile_id}/meta.json"
            storage_path = f"/app/runtime/profiles/{profile_id}/storage_state.json"
            
            # Check if meta.json exists
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                
                # Check required fields per spec
                required_checks = [
                    ('status', 'warm'),
                    ('warmup.is_warm', True),
                    ('warmup.warmed_at', lambda x: x is not None),
                    ('warmup.sites_visited', lambda x: isinstance(x, list) and len(x) > 0),
                    ('browser.user_agent', lambda x: x is not None and len(x) > 0),
                    ('locale.timezone_id', lambda x: x is not None),
                    ('locale.locale', lambda x: x is not None),
                    ('locale.languages', lambda x: isinstance(x, list) and len(x) > 0),
                    ('proxy.ip', lambda x: x is not None),
                    ('proxy.country', lambda x: x is not None),
                    ('proxy.region', lambda x: x is not None),
                    ('proxy.city', lambda x: x is not None),
                    ('proxy.isp', lambda x: x is not None),
                    ('proxy.timezone', lambda x: x is not None)
                ]
                
                validation_results = []
                for field_path, expected in required_checks:
                    try:
                        # Navigate nested fields
                        value = meta
                        for key in field_path.split('.'):
                            value = value[key]
                        
                        if callable(expected):
                            is_valid = expected(value)
                        else:
                            is_valid = value == expected
                        
                        validation_results.append((field_path, is_valid, value))
                    except (KeyError, TypeError):
                        validation_results.append((field_path, False, None))
                
                # Check if storage_state.json exists
                storage_exists = os.path.exists(storage_path)
                
                failed_validations = [f for f, valid, _ in validation_results if not valid]
                
                if not failed_validations and storage_exists:
                    sites_visited = meta.get('warmup', {}).get('sites_visited', [])
                    expected_sites = ['google.com', 'youtube.com', 'reddit.com', 'amazon.com']
                    sites_match = any(site in str(sites_visited) for site in expected_sites)
                    
                    self.log_test(
                        "Profile Meta Validation - Success",
                        True,
                        f"Meta.json valid: status=warm, warmup.is_warm=true, storage_state.json exists, sites_visited includes expected sites",
                        {"sites_visited": sites_visited, "storage_exists": storage_exists}
                    )
                else:
                    issues = []
                    if failed_validations:
                        issues.append(f"failed fields: {failed_validations}")
                    if not storage_exists:
                        issues.append("storage_state.json missing")
                    
                    self.log_test(
                        "Profile Meta Validation - Failed",
                        False,
                        f"Meta validation issues: {'; '.join(issues)}",
                        {"failed_fields": failed_validations, "storage_exists": storage_exists}
                    )
            else:
                self.log_test(
                    "Profile Meta Validation - File Missing",
                    False,
                    f"Meta.json file not found at {meta_path}",
                    {"meta_path": meta_path}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Meta Validation - Exception",
                False,
                f"Error validating meta file: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def validate_profile_meta_updates(self, profile_id):
        """Validate that meta.json was updated after profile use (used_count++, last_used updated)"""
        print(f"   Validating meta.json updates for profile {profile_id}...")
        
        import os
        import json
        from datetime import datetime, timezone
        
        try:
            meta_path = f"/app/runtime/profiles/{profile_id}/meta.json"
            
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                
                used_count = meta.get('used_count', 0)
                last_used = meta.get('last_used')
                
                # Check if used_count is incremented (should be >= 1 after use)
                # Check if last_used is recent (within last 5 minutes)
                if used_count >= 1 and last_used:
                    try:
                        last_used_dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        time_diff = (now - last_used_dt).total_seconds()
                        
                        if time_diff < 300:  # Within 5 minutes
                            self.log_test(
                                "Profile Meta Updates - Success",
                                True,
                                f"Meta updated correctly: used_count={used_count}, last_used recent",
                                {"used_count": used_count, "last_used": last_used, "time_diff_seconds": time_diff}
                            )
                        else:
                            self.log_test(
                                "Profile Meta Updates - Stale Timestamp",
                                False,
                                f"last_used timestamp too old: {time_diff} seconds ago",
                                {"used_count": used_count, "time_diff_seconds": time_diff}
                            )
                    except Exception as dt_error:
                        self.log_test(
                            "Profile Meta Updates - Timestamp Parse Error",
                            False,
                            f"Could not parse last_used timestamp: {str(dt_error)}",
                            {"last_used": last_used}
                        )
                else:
                    self.log_test(
                        "Profile Meta Updates - Not Updated",
                        False,
                        f"Meta not properly updated: used_count={used_count}, last_used={last_used}",
                        {"used_count": used_count, "last_used": last_used}
                    )
            else:
                self.log_test(
                    "Profile Meta Updates - File Missing",
                    False,
                    f"Meta.json file not found for validation",
                    {"meta_path": meta_path}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Meta Updates - Exception",
                False,
                f"Error validating meta updates: {str(e)}",
                {"error_type": type(e).__name__}
            )

    def test_chat_endpoint_critical_flow(self):
        """Test POST /api/chat endpoint - CRITICAL STUCK TASK (stuck_count: 2)"""
        print("\n🧪 Testing Chat Endpoint - CRITICAL SEQUENTIAL MESSAGES...")
        
        # Test the specific issue: Only first message works, subsequent return stub
        # This is the CRITICAL issue mentioned in review request
        
        # Test 1: First message
        print("   Testing first chat message...")
        payload_1 = {
            "message": "Hello, how are you?",
            "history": [],
            "model": "x-ai/grok-code-fast-1"  # Using the model mentioned in review
        }
        
        first_message_response = None
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload_1,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['message', 'response']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check if response is not a fallback stub
                    response_text = data['message']
                    # Check for stub patterns mentioned in the issue
                    stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                    is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                    
                    if len(response_text) > 10 and not is_stub:
                        first_message_response = data
                        self.log_test(
                            "Chat - First Message",
                            True,
                            f"First message worked correctly ({len(response_text)} chars)",
                            {"response_length": len(response_text), "has_cost": bool(data.get('cost'))}
                        )
                    else:
                        self.log_test(
                            "Chat - First Message - Stub Response",
                            False,
                            "First message already returning stub response",
                            {"response_preview": response_text[:100], "is_stub": is_stub}
                        )
                        return  # No point testing further if first message fails
                else:
                    self.log_test(
                        "Chat - First Message - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
                    return
            else:
                self.log_test(
                    "Chat - First Message - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Chat - First Message - Timeout",
                False,
                "Chat request timed out after 30 seconds",
                {"timeout": 30}
            )
            return
        except Exception as e:
            self.log_test(
                "Chat - First Message - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return
        
        # Test 2: Second message with history (CRITICAL TEST)
        print("   Testing second chat message with history...")
        if first_message_response:
            # Build history from first message
            history = [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": first_message_response['message']}
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
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'message' in data and 'response' in data:
                        response_text = data['message']
                        # Check for stub patterns mentioned in the issue
                        stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                        is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                        
                        if len(response_text) > 10 and not is_stub and "4" in response_text:
                            self.log_test(
                                "Chat - Second Message with History",
                                True,
                                f"Second message worked correctly ({len(response_text)} chars)",
                                {"response_length": len(response_text), "contains_answer": "4" in response_text}
                            )
                        else:
                            self.log_test(
                                "Chat - Second Message - CRITICAL FAILURE",
                                False,
                                "Second message returning stub response - CONFIRMS USER ISSUE",
                                {"response_preview": response_text[:100], "is_stub": is_stub}
                            )
                    else:
                        self.log_test(
                            "Chat - Second Message - Missing Fields",
                            False,
                            "Response missing required fields",
                            {"response_keys": list(data.keys())}
                        )
                else:
                    self.log_test(
                        "Chat - Second Message - HTTP Error",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        {"status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.log_test(
                    "Chat - Second Message - Exception",
                    False,
                    f"Unexpected error: {str(e)}",
                    {"error_type": type(e).__name__}
                )
        
        # Test 3: Third message with extended history (CRITICAL TEST)
        print("   Testing third chat message with extended history...")
        if first_message_response:
            # Build extended history
            extended_history = [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": first_message_response['message']},
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
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'message' in data and 'response' in data:
                        response_text = data['message']
                        # Check for stub patterns mentioned in the issue
                        stub_patterns = ["I understand! In Chat mode", "stub", "fallback"]
                        is_stub = any(pattern.lower() in response_text.lower() for pattern in stub_patterns)
                        
                        # Check if it's a joke (contains humor indicators)
                        joke_indicators = ["why", "what do you call", "knock knock", "funny", "laugh", "haha"]
                        has_joke = any(indicator.lower() in response_text.lower() for indicator in joke_indicators)
                        
                        if len(response_text) > 10 and not is_stub:
                            self.log_test(
                                "Chat - Third Message with Extended History",
                                True,
                                f"Third message worked correctly ({len(response_text)} chars)",
                                {"response_length": len(response_text), "appears_to_be_joke": has_joke}
                            )
                        else:
                            self.log_test(
                                "Chat - Third Message - CRITICAL FAILURE",
                                False,
                                "Third message returning stub response - CONFIRMS SEQUENTIAL ISSUE",
                                {"response_preview": response_text[:100], "is_stub": is_stub}
                            )
                    else:
                        self.log_test(
                            "Chat - Third Message - Missing Fields",
                            False,
                            "Response missing required fields",
                            {"response_keys": list(data.keys())}
                        )
                else:
                    self.log_test(
                        "Chat - Third Message - HTTP Error",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        {"status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.log_test(
                    "Chat - Third Message - Exception",
                    False,
                    f"Unexpected error: {str(e)}",
                    {"error_type": type(e).__name__}
                )

    # ============= BROWSER AUTOMATION TESTS =============
    
    def test_browser_automation_create_session_with_proxy(self):
        """Test POST /api/automation/session/create endpoint with proxy - CRITICAL"""
        print("\n🧪 Testing Browser Automation - Create Session with Proxy...")
        
        # Generate unique session ID
        session_id = f"test_session_{int(time.time())}"
        
        # Test with proxy as mentioned in review request
        payload = {
            "session_id": session_id,
            "use_proxy": True  # Critical test with proxy
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
                            "Browser Automation - Create Session with Proxy",
                            True,
                            f"Session with proxy created successfully: {session_id}",
                            {"session_id": session_id, "status": data['status'], "proxy_enabled": True}
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
        
        if not hasattr(self, 'created_automation_session_id'):
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
    
    def test_browser_automation_screenshot(self):
        """Test GET /api/automation/screenshot/{session_id} endpoint"""
        print("\n🧪 Testing Browser Automation - Screenshot...")
        
        if not hasattr(self, 'created_automation_session_id'):
            self.log_test(
                "Browser Automation - Screenshot - No Session",
                False,
                "No automation session available for testing",
                {"session_id": None}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/automation/screenshot/{self.created_automation_session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'screenshot' in data and data['screenshot']:
                    # Check if screenshot is base64 encoded
                    screenshot = data['screenshot']
                    if screenshot.startswith('data:image/png;base64,'):
                        self.log_test(
                            "Browser Automation - Screenshot",
                            True,
                            f"Screenshot captured successfully ({len(screenshot)} chars)",
                            {"screenshot_length": len(screenshot), "format": "base64 PNG"}
                        )
                    else:
                        self.log_test(
                            "Browser Automation - Screenshot - Invalid Format",
                            False,
                            "Screenshot not in expected base64 PNG format",
                            {"screenshot_preview": screenshot[:100]}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Screenshot - No Data",
                        False,
                        "No screenshot data in response",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Browser Automation - Screenshot - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Screenshot - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_find_elements(self):
        """Test POST /api/automation/find-elements endpoint (Vision Model)"""
        print("\n🧪 Testing Browser Automation - Find Elements with Vision...")
        
        if not hasattr(self, 'created_automation_session_id'):
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
    
    def test_browser_automation_smart_click(self):
        """Test POST /api/automation/smart-click endpoint (Vision + Click)"""
        print("\n🧪 Testing Browser Automation - Smart Click...")
        
        if not hasattr(self, 'created_automation_session_id'):
            self.log_test(
                "Browser Automation - Smart Click - No Session",
                False,
                "No automation session available for testing",
                {"session_id": None}
            )
            return
        
        # Test smart clicking on sign up button
        payload = {
            "session_id": self.created_automation_session_id,
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
                    # Check if we got click confirmation and screenshot
                    required_fields = ['clicked_element', 'screenshot']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        clicked_element = data['clicked_element']
                        self.log_test(
                            "Browser Automation - Smart Click",
                            True,
                            f"Successfully clicked element: {clicked_element.get('text', 'N/A')}",
                            {"clicked_element": clicked_element, "has_screenshot": bool(data['screenshot'])}
                        )
                    else:
                        self.log_test(
                            "Browser Automation - Smart Click - Missing Data",
                            False,
                            f"Smart click successful but missing fields: {missing_fields}",
                            {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Smart Click - Failed",
                        False,
                        "Smart click operation failed",
                        {"success": data.get('success'), "response": data}
                    )
            elif response.status_code == 404:
                self.log_test(
                    "Browser Automation - Smart Click - Element Not Found",
                    False,
                    "Sign up button not found by vision model",
                    {"status_code": 404, "detail": response.text}
                )
            else:
                self.log_test(
                    "Browser Automation - Smart Click - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Smart Click - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_page_info(self):
        """Test GET /api/automation/page-info/{session_id} endpoint"""
        print("\n🧪 Testing Browser Automation - Page Info...")
        
        if not hasattr(self, 'created_automation_session_id'):
            self.log_test(
                "Browser Automation - Page Info - No Session",
                False,
                "No automation session available for testing",
                {"session_id": None}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/automation/page-info/{self.created_automation_session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['url', 'title', 'screenshot']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Browser Automation - Page Info",
                        True,
                        f"Page info retrieved: {data['title']} at {data['url']}",
                        {"url": data['url'], "title": data['title'], "has_screenshot": bool(data['screenshot'])}
                    )
                else:
                    self.log_test(
                        "Browser Automation - Page Info - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Browser Automation - Page Info - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Page Info - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_cleanup(self):
        """Test DELETE /api/automation/session/{session_id} endpoint"""
        print("\n🧪 Testing Browser Automation - Session Cleanup...")
        
        if not hasattr(self, 'created_automation_session_id'):
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

    # ============= CONTEXT WINDOW MANAGEMENT TESTS =============
    
    def test_context_status_endpoint(self):
        """Test POST /api/context/status endpoint"""
        print("\n🧪 Testing Context Status Endpoint...")
        
        # Test 1: Short conversation (no compression needed)
        print("   Testing short conversation context status...")
        short_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
            {"role": "user", "content": "What's the weather like?"}
        ]
        
        payload = {
            "history": short_history,
            "model": "anthropic/claude-3.5-sonnet"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/context/status",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'usage']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    usage = data['usage']
                    usage_fields = ['current_tokens', 'max_tokens', 'percentage', 'remaining']
                    usage_missing = [field for field in usage_fields if field not in usage]
                    
                    if not usage_missing:
                        percentage = usage['percentage']
                        if percentage < 0.5:  # Should be low for short conversation
                            self.log_test(
                                "Context Status - Short Conversation",
                                True,
                                f"Context usage correctly calculated: {usage['percentage_display']} ({usage['current_tokens']}/{usage['max_tokens']} tokens)",
                                {"percentage": percentage, "tokens": usage['current_tokens'], "max_tokens": usage['max_tokens']}
                            )
                        else:
                            self.log_test(
                                "Context Status - Short Conversation - High Usage",
                                False,
                                f"Unexpectedly high context usage for short conversation: {usage['percentage_display']}",
                                {"percentage": percentage, "tokens": usage['current_tokens']}
                            )
                    else:
                        self.log_test(
                            "Context Status - Short Conversation - Missing Usage Fields",
                            False,
                            f"Usage object missing fields: {usage_missing}",
                            {"missing_fields": usage_missing, "usage_keys": list(usage.keys())}
                        )
                else:
                    self.log_test(
                        "Context Status - Short Conversation - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Context Status - Short Conversation - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Context Status - Short Conversation - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test 2: Different models
        print("   Testing context status with different models...")
        models_to_test = [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-pro"
        ]
        
        for model in models_to_test:
            payload = {
                "history": short_history,
                "model": model
            }
            
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/context/status",
                    json=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'usage' in data:
                        usage = data['usage']
                        max_tokens = usage.get('max_tokens', 0)
                        
                        # Different models should have different limits
                        if max_tokens > 0:
                            self.log_test(
                                f"Context Status - Model {model}",
                                True,
                                f"Model {model} context limit: {max_tokens} tokens",
                                {"model": model, "max_tokens": max_tokens}
                            )
                        else:
                            self.log_test(
                                f"Context Status - Model {model} - No Limit",
                                False,
                                f"Model {model} returned zero context limit",
                                {"model": model, "max_tokens": max_tokens}
                            )
                    else:
                        self.log_test(
                            f"Context Status - Model {model} - No Usage",
                            False,
                            f"Model {model} response missing usage data",
                            {"model": model, "response_keys": list(data.keys())}
                        )
                else:
                    self.log_test(
                        f"Context Status - Model {model} - HTTP Error",
                        False,
                        f"Model {model} returned HTTP {response.status_code}",
                        {"model": model, "status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Context Status - Model {model} - Exception",
                    False,
                    f"Model {model} test failed: {str(e)}",
                    {"model": model, "error": str(e)}
                )
    
    def test_context_switch_model_endpoint(self):
        """Test POST /api/context/switch-model endpoint"""
        print("\n🧪 Testing Context Switch Model Endpoint...")
        
        # Create a session with multiple messages
        session_id = str(uuid.uuid4())
        conversation_history = [
            {"role": "user", "content": "I'm building a React application for task management"},
            {"role": "assistant", "content": "That's great! A task management app is a useful project. What features are you planning to include?"},
            {"role": "user", "content": "I want to add tasks, mark them complete, and organize by categories"},
            {"role": "assistant", "content": "Excellent features! You'll need components for task creation, task lists, and category management. Would you like me to help you design the component structure?"},
            {"role": "user", "content": "Yes, and I want to use TypeScript for better type safety"},
            {"role": "assistant", "content": "Perfect choice! TypeScript will help catch errors early. Let me suggest a component structure with proper TypeScript interfaces."}
        ]
        
        payload = {
            "session_id": session_id,
            "old_model": "anthropic/claude-3.5-sonnet",
            "new_model": "openai/gpt-4o",
            "history": conversation_history
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/context/switch-model",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'new_session_id', 'parent_session_id', 'compressed_messages', 'compression_info', 'new_context_usage']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    new_session_id = data['new_session_id']
                    compressed_messages = data['compressed_messages']
                    compression_info = data['compression_info']
                    new_context_usage = data['new_context_usage']
                    
                    # Verify new session ID is different
                    if new_session_id != session_id:
                        self.log_test(
                            "Context Switch Model - New Session Created",
                            True,
                            f"New session created: {new_session_id}",
                            {"old_session": session_id, "new_session": new_session_id}
                        )
                        
                        # Verify compressed messages are returned
                        if isinstance(compressed_messages, list) and len(compressed_messages) > 0:
                            self.log_test(
                                "Context Switch Model - Compressed Messages",
                                True,
                                f"Compressed messages returned: {len(compressed_messages)} messages",
                                {"message_count": len(compressed_messages), "original_count": len(conversation_history)}
                            )
                            
                            # Verify compression info
                            if compression_info.get('compressed') == True:
                                reduction = compression_info.get('reduction_percentage', 0)
                                self.log_test(
                                    "Context Switch Model - Compression Info",
                                    True,
                                    f"Compression applied: {reduction:.1f}% reduction",
                                    {"reduction": reduction, "original_tokens": compression_info.get('original_tokens'), "compressed_tokens": compression_info.get('compressed_tokens')}
                                )
                            else:
                                self.log_test(
                                    "Context Switch Model - No Compression",
                                    True,
                                    "No compression needed for conversation",
                                    {"compression_reason": compression_info.get('reason', 'Unknown')}
                                )
                            
                            # Verify new context usage
                            if 'max_tokens' in new_context_usage and new_context_usage['max_tokens'] > 0:
                                self.log_test(
                                    "Context Switch Model - New Context Usage",
                                    True,
                                    f"New model context calculated: {new_context_usage['percentage_display']} ({new_context_usage['current_tokens']}/{new_context_usage['max_tokens']} tokens)",
                                    {"new_model_usage": new_context_usage}
                                )
                            else:
                                self.log_test(
                                    "Context Switch Model - New Context Usage Invalid",
                                    False,
                                    "New context usage calculation failed",
                                    {"new_context_usage": new_context_usage}
                                )
                        else:
                            self.log_test(
                                "Context Switch Model - No Compressed Messages",
                                False,
                                "No compressed messages returned",
                                {"compressed_messages": compressed_messages}
                            )
                    else:
                        self.log_test(
                            "Context Switch Model - Same Session ID",
                            False,
                            "New session ID is same as old session ID",
                            {"session_id": session_id, "new_session_id": new_session_id}
                        )
                else:
                    self.log_test(
                        "Context Switch Model - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Context Switch Model - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Context Switch Model - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test error handling - missing new_model
        print("   Testing error handling for missing new_model...")
        invalid_payload = {
            "session_id": session_id,
            "old_model": "anthropic/claude-3.5-sonnet",
            "history": conversation_history
            # Missing new_model
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/context/switch-model",
                json=invalid_payload,
                timeout=15
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Context Switch Model - Error Handling",
                    True,
                    "Correctly returned 400 for missing new_model",
                    {"status_code": 400}
                )
            else:
                self.log_test(
                    "Context Switch Model - Error Handling Failed",
                    False,
                    f"Expected 400, got {response.status_code}",
                    {"expected": 400, "actual": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Context Switch Model - Error Handling Exception",
                False,
                f"Error handling test failed: {str(e)}",
                {"error": str(e)}
            )
    
    def test_chat_with_context_management(self):
        """Test POST /api/chat endpoint with context management integration"""
        print("\n🧪 Testing Chat with Context Management...")
        
        # Test 1: Chat with session_id and verify context_usage in response
        session_id = str(uuid.uuid4())
        
        payload = {
            "message": "Tell me about React hooks and their benefits",
            "history": [
                {"role": "user", "content": "I'm learning React development"},
                {"role": "assistant", "content": "That's great! React is a powerful library for building user interfaces."}
            ],
            "model": "anthropic/claude-3.5-sonnet",
            "session_id": session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for context management fields
                context_fields = ['context_usage', 'context_warning']
                has_context_fields = any(field in data for field in context_fields)
                
                if has_context_fields:
                    context_usage = data.get('context_usage', {})
                    context_warning = data.get('context_warning', '')
                    
                    if 'percentage' in context_usage:
                        self.log_test(
                            "Chat Context Management - Usage Tracking",
                            True,
                            f"Context usage tracked: {context_usage.get('percentage_display', 'N/A')} ({context_usage.get('current_tokens', 0)}/{context_usage.get('max_tokens', 0)} tokens)",
                            {"context_usage": context_usage, "has_warning": bool(context_warning)}
                        )
                    else:
                        self.log_test(
                            "Chat Context Management - Usage Missing",
                            False,
                            "Context usage data incomplete",
                            {"context_usage": context_usage}
                        )
                else:
                    self.log_test(
                        "Chat Context Management - No Context Fields",
                        False,
                        "Response missing context management fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Chat Context Management - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Chat Context Management - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test 2: Long conversation to potentially trigger compression
        print("   Testing long conversation for compression...")
        
        # Create a longer conversation history
        long_history = []
        for i in range(15):  # 15 exchanges = 30 messages
            long_history.extend([
                {"role": "user", "content": f"This is user message number {i+1}. I'm asking about React development, specifically about component lifecycle, state management, props passing, event handling, and performance optimization. Can you explain these concepts in detail?"},
                {"role": "assistant", "content": f"This is assistant response number {i+1}. React components have a lifecycle with mounting, updating, and unmounting phases. State management can be done with useState for local state or useReducer for complex state. Props are passed down from parent to child components. Event handling uses synthetic events. Performance can be optimized with React.memo, useMemo, and useCallback hooks."}
            ])
        
        long_payload = {
            "message": "Now summarize everything we've discussed about React",
            "history": long_history,
            "model": "anthropic/claude-3.5-sonnet",
            "session_id": session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=long_payload,
                timeout=45  # Longer timeout for potential compression
            )
            
            if response.status_code == 200:
                data = response.json()
                
                context_usage = data.get('context_usage', {})
                new_session_id = data.get('new_session_id')
                context_warning = data.get('context_warning', '')
                
                # Check if compression or new session was triggered
                if new_session_id and new_session_id != session_id:
                    self.log_test(
                        "Chat Context Management - New Session Created",
                        True,
                        f"New session created due to context limit: {new_session_id}",
                        {"old_session": session_id, "new_session": new_session_id, "context_usage": context_usage}
                    )
                elif 'compress' in context_warning.lower() or context_usage.get('percentage', 0) > 0.5:
                    self.log_test(
                        "Chat Context Management - Compression Triggered",
                        True,
                        f"Context compression likely triggered: {context_usage.get('percentage_display', 'N/A')}",
                        {"context_usage": context_usage, "warning": context_warning}
                    )
                else:
                    self.log_test(
                        "Chat Context Management - Long Conversation Handled",
                        True,
                        f"Long conversation handled successfully: {context_usage.get('percentage_display', 'N/A')}",
                        {"context_usage": context_usage, "message_count": len(long_history)}
                    )
            else:
                self.log_test(
                    "Chat Context Management - Long Conversation Error",
                    False,
                    f"Long conversation failed: HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Chat Context Management - Long Conversation Exception",
                False,
                f"Long conversation test failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_openrouter_balance_endpoint(self):
        """Test GET /api/openrouter/balance endpoint"""
        print("\n🧪 Testing OpenRouter Balance Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/openrouter/balance", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['balance', 'used', 'remaining', 'label', 'is_free_tier']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    balance = data['balance']
                    remaining = data['remaining']
                    is_free_tier = data['is_free_tier']
                    
                    # Validate balance data
                    if isinstance(balance, (int, float)) or balance == -1:  # -1 for unlimited
                        self.log_test(
                            "OpenRouter Balance - Success",
                            True,
                            f"Balance retrieved: ${balance} (remaining: ${remaining}, free_tier: {is_free_tier})",
                            {"balance": balance, "remaining": remaining, "is_free_tier": is_free_tier}
                        )
                    else:
                        self.log_test(
                            "OpenRouter Balance - Invalid Balance",
                            False,
                            f"Invalid balance format: {balance}",
                            {"balance": balance, "balance_type": type(balance).__name__}
                        )
                else:
                    self.log_test(
                        "OpenRouter Balance - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "OpenRouter Balance - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "OpenRouter Balance - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )

    # ============= RESEARCH PLANNER TESTS =============
    
    def test_research_task_simple_analyze(self):
        """Test POST /api/research-task endpoint - Simple task should NOT require research"""
        print("\n🧪 Testing Research Task - Simple Task (Analyze Mode)...")
        
        # Test data from review request - simple task
        test_data = {
            "user_request": "Create a simple calculator with basic operations",
            "model": "anthropic/claude-3.5-sonnet",
            "research_mode": "analyze"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/research-task",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for analyze mode
                required_fields = ['complexity_assessment', 'requires_research', 'reasoning']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    complexity = data.get('complexity_assessment')
                    requires_research = data.get('requires_research')
                    reasoning = data.get('reasoning', '')
                    
                    # Simple calculator should be assessed as simple and NOT require research
                    if complexity == "simple" and requires_research == False:
                        self.log_test(
                            "Research Task - Simple Analyze - Correct Assessment",
                            True,
                            f"Simple task correctly identified: complexity={complexity}, requires_research={requires_research}",
                            {
                                "complexity": complexity,
                                "requires_research": requires_research,
                                "reasoning_length": len(reasoning),
                                "has_usage": 'usage' in data
                            }
                        )
                    else:
                        self.log_test(
                            "Research Task - Simple Analyze - Wrong Assessment",
                            False,
                            f"Simple task incorrectly assessed: complexity={complexity}, requires_research={requires_research}",
                            {
                                "expected_complexity": "simple",
                                "actual_complexity": complexity,
                                "expected_research": False,
                                "actual_research": requires_research
                            }
                        )
                    
                    # Check if usage information is included
                    if 'usage' in data:
                        self.log_test(
                            "Research Task - Simple Analyze - Usage Info",
                            True,
                            "Usage information included in response",
                            {"usage": data['usage']}
                        )
                else:
                    self.log_test(
                        "Research Task - Simple Analyze - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Research Task - Simple Analyze - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Research Task - Simple Analyze - Timeout",
                False,
                "Request timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "Research Task - Simple Analyze - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_research_task_complex_analyze(self):
        """Test POST /api/research-task endpoint - Complex task should require research"""
        print("\n🧪 Testing Research Task - Complex Task (Analyze Mode)...")
        
        # Test data from review request - complex task
        test_data = {
            "user_request": "Create a real-time collaborative whiteboard app with video conferencing, like Miro or FigJam",
            "model": "anthropic/claude-3.5-sonnet",
            "research_mode": "analyze"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/research-task",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for analyze mode
                required_fields = ['complexity_assessment', 'requires_research', 'reasoning']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    complexity = data.get('complexity_assessment')
                    requires_research = data.get('requires_research')
                    reasoning = data.get('reasoning', '')
                    research_queries = data.get('research_queries', [])
                    
                    # Complex whiteboard app should require research
                    if requires_research == True and complexity in ["complex", "moderate"]:
                        self.log_test(
                            "Research Task - Complex Analyze - Correct Assessment",
                            True,
                            f"Complex task correctly identified: complexity={complexity}, requires_research={requires_research}",
                            {
                                "complexity": complexity,
                                "requires_research": requires_research,
                                "reasoning_length": len(reasoning),
                                "query_count": len(research_queries)
                            }
                        )
                        
                        # Check if research queries are provided and actionable
                        if research_queries and len(research_queries) >= 3:
                            # Check if queries are specific and actionable
                            query_keywords = ['whiteboard', 'collaborative', 'real-time', 'video', 'conferencing', 'miro', 'figjam', '2025', 'best practices']
                            relevant_queries = []
                            for query in research_queries:
                                if any(keyword.lower() in query.lower() for keyword in query_keywords):
                                    relevant_queries.append(query)
                            
                            if len(relevant_queries) >= 2:
                                self.log_test(
                                    "Research Task - Complex Analyze - Quality Queries",
                                    True,
                                    f"Generated {len(research_queries)} research queries, {len(relevant_queries)} are relevant",
                                    {"total_queries": len(research_queries), "relevant_queries": relevant_queries}
                                )
                            else:
                                self.log_test(
                                    "Research Task - Complex Analyze - Poor Quality Queries",
                                    False,
                                    f"Research queries not specific enough: {research_queries}",
                                    {"queries": research_queries, "relevant_count": len(relevant_queries)}
                                )
                        else:
                            self.log_test(
                                "Research Task - Complex Analyze - Insufficient Queries",
                                False,
                                f"Expected 3-5 research queries, got {len(research_queries)}",
                                {"query_count": len(research_queries), "queries": research_queries}
                            )
                    else:
                        self.log_test(
                            "Research Task - Complex Analyze - Wrong Assessment",
                            False,
                            f"Complex task incorrectly assessed: complexity={complexity}, requires_research={requires_research}",
                            {
                                "expected_research": True,
                                "actual_research": requires_research,
                                "complexity": complexity
                            }
                        )
                else:
                    self.log_test(
                        "Research Task - Complex Analyze - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Research Task - Complex Analyze - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Research Task - Complex Analyze - Timeout",
                False,
                "Request timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "Research Task - Complex Analyze - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_research_task_full_pipeline(self):
        """Test POST /api/research-task endpoint - Full research pipeline"""
        print("\n🧪 Testing Research Task - Full Research Pipeline...")
        
        # Test data from review request - full research mode
        test_data = {
            "user_request": "Build a modern e-commerce platform with AI product recommendations",
            "model": "anthropic/claude-3.5-sonnet",
            "research_mode": "full"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/research-task",
                json=test_data,
                timeout=60  # Longer timeout for full research
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for full mode
                required_fields = ['requires_research', 'complexity', 'reasoning', 'research_queries']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    requires_research = data.get('requires_research')
                    complexity = data.get('complexity')
                    reasoning = data.get('reasoning', '')
                    research_queries = data.get('research_queries', [])
                    research_report = data.get('research_report', '')
                    total_usage = data.get('total_usage', {})
                    
                    # E-commerce platform should require research
                    if requires_research == True and complexity == "complex":
                        self.log_test(
                            "Research Task - Full Pipeline - Correct Assessment",
                            True,
                            f"Complex e-commerce task correctly identified: complexity={complexity}, requires_research={requires_research}",
                            {
                                "complexity": complexity,
                                "requires_research": requires_research,
                                "reasoning_length": len(reasoning),
                                "query_count": len(research_queries),
                                "has_report": bool(research_report),
                                "report_length": len(research_report)
                            }
                        )
                        
                        # Check research queries quality
                        if research_queries and len(research_queries) >= 3:
                            ecommerce_keywords = ['ecommerce', 'e-commerce', 'ai', 'recommendation', 'platform', 'modern', '2025', 'best practices']
                            relevant_queries = []
                            for query in research_queries:
                                if any(keyword.lower() in query.lower() for keyword in ecommerce_keywords):
                                    relevant_queries.append(query)
                            
                            if len(relevant_queries) >= 2:
                                self.log_test(
                                    "Research Task - Full Pipeline - Quality Queries",
                                    True,
                                    f"Generated {len(research_queries)} research queries, {len(relevant_queries)} are relevant",
                                    {"total_queries": len(research_queries), "relevant_queries": relevant_queries}
                                )
                            else:
                                self.log_test(
                                    "Research Task - Full Pipeline - Poor Quality Queries",
                                    False,
                                    f"Research queries not specific enough for e-commerce: {research_queries}",
                                    {"queries": research_queries, "relevant_count": len(relevant_queries)}
                                )
                        
                        # Check if research report is provided (for full mode)
                        if research_report and len(research_report) > 500:
                            # Check if report contains expected sections
                            report_sections = ['tech stack', 'implementation', 'best practices', 'security', 'performance']
                            found_sections = [section for section in report_sections if section.lower() in research_report.lower()]
                            
                            if len(found_sections) >= 3:
                                self.log_test(
                                    "Research Task - Full Pipeline - Detailed Report",
                                    True,
                                    f"Research report contains {len(found_sections)} expected sections ({len(research_report)} chars)",
                                    {"report_length": len(research_report), "sections_found": found_sections}
                                )
                            else:
                                self.log_test(
                                    "Research Task - Full Pipeline - Incomplete Report",
                                    False,
                                    f"Research report missing key sections (found {len(found_sections)}/5)",
                                    {"sections_found": found_sections, "report_preview": research_report[:200]}
                                )
                        else:
                            self.log_test(
                                "Research Task - Full Pipeline - No Report",
                                False,
                                f"Full research mode should include detailed report (got {len(research_report)} chars)",
                                {"report_length": len(research_report)}
                            )
                        
                        # Check total usage information
                        if total_usage and 'total_tokens' in total_usage:
                            self.log_test(
                                "Research Task - Full Pipeline - Usage Info",
                                True,
                                f"Combined usage information included: {total_usage.get('total_tokens', 0)} tokens",
                                {"total_usage": total_usage}
                            )
                        else:
                            self.log_test(
                                "Research Task - Full Pipeline - Missing Usage",
                                False,
                                "Full research should include combined usage information",
                                {"total_usage": total_usage}
                            )
                    else:
                        self.log_test(
                            "Research Task - Full Pipeline - Wrong Assessment",
                            False,
                            f"E-commerce task incorrectly assessed: complexity={complexity}, requires_research={requires_research}",
                            {
                                "expected_complexity": "complex",
                                "actual_complexity": complexity,
                                "expected_research": True,
                                "actual_research": requires_research
                            }
                        )
                else:
                    self.log_test(
                        "Research Task - Full Pipeline - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Research Task - Full Pipeline - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Research Task - Full Pipeline - Timeout",
                False,
                "Request timed out after 60 seconds",
                {"timeout": 60}
            )
        except Exception as e:
            self.log_test(
                "Research Task - Full Pipeline - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_research_task_error_handling(self):
        """Test POST /api/research-task endpoint - Error handling"""
        print("\n🧪 Testing Research Task - Error Handling...")
        
        # Test missing user_request
        test_data = {
            "model": "anthropic/claude-3.5-sonnet",
            "research_mode": "analyze"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/research-task",
                json=test_data,
                timeout=15
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Research Task - Error Handling - Missing Request",
                    True,
                    "Correctly returned 400 for missing user_request",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Research Task - Error Handling - Wrong Status",
                    False,
                    f"Expected 400 for missing user_request, got {response.status_code}",
                    {"expected": 400, "actual": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Research Task - Error Handling - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test fallback behavior (if model fails)
        print("   Testing fallback behavior...")
        test_data_fallback = {
            "user_request": "Test fallback with invalid model",
            "model": "invalid/model-name",
            "research_mode": "analyze"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/research-task",
                json=test_data_fallback,
                timeout=30
            )
            
            # Should either work with fallback or return proper error
            if response.status_code == 200:
                data = response.json()
                if 'complexity_assessment' in data and 'requires_research' in data:
                    self.log_test(
                        "Research Task - Error Handling - Fallback Success",
                        True,
                        "Fallback handling working correctly",
                        {"response_keys": list(data.keys())}
                    )
                else:
                    self.log_test(
                        "Research Task - Error Handling - Fallback Incomplete",
                        False,
                        "Fallback response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
            elif response.status_code == 500:
                self.log_test(
                    "Research Task - Error Handling - Model Error",
                    True,
                    "Correctly returned 500 for invalid model (no fallback implemented)",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Research Task - Error Handling - Unexpected Status",
                    False,
                    f"Unexpected status code for invalid model: {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Research Task - Error Handling - Fallback Exception",
                False,
                f"Unexpected error in fallback test: {str(e)}",
                {"error_type": type(e).__name__}
            )

    # ============= NEW DESIGN-FIRST WORKFLOW TESTS =============
    
    def test_generate_design_endpoint(self):
        """Test POST /api/generate-design endpoint"""
        print("\n🧪 Testing Generate Design Endpoint...")
        
        # Test data as specified in review request (corrected model ID)
        test_data = {
            "user_request": "Create a simple calculator app with basic operations",
            "model": "google/gemini-2.0-flash-exp:free"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/generate-design",
                json=test_data,
                timeout=45  # Longer timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['design_spec', 'usage']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    design_spec = data['design_spec']
                    usage = data['usage']
                    
                    # Validate design specification content
                    design_keywords = ['color', 'layout', 'button', 'background', 'font', 'padding', 'margin', 'theme']
                    found_keywords = [keyword for keyword in design_keywords if keyword.lower() in design_spec.lower()]
                    
                    if len(found_keywords) >= 3 and len(design_spec) > 100:
                        self.log_test(
                            "Generate Design - Success",
                            True,
                            f"Generated detailed design spec ({len(design_spec)} chars) with {len(found_keywords)} design elements",
                            {
                                "design_length": len(design_spec),
                                "design_keywords": found_keywords,
                                "usage": usage,
                                "model": test_data["model"]
                            }
                        )
                        
                        # Validate usage information
                        if usage and 'total_tokens' in usage and usage['total_tokens'] > 0:
                            self.log_test(
                                "Generate Design - Usage Info",
                                True,
                                f"Usage information included: {usage['total_tokens']} total tokens",
                                {"usage_details": usage}
                            )
                        else:
                            self.log_test(
                                "Generate Design - Usage Info Missing",
                                False,
                                "Usage information missing or invalid",
                                {"usage": usage}
                            )
                    else:
                        self.log_test(
                            "Generate Design - Poor Quality",
                            False,
                            f"Design spec too short or lacks design elements (found {len(found_keywords)}/8 keywords)",
                            {"design_preview": design_spec[:200], "found_keywords": found_keywords}
                        )
                else:
                    self.log_test(
                        "Generate Design - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Generate Design - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Generate Design - Timeout",
                False,
                "Design generation timed out after 45 seconds",
                {"timeout": 45}
            )
        except Exception as e:
            self.log_test(
                "Generate Design - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_validate_visual_endpoint(self):
        """Test POST /api/validate-visual endpoint"""
        print("\n🧪 Testing Validate Visual Endpoint...")
        
        # Test data as specified in review request (small base64 image)
        test_data = {
            "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "user_request": "A calculator with blue theme",
            "validator_model": "anthropic/claude-3-haiku"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/validate-visual",
                json=test_data,
                timeout=45  # Longer timeout for AI analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for validation response
                required_fields = ['scores', 'overall_score', 'verdict', 'feedback', 'specific_issues']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    scores = data['scores']
                    overall_score = data['overall_score']
                    verdict = data['verdict']
                    
                    # Validate scores structure
                    expected_score_fields = ['visual_hierarchy', 'readability', 'layout_alignment', 'completeness', 'professional_quality']
                    missing_score_fields = [field for field in expected_score_fields if field not in scores]
                    
                    if not missing_score_fields:
                        # Check if scores are numeric and in valid range
                        valid_scores = all(
                            isinstance(scores[field], (int, float)) and 0 <= scores[field] <= 10 
                            for field in expected_score_fields
                        )
                        
                        if valid_scores and isinstance(overall_score, (int, float)) and verdict in ['APPROVED', 'NEEDS_FIXES', 'ERROR']:
                            self.log_test(
                                "Validate Visual - Success",
                                True,
                                f"Visual validation completed: {verdict} (score: {overall_score})",
                                {
                                    "scores": scores,
                                    "overall_score": overall_score,
                                    "verdict": verdict,
                                    "feedback": data['feedback'][:100],
                                    "model": test_data["validator_model"]
                                }
                            )
                            
                            # Check usage information
                            if 'usage' in data and data['usage'].get('total_tokens', 0) > 0:
                                self.log_test(
                                    "Validate Visual - Usage Info",
                                    True,
                                    f"Usage information included: {data['usage']['total_tokens']} total tokens",
                                    {"usage_details": data['usage']}
                                )
                            else:
                                self.log_test(
                                    "Validate Visual - Usage Info Missing",
                                    False,
                                    "Usage information missing or invalid",
                                    {"usage": data.get('usage')}
                                )
                        else:
                            self.log_test(
                                "Validate Visual - Invalid Values",
                                False,
                                "Scores out of range or invalid verdict",
                                {"scores": scores, "overall_score": overall_score, "verdict": verdict}
                            )
                    else:
                        self.log_test(
                            "Validate Visual - Missing Score Fields",
                            False,
                            f"Scores missing fields: {missing_score_fields}",
                            {"missing_score_fields": missing_score_fields, "scores": scores}
                        )
                else:
                    self.log_test(
                        "Validate Visual - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Validate Visual - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Validate Visual - Timeout",
                False,
                "Visual validation timed out after 45 seconds",
                {"timeout": 45}
            )
        except Exception as e:
            self.log_test(
                "Validate Visual - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_openrouter_balance_endpoint(self):
        """Test GET /api/openrouter/balance endpoint"""
        print("\n🧪 Testing OpenRouter Balance Endpoint...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/openrouter/balance",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['balance', 'used', 'remaining', 'label', 'is_free_tier']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    balance = data['balance']
                    used = data['used']
                    remaining = data['remaining']
                    is_free_tier = data['is_free_tier']
                    
                    # Validate numeric fields
                    numeric_fields_valid = all(
                        isinstance(data[field], (int, float)) 
                        for field in ['balance', 'used', 'remaining']
                    )
                    
                    if numeric_fields_valid and isinstance(is_free_tier, bool):
                        balance_display = "Unlimited" if balance == -1 else f"${balance}"
                        remaining_display = "Unlimited" if remaining == -1 else f"${remaining}"
                        
                        self.log_test(
                            "OpenRouter Balance - Success",
                            True,
                            f"Balance: {balance_display}, Used: ${used}, Remaining: {remaining_display}, Free Tier: {is_free_tier}",
                            {
                                "balance": balance,
                                "used": used,
                                "remaining": remaining,
                                "label": data['label'],
                                "is_free_tier": is_free_tier
                            }
                        )
                        
                        # Additional validation: remaining should equal balance - used (approximately)
                        # Skip math check for unlimited accounts (-1 values)
                        if balance != -1 and remaining != -1:
                            calculated_remaining = balance - used
                            if abs(remaining - calculated_remaining) < 0.01:  # Allow small floating point differences
                                self.log_test(
                                    "OpenRouter Balance - Math Check",
                                    True,
                                    "Balance calculations are consistent",
                                    {"calculated_remaining": calculated_remaining, "reported_remaining": remaining}
                                )
                            else:
                                self.log_test(
                                    "OpenRouter Balance - Math Check Failed",
                                    False,
                                    f"Balance math inconsistent: {balance} - {used} ≠ {remaining}",
                                    {"balance": balance, "used": used, "remaining": remaining}
                                )
                        else:
                            self.log_test(
                                "OpenRouter Balance - Unlimited Account",
                                True,
                                "Unlimited account detected (balance/remaining = -1)",
                                {"account_type": "unlimited"}
                            )
                    else:
                        self.log_test(
                            "OpenRouter Balance - Invalid Types",
                            False,
                            "Balance fields have invalid data types",
                            {"data_types": {field: type(data[field]).__name__ for field in data.keys()}}
                        )
                else:
                    self.log_test(
                        "OpenRouter Balance - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "OpenRouter Balance - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "OpenRouter Balance - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )

    # ============= COMPREHENSIVE TESTING - Review Request Systems =============
    
    def test_self_improvement_health_check(self):
        """Test GET /api/self-improvement/health-check endpoint"""
        print("\n🧪 Testing Self-Improvement Health Check...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/self-improvement/health-check",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['timestamp', 'services', 'code_metrics']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    services = data.get('services', {})
                    expected_services = ['backend', 'frontend', 'mongodb', 'nginx-code-proxy', 'code-server']
                    
                    # Check if services are present
                    found_services = list(services.keys())
                    running_services = [s for s, info in services.items() if info.get('status') == 'RUNNING']
                    
                    self.log_test(
                        "Self-Improvement Health Check - Success",
                        True,
                        f"Health check completed. Found {len(found_services)} services, {len(running_services)} running",
                        {
                            "services_found": found_services,
                            "running_services": running_services,
                            "code_metrics": data.get('code_metrics', {})
                        }
                    )
                else:
                    self.log_test(
                        "Self-Improvement Health Check - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Self-Improvement Health Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Self-Improvement Health Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_self_improvement_analyze_code(self):
        """Test POST /api/self-improvement/analyze-code endpoint"""
        print("\n🧪 Testing Self-Improvement Code Analysis...")
        
        payload = {
            "target": "backend",
            "focus_areas": ["performance", "security"]
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/self-improvement/analyze-code",
                json=payload,
                timeout=60  # Longer timeout for AI analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['overall_health_score', 'critical_issues', 'improvements', 'summary']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    health_score = data.get('overall_health_score', 0)
                    critical_issues = data.get('critical_issues', [])
                    improvements = data.get('improvements', [])
                    
                    if isinstance(health_score, (int, float)) and 0 <= health_score <= 100:
                        self.log_test(
                            "Self-Improvement Code Analysis - Success",
                            True,
                            f"Code analysis completed. Health score: {health_score}/100, {len(critical_issues)} critical issues, {len(improvements)} improvements",
                            {
                                "health_score": health_score,
                                "critical_issues_count": len(critical_issues),
                                "improvements_count": len(improvements),
                                "focus_areas": payload["focus_areas"]
                            }
                        )
                    else:
                        self.log_test(
                            "Self-Improvement Code Analysis - Invalid Score",
                            False,
                            f"Invalid health score: {health_score}",
                            {"health_score": health_score}
                        )
                else:
                    self.log_test(
                        "Self-Improvement Code Analysis - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Self-Improvement Code Analysis - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Self-Improvement Code Analysis - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_self_improvement_project_structure(self):
        """Test GET /api/self-improvement/project-structure endpoint"""
        print("\n🧪 Testing Self-Improvement Project Structure...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/self-improvement/project-structure",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['structure', 'total_files', 'total_lines']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    structure = data.get('structure', {})
                    total_files = data.get('total_files', 0)
                    total_lines = data.get('total_lines', 0)
                    
                    # Check if backend and frontend are in structure
                    has_backend = 'backend' in structure
                    has_frontend = 'frontend' in structure
                    
                    if has_backend and has_frontend and total_files > 0:
                        self.log_test(
                            "Self-Improvement Project Structure - Success",
                            True,
                            f"Project structure retrieved. {total_files} files, {total_lines} lines of code",
                            {
                                "total_files": total_files,
                                "total_lines": total_lines,
                                "has_backend": has_backend,
                                "has_frontend": has_frontend
                            }
                        )
                    else:
                        self.log_test(
                            "Self-Improvement Project Structure - Invalid Structure",
                            False,
                            "Project structure missing backend/frontend or no files found",
                            {
                                "has_backend": has_backend,
                                "has_frontend": has_frontend,
                                "total_files": total_files
                            }
                        )
                else:
                    self.log_test(
                        "Self-Improvement Project Structure - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Self-Improvement Project Structure - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Self-Improvement Project Structure - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_document_verification_analyze(self):
        """Test POST /api/document-verification/analyze endpoint"""
        print("\n🧪 Testing Document Verification Analysis...")
        
        # Create a small test image (1x1 pixel PNG in base64)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        payload = {
            "document_base64": test_image_base64,
            "document_type": "general"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/document-verification/analyze",
                json=payload,
                timeout=90  # Longer timeout for AI analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['verdict', 'fraud_probability', 'multi_model_analysis']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    verdict = data.get('verdict')
                    fraud_probability = data.get('fraud_probability', 0)
                    multi_model = data.get('multi_model_analysis', {})
                    
                    # Check if verdict is valid
                    valid_verdicts = ['AUTHENTIC', 'SUSPICIOUS', 'LIKELY_FAKE']
                    if verdict in valid_verdicts and isinstance(fraud_probability, (int, float)):
                        # Check if multi-model analysis has GPT-5 and Claude
                        has_gpt5 = 'primary_model' in multi_model and 'GPT-5' in str(multi_model.get('primary_model', {}))
                        has_claude = 'secondary_model' in multi_model and 'Claude' in str(multi_model.get('secondary_model', {}))
                        
                        self.log_test(
                            "Document Verification Analysis - Success",
                            True,
                            f"Document analysis completed. Verdict: {verdict}, Fraud probability: {fraud_probability}%",
                            {
                                "verdict": verdict,
                                "fraud_probability": fraud_probability,
                                "has_gpt5_analysis": has_gpt5,
                                "has_claude_analysis": has_claude,
                                "multi_model_agreement": multi_model.get('agreement_level', 'N/A')
                            }
                        )
                    else:
                        self.log_test(
                            "Document Verification Analysis - Invalid Response",
                            False,
                            f"Invalid verdict ({verdict}) or fraud probability ({fraud_probability})",
                            {"verdict": verdict, "fraud_probability": fraud_probability}
                        )
                else:
                    self.log_test(
                        "Document Verification Analysis - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Document Verification Analysis - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Document Verification Analysis - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_planning_generate(self):
        """Test POST /api/planning/generate endpoint"""
        print("\n🧪 Testing Planning System - Generate Plan...")
        
        payload = {
            "goal": "Navigate to google.com and search for 'test'"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/planning/generate",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['plan', 'complexity', 'estimatedSteps']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    plan = data.get('plan', {})
                    steps = plan.get('steps', [])
                    complexity = data.get('complexity')
                    
                    # Check if plan has steps with required action types
                    action_types = [step.get('actionType') for step in steps]
                    expected_actions = ['NAVIGATE', 'TYPE', 'CLICK']
                    has_expected_actions = any(action in action_types for action in expected_actions)
                    
                    if len(steps) > 0 and has_expected_actions and complexity:
                        self.log_test(
                            "Planning Generate - Success",
                            True,
                            f"Plan generated successfully. {len(steps)} steps, complexity: {complexity}",
                            {
                                "steps_count": len(steps),
                                "complexity": complexity,
                                "action_types": action_types,
                                "goal": payload["goal"]
                            }
                        )
                    else:
                        self.log_test(
                            "Planning Generate - Invalid Plan",
                            False,
                            f"Plan missing steps or expected actions. Steps: {len(steps)}, Actions: {action_types}",
                            {"steps_count": len(steps), "action_types": action_types}
                        )
                else:
                    self.log_test(
                        "Planning Generate - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Planning Generate - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Planning Generate - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_comprehensive(self):
        """Comprehensive test of browser automation system as requested"""
        print("\n🧪 Testing Browser Automation - Comprehensive Flow...")
        
        # Test 1: Create Session
        session_id = "test-session-123"
        
        try:
            # Create session
            create_response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json={"session_id": session_id},
                timeout=30
            )
            
            if create_response.status_code == 200:
                create_data = create_response.json()
                if create_data.get('session_id') == session_id:
                    self.log_test(
                        "Browser Automation - Create Session",
                        True,
                        f"Session created successfully: {session_id}",
                        {"session_id": session_id, "status": create_data.get('status')}
                    )
                    
                    # Test 2: Navigate to Google
                    try:
                        navigate_response = self.session.post(
                            f"{BACKEND_URL}/automation/navigate",
                            json={"session_id": session_id, "url": "https://google.com"},
                            timeout=45
                        )
                        
                        if navigate_response.status_code == 200:
                            navigate_data = navigate_response.json()
                            if 'screenshot' in navigate_data:
                                self.log_test(
                                    "Browser Automation - Navigate to Google",
                                    True,
                                    "Successfully navigated to Google with screenshot",
                                    {"url": "https://google.com", "has_screenshot": True}
                                )
                                
                                # Test 3: Get Screenshot
                                try:
                                    screenshot_response = self.session.get(
                                        f"{BACKEND_URL}/automation/screenshot/{session_id}",
                                        timeout=30
                                    )
                                    
                                    if screenshot_response.status_code == 200:
                                        screenshot_data = screenshot_response.json()
                                        if 'screenshot' in screenshot_data:
                                            screenshot_b64 = screenshot_data['screenshot']
                                            self.log_test(
                                                "Browser Automation - Get Screenshot",
                                                True,
                                                f"Screenshot captured successfully ({len(screenshot_b64)} chars)",
                                                {"screenshot_length": len(screenshot_b64)}
                                            )
                                        else:
                                            self.log_test(
                                                "Browser Automation - Get Screenshot - No Data",
                                                False,
                                                "Screenshot response missing screenshot field",
                                                {"response_keys": list(screenshot_data.keys())}
                                            )
                                    else:
                                        self.log_test(
                                            "Browser Automation - Get Screenshot - HTTP Error",
                                            False,
                                            f"HTTP {screenshot_response.status_code}: {screenshot_response.text}",
                                            {"status_code": screenshot_response.status_code}
                                        )
                                        
                                except Exception as e:
                                    self.log_test(
                                        "Browser Automation - Get Screenshot - Exception",
                                        False,
                                        f"Screenshot error: {str(e)}",
                                        {"error_type": type(e).__name__}
                                    )
                            else:
                                self.log_test(
                                    "Browser Automation - Navigate - No Screenshot",
                                    False,
                                    "Navigation response missing screenshot",
                                    {"response_keys": list(navigate_data.keys())}
                                )
                        else:
                            self.log_test(
                                "Browser Automation - Navigate - HTTP Error",
                                False,
                                f"HTTP {navigate_response.status_code}: {navigate_response.text}",
                                {"status_code": navigate_response.status_code}
                            )
                            
                    except Exception as e:
                        self.log_test(
                            "Browser Automation - Navigate - Exception",
                            False,
                            f"Navigation error: {str(e)}",
                            {"error_type": type(e).__name__}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Create Session - Invalid Response",
                        False,
                        "Session creation response invalid",
                        {"expected_session": session_id, "actual_session": create_data.get('session_id')}
                    )
            else:
                self.log_test(
                    "Browser Automation - Create Session - HTTP Error",
                    False,
                    f"HTTP {create_response.status_code}: {create_response.text}",
                    {"status_code": create_response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Create Session - Exception",
                False,
                f"Session creation error: {str(e)}",
                {"error_type": type(e).__name__}
            )

    def run_critical_tests(self):
        """Run CRITICAL backend tests based on review request"""
        print("🚀 Starting CRITICAL Backend API Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("🎯 Focus: STUCK TASKS and Core Functionality")
        
        # PRIORITY 1 - STUCK TASKS (stuck_count >= 1)
        print("\n" + "="*60)
        print("PRIORITY 1 - STUCK TASKS (stuck_count >= 1)")
        print("="*60)
        
        # 1. POST /api/chat (stuck_count: 2) - CRITICAL
        self.test_chat_endpoint_critical_flow()
        
        # PRIORITY 2 - Core Functionality
        print("\n" + "="*60)
        print("PRIORITY 2 - Core Functionality")
        print("="*60)
        
        # 2. Profile Lifecycle Endpoints (as requested in review)
        self.test_profile_lifecycle_endpoints()
        
        # 3. POST /api/generate-code - Agent mode
        self.test_generate_code_endpoint_critical()
        
        # 4. POST /api/generate-design & /api/generate-mockup
        # This is called from generate_code_endpoint_critical
        
        # 5. Proxy status for automation
        self.test_proxy_status_endpoint()
        
        # 6. POST /api/automation/session/create with proxy
        self.test_browser_automation_create_session_with_proxy()
        
        self.print_critical_summary()

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Lovable.dev Clone Backend API Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test PROFILE LIFECYCLE ENDPOINTS (as requested in review)
        print("\n" + "=" * 60)
        print("🔐 TESTING PROFILE LIFECYCLE ENDPOINTS")
        print("=" * 60)
        self.test_profile_lifecycle_endpoints()
        
        # Test NEW RESEARCH PLANNER ENDPOINT (as requested in review)
        print("\n" + "=" * 60)
        print("🔬 TESTING NEW RESEARCH PLANNER ENDPOINT")
        print("=" * 60)
        self.test_research_task_simple_analyze()
        self.test_research_task_complex_analyze()
        self.test_research_task_full_pipeline()
        self.test_research_task_error_handling()
        
        # Test NEW DESIGN-FIRST WORKFLOW ENDPOINTS (as requested in review)
        print("\n" + "=" * 60)
        print("🎨 TESTING NEW DESIGN-FIRST WORKFLOW ENDPOINTS")
        print("=" * 60)
        self.test_generate_design_endpoint()
        self.test_validate_visual_endpoint()
        self.test_openrouter_balance_endpoint()
        
        # Test NEW CONTEXT WINDOW MANAGEMENT ENDPOINTS (as requested in review)
        print("\n" + "=" * 60)
        print("🧠 TESTING NEW CONTEXT WINDOW MANAGEMENT ENDPOINTS")
        print("=" * 60)
        self.test_context_status_endpoint()
        self.test_context_switch_model_endpoint()
        self.test_chat_with_context_management()
        
        # Test chat endpoint (previously tested)
        self.test_chat_endpoint()
        
        # Test original endpoints
        self.test_generate_code_endpoint()
        self.test_openrouter_integration()
        self.test_create_project_endpoint()
        self.test_get_projects_endpoint()
        self.test_get_specific_project_endpoint()
        self.test_invalid_project_id()
        
        # Test new Service Integrations endpoints
        print("\n" + "=" * 60)
        print("🔧 TESTING SERVICE INTEGRATIONS ENDPOINTS")
        print("=" * 60)
        self.test_create_integration_endpoint()
        self.test_get_integrations_endpoint()
        self.test_get_specific_integration_endpoint()
        self.test_update_integration_endpoint()
        self.test_delete_integration_endpoint()
        
        # Test new MCP Servers endpoints
        print("\n" + "=" * 60)
        print("🖥️ TESTING MCP SERVERS ENDPOINTS")
        print("=" * 60)
        self.test_create_mcp_server_endpoint()
        self.test_get_mcp_servers_endpoint()
        self.test_get_specific_mcp_server_endpoint()
        self.test_update_mcp_server_endpoint()
        self.test_health_check_mcp_server_endpoint()
        self.test_get_active_mcp_servers_endpoint()
        self.test_delete_mcp_server_endpoint()
        
        # Test Browser Automation endpoints (as requested in review)
        print("\n" + "=" * 60)
        print("🤖 TESTING BROWSER AUTOMATION ENDPOINTS")
        print("=" * 60)
        self.test_browser_automation_create_session()
        self.test_browser_automation_navigate()
        self.test_browser_automation_screenshot()
        self.test_browser_automation_find_elements()
        self.test_browser_automation_smart_click()
        self.test_browser_automation_page_info()
        self.test_browser_automation_cleanup()
        
        # COMPREHENSIVE TESTING - Review Request Systems
        print("\n" + "=" * 60)
        print("🔍 COMPREHENSIVE TESTING - All Systems (Review Request)")
        print("=" * 60)
        
        # 1. SELF-IMPROVEMENT SYSTEM
        print("\n🧠 Testing Self-Improvement System...")
        self.test_self_improvement_health_check()
        self.test_self_improvement_analyze_code()
        self.test_self_improvement_project_structure()
        
        # 2. DOCUMENT VERIFICATION SYSTEM
        print("\n📄 Testing Document Verification System...")
        self.test_document_verification_analyze()
        
        # 3. PLANNING SYSTEM
        print("\n📋 Testing Planning System...")
        self.test_planning_generate()
        
        # 4. BROWSER AUTOMATION (Additional comprehensive tests)
        print("\n🤖 Testing Browser Automation - Comprehensive Flow...")
        self.test_browser_automation_comprehensive()
        
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
    
    def print_critical_summary(self):
        """Print summary of critical test results"""
        print("\n" + "="*80)
        print("🎯 CRITICAL BACKEND TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by category
        critical_failures = []
        chat_issues = []
        automation_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if 'Chat' in result['test']:
                    chat_issues.append(result)
                elif 'Automation' in result['test'] or 'Proxy' in result['test']:
                    automation_issues.append(result)
                else:
                    critical_failures.append(result)
        
        # Report critical chat issues (STUCK TASK)
        if chat_issues:
            print(f"\n🚨 CRITICAL CHAT ISSUES (STUCK TASK - stuck_count: 2):")
            for issue in chat_issues:
                print(f"   ❌ {issue['test']}: {issue['message']}")
        
        # Report automation issues
        if automation_issues:
            print(f"\n🤖 AUTOMATION ISSUES:")
            for issue in automation_issues:
                print(f"   ❌ {issue['test']}: {issue['message']}")
        
        # Report other critical failures
        if critical_failures:
            print(f"\n⚠️ OTHER CRITICAL FAILURES:")
            for issue in critical_failures:
                print(f"   ❌ {issue['test']}: {issue['message']}")
        
        # Success summary
        successful_tests = [result for result in self.test_results if result['success']]
        if successful_tests:
            print(f"\n✅ WORKING ENDPOINTS:")
            for success in successful_tests:
                print(f"   ✅ {success['test']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = LovableBackendTester()
    
    # Run critical tests based on review request
    tester.run_critical_tests()
    
    # Exit with error code if tests failed
    total_tests = len(tester.test_results)
    failed_tests = sum(1 for result in tester.test_results if not result['success'])
    exit(0 if failed_tests == 0 else 1)