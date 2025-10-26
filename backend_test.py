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
BACKEND_URL = "https://devai-studio-5.preview.emergentagent.com/api"

class LovableBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_project_id = None
        self.created_integration_id = None
        self.created_mcp_server_id = None
        
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
    
    def test_chat_endpoint(self):
        """Test POST /api/chat endpoint - Chat conversation mode"""
        print("\n🧪 Testing Chat Endpoint...")
        
        # Test 1: Basic chat in English
        print("   Testing basic chat in English...")
        payload_english = {
            "message": "Hello, how are you?",
            "history": [],
            "model": "anthropic/claude-3.5-sonnet"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload_english,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['message', 'response', 'cost']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check if response is not a fallback stub
                    response_text = data['message']
                    if len(response_text) > 10 and "Hello" in response_text or "Hi" in response_text:
                        self.log_test(
                            "Chat - Basic English",
                            True,
                            f"Chat responded naturally in English ({len(response_text)} chars)",
                            {"response_length": len(response_text), "has_cost": bool(data.get('cost'))}
                        )
                    else:
                        self.log_test(
                            "Chat - Basic English - Stub Response",
                            False,
                            "Response appears to be a fallback stub message",
                            {"response_preview": response_text[:100]}
                        )
                else:
                    self.log_test(
                        "Chat - Basic English - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Chat - Basic English - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Chat - Basic English - Timeout",
                False,
                "Chat request timed out after 30 seconds",
                {"timeout": 30}
            )
        except Exception as e:
            self.log_test(
                "Chat - Basic English - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test 2: Chat in Russian
        print("   Testing chat in Russian...")
        payload_russian = {
            "message": "Привет! Как дела?",
            "history": [],
            "model": "anthropic/claude-3.5-sonnet"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload_russian,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'response' in data:
                    response_text = data['message']
                    # Check if response contains Cyrillic characters (indicating Russian response)
                    has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in response_text)
                    
                    if has_cyrillic and len(response_text) > 10:
                        self.log_test(
                            "Chat - Russian Language",
                            True,
                            f"Chat responded in Russian ({len(response_text)} chars)",
                            {"response_length": len(response_text), "has_cyrillic": has_cyrillic}
                        )
                    else:
                        self.log_test(
                            "Chat - Russian Language - Wrong Language",
                            False,
                            "Response not in Russian or too short",
                            {"response_preview": response_text[:100], "has_cyrillic": has_cyrillic}
                        )
                else:
                    self.log_test(
                        "Chat - Russian Language - Missing Fields",
                        False,
                        "Response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Chat - Russian Language - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Chat - Russian Language - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test 3: Chat with history
        print("   Testing chat with conversation history...")
        payload_with_history = {
            "message": "What colors would look good?",
            "history": [
                {"role": "user", "content": "I want to build a fitness app"},
                {"role": "assistant", "content": "That sounds great! What features are you thinking about?"}
            ],
            "model": "anthropic/claude-3.5-sonnet"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chat",
                json=payload_with_history,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'response' in data:
                    response_text = data['message']
                    # Check if response is contextual (mentions fitness, app, or colors)
                    contextual_keywords = ['fitness', 'app', 'color', 'blue', 'green', 'red', 'design']
                    has_context = any(keyword.lower() in response_text.lower() for keyword in contextual_keywords)
                    
                    if has_context and len(response_text) > 20:
                        self.log_test(
                            "Chat - With History Context",
                            True,
                            f"Chat provided contextual response about fitness app colors ({len(response_text)} chars)",
                            {"response_length": len(response_text), "contextual": has_context}
                        )
                    else:
                        self.log_test(
                            "Chat - With History Context - No Context",
                            False,
                            "Response doesn't appear contextual to fitness app discussion",
                            {"response_preview": response_text[:150], "contextual": has_context}
                        )
                else:
                    self.log_test(
                        "Chat - With History Context - Missing Fields",
                        False,
                        "Response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Chat - With History Context - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Chat - With History Context - Exception",
                False,
                f"Unexpected error: {str(e)}",
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
                        self.log_test(
                            "OpenRouter Balance - Success",
                            True,
                            f"Balance: ${balance}, Used: ${used}, Remaining: ${remaining}, Free Tier: {is_free_tier}",
                            {
                                "balance": balance,
                                "used": used,
                                "remaining": remaining,
                                "label": data['label'],
                                "is_free_tier": is_free_tier
                            }
                        )
                        
                        # Additional validation: remaining should equal balance - used (approximately)
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

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Lovable.dev Clone Backend API Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test NEW DESIGN-FIRST WORKFLOW ENDPOINTS (as requested in review)
        print("\n" + "=" * 60)
        print("🎨 TESTING NEW DESIGN-FIRST WORKFLOW ENDPOINTS")
        print("=" * 60)
        self.test_generate_design_endpoint()
        self.test_validate_visual_endpoint()
        self.test_openrouter_balance_endpoint()
        
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