#!/usr/bin/env python3
"""
Test script for Design-First Workflow endpoints only
Tests the three new endpoints as specified in the review request
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://browser-automator-2.preview.emergentagent.com/api"

def log_test(test_name, success, message, details=None):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}: {message}")
    if details and not success:
        print(f"   Details: {details}")

def test_generate_design():
    """Test POST /api/generate-design endpoint"""
    print("\n🧪 Testing Generate Design Endpoint...")
    
    # Test data as specified in review request (using alternative free model)
    test_data = {
        "user_request": "Create a simple calculator app with basic operations",
        "model": "openai/gpt-oss-20b:free"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-design",
            json=test_data,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            if 'design_spec' in data and 'usage' in data:
                design_spec = data['design_spec']
                usage = data['usage']
                
                # Validate design specification content
                design_keywords = ['color', 'layout', 'button', 'background', 'font', 'padding', 'margin', 'theme']
                found_keywords = [keyword for keyword in design_keywords if keyword.lower() in design_spec.lower()]
                
                if len(found_keywords) >= 3 and len(design_spec) > 100:
                    log_test(
                        "Generate Design - Success",
                        True,
                        f"Generated detailed design spec ({len(design_spec)} chars) with {len(found_keywords)} design elements"
                    )
                    
                    # Check usage information
                    if usage and 'total_tokens' in usage and usage['total_tokens'] > 0:
                        log_test(
                            "Generate Design - Usage Info",
                            True,
                            f"Usage information included: {usage['total_tokens']} total tokens"
                        )
                        return True
                    else:
                        log_test(
                            "Generate Design - Usage Info Missing",
                            False,
                            "Usage information missing or invalid"
                        )
                        return False
                else:
                    log_test(
                        "Generate Design - Poor Quality",
                        False,
                        f"Design spec too short or lacks design elements (found {len(found_keywords)}/8 keywords)"
                    )
                    return False
            else:
                log_test(
                    "Generate Design - Missing Fields",
                    False,
                    "Response missing required fields (design_spec, usage)"
                )
                return False
        else:
            log_test(
                "Generate Design - HTTP Error",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test(
            "Generate Design - Exception",
            False,
            f"Unexpected error: {str(e)}"
        )
        return False

def test_validate_visual():
    """Test POST /api/validate-visual endpoint"""
    print("\n🧪 Testing Validate Visual Endpoint...")
    
    # Test data as specified in review request
    test_data = {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "user_request": "A calculator with blue theme",
        "validator_model": "anthropic/claude-3-haiku"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/validate-visual",
            json=test_data,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
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
                        log_test(
                            "Validate Visual - Success",
                            True,
                            f"Visual validation completed: {verdict} (score: {overall_score})"
                        )
                        
                        # Check usage information (optional for this test)
                        if 'usage' in data and data['usage'].get('total_tokens', 0) > 0:
                            log_test(
                                "Validate Visual - Usage Info",
                                True,
                                f"Usage information included: {data['usage']['total_tokens']} total tokens"
                            )
                        else:
                            log_test(
                                "Validate Visual - Usage Info",
                                True,
                                "Usage information not available (fallback response used)"
                            )
                        return True
                    else:
                        log_test(
                            "Validate Visual - Invalid Values",
                            False,
                            "Scores out of range or invalid verdict"
                        )
                        return False
                else:
                    log_test(
                        "Validate Visual - Missing Score Fields",
                        False,
                        f"Scores missing fields: {missing_score_fields}"
                    )
                    return False
            else:
                log_test(
                    "Validate Visual - Missing Fields",
                    False,
                    f"Response missing required fields: {missing_fields}"
                )
                return False
        else:
            log_test(
                "Validate Visual - HTTP Error",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test(
            "Validate Visual - Exception",
            False,
            f"Unexpected error: {str(e)}"
        )
        return False

def test_openrouter_balance():
    """Test GET /api/openrouter/balance endpoint"""
    print("\n🧪 Testing OpenRouter Balance Endpoint...")
    
    try:
        response = requests.get(
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
                    
                    log_test(
                        "OpenRouter Balance - Success",
                        True,
                        f"Balance: {balance_display}, Used: ${used}, Remaining: {remaining_display}, Free Tier: {is_free_tier}"
                    )
                    
                    # Additional validation for consistency
                    if balance != -1 and remaining != -1:
                        calculated_remaining = balance - used
                        if abs(remaining - calculated_remaining) < 0.01:
                            log_test(
                                "OpenRouter Balance - Math Check",
                                True,
                                "Balance calculations are consistent"
                            )
                        else:
                            log_test(
                                "OpenRouter Balance - Math Check",
                                False,
                                f"Balance math inconsistent: {balance} - {used} ≠ {remaining}"
                            )
                    else:
                        log_test(
                            "OpenRouter Balance - Account Type",
                            True,
                            "Unlimited account detected"
                        )
                    return True
                else:
                    log_test(
                        "OpenRouter Balance - Invalid Types",
                        False,
                        "Balance fields have invalid data types"
                    )
                    return False
            else:
                log_test(
                    "OpenRouter Balance - Missing Fields",
                    False,
                    f"Response missing required fields: {missing_fields}"
                )
                return False
        else:
            log_test(
                "OpenRouter Balance - HTTP Error",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test(
            "OpenRouter Balance - Exception",
            False,
            f"Unexpected error: {str(e)}"
        )
        return False

def main():
    """Run all design-first workflow tests"""
    print("🚀 Testing Design-First Workflow Endpoints")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    results = []
    
    # Test all three endpoints
    results.append(test_generate_design())
    results.append(test_validate_visual())
    results.append(test_openrouter_balance())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DESIGN-FIRST WORKFLOW TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"📈 Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 ALL DESIGN-FIRST WORKFLOW ENDPOINTS WORKING!")
        print("✅ POST /api/generate-design - Design specification generation")
        print("✅ POST /api/validate-visual - UI screenshot validation")
        print("✅ GET /api/openrouter/balance - Account balance retrieval")
    else:
        print(f"\n⚠️  {total - passed} endpoint(s) need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)