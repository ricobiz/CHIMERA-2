#!/usr/bin/env python3
"""
Focused test for POST /api/generate-image endpoint
Testing the image generation functionality as requested in the review.
"""

import asyncio
import httpx
import json
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from environment
BACKEND_URL = "https://chimera-auto.preview.emergentagent.com"

class ImageGenerationTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.results = []
        
    async def test_image_generation_endpoint(self):
        """Test POST /api/generate-image endpoint with the specific request from review"""
        logger.info("🎨 Testing POST /api/generate-image endpoint...")
        
        test_request = {
            "prompt": "A modern fitness app dashboard with dark theme"
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"📤 Sending request to {self.backend_url}/api/generate-image")
                logger.info(f"📋 Request payload: {json.dumps(test_request, indent=2)}")
                
                start_time = datetime.now()
                response = await client.post(
                    f"{self.backend_url}/api/generate-image",
                    json=test_request,
                    headers={"Content-Type": "application/json"}
                )
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"⏱️ Response time: {duration:.2f}s")
                logger.info(f"📊 Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ SUCCESS: Image generation endpoint responded")
                    
                    # Check response structure as specified in review
                    logger.info("🔍 Checking response structure...")
                    
                    # Check for mockup_data field
                    if 'mockup_data' in data or 'image_url' in data:
                        image_data = data.get('mockup_data') or data.get('image_url')
                        logger.info(f"✅ Image data field present: {len(str(image_data))} characters")
                        
                        # Check if it's base64 image data
                        if isinstance(image_data, str) and image_data.startswith('data:image/png;base64,'):
                            logger.info("✅ Image data is properly formatted base64 PNG")
                            self.results.append({
                                "test": "Image data format",
                                "status": "PASS",
                                "details": f"Base64 PNG format, {len(image_data)} chars"
                            })
                        elif isinstance(image_data, str) and (image_data.startswith('http') or image_data.startswith('data:image')):
                            logger.info("✅ Image data is URL or data URI format")
                            self.results.append({
                                "test": "Image data format", 
                                "status": "PASS",
                                "details": f"URL/URI format, {len(image_data)} chars"
                            })
                        else:
                            logger.warning(f"⚠️ Image data format unexpected: {str(image_data)[:100]}...")
                            self.results.append({
                                "test": "Image data format",
                                "status": "FAIL", 
                                "details": f"Unexpected format: {type(image_data)} - {str(image_data)[:100]}"
                            })
                    else:
                        logger.error("❌ No mockup_data or image_url field in response")
                        self.results.append({
                            "test": "Image data field",
                            "status": "FAIL",
                            "details": "Missing mockup_data/image_url field"
                        })
                    
                    # Check for is_image field
                    if 'is_image' in data:
                        is_image = data['is_image']
                        logger.info(f"✅ is_image field present: {is_image}")
                        if is_image:
                            self.results.append({
                                "test": "is_image flag",
                                "status": "PASS",
                                "details": "is_image: true"
                            })
                        else:
                            logger.warning("⚠️ is_image is false - image generation may have failed")
                            self.results.append({
                                "test": "is_image flag",
                                "status": "FAIL",
                                "details": "is_image: false - generation failed"
                            })
                    else:
                        logger.warning("⚠️ No is_image field in response")
                        self.results.append({
                            "test": "is_image field",
                            "status": "FAIL", 
                            "details": "Missing is_image field"
                        })
                    
                    # Check for usage information
                    if 'usage' in data or 'cost' in data:
                        usage_info = data.get('usage') or data.get('cost')
                        logger.info(f"✅ Usage information present: {usage_info}")
                        self.results.append({
                            "test": "Usage information",
                            "status": "PASS",
                            "details": f"Usage data: {usage_info}"
                        })
                    else:
                        logger.warning("⚠️ No usage information in response")
                        self.results.append({
                            "test": "Usage information",
                            "status": "FAIL",
                            "details": "Missing usage/cost information"
                        })
                    
                    # Log full response structure (truncated)
                    logger.info(f"📋 Response keys: {list(data.keys())}")
                    for key, value in data.items():
                        if key in ['mockup_data', 'image_url'] and isinstance(value, str) and len(value) > 100:
                            logger.info(f"   {key}: {type(value)} ({len(value)} chars) - {str(value)[:50]}...")
                        else:
                            logger.info(f"   {key}: {value}")
                    
                    self.results.append({
                        "test": "Image generation endpoint",
                        "status": "PASS",
                        "details": f"Responded in {duration:.2f}s with {len(data)} fields"
                    })
                    
                else:
                    error_text = response.text
                    logger.error(f"❌ FAIL: Status {response.status_code}")
                    logger.error(f"❌ Error response: {error_text}")
                    self.results.append({
                        "test": "Image generation endpoint",
                        "status": "FAIL",
                        "details": f"HTTP {response.status_code}: {error_text}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Exception during image generation test: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Image generation endpoint",
                "status": "ERROR",
                "details": f"Exception: {str(e)}"
            })
    
    async def check_backend_logs(self):
        """Check backend logs for any errors during image generation"""
        logger.info("📋 Checking backend logs for image generation errors...")
        
        try:
            # Check recent backend logs
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "20", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                if log_content.strip():
                    logger.info("📋 Recent backend error logs:")
                    for line in log_content.strip().split('\n')[-10:]:  # Last 10 lines
                        if 'IMAGE GEN' in line or 'generate-image' in line or 'ERROR' in line:
                            logger.info(f"   {line}")
                else:
                    logger.info("✅ No recent error logs found")
            else:
                logger.warning("⚠️ Could not read backend logs")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not check backend logs: {str(e)}")
    
    async def run_all_tests(self):
        """Run all image generation tests"""
        logger.info("🚀 Starting Image Generation Endpoint Tests")
        logger.info("=" * 60)
        
        await self.test_image_generation_endpoint()
        await self.check_backend_logs()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        for result in self.results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            logger.info(f"{status_icon} {result['test']}: {result['status']} - {result['details']}")
        
        logger.info("=" * 60)
        logger.info(f"📈 Results: {passed} PASSED, {failed} FAILED, {errors} ERRORS")
        
        return {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "results": self.results
        }

async def main():
    """Main test runner"""
    tester = ImageGenerationTester()
    results = await tester.run_all_tests()
    
    # Return exit code based on results
    if results['failed'] > 0 or results['errors'] > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())