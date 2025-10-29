#!/usr/bin/env python3
"""
Comprehensive test for image generation endpoint with multiple models
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
BACKEND_URL = "https://imagefix-debug.preview.emergentagent.com"

class ComprehensiveImageTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.results = []
        
        # Models to test
        self.models_to_test = [
            "google/gemini-2.5-flash-image",
            "google/gemini-2.5-flash-image-preview", 
            "openai/gpt-5-image-mini",
            "openai/gpt-5-image"
        ]
        
    async def test_model(self, model_name):
        """Test image generation with a specific model"""
        logger.info(f"🎨 Testing model: {model_name}")
        
        test_request = {
            "prompt": "A modern fitness app dashboard with dark theme",
            "model": model_name
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                start_time = datetime.now()
                response = await client.post(
                    f"{self.backend_url}/api/generate-image",
                    json=test_request,
                    headers={"Content-Type": "application/json"}
                )
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"⏱️ {model_name} response time: {duration:.2f}s")
                logger.info(f"📊 {model_name} status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if image was generated successfully
                    is_image = data.get('is_image', False)
                    has_image_data = 'mockup_data' in data or 'image_url' in data
                    
                    if is_image and has_image_data:
                        image_data = data.get('mockup_data') or data.get('image_url')
                        logger.info(f"✅ {model_name} SUCCESS: Generated image ({len(str(image_data))} chars)")
                        
                        self.results.append({
                            "model": model_name,
                            "status": "SUCCESS",
                            "duration": duration,
                            "image_size": len(str(image_data)),
                            "details": f"Generated image successfully in {duration:.2f}s"
                        })
                        return True
                    else:
                        error_msg = data.get('error', 'Unknown error')
                        logger.warning(f"⚠️ {model_name} FAILED: {error_msg[:100]}...")
                        
                        self.results.append({
                            "model": model_name,
                            "status": "FAILED",
                            "duration": duration,
                            "details": f"Image generation failed: {error_msg[:200]}"
                        })
                        return False
                else:
                    error_text = response.text
                    logger.error(f"❌ {model_name} HTTP ERROR: {response.status_code}")
                    
                    self.results.append({
                        "model": model_name,
                        "status": "HTTP_ERROR",
                        "duration": duration,
                        "details": f"HTTP {response.status_code}: {error_text[:200]}"
                    })
                    return False
                    
        except Exception as e:
            logger.error(f"❌ {model_name} EXCEPTION: {str(e)}")
            
            self.results.append({
                "model": model_name,
                "status": "EXCEPTION",
                "details": f"Exception: {str(e)}"
            })
            return False
    
    async def test_direct_openrouter_call(self):
        """Test direct OpenRouter API call to understand the response format"""
        logger.info("🔍 Testing direct OpenRouter API call...")
        
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("❌ No OpenRouter API key found")
            return
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Test with Gemini 2.5 Flash Image
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://chimera-aios.com",
                        "X-Title": "Chimera AIOS"
                    },
                    json={
                        "model": "google/gemini-2.5-flash-image",
                        "messages": [
                            {
                                "role": "user",
                                "content": "Generate a modern fitness app dashboard with dark theme"
                            }
                        ],
                        "modalities": ["image", "text"]
                    }
                )
                
                logger.info(f"📊 Direct API status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"🔍 Direct API response keys: {list(data.keys())}")
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        choice = data['choices'][0]
                        message = choice.get('message', {})
                        
                        logger.info(f"🔍 Message keys: {list(message.keys())}")
                        
                        # Check for images in different locations
                        if 'images' in message:
                            logger.info(f"✅ Found images in message: {len(message['images'])}")
                            logger.info(f"🔍 First image type: {type(message['images'][0])}")
                        elif 'content' in message:
                            content = message['content']
                            logger.info(f"🔍 Content type: {type(content)}, length: {len(str(content))}")
                            logger.info(f"🔍 Content preview: {str(content)[:200]}...")
                        
                        # Check if there are images at the root level
                        if 'images' in data:
                            logger.info(f"✅ Found images at root level: {len(data['images'])}")
                    
                    self.results.append({
                        "test": "Direct OpenRouter API",
                        "status": "SUCCESS",
                        "details": f"Response structure analyzed - keys: {list(data.keys())}"
                    })
                else:
                    error_text = response.text
                    logger.error(f"❌ Direct API error: {error_text}")
                    
                    self.results.append({
                        "test": "Direct OpenRouter API",
                        "status": "FAILED",
                        "details": f"HTTP {response.status_code}: {error_text[:200]}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Direct API exception: {str(e)}")
            
            self.results.append({
                "test": "Direct OpenRouter API",
                "status": "EXCEPTION",
                "details": f"Exception: {str(e)}"
            })
    
    async def run_all_tests(self):
        """Run comprehensive image generation tests"""
        logger.info("🚀 Starting Comprehensive Image Generation Tests")
        logger.info("=" * 70)
        
        # Test direct OpenRouter API first
        await self.test_direct_openrouter_call()
        
        # Test each model
        successful_models = []
        for model in self.models_to_test:
            success = await self.test_model(model)
            if success:
                successful_models.append(model)
        
        # Print summary
        logger.info("=" * 70)
        logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 70)
        
        for result in self.results:
            if 'model' in result:
                status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
                logger.info(f"{status_icon} {result['model']}: {result['status']} - {result['details']}")
            else:
                status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
                logger.info(f"{status_icon} {result['test']}: {result['status']} - {result['details']}")
        
        logger.info("=" * 70)
        logger.info(f"📈 Working models: {len(successful_models)}/{len(self.models_to_test)}")
        if successful_models:
            logger.info(f"✅ Successful models: {', '.join(successful_models)}")
        else:
            logger.warning("⚠️ No models successfully generated images")
        
        return {
            "successful_models": successful_models,
            "total_models": len(self.models_to_test),
            "results": self.results
        }

async def main():
    """Main test runner"""
    tester = ComprehensiveImageTester()
    results = await tester.run_all_tests()
    
    # Return exit code based on results
    if len(results['successful_models']) == 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())