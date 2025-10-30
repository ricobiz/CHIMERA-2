#!/usr/bin/env python3
"""
Final comprehensive test for image generation endpoint
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BACKEND_URL = "https://chimera-aios-3.preview.emergentagent.com"

class FinalImageTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.results = []
        
    async def test_scenario(self, name, request_data):
        """Test a specific scenario"""
        logger.info(f"🎨 Testing scenario: {name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                start_time = datetime.now()
                response = await client.post(
                    f"{self.backend_url}/api/generate-image",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"⏱️ {name} response time: {duration:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if image was generated successfully
                    is_image = data.get('is_image', False)
                    has_image_data = 'mockup_data' in data or 'image_url' in data
                    
                    if is_image and has_image_data:
                        image_data = data.get('mockup_data') or data.get('image_url')
                        logger.info(f"✅ {name} SUCCESS: Generated image ({len(str(image_data))} chars)")
                        
                        self.results.append({
                            "scenario": name,
                            "status": "SUCCESS",
                            "duration": duration,
                            "image_size": len(str(image_data)),
                            "has_usage": 'usage' in data or 'cost' in data
                        })
                        return True
                    else:
                        error_msg = data.get('error', 'Unknown error')
                        logger.warning(f"⚠️ {name} FAILED: {error_msg[:100]}...")
                        
                        self.results.append({
                            "scenario": name,
                            "status": "FAILED",
                            "duration": duration,
                            "error": error_msg[:200]
                        })
                        return False
                else:
                    error_text = response.text
                    logger.error(f"❌ {name} HTTP ERROR: {response.status_code}")
                    
                    self.results.append({
                        "scenario": name,
                        "status": "HTTP_ERROR",
                        "duration": duration,
                        "error": f"HTTP {response.status_code}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            logger.error(f"❌ {name} EXCEPTION: {str(e)}")
            
            self.results.append({
                "scenario": name,
                "status": "EXCEPTION",
                "error": str(e)
            })
            return False
    
    async def run_all_tests(self):
        """Run comprehensive image generation tests"""
        logger.info("🚀 Starting Final Image Generation Tests")
        logger.info("=" * 60)
        
        # Test scenarios
        scenarios = [
            {
                "name": "Basic fitness app dashboard",
                "request": {"prompt": "A modern fitness app dashboard with dark theme"}
            },
            {
                "name": "Simple geometric shape",
                "request": {"prompt": "A simple red circle on white background"}
            },
            {
                "name": "UI mockup with specific model",
                "request": {
                    "prompt": "A login screen for mobile app with blue gradient",
                    "model": "google/gemini-2.5-flash-image"
                }
            },
            {
                "name": "Complex scene",
                "request": {"prompt": "A futuristic dashboard with charts and graphs, neon colors"}
            }
        ]
        
        successful_tests = 0
        for scenario in scenarios:
            success = await self.test_scenario(scenario["name"], scenario["request"])
            if success:
                successful_tests += 1
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 FINAL TEST SUMMARY")
        logger.info("=" * 60)
        
        for result in self.results:
            if result['status'] == 'SUCCESS':
                logger.info(f"✅ {result['scenario']}: SUCCESS ({result['duration']:.2f}s, {result['image_size']} chars, usage: {result['has_usage']})")
            else:
                logger.info(f"❌ {result['scenario']}: {result['status']} - {result.get('error', 'No details')}")
        
        logger.info("=" * 60)
        logger.info(f"📈 Results: {successful_tests}/{len(scenarios)} scenarios passed")
        
        if successful_tests == len(scenarios):
            logger.info("🎉 ALL TESTS PASSED - Image generation endpoint is fully functional!")
        elif successful_tests > 0:
            logger.info("⚠️ PARTIAL SUCCESS - Some scenarios working")
        else:
            logger.error("❌ ALL TESTS FAILED - Image generation has issues")
        
        return {
            "total_scenarios": len(scenarios),
            "successful": successful_tests,
            "success_rate": (successful_tests / len(scenarios)) * 100,
            "results": self.results
        }

async def main():
    """Main test runner"""
    tester = FinalImageTester()
    results = await tester.run_all_tests()
    
    # Return exit code based on results
    if results['successful'] == 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())